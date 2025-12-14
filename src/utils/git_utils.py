import subprocess
import json
from pathlib import Path
from datetime import datetime
from typing import List, Optional, Generator
import pandas as pd
from tqdm import tqdm

from ..models.commit import Commit
from config.settings import Config
import os


class GitDataCollector:
    """Git数据收集器 - 使用GitPython库"""

    def __init__(self, repo_path: Optional[Path] = None):
        self.repo_path = repo_path or Config.DJANGO_REPO_PATH

    def clone_repository(self) -> bool:
        """克隆Django仓库（如果不存在）"""
        if self.repo_path.exists():
            print(f"仓库已存在: {self.repo_path}")
            return True

        print(f"开始克隆Django仓库...")
        print(f"源: {Config.DJANGO_REPO_URL}")
        print(f"目标: {self.repo_path}")

        repo_url = Config.DJANGO_REPO_URL

        try:
            # 执行git命令
            result = subprocess.run(
                ["git", "clone", repo_url, str(self.repo_path)],
                capture_output=True,
                text=True,
                timeout=600  # 10分钟超时
            )

            if result.returncode == 0:
                print("✅ Django仓库克隆成功")
                return True
            else:
                print(f"❌ 克隆失败: {result.stderr[:200]}")
                return False

        except subprocess.TimeoutExpired:
            print("❌ 克隆超时!")
            return False
        except Exception as e:
            print(f"❌ 克隆异常: {e}")
            return False

    def get_commit_count(self) -> int:
        """获取总提交数"""
        if not self.repo_path.exists():
            return 0

        cmd = ["git", "-C", str(self.repo_path), "rev-list", "--count", "HEAD"]
        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode == 0:
            return int(result.stdout.strip())
        return 0

    def extract_commits(self, max_commits: int = 100) -> List[Commit]:
        """提取提交数据"""
        if not self.repo_path.exists():
            print("❌ 仓库不存在，请先克隆")
            return []

        print(f"正在提取提交数据（最多 {max_commits} 个）...")

        # 使用git log命令获取数据
        cmd = [
            "git", "-C", str(self.repo_path), "log",
            f"--max-count={max_commits}",
            "--pretty=format:COMMIT_START%n%H|%an|%ae|%ad|%s",
            "--date=iso-strict",
            "--numstat",
            "--no-merges"
        ]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            commits = self._parse_git_output(result.stdout)
            print(f"✅ 成功提取 {len(commits)} 个提交")
            return commits

        except Exception as e:
            print(f"❌ 提取提交失败: {e}")
            return []

    def _parse_git_output(self, output: str) -> List[Commit]:
        """解析git log输出"""
        commits = []
        lines = output.split('\n')

        i = 0
        while i < len(lines):
            if lines[i] == "COMMIT_START" and i + 1 < len(lines):
                i += 1
                # 解析提交信息行
                commit_line = lines[i]
                parts = commit_line.split('|')

                if len(parts) >= 5:
                    commit_hash = parts[0]
                    author_name = parts[1]
                    author_email = parts[2]
                    date_str = parts[3]
                    message = '|'.join(parts[4:])  # 消息可能包含'|'

                    i += 1
                    # 解析numstat数据
                    insertions = 0
                    deletions = 0
                    file_stats = {}

                    while i < len(lines) and lines[i] and lines[i] != "COMMIT_START":
                        if lines[i] and not lines[i].startswith('-') and '\t' in lines[i]:
                            parts = lines[i].split('\t')
                            if len(parts) == 3:
                                ins_str, del_str, filename = parts

                                # 处理特殊字符（-表示二进制文件）
                                ins = int(ins_str) if ins_str.isdigit() else 0
                                del_val = int(del_str) if del_str.isdigit() else 0

                                insertions += ins
                                deletions += del_val
                                file_stats[filename] = {
                                    "insertions": ins,
                                    "deletions": del_val
                                }
                        i += 1

                    # 创建Commit对象
                    try:
                        commit_date = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                        commit = Commit(
                            hash=commit_hash,
                            author_name=author_name,
                            author_email=author_email,
                            committed_date=commit_date,
                            message=message,
                            insertions=insertions,
                            deletions=deletions,
                            files_changed=len(file_stats),
                            file_stats=file_stats
                        )
                        commits.append(commit)
                    except ValueError as e:
                        print(f"❌ 解析日期失败 {date_str}: {e}")
                        continue
                else:
                    i += 1
            else:
                i += 1

        return commits

    def save_to_csv(self, commits: List[Commit], filename: str = "commits.csv"):
        """保存提交数据到CSV"""
        if not commits:
            print("❌ 没有数据可保存")
            return

        # 转换为DataFrame
        data = [commit.to_dict() for commit in commits]
        df = pd.DataFrame(data)

        # 保存
        save_path = Config .PROCESSED_DATA_DIR / filename
        df.to_csv(save_path, index=False, encoding='utf-8')

        print(f"✅ 数据已保存到: {save_path}")
        print(f"数据统计:")
        print(f"时间范围: {df['committed_date'].min()} 到 {df['committed_date'].max()}")
        print(f"作者数量: {df['author_name'].nunique()}")
        print(f"总提交数: {len(df)}")
        print(f"总变更行数: {df['total_changes'].sum():,}")

        return save_path