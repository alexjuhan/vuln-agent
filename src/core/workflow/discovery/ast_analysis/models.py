from dataclasses import dataclass
from typing import Set, List

@dataclass
class DataFlow:
    source: str
    sink: str
    path: List[str]
    variables_involved: Set[str]

    def to_dict(self) -> dict:
        """Convert the DataFlow object to a dictionary representation"""
        return {
            'source': self.source,
            'sink': self.sink,
            'path': self.path,
            'variables_involved': list(self.variables_involved)  # Convert set to list for JSON serialization
        }

    def __repr__(self):
        return f"DataFlow(source='{self.source}', sink='{self.sink}', path={self.path}, variables_involved={self.variables_involved})"

@dataclass
class TrustBoundary:
    name: str
    entry_points: Set[str]
    exit_points: Set[str]
    sanitizers: Set[str] 