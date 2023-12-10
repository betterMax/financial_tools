from utilities.excel_utils import find_data, split_excel_by_blank_rows, process_data_blocks, save_new_dfs_to_excel
import pandas as pd
import numpy as np


def run(input_path, output_path):
    dataframes = split_excel_by_blank_rows(input_path, 'Sheet1')

    processed_data_blocks = process_data_blocks(dataframes)

    # 打印处理后的数据块作为示例
    all_new_dfs = []
    for i, df in enumerate(processed_data_blocks):
        print(f"Data Block {i + 1}:")
        # 使用 set 函数收集所有单独的行名和列名，然后用 numpy 的 unique 函数得到所有不重复的行名和列名
        row_names = {name for row_name in df.index for name in row_name.split('+')}
        column_names = {name for column_name in df.columns for name in column_name.split('+')}

        # 去除重复的行名和列名
        unique_row_names = np.unique(list(row_names))
        unique_column_names = np.unique(list(column_names))

        # 创建一个新的数据框，行名和列名都是我们刚才获取的不重复的行名和列名
        new_df = pd.DataFrame(index=unique_row_names, columns=unique_column_names)

        # 使用我们之前的函数来填充新的数据框
        for row_name in unique_row_names:
            for column_name in unique_column_names:
                # 调用 find_data 来计算原始数据框中对应的数据的和
                data_sum = find_data(df, row_name, column_name)

                # 将这个和填入新的数据框中的对应位置
                new_df.loc[row_name, column_name] = data_sum

        # print(f'new_df: {new_df}')
        all_new_dfs.append(new_df)

    # 保存所有 new_df 到Excel文件
    save_new_dfs_to_excel(all_new_dfs, output_path)