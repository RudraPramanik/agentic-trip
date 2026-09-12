from dataclasses import dataclass


@dataclass(frozen=True)
class LlmUnavailable:
    role: str
    reason: str = "unconfigured"
