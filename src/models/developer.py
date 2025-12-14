from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional
from .commit import Commit


@dataclass
class Developer:
    """开发者数据模型"""

    name: str
    email: str
    commits: List[Commit] = None

    def __post_init__(self):
        if self.commits is None:
            self.commits = []

    @property
    def total_commits(self) -> int:
        return len(self.commits)