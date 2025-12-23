from datetime import datetime

import pandas as pd


class ContributorAnalyzer:
    """
    基础贡献指标计算
    1.提交次数
    2.改变总行数
    3.净改变行数
    4.平均每次提交变更行数
    5.从首次提交到最后一次提交的时间跨度
    """
    def calculate_basic_metrics(self, commits_df):
        if commits_df.empty:
            return pd.DataFrame

        # 确保必要列存在
        required_column = ['author_name','insertions','deletions']
        if not all(col in commits_df.columns for col in required_column):
            raise ValueError(f"DataFrame必须包含以下列：{required_column}")

        # 确保日期为datetime类型
        if not pd.api.types.is_datetime64_any_dtype(commits_df['committed_date']):
            commits_df['committed_date'] = pd.to_datetime(commits_df['committed_date'], utc=True)
        has_date = 'committed_date' in commits_df.columns

        """按作者分组并计算相关指标"""
        def calculate_metrics(group):
            metrics = {
                'commit_count': len(group),
                'total_lines_changed': group['insertions'].sum()+group['deletions'].sum(),
                'net_lines_changed': group['insertions'].sum()-group['deletions'].sum(),
                'total_insertions': group['insertions'].sum(),
                'total_deletions': group['deletions'].sum()
            }

            # 计算平均每次提交变更行数
            if metrics['commit_count'] > 0:
                metrics['avg_lines_per_commit'] = metrics['total_lines_changed']/metrics['commit_count']
            else:
                metrics['avg_lines_per_commit'] = 0

            # 计算时间跨度
            if has_date:
                dates = pd.to_datetime(group['committed_date'])
                metrics['first_commit_date'] = dates.min()
                metrics['last_commit_date'] = dates.max()
                metrics['contribution_span_days'] = (dates.max()-dates.min()).days
            else:
                metrics['first_commit_date'] = pd.NaT
                metrics['last_commit_date'] = pd.NaT
                metrics['contribution_span_days'] = 0

            return pd.Series(metrics)

        # 按照作者名字分组
        result = commits_df.groupby('author_name').apply(calculate_metrics).reset_index()

        # 计算贡献百分比
        total_commits = result['commit_count'].sum()
        total_lines = result['total_lines_changed'].sum()

        if total_commits>0:
            result['commit_percentage'] = (result['commit_count']/total_commits*100).round(2)
        else:
            result['commit_percentage'] = 0

        if total_lines>0:
            result['lines_percentage'] = (result['total_lines_changed']/total_lines*100).round(2)
        else:
            result['lines_percentage'] = 0

        # 按照提交数量降序排列
        result = result.sort_values('commit_count',ascending = False).reset_index(drop=True)

        return result

    def identify_core_contributor(self, commits_df,threshold_percent=0.0):
      """识别核心贡献者"""
      if commits_df.empty:
          return [], 0.0

      metrics_df = self.caculate_basic_metrics(commits_df)
      if metrics_df.empty:
          return [], 0.0

      # 按照提交数量降序排列
      sorted_metrics = metrics_df.sort_values('commit_count',ascending = False).reset_index(drop=True)

      total_commits = sorted_metrics['commit_count'].sum()
      sorted_metrics['cumulative_commits'] = sorted_metrics['commit_count'].cumsum()
      sorted_metrics['cumulative_percentage'] = (sorted_metrics['cumulative_commits']/total_commits*100).round(2)

      threshold_percent_pct = threshold_percent*100

      # 找到第一个达到或超过阈值的行
      core_contributors_mask = sorted_metrics['cumulative_percentage'] >= threshold_percent_pct
      if core_contributors_mask.any():
          first_core_idx = sorted_metrics[core_contributors_mask].index[0]
          core_contributors = sorted_metrics.loc[:first_core_idx, 'author_name'].tolist()

          core_total_commits = sorted_metrics.loc[:first_core_idx, 'commit_count'].sum()
          core_contribution_percentage = (core_total_commits/total_commits*100).round(2)
          core_contributors_percentage = len(core_contributors)/len(sorted_metrics)

          print("核心贡献者分析结果：")
          print(f"- 总开发者数量：{len(sorted_metrics)}")
          print(f"- 核心贡献者数量：{len(core_contributors)}（{core_contributors_percentage:.1%}）")
          print(f"- 核心贡献者提交占比： {core_contribution_percentage}%")
          print(f"- 目标阈值：{threshold_percent_pct}%")

          return core_contributors, core_contribution_percentage/100
      else:
          print(f"未达到阈值{threshold_percent_pct}%!")
          return [], 0.0

    """获取Top N的贡献者"""
    def get_top_contributors(self, commits_df, top_n=10, metric='commit_count'):
      metrics_df = self.caculate_basic_metrics(commits_df)

      if metrics_df.empty:
          return pd.DataFrame()

      valid_metric = ['commit_count','total_lines_changed','net_lines_changed']
      if metric not in valid_metric:
          raise ValueError(f"metric必须是以下之一:{valid_metric}")

      top_contributors = metrics_df.sort_values(metric,ascending=False).head(top_n)
      return top_contributors


class ContributorLifeCycleAnalyzer:
    def analyze_participation_pattern(self, commits_df):
        """
        分析开发者参与程度
        计算每位开发者活跃天数并以此分类
        统计各类别人数和贡献占比
        """
        if commits_df.empty:
            return pd.DataFrame(),{}

        # 检查必要列
        required_columns = ['author_name','committed_date']
        if not all(col in commits_df.columns for col in required_columns):
            missing_cols = [col for col in commits_df.columns if col not in required_columns]
            return ValueError(f"缺少必要列：{missing_cols}")

        df = commits_df.copy()
        df['committed_date'] = pd.to_datetime(df['committed_date'], errors='coerce')

        # 按开发者分组计算指标
        developer_stats = []
        for author, group in df.groupby('author_name'):
            commit_dates = group['committed_date'].dropna()

            if len(commit_dates) == 0:
                continue

            commit_count = len(group)
            first_commit = commit_dates.min()
            last_commit = commit_dates.max()
            active_days = (last_commit - first_commit).days
            active_months = active_days/30.44

            # 按照贡献时间将贡献者分类
            if commit_count == 1:
                contributor_type = '一次性贡献者'
            elif active_months <=6:
                contributor_type = '短期贡献者'
            elif active_months <=24:
                contributor_type = '中期贡献者'
            else:
                contributor_type = '长期贡献者'

            developer_stats.append({
                'author_name': author,
                'commit_count': commit_count,
                'first_commit': first_commit,
                'last_commit': last_commit,
                'active_days': active_days,
                'active_months': active_months,
                'contributor_type': contributor_type,
                'insertions': group['insertions'].sum() if 'insertions' in group.columns else 0,
                'deletions': group['deletions'].sum() if 'deletions' in group.columns else 0
            })

        stats_df = pd.DataFrame(developer_stats)

        if stats_df.empty:
            return pd.DataFrame(),{}

        # 按照活跃天数降序排序
        stats_df = stats_df.sort_values('active_days', ascending=False).reset_index(drop=True)

        # 按类别统计
        category_stats = {}
        total_developers = len(stats_df)
        total_commits = stats_df['commit_count'].sum()
        total_lines_changed = stats_df['insertions'].sum() + stats_df['deletions'].sum()

        categories = ['一次性贡献者','短期贡献者','中期贡献者','长期贡献者']
        for category in categories:
            cat_df = stats_df[stats_df['contributor_type'] == category]

            if len(cat_df) > 0:
                category_stats[category] = {
                    'developer_count': len(cat_df),
                    'developer_percentage': round(len(cat_df)/total_developers*100, 2),
                    'total_commits': int(cat_df['commit_count'].sum()),
                    'avg_commits_per_dev': round(cat_df['commit_count'].mean(),1),
                    'total_lines_changed': int(cat_df['insertions'].sum()+cat_df['deletions'].sum()),
                    'lines_percentage': round((cat_df['insertions'].sum()+cat_df['deletions'].sum())/
                                              total_lines_changed*100,2) if total_lines_changed >0 else 0,
                    'avg_active_months': round(cat_df['active_months'].mean(),1)
                }
            else:
                category_stats[category] = {
                    'developer_count': 0,
                    'developer_percentage': 0,
                    'total_commits': 0,
                    'avg_commits_per_dev': 0,
                    'total_lines_changed': 0,
                    'lines_percentage': 0,
                    'avg_active_months': 0
                }

        overall_stats = {
            'total_developers': total_developers,
            'total_commits': total_commits,
            'avg_commits_per_dev': round(total_commits/total_developers,1),
            'avg_active_months': round(stats_df['active_months'].mean(),1),
            'median_active_months': round(stats_df['active_months'].median(),1),
            'most_common_category': stats_df['contributor_type'].mode().iloc[0] if not
                                stats_df['contributor_type'].mode().empty else 'N/A'
        }

        category_stats['overall'] = overall_stats

        return stats_df, category_stats

    def calculate_retention_rate(self, commits_df, year_window=1):
        """
        计算贡献者留存率：新贡献者x年后还在贡献吗？
        1.识别每年新加入的贡献者
        2.追踪他们year_window年后的贡献情况
        3.计算留存比例
        """
        if commits_df.empty:
            return {}

        # 检查必要列
        required_columns = ['author_name', 'committed_date']
        if not all(col in commits_df.columns for col in required_columns):
            missing_cols = [col for col in required_columns if col not in commits_df.columns]
            raise ValueError(f"缺少必要列：{missing_cols}")

        df = commits_df.copy()
        df['committed_date'] = pd.to_datetime(df['committed_date'], errors='coerce', utc=True)
        df['committed_date'] = df['committed_date'].dt.tz_convert(None)
        df = df.dropna(subset=['committed_date'])

        # 按照作者和日期排序
        df = df.sort_values(['author_name', 'committed_date'])

        # 识别每个作者的首次提交年份
        author_first_dates = df.groupby(['author_name'])['committed_date'].min()

        all_dates = df['committed_date']
        min_date = all_dates.min()
        max_date = all_dates.max()
        min_year = min_date.year
        max_year = max_date.year

        print(f"数据集时间范围：{min_date.date()}到{max_date.date()}")

        retention_stats = {}

        for start_year in range(min_year,max_year-year_window+1):
            # 识别该年份的新贡献者
            year_start = datetime(start_year, 1, 1)
            year_end = datetime(start_year+1, 1, 1)
            new_authors = [
                author for author, first_date in author_first_dates.items()
                if year_start <= first_date < year_end
            ]

            if not new_authors:
                continue

            retention_count = 0
            for author in new_authors:
                # 获取该作者所有提交日期
                author_commits = df[df['author_name'] == author]['committed_date']

                end_window = datetime(start_year+year_window,1,1)

                # 检查作者在目标年份是否有提交
                has_commits_in_target_year = any(
                    (commit_date >= end_window) for commit_date in author_commits
                )

                if has_commits_in_target_year:
                    retention_count += 1

            new_count = len(new_authors)
            retention_rate = round(retention_count/new_count*100, 2) if new_count>0 else 0

            retention_stats[start_year] = {
                'new_contributions': new_count,
                'retained_count': retention_count,
                'retention_rate': retention_rate,
                'target_year': start_year + year_window
            }

        # 如果没有足够的年份数据
        if not retention_stats and len(df) > 0:
            all_authors = df['author_name'].unique()

            authors_with_multiple_commit = 0
            for author in all_authors:
                author_commits = df[df['author_name'] == author]
                if len(author_commits) >= 2:
                    authors_with_multiple_commit += 1

            total_authors = len(all_authors)
            overall_retention_rate = round(authors_with_multiple_commit / total_authors*100, 2) if total_authors > 0 else 0

            current_year = datetime.now().year
            retention_stats['overall'] = {
                'new_contributions': total_authors,
                'retained_count': authors_with_multiple_commit,
                'retention_rate': overall_retention_rate,
                'target_year': '所有年份',
                'description': f"基于{year_window}年时间窗口的总体留存率"
            }

        return retention_stats