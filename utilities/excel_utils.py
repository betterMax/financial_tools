import pandas as pd


def excel_column_to_list(file_path, column_name):
    df = pd.read_excel(file_path)
    return df[column_name].tolist()


def save_results_to_excel(results, excel_path):
    try:
        df = pd.read_excel(excel_path)
    except FileNotFoundError:
        df = pd.DataFrame()

    for idx, (value_1, value_2) in enumerate(results, start=1):
        value_2 = round(float(value_2), 1)
        df.at[idx-1, '代码'] = value_1
        df.at[idx-1, '价格'] = value_2

    df.to_excel(excel_path, index=False)
