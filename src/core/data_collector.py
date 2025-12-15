"""
数据收集器 - 使用GitPython
"""
import subprocess
import json
from datetime import datetime
from typing import List
import pandas as pd

# 导入在同一目录下的模块
from config.settings import Config
from src.models.commit import Commit

class GitDataCollector:
    """Git数据收集器"""

    def __init__(self):
        self.repo_path = Config.DJANGO_REPO_PATH

    def clone_repository(self) -> bool:
        """克隆Django仓库"""
        if self.repo_path.exists():
            print(f"⭐️ 仓库已存在: {self.repo_path}")
            return True

        print(f"⭐️ 开始克隆Django仓库...")

        try:
            repo_url = Config.DJANGO_REPO_URL

            result = subprocess.run(
                ["git", "clone", repo_url, str(self.repo_path)],
                capture_output=True,
                text=True,
                encoding = 'utf-8',
                timeout=300
            )

            if result.returncode == 0:
                print("✅ 克隆成功")
                return True
            else:
                print(f"❌ 克隆失败: {result.stderr[:200]}")# 显示错误内容
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
            print("❌ 仓库不存在")
            return []

        print(f"⭐️ 正在提取 {max_commits} 个提交...")

        # 使用git log命令
        cmd = [
            "git", "-C", str(self.repo_path), "log",
            f"--max-count={max_commits}",
            "--pretty=format:%H|%an|%ae|%ad|%s",
            "--date=iso-strict",
            "--numstat",
            "--no-merges"
        ]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            commits = self._parse_git_output(result.stdout)
            print(f"✅ 提取 {len(commits)} 个提交")
            return commits

        except Exception as e:
            print(f"❌ 提取失败: {e}")
            return []

    def _parse_git_output(self, output: str) -> List[Commit]:
        """解析git log输出"""
        commits = []
        lines = output.strip().split('\n')

        i = 0
        while i < len(lines):
            line = lines[i].strip()

            if line and '|' in line:
                # 解析提交信息行
                parts = line.split('|', 4)  # 最多分割4次，保留message中的'|'

                if len(parts) >= 5:
                    commit_hash, author_name, author_email, date_str, message = parts

                    i += 1
                    insertions = 0
                    deletions = 0
                    files_changed = 0

                    # 解析numstat数据
                    while i < len(lines) and lines[i].strip() and '|' not in lines[i]:
                        numstat_line = lines[i].strip()
                        if '\t' in numstat_line:
                            parts = numstat_line.split('\t')
                            if len(parts) == 3:
                                ins_str, del_str, _ = parts
                                # 处理数字或'-'（二进制文件）
                                if ins_str.isdigit():
                                    insertions += int(ins_str)
                                if del_str.isdigit():
                                    deletions += int(del_str)
                                files_changed += 1
                        i += 1

                    # 创建Commit对象
                    try:
                        # 处理时区（Z表示UTC）
                        if date_str.endswith('Z'):
                            date_str = date_str[:-1] + '+00:00'

                        commit_date = datetime.fromisoformat(date_str)
                        commit = Commit(
                            hash=commit_hash,
                            author_name=author_name,
                            author_email=author_email,
                            committed_date=commit_date,
                            message=message,
                            insertions=insertions,
                            deletions=deletions,
                            files_changed=files_changed
                        )
                        commits.append(commit)
                    except ValueError as e:
                        print(f"[收集器] ⚠️ 日期解析失败 {date_str}: {e}")
                        # 继续处理下一个提交
                        i += 1
                else:
                    i += 1
            else:
                i += 1

        return commits

    def save_to_csv(self, commits: List[Commit], filename: str = "commits.csv") -> str:
        """保存提交数据到CSV"""
        if not commits:
            print("[收集器] ⚠️ 没有数据可保存")
            return ""

        # 转换为DataFrame
        data = [commit.to_dict() for commit in commits]
        df = pd.DataFrame(data)

        # 保存
        save_path = Config.PROCESSED_DATA_DIR / filename
        df.to_csv(save_path, index=False, encoding='utf-8')

        print(f"[收集器] ✅ 数据已保存: {save_path}")
        return str(save_path)