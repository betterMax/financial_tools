from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import os
import requests
import pandas as pd
import time
from tqdm import tqdm
from urllib.parse import quote
import logging


def init_chrome():
    current_directory = os.path.dirname(os.path.realpath(__file__))
    parent_directory = os.path.dirname(current_directory)
    os.environ["PATH"] += os.pathsep + parent_directory
    chrome_options = Options()
    chrome_options.add_argument('--headless')  # 注释这行以便观察
    # chromedriver_path = '/Users/maxfeng/Documents/GitHub/financial_tools/chromedriver'
    # driver = webdriver.Chrome(executable_path=chromedriver_path, options=chrome_options)
    driver = webdriver.Chrome(options=chrome_options)

    return driver


def get_urls(code, test_links=False):
    if code != 0:
        if code[:2] == 'SI':
            sina_url = f'https://finance.sina.com.cn/futures/quotes/gfex/{code}.shtml'
            shangjia_url = f'https://www.shangjia.com/qihuo/{code.lower()}/qixianjiegou'
        else:
            sina_url = f'https://finance.sina.com.cn/futures/quotes/{code}.shtml'
            shangjia_url = f'https://www.shangjia.com/qihuo/{code.lower()}/qixianjiegou'

        if test_links:
            test_link(sina_url)
            test_link(shangjia_url)

        return sina_url, shangjia_url
    else:
        return None, None


def test_link(url):
    response = requests.head(url)

    if response.status_code != 200:
        print(f'Warning: {url} is not accessible. Status code: {response.status_code}')


def get_latest_price(code, driver=None):
    sina_url, shangjia_url = get_urls(code)
    price = None

    # 创建一个chrome浏览器的驱动，设置为无头模式
    current_directory = os.path.dirname(os.path.realpath(__file__))
    parent_directory = os.path.dirname(current_directory)
    os.environ["PATH"] += os.pathsep + parent_directory
    # print(f'path: {os.environ["PATH"]}')
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    driver = webdriver.Chrome(options=chrome_options) # https://googlechromelabs.github.io/chrome-for-testing/ 更新

    # 尝试从新浪财经获取价格
    try:
        # 打开网页
        driver.get(sina_url)

        # 等待JavaScript加载完成
        driver.implicitly_wait(5)

        # 提取价格
        price_tag = driver.find_element(By.CSS_SELECTOR, 'td[class*="price"]')
        price = price_tag.text
        print(f'getting {code} price {price} succesfully from sina')
    except Exception as e:
        print(f'Error getting price from sina: {e}')

    # 如果从新浪财经获取价格失败，尝试从商家网获取价格
    if price is None or price == '--' or code[:2] == 'SM' or code[:2] == 'C2':
        try:
            # 打开网页
            driver.get(shangjia_url)

            # 等待JavaScript加载完成
            driver.implicitly_wait(10)

            # 提取价格
            # price_tag = driver.find_element(By.CSS_SELECTOR, 'div[class*="remove_data"]')
            price_tag = driver.find_element(By.XPATH, "//span[text()='收盘价']/following-sibling::strong")
            price = price_tag.text
            print(f'getting {code} price {price} succesfully from shangjia')
        except Exception as e:
            print(f'Error getting price from shangjia: {e}')
            price = 0

    # 不要忘记最后要关闭浏览器
    driver.quit()

    return price


def format_decimal(x):
    if x is None:
        return x
    try:
        # Remove commas (for thousands separators)
        x_cleaned = x.replace(',', '')
        return round(float(x_cleaned), 1)
    except ValueError:
        return x


def extract_data_with_refined_trim():
    # 创建一个chrome浏览器的驱动，不使用无头模式以便观察
    current_directory = os.path.dirname(os.path.realpath(__file__))
    parent_directory = os.path.dirname(current_directory)
    os.environ["PATH"] += os.pathsep + parent_directory
    chrome_options = Options()
    chrome_options.add_argument('--headless')  # 注释这行以便观察
    driver = webdriver.Chrome(options=chrome_options)

    base_url = "http://vip.stock.finance.sina.com.cn/quotes_service/view/qihuohangqing.html"
    results = []

    # 在 driver.get(base_url) 之前存储原始窗口句柄
    original_window = driver.current_window_handle

    driver.get(base_url)

    # 切换回原始窗口
    driver.switch_to.window(original_window)

    # 获取所有的导航按钮
    nav_buttons = driver.find_elements(By.CSS_SELECTOR, "ul li a[id^='tab_switch_']")

    # 创建一个索引列表来表示你想要的顺序
    desired_order = [0, 1, 2, 4, 3]
    for index in desired_order:
        btn = nav_buttons[index]  # 根据所需顺序获取按钮
        if index != 0:  # 如果不是第一页，则点击并等待
            btn.click()
            # 等待页面加载完成，此处增加固定等待时间，例如5秒
            time.sleep(3)
    # for index, btn in enumerate(nav_buttons):
    #     if index != 0:  # 如果不是第一页，则点击并等待
    #         btn.click()
    #         # 等待页面加载完成，此处增加固定等待时间，例如5秒
    #         time.sleep(3)

        print(f'Processing page {index} - {btn.text if index != 0 else "首页"}')

        # 等待 div 加载
        WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div.div_cont_wt"))
        )

        # 找到所有的<div class="div_cont_wt">
        divs = driver.find_elements(By.CSS_SELECTOR, "div.div_cont_wt")

        for div in tqdm(divs, desc="Processing tables", leave=True):
            if not div.is_displayed():
                continue  # 跳过当前迭代，处理下一个div

            item_df = get_table_data(div)  # 获取第一页的数据
            if "成交量" in item_df.columns and "代码" in item_df.columns:

                while True:
                    # 检查当前页面的 DataFrame 是否满足条件
                    item_df.sort_values(by=["成交量", "代码"], inplace=True)
                    item_df.reset_index(drop=True, inplace=True)
                    first_satisfied, all_satisfied = False, False
                    for i, row in item_df.iterrows():
                        if (len(row["代码"]) == 3 or len(row["代码"]) == 2) and row["代码"][:-1].isalpha() and row["代码"][
                            -1].isdigit():
                            if i + 1 < len(item_df) and item_df.iloc[i + 1]["成交量"] == row["成交量"]:
                                first_satisfied = True
                                break

                    if first_satisfied:
                        if len(item_df) <= 2:
                            print(f'processing {item_df.iloc[0, 0]}')
                            break
                        else:
                            columns_to_format = [col for col in item_df.columns if col not in ['代码', '名称', '涨跌幅']]
                            for col in columns_to_format:
                                item_df[col] = item_df[col].apply(format_decimal)
                            value_1 = item_df.iloc[i + 1]["代码"]
                            value_2 = item_df.iloc[i + 1]["最新价"]
                            results.append((value_1, value_2))
                            break  # 如果条件满足，跳出循环

                    # 检查是否有下一页，并翻页
                    next_page_buttons = div.find_elements(By.CSS_SELECTOR, "div.pages a:not(.pagedisabled)")
                    all_satisfied = True
                    if next_page_buttons and "下一页" in [btn.text for btn in next_page_buttons]:
                        next_page_buttons[-1].click()
                        time.sleep(3)
                        # 获取新页面的数据并添加到 item_df
                        new_page_df = get_table_data(div)
                        item_df = pd.concat([item_df, new_page_df], ignore_index=True)
                    else:
                        break  # 如果没有更多页，结束循环

                if first_satisfied and not all_satisfied:
                    continue

                if first_satisfied and all_satisfied:
                    if len(item_df) <= 2:
                        print(f'processing {item_df.iloc[0, 0]}')
                        pass
                    else:
                        columns_to_format = [col for col in item_df.columns if col not in ['代码', '名称', '涨跌幅']]
                        for col in columns_to_format:
                            item_df[col] = item_df[col].apply(format_decimal)

                        # Sort the dataframe
                        item_df = item_df.sort_values(
                            by=["成交量", "代码"])  # assuming 最新价 is the second last column and 代码 is the first column
                        item_df = item_df.reset_index(drop=True)

                        # Extract value_1 and value_2
                        for i, row in item_df.iterrows():
                            if (len(row["代码"]) == 3 or len(row["代码"]) == 2) and row["代码"][:-1].isalpha() and \
                                    row["代码"][-1].isdigit():
                                print(
                                    f'item_df for {item_df.iloc[0, 0]} and shape for {item_df.shape} and length: {len(item_df)}')
                                if i + 1 < len(item_df) and item_df.iloc[i + 1]["成交量"] == row["成交量"]:
                                    value_1 = item_df.iloc[i + 1]["代码"]
                                    value_2 = item_df.iloc[i + 1]["最新价"]
                                    results.append((value_1, value_2))
                                    break
            else:
                driver.close()
                # 去重处理
                unique_results = list(set(results))
                return unique_results

    driver.close()
    # 去重处理
    unique_results = list(set(results))
    return unique_results


def get_table_data(div):
    # 获取列名
    thead_tr = div.find_element(By.CSS_SELECTOR, "thead tr")
    columns_th = [th.text for th in thead_tr.find_elements(By.TAG_NAME, "th") if th.text != "股吧"]
    columns_td = [td.text for td in thead_tr.find_elements(By.TAG_NAME, "td") if td.text != "股吧"]
    columns = columns_th + columns_td

    all_data = []
    trs = div.find_elements(By.CSS_SELECTOR, "tbody tr")
    for tr in trs:
        tds = tr.find_elements(By.TAG_NAME, "td")
        ths = tr.find_elements(By.TAG_NAME, "th")
        row_data_th = [th.text for th in ths]
        row_data_td = [td.text for td in tds]
        row_data = row_data_th + row_data_td

        # 清理并匹配列长度
        row_data = [data for data in row_data if data]
        if len(row_data) > len(columns):
            row_data = row_data[:len(columns)]
        all_data.append(row_data)

    # 检查是否有数据
    if not all_data or not columns:
        return pd.DataFrame()

    try:
        # 尝试创建DataFrame
        item_df = pd.DataFrame(all_data, columns=columns)
    except ValueError as e:
        # 捕获ValueError异常并记录日志
        logging.error("Error creating DataFrame: %s", e)
        # 返回一个空的DataFrame或者执行其他错误处理逻辑
        return pd.DataFrame()

    item_df = item_df.dropna(how='all')

    return item_df


def get_stock_latest_price(driver, code):
    price_text = None
    try:
        # print(f'{code}: {type(code)}')
        if isinstance(code, int):
            code = str(code)
        # print(f'after check - {code}: {type(code)}')
        url = f"https://quote.cfi.cn/quote_{quote(code)}.html"
        driver.get(url)

        # 获取目标信息
        try:
            element = WebDriverWait(driver, 3).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'td[class^="s_pclose"]'))
            )
            price_text = element.text.split('↑')[0].split('↓')[0].strip()
            print(f'{price_text} and {type(price_text)} and {url}')
        except Exception as e:
            print(f"Error: {e}")
    except Exception as e:
        print(f"Error: {e}")

    return price_text