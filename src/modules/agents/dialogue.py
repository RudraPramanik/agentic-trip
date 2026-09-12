from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal, TypedDict

from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command, interrupt

from src.modules.agents.intent import parse_intent
from src.modules.geo.scope import classify_scope
from src.modules.geo.service import GeoService
from src.modules.geo.types import (
    AskClarification,
    GeoCandidate,
    NeedsHitl,
    TripIntent,
    TripScope,
)
from src.ports import LlmGateway


class DialogueState(TypedDict, total=False):
    user_text: str
    intent: dict[str, Any] | None
    candidates: list[dict[str, Any]]
    chosen_candidate: dict[str, Any] | None
    trip_scope: dict[str, Any] | None
    hitl: dict[str, Any] | None
    assistant_message: str | None
    status: str  # ask | hitl | confirmed | error
    error: str | None


@dataclass
class DialogueOutcome:
    status: Literal["ask", "hitl", "confirmed", "error"]
    assistant_message: str
    hitl: dict[str, Any] | None = None
    trip_scope: dict[str, Any] | None = None
    intent: dict[str, Any] | None = None
    error_code: str | None = None


@dataclass
class DialogueDeps:
    llm: LlmGateway
    geo: GeoService


def _thread_config(session_id: str) -> dict[str, Any]:
    return {"configurable": {"thread_id": session_id}}


def build_dialogue_graph(
    deps: DialogueDeps,
    checkpointer: BaseCheckpointSaver | None = None,
) -> Any:
    """Compile LangGraph dialogue: parse → geocode → classify → HITL → confirm."""

    saver = checkpointer or InMemorySaver()

    async def node_parse_intent(state: DialogueState) -> dict[str, Any]:
        result = await parse_intent(state.get("user_text") or "", deps.llm)
        if isinstance(result, AskClarification):
            return {
                "status": "ask",
                "assistant_message": result.question,
                "intent": None,
                "trip_scope": None,
                "hitl": None,
            }
        return {
            "intent": result.to_dict(),
            "status": "running",
            "assistant_message": None,
        }

    async def node_geocode_search(state: DialogueState) -> dict[str, Any]:
        intent_data = state.get("intent") or {}
        query = str(intent_data.get("place_query") or "")
        result = deps.geo.geocode_search(query)
        candidates = [c.to_dict() for c in result.candidates]
        if result.count == 0:
            return {
                "candidates": [],
                "status": "ask",
                "assistant_message": (
                    f"I couldn't find a place matching “{query}”. "
                    "Try a different spelling or a nearby city — "
                    "I won't invent a country centroid."
                ),
                "hitl": None,
                "trip_scope": None,
            }
        if result.count > 1:
            hitl = NeedsHitl(
                kind="place",
                candidates=[
                    {
                        "choice_id": c["geo_id"],
                        "label": c["display_name"],
                        **c,
                    }
                    for c in candidates
                ],
                prompt=f"I found several matches for “{query}”. Which one did you mean?",
            ).to_hitl_projection()
            return {
                "candidates": candidates,
                "hitl": hitl,
                "status": "hitl_pending",
            }
        return {
            "candidates": candidates,
            "chosen_candidate": candidates[0],
            "hitl": None,
            "status": "running",
        }

    def node_request_hitl(state: DialogueState) -> dict[str, Any]:
        hitl = state.get("hitl") or {}
        # Interrupt surfaces candidates to the client; resume value is choice_id.
        choice = interrupt(hitl)
        choice_id = choice
        if isinstance(choice, dict):
            choice_id = choice.get("choice_id") or choice.get("text")
        choice_id = str(choice_id or "")

        candidates = list(state.get("candidates") or hitl.get("candidates") or [])
        chosen = None
        for c in candidates:
            if str(c.get("choice_id") or c.get("geo_id")) == choice_id:
                chosen = c
                break
        if chosen is None and candidates and hitl.get("kind") == "hubs":
            # Free-text / default hubs path — keep country candidate if present
            chosen = state.get("chosen_candidate") or (
                candidates[0] if candidates else None
            )

        if chosen is None:
            return {
                "status": "ask",
                "assistant_message": "I didn't recognize that choice. Please pick one of the options.",
                "hitl": hitl,
            }

        return {
            "chosen_candidate": chosen,
            "hitl": {**hitl, "status": "resolved", "choice_id": choice_id},
            "status": "running",
        }

    def node_classify_scope(state: DialogueState) -> dict[str, Any]:
        intent_data = state.get("intent") or {}
        chosen = state.get("chosen_candidate")
        if not chosen or not intent_data:
            return {
                "status": "error",
                "error": "missing_intent_or_candidate",
                "assistant_message": "Something went wrong classifying scope. Please try again.",
            }
        intent = TripIntent(
            place_query=str(intent_data.get("place_query") or ""),
            duration_days=intent_data.get("duration_days"),
            vibe=list(intent_data.get("vibe") or []),
            constraints=list(intent_data.get("constraints") or []),
            raw_text=str(intent_data.get("raw_text") or ""),
        )
        candidate = GeoCandidate.from_dict(chosen)
        outcome = classify_scope(intent, candidate)
        if isinstance(outcome, NeedsHitl):
            return {
                "hitl": outcome.to_hitl_projection(),
                "status": "hitl_pending",
                "candidates": outcome.candidates,
            }
        return {
            "trip_scope": outcome.to_dict(),
            "hitl": None,
            "status": "ready_confirm",
        }

    def node_confirm_scope(state: DialogueState) -> dict[str, Any]:
        scope = state.get("trip_scope")
        if not scope:
            return {
                "status": "error",
                "assistant_message": "No trip scope to confirm.",
                "error": "missing_trip_scope",
            }
        explain = scope.get("explain") or (
            f"Locked scope: {scope.get('kind')} — {scope.get('name')}."
        )
        return {
            "status": "confirmed",
            "assistant_message": explain,
            "hitl": {"status": "resolved"} if state.get("hitl") else None,
            "trip_scope": scope,
        }

    def route_after_parse(state: DialogueState) -> str:
        if state.get("status") == "ask":
            return END
        return "geocode_search"

    def route_after_geocode(state: DialogueState) -> str:
        if state.get("status") == "ask":
            return END
        if state.get("status") == "hitl_pending":
            return "request_hitl"
        return "classify_scope"

    def route_after_hitl(state: DialogueState) -> str:
        if state.get("status") == "ask":
            return END
        return "classify_scope"

    def route_after_classify(state: DialogueState) -> str:
        if state.get("status") == "hitl_pending":
            return "request_hitl"
        if state.get("status") == "error":
            return END
        return "confirm_scope"

    graph = StateGraph(DialogueState)
    graph.add_node("parse_intent", node_parse_intent)
    graph.add_node("geocode_search", node_geocode_search)
    graph.add_node("request_hitl", node_request_hitl)
    graph.add_node("classify_scope", node_classify_scope)
    graph.add_node("confirm_scope", node_confirm_scope)

    graph.add_edge(START, "parse_intent")
    graph.add_conditional_edges("parse_intent", route_after_parse, path_map=["geocode_search", END])
    graph.add_conditional_edges(
        "geocode_search",
        route_after_geocode,
        path_map=["request_hitl", "classify_scope", END],
    )
    graph.add_conditional_edges(
        "request_hitl",
        route_after_hitl,
        path_map=["classify_scope", END],
    )
    graph.add_conditional_edges(
        "classify_scope",
        route_after_classify,
        path_map=["request_hitl", "confirm_scope", END],
    )
    graph.add_edge("confirm_scope", END)

    return graph.compile(checkpointer=saver)


class DialogueRunner:
    """Facade over the compiled dialogue graph for ChatService."""

    def __init__(
        self,
        deps: DialogueDeps,
        checkpointer: BaseCheckpointSaver | None = None,
    ) -> None:
        self._deps = deps
        self._checkpointer = checkpointer or InMemorySaver()
        self._graph = build_dialogue_graph(deps, self._checkpointer)

    @property
    def checkpointer(self) -> BaseCheckpointSaver:
        return self._checkpointer

    async def run_turn(self, session_id: str, text: str) -> DialogueOutcome:
        config = _thread_config(session_id)
        try:
            result = await self._graph.ainvoke(
                {
                    "user_text": text,
                    "status": "running",
                    "assistant_message": None,
                    "hitl": None,
                    "trip_scope": None,
                    "intent": None,
                    "candidates": [],
                    "chosen_candidate": None,
                    "error": None,
                },
                config=config,
            )
        except Exception as exc:  # noqa: BLE001
            # Checkpoint / graph failures stay honest.
            return DialogueOutcome(
                status="error",
                assistant_message=(
                    "Dialogue checkpoint or graph failed. "
                    "Your session is intact — try again."
                ),
                error_code="checkpoint_or_graph_error",
            )

        return self._outcome_from_state(result, config)

    async def resume(self, session_id: str, choice_id: str | None, text: str | None) -> DialogueOutcome:
        config = _thread_config(session_id)
        resume_value: Any = choice_id or text or ""
        try:
            result = await self._graph.ainvoke(
                Command(resume=resume_value),
                config=config,
            )
        except Exception:  # noqa: BLE001
            return DialogueOutcome(
                status="error",
                assistant_message=(
                    "Could not resume HITL (checkpoint unavailable). "
                    "Please send your trip prompt again."
                ),
                error_code="checkpoint_unavailable",
            )
        return self._outcome_from_state(result, config)

    def _outcome_from_state(
        self, result: dict[str, Any], config: dict[str, Any]
    ) -> DialogueOutcome:
        # Detect open interrupt via graph state.
        try:
            snap = self._graph.get_state(config)
            if snap.interrupts:
                payload = snap.interrupts[0].value
                if not isinstance(payload, dict):
                    payload = {"kind": "place", "candidates": [], "status": "pending"}
                payload = {**payload, "status": "pending"}
                return DialogueOutcome(
                    status="hitl",
                    assistant_message=str(
                        payload.get("prompt")
                        or "Please pick an option to continue."
                    ),
                    hitl=payload,
                    intent=result.get("intent"),
                )
        except Exception:  # noqa: BLE001
            pass

        status = str(result.get("status") or "error")
        message = str(result.get("assistant_message") or "")
        if status == "confirmed":
            return DialogueOutcome(
                status="confirmed",
                assistant_message=message or "Scope confirmed.",
                trip_scope=result.get("trip_scope"),
                hitl=result.get("hitl"),
                intent=result.get("intent"),
            )
        if status == "ask":
            return DialogueOutcome(
                status="ask",
                assistant_message=message or "Could you clarify?",
                intent=result.get("intent"),
            )
        if status == "hitl_pending" or result.get("hitl", {}).get("status") == "pending":
            hitl = result.get("hitl") or {"status": "pending", "candidates": []}
            return DialogueOutcome(
                status="hitl",
                assistant_message=message
                or str(hitl.get("prompt") or "Please pick an option."),
                hitl=hitl,
                intent=result.get("intent"),
            )
        return DialogueOutcome(
            status="error",
            assistant_message=message or "Dialogue turn failed.",
            error_code=str(result.get("error") or "dialogue_error"),
            intent=result.get("intent"),
        )


def build_postgres_checkpointer(database_url: str) -> BaseCheckpointSaver:
    """Create a Postgres checkpointer; caller should handle setup failures honestly."""
    from langgraph.checkpoint.postgres import PostgresSaver

    sync_url = database_url.replace("postgresql+asyncpg://", "postgresql://")
    # from_conn_string returns a context manager in some versions; open eagerly.
    cm = PostgresSaver.from_conn_string(sync_url)
    saver = cm.__enter__()
    saver.setup()
    return saver


def build_checkpointer(database_url: str | None, *, prefer_postgres: bool = True) -> BaseCheckpointSaver:
    if prefer_postgres and database_url:
        try:
            return build_postgres_checkpointer(database_url)
        except Exception:
            # Fail soft to memory — ChatService still persists hitl on session.
            return InMemorySaver()
    return InMemorySaver()
