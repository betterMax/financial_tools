# 导入库
import numpy as np
import pandas as pd


def find_data(df, row_name, column_name):
    rows = row_name.split('+')
    columns = column_name.split('+')

    data_sum = 0
    data_found = False  # 添加一个标志变量来记录是否找到数据

    for index, row in df.iterrows():
        row_parts = index.split('+')
        if any(r in row_parts for r in rows):
            for df_col in df.columns:
                col_parts = df_col.split('+')
                if any(col in col_parts for col in columns) and pd.notna(row[df_col]):
                    value = row[df_col]
                    if isinstance(value, (int, float)):
                        data_sum += value
                        data_found = True  # 设置标志为True表示找到了数据
                    else:
                        print(f"Non-numeric value found: {value}, Row: {index}, Column: {df_col}")

    # 如果没有找到数据，返回None
    if not data_found:
        return None

    # 如果找到了数据，按照之前的逻辑处理
    if data_sum % 1 == 0:  # 如果是整数
        return int(data_sum)  # 返回整数形式
    else:  # 如果是带小数的数值
        return round(data_sum, 2)  # 保留两位小数


def split_excel_by_blank_rows(file_path, sheet_name):
    df = pd.read_excel(file_path, sheet_name=sheet_name, header=None, index_col=None)
    print(df.shape)
    # 查找空白行的索引以横向分割
    blank_row_indices = df[df.isnull().all(axis=1)].index

    dataframes = []
    start_row = 0
    for end_row in blank_row_indices:
        if end_row - start_row >= 2:  # 空白行超过2行，分割数据块
            block = df.iloc[start_row:end_row]
            # 纵向分割：删除全部为空的行
            block = block.dropna(axis=0, how='all')
            if block.shape[0] > 0 and block.shape[1] > 0:
                # 设置第一行和第一列为列名和行名
                block.columns = block.iloc[0]
                block = block[1:]
                block = block.set_index(block.columns[0])
                dataframes.append(block)
            start_row = end_row + 1
    print(f'start_row: {start_row}, len of df: {len(df)}')
    # 添加最后一个数据块
    if start_row < len(df):
        # 查找最后一个数据块的真实起始行
        last_block_start = df[start_row:].dropna(how='all').index[0]
        block = df.iloc[last_block_start:]
        block = block.dropna(axis=1, how='all')
        if block.shape[0] > 0 and block.shape[1] > 0:
            block.columns = block.iloc[0]
            block = block[1:]
            block = block.set_index(block.columns[0])
            dataframes.append(block)

    return dataframes


def process_data_blocks(dataframes):
    processed_blocks = []
    for df in dataframes:
        if df.shape[0] > 0 and df.shape[1] > 0:
            # 检查并删除第一行如果它是列标题的重复
            if df.iloc[0, 0] == '形态':
                df = df.iloc[1:]

            # 移除以 "Unnamed" 开头的列
            df = df.loc[:, ~df.columns.str.contains('^Unnamed')]

            # 移除完全为空的列
            df = df.dropna(axis=1, how='all')

            # 将“形态”列作为行名（如果存在）
            if '形态' in df.columns:
                df = df.set_index('形态')

            # 可以在这里添加更多针对每个数据块的处理逻辑

            processed_blocks.append(df)

    return processed_blocks


def save_new_dfs_to_excel(new_dfs, file_path):
    with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
        startrow = 0
        for new_df in new_dfs:
            new_df.to_excel(writer, sheet_name='Sheet1', startrow=startrow, index=True)
            startrow += len(new_df.index) + 6  # 数据块长度 + 5行空白 + 1行因自增而来的


dataframes = split_excel_by_blank_rows('/Users/maxfeng/Downloads/Book3.xlsx', 'Sheet1')

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
save_new_dfs_to_excel(all_new_dfs, '/Users/maxfeng/Downloads/Future_Strategy.xlsx')

