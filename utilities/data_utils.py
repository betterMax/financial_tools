from utilities.web_scraping_utils import fetch_prices_for_code


def get_price_with_error_handling(get_price_func, code, driver=None):
    try:
        if driver:
            latest_price = get_price_func(driver, code)
        else:
            latest_price = get_price_func(code)
        if latest_price is None:
            return 0
        return float(latest_price)
    except ValueError:
        print(f'Warning: Cannot convert price "{latest_price}" to number for code {code}.')
        return 0
    except Exception as e:
        print(f'Error while getting price for {code}: {e}')
        return 0


def update_prices(df, get_price_func, ws_output, driver=None, results=None):
    # 将 results 转换为字典以便快速查找
    results_dict = dict(results) if results else {}

    # 删除重复的代码，但先记录每个代码对应的所有位置
    code_positions = df.groupby('code')['position'].apply(list).to_dict()

    for code, positions in code_positions.items():
        # print(f"Checking code: {code}")  # 调试用

        # 首先检查 results 中是否已有价格
        if code in results_dict:
            price = results_dict[code]
            print(f'Price for {code} is {price} already in results')
        elif code == "":
            continue
        elif code == 0:
            continue
        else:
            # 如果没有，使用爬虫获取价格
            print(f'Updating price for {code} with clawler')
            price = get_price_with_error_handling(get_price_func, code, driver)

        # 更新这个代码对应的所有位置
        for position in positions:
            ws_output[position].value = price


def update_prices_copy(df, get_price_func, ws_output, driver=None, results=None):
    # 将 results 转换为字典以便快速查找
    results_dict = dict(results) if results else {}

    # 记录尚未获取价格的codes
    missing_codes = []

    # 删除重复的代码，但先记录每个代码对应的所有位置
    code_positions = df.groupby('code')['position'].apply(list).to_dict()

    for code, positions in code_positions.items():
        if code not in results_dict:
            missing_codes.append(code)

    if missing_codes:
        # 仅处理第一个缺失价格的code
        missing_code = missing_codes[0]
        print(f"Fetching missing price for code: {missing_code}")
        # 假设fetch_prices_for_code现在接受一个代码列表，并返回这些代码的价格
        valid_urls, common_prices = fetch_prices_for_code([missing_code])
        print(f"results_dict: {results_dict}")
        results_dict.update(common_prices)
        print(f"results_dict after update: {results_dict}")

    for code, positions in code_positions.items():
        # print(f"Checking code: {code}")  # 调试用

        # 首先检查 results 中是否已有价格
        if code in results_dict:
            price = results_dict[code]
            print(f'Price for {code} is {price} already in results')
        elif code == "":
            continue
        elif code == 0:
            continue
        else:
            # 如果没有，使用爬虫获取价格
            print(f'Updating price for {code} with clawler')
            price = get_price_with_error_handling(get_price_func, code, driver)

        # 更新这个代码对应的所有位置
        for position in positions:
            ws_output[position].value = price