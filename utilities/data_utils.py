def get_price_with_error_handling(get_price_func, code, driver=None):
    try:
        if driver:
            latest_price = get_price_func(driver, code)
        else:
            latest_price = get_price_func(code)
        # latest_price = get_price_func(driver, code) if driver else get_price_func(code)
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
        else:
            # 如果没有，使用爬虫获取价格
            print(f'Updating price for {code} with clawler')
            price = get_price_with_error_handling(get_price_func, code, driver)

        # 更新这个代码对应的所有位置
        for position in positions:
            ws_output[position].value = price
