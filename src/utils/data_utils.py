"""
工具函数
"""
import pandas as pd

def load_commit_data(file_path):
    """
    加载提交数据
    """
    try:
        df = pd.read_csv(file_path)

        # 打印列信息调试
        print(f"[调试] 原始数据类型: {df['committed_date'].dtype}")
        print(f"[调试] 前几个值: {df['committed_date'].head()}")

        # 强制转换为 datetime，设置 errors='coerce' 将无效值转为 NaT
        df['committed_date'] = pd.to_datetime(df['committed_date'], utc=True, errors='coerce')

        # 检查转换结果
        print(f"[调试] 转换后数据类型: {df['committed_date'].dtype}")
        print(f"[调试] 空值数量: {df['committed_date'].isna().sum()}")

        # 删除转换失败的行
        original_count = len(df)
        df = df.dropna(subset=['committed_date'])
        print(f"[调试] 删除空值后行数: {len(df)}/{original_count}")

        return df
    except Exception as e:
        print(f"[错误] 加载数据失败: {e}")
        return pd.DataFrame()


def get_basic_statistics(df: pd.DataFrame) -> dict:
    """获取基本统计信息"""
    if df.empty or 'committed_date' not in df.columns:
        return {}

    stats = {
        'total_commits': len(df),
        'unique_authors': df['author_name'].nunique(),
        'time_span_days': (df['committed_date'].max() - df['committed_date'].min()).days,
        'first_commit': df['committed_date'].min().strftime('%Y-%m-%d'),
        'last_commit': df['committed_date'].max().strftime('%Y-%m-%d'),
        'total_changes': df['total_changes'].sum(),
        'avg_changes_per_commit': df['total_changes'].mean(),
    }

    return stats


def display_author_stats(df: pd.DataFrame, top_n: int = 10):
    """显示作者统计"""
    if df.empty:
        return

    author_stats = df.groupby('author_name').agg({
        'hash': 'count',
        'total_changes': 'sum'
    }).sort_values('hash', ascending=False)

    print(f"\n作者贡献排名 (前{top_n}名):")
    print("-" * 60)
    print(f"{'排名':<4} {'作者':<25} {'提交数':<8} {'变更行数':<12}")
    print("-" * 60)

    for i, (author, row) in enumerate(author_stats.head(top_n).iterrows(), 1):
        print(f"{i:<4} {author:<25} {row['hash']:<8} {row['total_changes']:<12,}")