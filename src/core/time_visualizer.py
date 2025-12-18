import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

# 设置中文字体支持
plt.rcParams['font.sans-serif'] = ['SimHei', 'Arial Unicode MS', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

class TimeVisualizer:
    def create_heatmap(self, commits_df, save_path=None):
        if commits_df.empty:
            print("数据为空，无法创建热力图！")
            return None

        # 确保日期为datetime类型
        if not pd.api.types.is_datetime64_any_dtype(commits_df['committed_date']):
            commits_df['committed_date'] = pd.to_datetime(commits_df['committed_date'],utc = True)

        # 提取小时和星期几
        commits_df['hour'] = commits_df['committed_date'].dt.hour
        commits_df['weekday'] = commits_df['committed_date'].dt.weekday

        try:
            heatmap_data = commits_df.pivot_table(
                index='hour',
                columns='weekday',
                aggfunc='size',
                fill_value=0
            )

            heatmap_data = heatmap_data.reindex(index=range(24),columns=range(7),fill_value=0)

        except Exception as e:
            print(f"创建热力图失败：{e}")

        plt.figure(figsize=(4, 8))
        ax = sns.heatmap(
            heatmap_data,
            cmap='YlOrRd',
            linewidths=0.5,
            linecolor='gray',
            annot=True,
            fmt='d',
            annot_kws={'size':8},
            cbar_kws={'label': '提交数量'},
            square=True
        )

        # 设置坐标轴标签
        ax.set_title('提交时间分布热力图（小时 × 星期几）',fontsize=16, fontweight='bold',pad = 20)
        ax.set_xlabel('星期几',fontsize=12)
        ax.set_ylabel('小时',fontsize=12)

        # 分别设置x轴和y轴的刻度标签
        weekday_labels = ['周一','周二','周三','周四','周五','周六','周日']
        ax.set_xticks(np.arange(7)+0.5)
        ax.set_xticklabels(weekday_labels, rotation=0, fontsize=10)

        hour_labels=[f'{h:02d}:00' for h in range(24)]
        ax.set_yticks(np.arange(24)+0.5)
        ax.set_yticklabels(hour_labels, rotation=0, fontsize=10)

        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"热力图已保存到：{save_path}")

        return plt.gcf()

    def create_combined_visualization(self,commits_df, save_path=None):
        if commits_df.empty:
            print("数据为空，无法创建可视化图表！")
            return None

        # 确保日期为datetime类型
        if not pd.api.types.is_datetime64_any_dtype(commits_df['committed_date']):
            commits_df['committed_date'] = pd.to_datetime(commits_df['committed_date'],utc=True)

        # 提取小时和星期几
        commits_df['hour'] = commits_df['committed_date'].dt.hour
        commits_df['weekday'] = commits_df['committed_date'].dt.weekday

        fig = plt.figure(figsize=(12, 12))

        # 1.热力图
        ax1 = plt.subplot(2,2,1)
        heatmap_data = commits_df.pivot_table(
            index='hour',
            columns='weekday',
            aggfunc='size',
            fill_value=0
        )
        heatmap_data = heatmap_data.reindex(index=range(24), columns=range(7), fill_value=0)

        sns.heatmap(
            heatmap_data,
            cmap='YlOrRd',
            linewidths=0.5,
            linecolor='gray',
            annot=True,
            fmt='d',
            annot_kws={'size': 6},
            cbar_kws={'label': '提交数量'},
            ax=ax1,
            square=False
        )
        ax1.set_title('提交时间热力图', fontsize=14, fontweight='bold')
        ax1.set_ylabel('小时')
        ax1.set_xticks(np.arange(7) + 0.5)
        ax1.set_xticklabels(['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'])
        ax1.set_yticks(np.arange(0, 24, 3) + 0.5)
        ax1.set_yticklabels([f'{h:02d}:00' for h in range(0, 24, 3)])

        # 2.小时分布条形图
        ax2 = plt.subplot(2,2,2)
        hourly_counts = commits_df['hour'].value_counts().sort_index()
        hourly_counts = hourly_counts.reindex(range(24), fill_value=0)

        colors = plt.cm.YlOrRd(hourly_counts / max(hourly_counts.max(), 1))
        ax2.bar(range(24),hourly_counts.values, color=colors, edgecolor='black')
        ax2.set_title('24小时提交分布', fontsize=14, fontweight='bold')
        ax2.set_ylabel('提交数量')
        ax2.set_xticks(range(0,24,3))
        ax2.set_xticklabels([f'{h:02d}:00' for h in range(0,24,3)])
        ax2.grid(True, alpha=0.3)

        # 3.星期分布条形图
        ax3 = plt.subplot(2,2,3)
        weekday_counts = commits_df['weekday'].value_counts().sort_index()
        weekday_counts = weekday_counts.reindex(range(7), fill_value=0)

        weekday_labels = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        colors = plt.cm.YlOrRd(weekday_counts / max(weekday_counts.max(), 1))
        bars = ax3.bar(range(7), weekday_counts.values, color=colors, edgecolor='black')
        ax3.set_title('星期提交分布', fontsize=14, fontweight='bold')
        ax3.set_ylabel('提交数量')
        ax3.set_xticks(range(7))
        ax3.set_xticklabels([label[:3] for label in weekday_labels])
        ax3.grid(True, alpha=0.3)

        # 4.工作日vs周末饼图
        ax4 = plt.subplot(2,2,4)
        workday_mask = commits_df['weekday'] < 5
        weekend_mask = commits_df['weekday'] >=5

        workday_count = workday_mask.sum()
        weekend_count = weekend_mask.sum()

        sizes = [workday_count, weekend_count]
        labels = ['工作日', '周末']
        colors = ['#FFA726', '#42A5F5']

        if sum(sizes) > 0:
            ax4.pie(sizes,labels=labels,colors=colors,autopct='%1.1f%%',
                    startangle=90, textprops={'fontsize': 10})
            ax4.set_title('工作日 vs 周末提交比例',fontsize=14, fontweight='bold')
        else:
            ax4.text(0.5, 0.5, '无提交数据', ha='center', va='center', fontsize=12)
            ax4.set_title('工作日 vs 周末提交比例', fontsize=14, fontweight='bold')

        plt.suptitle('提交时间模式分析', fontsize=18, fontweight='bold', y=0.98)
        plt.tight_layout()

        # 保存图像
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"综合可视化图标已经保存到：{save_path}")

        return fig