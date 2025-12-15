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
    def caculate_basic_metrics(selfself,commits_df):
        if commits_df.empty:
            return pd.DataFrame

        # 确保必要列存在
        required_column = ['author_name','insertions','deletions']
        if not all(col in commits_df.columns for col in required_column):
            raise ValueError(f"DataFrame必须包含以下列：{required_column}")

        has_date = 'commit_date' in commits_df.columns

        """按作者分组并计算相关指标"""
        def calculate_metrics(group):
            metrics = {
                'commit_count': len(group),
                'total_lines_changed': group['insertions'].sum()+group['deletions'].sum(),
                'net_lines_changed': group['insertions'].sum()-group['deletions'].sum(),
                'total_insertions': group['insertions'].sum(),
                'total_insertions': group['deletions'].sum()
            }

            # 计算平均每次提交变更行数
            if metrics['commit_count'] > 0:
                metrics['avg_lines_per_commit'] = metrics['total_lines_changed']/metrics['commit_count']
            else:
                metrics['avg_lines_per_commit'] = 0

            # 计算时间跨度
            if has_date:
                dates = pd.to_datetime(group['commit_Date'])
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
      core_contributiors_mask = sorted_metrics['cumulative_percentage'] >= threshold_percent_pct
      if core_contributiors_mask.any():
          first_core_idx = sorted_metrics[core_contributiors_mask].index[0]
          core_contributiors = sorted_metrics.loc[:first_core_idx, 'author_name'].tolist()

          core_total_commits = sorted_metrics.loc[:first_core_idx, 'commit_count'].sum()
          core_contribution_percentage = (core_total_commits/total_commits*100).round(2)
          core_contributors_percentage = len(core_contributiors)/len(sorted_metrics)

          print("核心贡献者分析结果：")
          print(f"- 总开发者数量：{len(sorted_metrics)}")
          print(f"- 核心贡献者数量：{len(core_contributiors)}（{core_contributors_percentage:.1%}）")
          print(f"- 核心贡献者提交占比： {core_contribution_percentage}%")
          print(f"- 目标阈值：{threshold_percent_pct}%")

          return core_contributiors, core_contribution_percentage/100
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