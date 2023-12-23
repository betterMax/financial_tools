def get_price_with_error_handling(get_price_func, code, driver=None):
    try:
        latest_price = get_price_func(driver, code) if driver else get_price_func(code)
        if latest_price is None:
            return 0
        return float(latest_price)
    except ValueError:
        print(f'Warning: Cannot convert price "{latest_price}" to number for code {code}.')
        return 0
    except Exception as e:
        print(f'Error while getting price for {code}: {e}')
        return 0


def update_prices(df, get_price_func, ws_output, driver=None):
    df = df.drop_duplicates(subset='code')

    for _, row in df.iterrows():
        code = row['code']
        print(f'Updating price for {code}')
        price = get_price_with_error_handling(get_price_func, code, driver)
        ws_output[row['position']].value = price