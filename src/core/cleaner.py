import pandas as pd


class DataCleaner:
    @staticmethod
    def clean_commit_date(df):
        if df.empty:
            return df

        # 确保日期为datetime类型
        if not pd.api.types.is_datetime64_any_dtype(df['committed_date']):
            df['committed_date'] = pd.to_datetime(df['committed_date'], utc=True)

        cleaned_df = df.copy()

        # 检查必要列
        required_cols = ['committed_date']
        missing_cols = [col for col in required_cols if col not in cleaned_df.columns]
        if missing_cols:
            raise ValueError(f"缺少必要列:{missing_cols}")

        cleaned_df = DataCleaner.clean_dates(cleaned_df)

        cleaned_df = DataCleaner.remove_duplicates(cleaned_df)

        DataCleaner.validate_data(cleaned_df)

        return cleaned_df

    @staticmethod
    def clean_dates(df):
        df_clean = df.copy()

        # 移除无效日期
        df_clean = df_clean.dropna(subset=['committed_date'])

        # 过滤异常日期
        current_date = pd.Timestamp.now(tz='UTC')
        start_date = pd.Timestamp('2001-01-01', tz='UTC')

        mask = (
            (df_clean['committed_date'] >= start_date)&
            (df_clean['committed_date'] <= current_date)
        )
        df_clean = df_clean[mask]

        return df_clean

    @staticmethod
    def remove_duplicates(df):
        if 'commit_hash' in df.columns:
            # 按提交哈希去重
            df = df.drop_duplicates(subset=['commit_hash'], keep='first')
        else:
            # 按时间戳去重
            df = df.drop_duplicates(subset=['committed_date'],keep='first')

        return df

    @staticmethod
    def validate_data(df):
        if df.empty:
            print("清洗后数据为空！")
            return

        print(f"=== 数据验证报告 ===")
        print(f"总记录数: {len(df)}")
        print(f"时间范围: {df['committed_date'].min()} 到 {df['committed_date'].max()}")
        print(f"日期跨度: {(df['committed_date'].max() - df['committed_date'].min()).days} 天")

        if 'committed_date' in df.columns:
            df['year'] = df['committed_date'].dt.year
            year_counts = df['year'].value_counts().sort_index()
            print("\n按年份分布：")
            for year,count in year_counts.items():
                print(f" {year}:{count}条记录")