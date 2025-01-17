from dataclasses import dataclass
from typing import Set, List

@dataclass
class DataFlow:
    source: str
    sink: str
    path: List[str]
    variables_involved: Set[str]

@dataclass
class TrustBoundary:
    name: str
    entry_points: Set[str]
    exit_points: Set[str]
    sanitizers: Set[str] 