


def df_to_csv(df, file_path, index=False):
    """
    將 DataFrame 儲存為 CSV 檔案
    df: pandas DataFrame
    file_path: 儲存的檔案路徑
    index: 是否儲存索引，預設 False
    """
    df.to_csv(file_path, index=index)

def csv_to_df(file_path, header_lower_case=False):
    """
    從 CSV 檔案讀取資料為 DataFrame
    file_path: CSV 檔案路徑
    header_lower_case: 是否將欄位名稱轉為小寫，預設 False
    回傳 pandas DataFrame
    """
    import pandas as pd
    df = pd.read_csv(file_path)
    if header_lower_case:
        df.columns = [col.lower() for col in df.columns]
    return df