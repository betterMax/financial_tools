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
            shangjia_url = f'https://m.shangjia.com/qihuo/{code.lower()}/'
        else:
            sina_url = f'https://finance.sina.com.cn/futures/quotes/{code}.shtml'
            shangjia_url = f'https://m.shangjia.com/qihuo/{code.lower()}/'

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


def get_latest_price(code):
    sina_url, shangjia_url = get_urls(code)
    price = None

    # 创建一个chrome浏览器的驱动，设置为无头模式
    current_directory = os.path.dirname(os.path.realpath(__file__))
    parent_directory = os.path.dirname(current_directory)
    os.environ["PATH"] += os.pathsep + parent_directory
    # print(f'path: {os.environ["PATH"]}')
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    driver = webdriver.Chrome(options=chrome_options)

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
    if price is None or price == '--':  # or code[:2] == 'SM':
        try:
            # 打开网页
            driver.get(shangjia_url)

            # 等待JavaScript加载完成
            driver.implicitly_wait(10)

            # 提取价格
            price_tag = driver.find_element(By.CSS_SELECTOR, 'div[class*="remove_data"]')
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

    for index, btn in enumerate(nav_buttons):
        btn.click()
        # 等待页面加载完成，此处增加固定等待时间，例如5秒
        time.sleep(5)

        print(f'processing page {index} - {btn.text}')
        # 找到所有的<div class="div_cont_wt">
        divs = driver.find_elements(By.CSS_SELECTOR, "div.div_cont_wt")

        for div in tqdm(divs, desc="Processing tables", leave=True):
            if not div.is_displayed():
                continue  # 跳过当前迭代，处理下一个div
            all_data = []  # 临时存储所有页的数据

            # 获取列名
            thead_tr = div.find_element(By.CSS_SELECTOR, "thead tr")
            columns_th = [th.text for th in thead_tr.find_elements(By.TAG_NAME, "th") if th.text != "股吧"]
            columns_td = [td.text for td in thead_tr.find_elements(By.TAG_NAME, "td") if td.text != "股吧"]
            columns = columns_th + columns_td

            while True:
                trs = div.find_elements(By.CSS_SELECTOR, "tbody tr")
                print(len(trs))

                # 如果数据不超过两行，跳过这个div
                if len(trs) <= 2:
                    break

                for tr in trs:

                    tds = tr.find_elements(By.TAG_NAME, "td")
                    ths = tr.find_elements(By.TAG_NAME, "th")
                    row_data_th = [th.text for th in ths]
                    row_data_td = [td.text for td in tds]
                    row_data = row_data_th + row_data_td

                    # Ensure the length of row_data matches with columns, and remove empty strings
                    row_data = [data for data in row_data if data]
                    if len(row_data) > len(columns):
                        row_data = row_data[:len(columns)]
                    all_data.append(row_data)
                break

            # Convert all_data to DataFrame
            # Check if all_data only contains empty lists
            if all(len(sublist) == 0 for sublist in all_data):
                continue  # Skip to the next iteration

            item_df = pd.DataFrame(all_data, columns=columns)
            # Drop rows where all values are NaN
            item_df = item_df.dropna(how='all')

            # If after dropping NaN rows the dataframe has less than or equal to 2 rows, skip further processing
            if len(item_df) <= 2:
                print(f'processing {item_df.iloc[0,0]}')
                pass
            else:
                columns_to_format = [col for col in item_df.columns if col not in ['代码', '名称', '涨跌幅']]
                for col in columns_to_format:
                    item_df[col] = item_df[col].apply(format_decimal)

                # Sort the dataframe
                item_df = item_df.sort_values(
                    by=["最新价", "代码"])  # assuming 最新价 is the second last column and 代码 is the first column
                item_df = item_df.reset_index(drop=True)

                # Extract value_1 and value_2
                for i, row in item_df.iterrows():
                    if (len(row["代码"]) == 3 or len(row["代码"]) == 2) and row["代码"][:-1].isalpha() and row["代码"][-1].isdigit():
                        print(f'item_df for {item_df.iloc[0,0]} and shape for {item_df.shape} and length: {len(item_df)}')
                        if i + 1 < len(item_df):
                            value_1 = item_df.iloc[i + 1]["代码"]
                            value_2 = item_df.iloc[i + 1]["最新价"]
                            results.append((value_1, value_2))
                            break

    driver.close()
    # 去重处理
    unique_results = list(set(results))
    return unique_results


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