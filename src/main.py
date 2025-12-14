import argparse
import os
import sys
from pathlib import Path

# 获取当前文件所在目录（src/）
current_dir = os.path.dirname(os.path.abspath(__file__))
# 获取项目根目录（django-evolution-analyzer/）
project_root = os.path.dirname(current_dir)
# 将项目根目录添加到 Python 路径
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from core.data_collector import GitDataCollector
from utils import data_utils
from config.settings import Config


def display_banner():
    """显示项目横幅"""
    print("=" * 70)
    print("🚀 Django Evolution Analyzer")
    print("=" * 70)


def collect_data(args):
    """收集数据命令"""
    print("\n数据收集")
    print("-" * 40)

    collector = GitDataCollector()

    # 1. 确保仓库存在
    if not collector.repo_path.exists():
        print("仓库不存在，开始克隆...")
        if not collector.clone_repository():
            print("克隆失败，请检查网络连接")
            return

    # 2. 获取提交总数
    total_commits = collector.get_commit_count()
    print(f"Django仓库总提交数: {total_commits:,}")

    # 3. 提取样本数据
    sample_size = min(args.sample, total_commits) if args.sample > 0 else 100
    commits = collector.extract_commits(sample_size)

    if not commits:
        print("未能获取提交数据")
        return

    # 4. 保存数据
    filename = f"django_commits_{len(commits)}.csv"
    save_path = collector.save_to_csv(commits, filename)

    if save_path:
        # 5. 显示基本统计
        df = data_utils.load_commit_data(Path(save_path))
        if df is not None:
            stats = data_utils.get_basic_statistics(df)
            print("\n数据概况:")
            for key, value in stats.items():
                print(f"  {key}: {value}")


def analyze_data(args):
    """分析数据命令"""
    print("\n数据分析")
    print("-" * 40)

    # 查找最新的CSV文件
    csv_files = list(Config.PROCESSED_DATA_DIR.glob("django_commits_*.csv"))

    if not csv_files:
        print("没有找到数据文件，请先运行: python main.py collect")
        return

    # 使用最新的文件
    latest_file = max(csv_files, key=lambda x: x.stat().st_mtime)
    print(f"分析文件: {latest_file.name}")

    df = data_utils.load_commit_data(latest_file)
    if df is None:
        return

    # 基本统计
    stats = data_utils.get_basic_statistics(df)
    print("\n基本统计:")
    for key, value in stats.items():
        print(f"  {key}: {value}")

    # 作者排名
    data_utils.display_author_stats(df, args.top)

    # 时间分析
    if not df.empty and 'committed_date' in df.columns:
        print(f"\n时间分布:")
        df['year'] = df['committed_date'].dt.year
        yearly_stats = df.groupby('year').size()
        print("  年度提交数:")
        for year, count in yearly_stats.items():
            print(f"    {year}: {count} 次提交")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="Django框架演化分析工具",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    subparsers = parser.add_subparsers(dest='command', help='可用命令')

    # collect命令
    collect_parser = subparsers.add_parser('collect', help='收集数据')
    collect_parser.add_argument(
        '--sample',
        type=int,
        default=100,
        help='采集的提交数量 (默认: 100)'
    )

    # analyze命令
    analyze_parser = subparsers.add_parser('analyze', help='分析数据')
    analyze_parser.add_argument(
        '--top',
        type=int,
        default=10,
        help='显示前N名作者 (默认: 10)'
    )

    # 解析参数
    args = parser.parse_args()

    display_banner()

    if args.command == 'collect':
        collect_data(args)
    elif args.command == 'analyze':
        analyze_data(args)
    else:
        # 如果没有命令，显示帮助
        parser.print_help()


if __name__ == "__main__":
    main()