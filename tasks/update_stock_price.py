# from openpyxl import load_workbook
# import time
# from utilities.web_scraping_utils import init_chrome, get_stock_latest_price
# import pandas as pd


from utilities.excel_utils import load_workbooks, save_workbooks, sync_and_clear_extra_data, create_dataframe_from_columns
from utilities.data_utils import update_prices
from utilities.web_scraping_utils import init_chrome, get_stock_latest_price

def run(input_path, output_path, mode):
    wb_input, ws_input, wb_output, ws_output = load_workbooks(input_path, output_path)
    driver = init_chrome()

    relation_dict = {'I': 'L', 'J': 'M', 'K': 'N'}
    columns = ['I', 'J'] if mode == 'work' else ['I', 'J', 'K']

    sync_and_clear_extra_data(ws_input, ws_output, columns, relation_dict)

    df = create_dataframe_from_columns(ws_output, columns, relation_dict)
    update_prices(df, get_stock_latest_price, ws_output, driver)

    driver.quit()
    save_workbooks(wb_input, wb_output, input_path, output_path)


#
# def run(input_path, output_path, mode):
#     # 加载输入和输出工作簿
#     wb_input = load_workbook(filename=input_path, data_only=True)
#     ws_input = wb_input['Sheet1']
#
#     wb_output = load_workbook(filename=output_path, data_only=True)
#     ws_output = wb_output['Sheet1']
#     driver = init_chrome()
#
#     # 待处理的sheet列表
#     relation_dict = {'I': 'L', 'J': 'M', 'K': 'N'}
#     if mode == 'work':
#         columns = ['I', 'J']
#     else:
#         columns = ['I', 'J', 'K']
#
#     # 读取和同步数据
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
#         # 清除输出文件中多余的数据
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
#         related_column = relation_dict[column]
#         output_related_row = 3 + input_row_count
#         while ws_output[f'{related_column}{output_related_row}'].value is not None:
#             ws_output[f'{related_column}{output_related_row}'].value = None
#             output_related_row += 1
#
#     # 创建DataFrame并去重
#     df = pd.DataFrame(data)
#     df = df.drop_duplicates(subset='code')
#
#     # 更新价格
#     for _, row in df.iterrows():
#         code = row['code']
#         print(f'update {code} price')
#         latest_price = get_stock_latest_price(driver, code)
#         price = None
#
#         # 尝试将价格转换为浮点数
#         try:
#             if latest_price is not None:
#                 price = float(latest_price)
#             else:
#                 print(f'Warning: Latest price is None. Please check the price.')
#         except ValueError:
#             print(f'Warning: Cannot convert price "{latest_price}" to number. Please check the price.')
#             price = 0
#         ws_output[row['position']].value = price
#         time.sleep(1)  # 暂停一秒
#
#     driver.quit()
#     # 保存修改
#     wb_output.save(output_path)
#     wb_input.save(input_path)
#
