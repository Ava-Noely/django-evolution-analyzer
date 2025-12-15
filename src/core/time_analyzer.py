import pandas as pd
import warnings

warnings.filterwarnings('ignore', message='Converting to PeriodArray/Index representation will drop timezone information')

class TimeAnalyzer:
    """按照小时"""
    def analyze_hourly_pattern(self, commits_df):
        if commits_df.empty:
            return {
            'hourly_percentage': pd.Series(dtype=float),
            'busiest_hour': None,
            'busiest_hour_percentage': 0.0,
            'quietest_hour': None,
            'quietest_hour_percentage': 0.0
        }

        # 确保日期均为datetime类型
        if not pd.api.types.is_datetime64_any_dtype(commits_df['committed_date']):
            commits_df['committed_date']=pd.to_datetime(commits_df['committed_date'], utc =True)

        # 提取小时
        commits_df['hour']=commits_df['committed_date'].dt.hour

        # 按小时分组统计
        hourly_counts = commits_df['hour'].value_counts().sort_index()
        all_hours = pd.Series(0,index=range(24))
        hourly_counts = hourly_counts.reindex(all_hours.index,fill_value=0)

        # 规范化为百分比
        total_commits = hourly_counts.sum()
        if total_commits >0:
            hourly_percentage = (hourly_counts / total_commits*100).round(2)
        else:
            hourly_percentage = hourly_counts.astype(float)

        # 最忙时段和最闲时段
        if not hourly_percentage.empty:
            busiest_hour_idx = hourly_percentage.idxmax()
            quietest_hour_idx = hourly_percentage.idxmin()
            busiest_hour_percentage = hourly_percentage.max()
            quietest_hour_percentage = hourly_percentage.min()

        return {
            'hourly_percentage': hourly_percentage,
            'busiest_hour': busiest_hour_idx,
            'busiest_hour_percentage': busiest_hour_percentage,
            'quietest_hour': quietest_hour_idx,
            'quietest_hour_percentage': quietest_hour_percentage
        }

    """按照工作日 vs 休息日"""
    def analyze_weekday_pattern(self, commits_df):
        if commits_df.empty:
            return {
                'workday_percentage': 0.0,
                'weekend_percentage': 0.0,
                'daily_percentage': pd.Series(dtype=float),
                'busiest_day': None,
                'quietest_day': None
            }

        # 确保日期是datetime类型
        if not pd.api.types.is_datetime64_any_dtype(commits_df['committed_date']):
            commits_df['committed_date'] = pd.to_datetime(commits_df['committed_date'])

        # 提取星期（0-7分别对应周一到周日）
        commits_df['weekday'] = commits_df['committed_date'].dt.weekday

        # 分组统计
        weekday_counts = commits_df['weekday'].value_counts().sort_index()
        all_days = pd.Series(0,index=range(7))
        weekday_counts = weekday_counts.reindex(all_days.index,fill_value=0)

        # 分别计算工作日和周末的提交总数
        weekend_mask = weekday_counts.index >=5
        workday_mask = weekday_counts.index <5

        weekend_total = weekday_counts[weekend_mask].sum()
        workday_total = weekday_counts[workday_mask].sum()
        total_commits = weekday_counts.sum()

        # 转换为百分比
        if total_commits >0:
            workday_percentage = (workday_total / total_commits*100).round(2)
            weekend_percentage = (weekend_total / total_commits*100).round(2)
        else:
            workday_percentage = 0.0
            weekend_percentage = 0.0

        # 最忙的和最闲的日子
        if total_commits >0:
            daily_percentage = (weekday_counts / total_commits*100).round(2)
        else:
            daily_percentage = weekday_counts.astype(float)

        if not daily_percentage.empty:
            busiest_day_idx = daily_percentage.idxmax()
            quietest_day_idx = daily_percentage.idxmin()
            day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
            busiest_day = day_names[busiest_day_idx]
            quietest_day = day_names[quietest_day_idx]
        else:
            busiest_day = None
            quietest_day = None

        return {
            'workday_percentage': workday_percentage,
            'weekend_percentage': weekend_percentage,
            'daily_percentage': daily_percentage,
            'busiest_day': busiest_day,
            'quietest_day': quietest_day
        }

    '''按季节分析统计'''
    def analyze_seasonal_pattern(self, commits_df):
        if commits_df.empty:
            return {
                'monthly_trend': pd.Series(dtype=int),
                'quarterly_trend': pd.Series(dtype=int),
                'peak_months': [],
                'growth_rate': None,
                'yearly_summary': pd.Series(dtype=int)
            }

        # 确保日期是datetime类型
        if not pd.api.types.is_datetime64_any_dtype(commits_df['committed_date']):
            commits_df['committed_date'] = pd.to_datetime(commits_df['committed_date'])

        # 提取年份、月份和季度
        commits_df['year'] = commits_df['committed_date'].dt.year
        commits_df['month'] = commits_df['committed_date'].dt.month
        commits_df['quarter'] = commits_df['committed_date'].dt.quarter

        # 创建年月组合字符串
        commits_df['year_month'] = commits_df['committed_date'].dt.to_period('M')

        # 按年月分组统计
        monthly_trend = commits_df['year_month'].value_counts().sort_index()

        # 按季度分组统计
        commits_df['year_quarter'] = commits_df['year'].astype(str) + '-Q' + commits_df['quarter'].astype(str)
        quarterly_trend = commits_df['year_quarter'].value_counts().sort_index()

        # 按年份分组统计
        yearly_summary = commits_df['year'].value_counts().sort_index()

        # 识别提交高峰月份（取最高的3个月份）
        if len(monthly_trend) > 0:
            peak_months = monthly_trend.nlargest(min(3, len(monthly_trend)))
            peak_month_list = [f"{month.strftime('%Y-%m')} ({count} commits)"
                               for month, count in peak_months.items()]
        else:
            peak_month_list = []

        # 多年数据-计算增长率
        growth_rate = None
        if len(yearly_summary) >= 2:
            years = sorted(yearly_summary.index)
            latest_year = years[-1]
            previous_year = years[-2]

            if previous_year in yearly_summary and yearly_summary[previous_year] > 0:
                growth = ((yearly_summary[latest_year] - yearly_summary[previous_year]) /
                          yearly_summary[previous_year] * 100)
                growth_rate = round(growth, 2)

        return {
            'monthly_trend': monthly_trend,
            'quarterly_trend': quarterly_trend,
            'peak_months': peak_month_list,
            'growth_rate': growth_rate,
            'yearly_summary': yearly_summary
        }

    def get_time_analyzer_summary(self, commits_df):
        hourly_pattern = self.analyze_hourly_pattern(commits_df)
        weekday_pattern = self.analyze_weekday_pattern(commits_df)
        seasonal_trend = self.analyze_seasonal_pattern(commits_df)

        return {
            'hourly_distribution': hourly_pattern,
            'weekday_pattern': weekday_pattern,
            'seasonal_trend': seasonal_trend
        }