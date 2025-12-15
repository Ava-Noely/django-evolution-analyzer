import sys
import pandas as pd

from src.core.contributor_analyzer import ContributorAnalyzer
from src.core.time_analyzer import TimeAnalyzer

sys.path.insert(0, 'src')
from src.core.data_collector import GitDataCollector

print("测试数据收集器...")
collector = GitDataCollector()
print(f"仓库路径: {collector.repo_path}")
print(f"路径存在: {collector.repo_path.exists()}")

if collector.repo_path.exists():
    count = collector.get_commit_count()
    print(f"提交总数: {count}")

    # 测试提取少量数据
    test_count = 100
    commits = collector.extract_commits(test_count)
    print(f"提取到 {len(commits)} 个提交")

    if commits and len(commits) > 0:
        commits_df = pd.DataFrame(commits)
        contributor_analyzer = ContributorAnalyzer()
        contributor_basic = contributor_analyzer.caculate_basic_metrics(commits_df)
        print(contributor_basic)
        contributor_core = contributor_analyzer.identify_core_contributor(commits_df,0.8)
        print(contributor_core)
        contributor_top = contributor_analyzer.get_top_contributors(commits_df,3)
        print(contributor_top)
else:
    print("仓库不存在，测试克隆...")
    success = collector.clone_repository()
    print(f"克隆结果: {success}")