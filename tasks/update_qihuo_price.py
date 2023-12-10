# from openpyxl import load_workbook
# import pandas as pd
# from utilities.web_scraping_utils import get_latest_price


from utilities.excel_utils import load_workbooks, save_workbooks, sync_and_clear_extra_data, create_dataframe_from_columns
from utilities.data_utils import update_prices
from utilities.web_scraping_utils import get_latest_price


def run(input_path, output_path, mode):
    wb_input, ws_input, wb_output, ws_output = load_workbooks(input_path, output_path)

    relation_dict = {'A': 'D', 'B': 'E', 'C': 'F'}
    columns = ['A', 'B'] if mode == 'work' else ['A', 'B', 'C']

    sync_and_clear_extra_data(ws_input, ws_output, columns, relation_dict)

    df = create_dataframe_from_columns(ws_output, columns, relation_dict)
    update_prices(df, get_latest_price, ws_output)

    save_workbooks(wb_input, wb_output, input_path, output_path)


# def run(input_path, output_path, mode):
#     # 加载输入和输出工作簿
#     wb_input = load_workbook(filename=input_path, data_only=True)
#     ws_input = wb_input['Sheet1']
#
#     wb_output = load_workbook(filename=output_path, data_only=True)
#     ws_output = wb_output['Sheet1']
#
#     # 待处理的sheet列表
#     relation_dict = {'A': 'D', 'B': 'E', 'C': 'F'}
#     if mode == 'work':
#         columns = ['A', 'B']
#     else:
#         columns = ['A', 'B', 'C']
#
#     # 从输入文件读取数据并更新到输出文件
#     data = []
#     for column in columns:
#         row = 3
#         input_row_count = 0
#         while ws_input[f'{column}{row}'].value is not None:
#             value = ws_input[f'{column}{row}'].value
#             ws_output[f'{column}{row}'].value = value
#             data.append({'code': value, 'position': f'{relation_dict[column]}{row}'})
#             row += 1
#             input_row_count += 1
#
#         # 确保输出文件里的数据行数和输入文件里的一致
#         while ws_output[f'{column}{row}'].value is not None:
#             ws_output[f'{column}{row}'].value = None
#             row += 1
#
#         # 确保输入文件的代码和价格列数据行数一致
#         related_column = relation_dict[column]
#         input_related_row = 3 + input_row_count
#         while ws_input[f'{related_column}{input_related_row}'].value is not None:
#             ws_input[f'{related_column}{input_related_row}'].value = None
#             input_related_row += 1
#
#         # 确保输出文件的代码和价格列数据行数一致
#         output_related_row = 3 + input_row_count
#         while ws_output[f'{related_column}{output_related_row}'].value is not None:
#             ws_output[f'{related_column}{output_related_row}'].value = None
#             output_related_row += 1
#
#     # # 重新创建DataFrame，用于价格更新
#     # data = []
#     # for column in columns:
#     #     row = 3
#     #     while ws_output[f'{column}{row}'].value is not None:
#     #         code = ws_output[f'{column}{row}'].value
#     #         data.append({'code': code, 'position': f'{relation_dict[column]}{row}', 'price': 0})
#     #         row += 1
#
#     df = pd.DataFrame(data)
#
#     # 去重并获取价格
#     unique_codes = df['code'].unique()
#     for code in unique_codes:
#         try:
#             price = get_latest_price(code)  # 假设这个函数返回价格
#             if price is None:
#                 price = 0
#             else:
#                 price = float(price)
#         except:
#             price = 0
#         df.loc[df['code'] == code, 'price'] = price
#
#     # 更新价格到输出工作簿
#     for _, row in df.iterrows():
#         ws_output[row['position']] = row['price']
#
#     # 保存输出工作簿
#     wb_output.save(output_path)
#     wb_input.save(input_path)