from utilities.excel_utils import find_data, split_excel_by_blank_rows, process_data_blocks, save_new_dfs_to_excel
import pandas as pd
import numpy as np


def run(input_path, output_path):
    dataframes = split_excel_by_blank_rows(input_path, 'Sheet1')

    processed_data_blocks = process_data_blocks(dataframes)

    # 打印处理后的数据块作为示例
    all_new_dfs = []
    for i, df in enumerate(processed_data_blocks):
        # print(f"Data Block {i + 1}:")
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

    # 开始处理3个new_df，来获取最后的结果
    df1 = all_new_dfs[0]
    df2 = all_new_dfs[1]
    df3 = all_new_dfs[2]
    df1 = df1.reset_index().rename(columns={'index': '成功'})
    df2 = df2.reset_index().rename(columns={'index': '总数'})
    df3 = df3.reset_index().rename(columns={'index': '总收益'})

    # 对第一个DataFrame进行扩充，确保行和列的顺序与第二个和第三个DataFrame一致
    df1_expanded_correctly = df1.set_index('成功').reindex(df2.set_index(df2.columns[0]).index).reset_index()
    df1_expanded_correctly.rename(columns={'总数':'成功个数'}, inplace=True)

    # 第二步：创建两个新的DataFrame，一个用于保存分数形式的结果，另一个用于保存小数形式的结果
    # 分数形式
    df_fraction = df1_expanded_correctly.set_index('成功个数').astype(str).replace('\.0', '',
                                                                               regex=True) + '/' + df2.set_index(
        df2.columns[0]).astype(str).replace('\.0', '', regex=True)
    df_fraction = df_fraction.rename_axis(index={'成功个数': '成功比率分数'})

    # 小数形式
    df_decimal = df1_expanded_correctly.set_index('成功个数').div(df2.set_index(df2.columns[0]))
    df_decimal = df_decimal.astype('float64')
    df_decimal = df_decimal.round(2)
    df_decimal = df_decimal.rename_axis(index={'成功个数': '成功率'})

    # 第三步：使用第五个DataFrame（小数版本）和原始的第二个DataFrame进行操作
    # 相乘后除以第二个DataFrame中的值和10中的较大者
    df1_expanded_correctly.set_index('成功个数', inplace=True)
    df2_conditioned = df2.copy()
    df2_conditioned.set_index(df2_conditioned.columns[0], inplace=True)
    df2_conditioned[df2_conditioned < 10] = 10
    df6 = df1_expanded_correctly.div(df2_conditioned)
    df6 = df6.astype('float64')
    df6 = df6.round(2)
    df6 = df6.rename_axis(index={'成功个数': '绝对成功率'})

    # 第四步：根据第二个 DataFrame 的值进行条件操作
    df2_conditioned = df2.copy()
    df2_conditioned.set_index(df2_conditioned.columns[0], inplace=True)
    df2_conditioned[df2_conditioned < 10] = 100000
    df3_conditioned = df3.copy()
    df3_conditioned.set_index(df3_conditioned.columns[0], inplace=True)
    df7 = df3_conditioned.div(df2_conditioned)
    df7 = df7.astype('float64')
    df7 = df7.round(2)
    df7 = df7.rename_axis(index={'总收益': '绝对收益'})

    df2 = df2.set_index('总数')
    df3 = df3.set_index('总收益')

    # 第五步：调整 DataFrame 在列表中的顺序
    all_new_dfs = [df_fraction, df1_expanded_correctly, df2, df3, df_decimal, df6, df7]
    # all_new_dfs.insert(0, all_new_dfs.pop(3))  # 将第四个元素移动到第一个位置

    # 第六步：使用阈值筛选第六和第七个 DataFrame 的数据
    threshold_df6 = 0.5  # 第六个 DataFrame 的阈值
    threshold_df7 = 3000  # 第七个 DataFrame 的阈值

    # 筛选第六个 DataFrame
    df6_filtered = df6[df6 > threshold_df6].stack().reset_index()
    df6_filtered.columns = ['行名', '列名', '值']

    # 筛选第七个 DataFrame
    df7_filtered = df7[df7 > threshold_df7].stack().reset_index()
    df7_filtered.columns = ['行名', '列名', '值']

    df6_filtered['组合'] = df6_filtered['列名'] + '+' + df6_filtered['行名']
    df7_filtered['组合'] = df7_filtered['列名'] + '+' + df7_filtered['行名']

    df6_filtered = df6_filtered[['组合', '值']]
    df7_filtered = df7_filtered[['组合', '值']]
    merged_df = pd.merge(df6_filtered, df7_filtered, on='组合', how='outer', suffixes=('_成功率', '_收益'))
    merged_df.sort_values('组合', ascending=False, inplace=True)
    merged_df.set_index('组合', inplace=True)
    print(f'all_new_dfs: {all_new_dfs[0].shape},{all_new_dfs[1].shape},{all_new_dfs[2].shape}',
          f'{all_new_dfs[3].shape},{all_new_dfs[4].shape},{all_new_dfs[5].shape},{all_new_dfs[6].shape}'
          f'; merged_df: {merged_df.shape}')

    # 保存所有 new_df 到Excel文件
    save_new_dfs_to_excel(all_new_dfs, merged_df, output_path)
