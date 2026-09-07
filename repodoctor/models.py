from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class Check:
    id: str
    category: str
    severity: str
    passed: bool
    message: str
    details: List[str] = field(default_factory=list)
    skipped: bool = False


@dataclass
class Report:
    repo_path: str
    score: int
    checks: List[Check]
    has_critical_failure: bool
