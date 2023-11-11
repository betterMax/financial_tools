import pandas as pd
from utilities.web_scraping_utils import extract_data_with_refined_trim
from utilities.excel_utils import save_results_to_excel


def run(path):
    # 这是一个示例，展示如何使用上述函数
    results = extract_data_with_refined_trim()
    print(f'length: {len(results)} and results: {results}')

    # 保存到 .xlsx 文件
    save_results_to_excel(results, path)