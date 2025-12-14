"""
数据模型定义
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional


@dataclass
class Commit:
    """Git提交数据模型"""

    # 基础信息
    hash: str
    author_name: str
    author_email: str
    committed_date: datetime
    message: str

    # 变更统计
    insertions: int = 0
    deletions: int = 0
    files_changed: int = 0

    # 计算属性
    @property
    def total_changes(self) -> int:
        return self.insertions + self.deletions

    @property
    def net_changes(self) -> int:
        return self.insertions - self.deletions

    @property
    def short_hash(self) -> str:
        return self.hash[:8]

    @property
    def year_month(self) -> str:
        return self.committed_date.strftime("%Y-%m")

    @property
    def hour_of_day(self) -> int:
        return self.committed_date.hour

    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            'hash': self.hash,
            'author_name': self.author_name,
            'author_email': self.author_email,
            'committed_date': self.committed_date.isoformat(),
            'message': self.message,
            'insertions': self.insertions,
            'deletions': self.deletions,
            'files_changed': self.files_changed,
            'year_month': self.year_month,
            'hour_of_day': self.hour_of_day,
            'total_changes': self.total_changes,
            'net_changes': self.net_changes
        }