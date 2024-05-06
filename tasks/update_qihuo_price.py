from utilities.excel_utils import load_workbooks, save_workbooks, sync_and_clear_extra_data, create_dataframe_from_columns
from utilities.data_utils import update_prices, update_prices_copy
from utilities.web_scraping_utils import get_latest_price


def run(input_path, output_path, mode, results):
    wb_input, ws_input, wb_output, ws_output = load_workbooks(input_path, output_path)

    relation_dict = {'A': 'D', 'B': 'E', 'C': 'F'}
    # columns = ['A', 'B'] if mode == 'work' else ['A', 'B', 'C']
    if mode == 'work':
        columns = ['A', 'B']
    elif mode == 'urgent':
        columns = ['B']  # 只处理 B 列
    else:
        columns = ['A', 'B', 'C']  # 默认或其他模式

    sync_and_clear_extra_data(ws_input, ws_output, columns, relation_dict)

    df = create_dataframe_from_columns(ws_output, columns, relation_dict)
    update_prices(df, get_latest_price, ws_output, results=results)

    save_workbooks(wb_input, wb_output, input_path, output_path)

