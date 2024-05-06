import requests
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import os
from concurrent.futures import ProcessPoolExecutor, as_completed
import concurrent.futures


# 根据code获取链接
def get_urls(code, test_links=False):
    if code != 0:
        if code[:2] == 'SI':
            sina_url = f'https://finance.sina.com.cn/futures/quotes/gfex/{code}.shtml'
            shangjia_url = f'https://www.shangjia.com/qihuo/{code.lower()}/qixianjiegou'
            eastmoney_url = f'https://quote.eastmoney.com/qihuo/{code.lower()}.html'
            baidu_url1 = f'https://gushitong.baidu.com/futures/ab-{code.lower()}'
        else:
            sina_url = f'https://finance.sina.com.cn/futures/quotes/{code}.shtml'
            shangjia_url = f'https://www.shangjia.com/qihuo/{code.lower()}/qixianjiegou'
            eastmoney_url = f'https://quote.eastmoney.com/qihuo/{code.lower()}.html'
            baidu_url1 = f'https://gushitong.baidu.com/futures/ab-{code.lower()}'

        if test_links:
            test_link(sina_url)
            test_link(shangjia_url)
            test_link(eastmoney_url)
            test_link(baidu_url1)

        return [sina_url, shangjia_url, eastmoney_url, baidu_url1]
    else:
        return [None, None, None, None]


# 测试链接是否可用
def test_link(url):
    response = requests.head(url)

    if response.status_code != 200:
        print(f'Warning: {url} is not accessible. Status code: {response.status_code}')


# 初始化Chrome驱动
def init_chrome():
    current_directory = os.path.dirname(os.path.realpath(__file__))
    # print(f'current_directory: {current_directory}')
    # parent_directory = os.path.dirname(current_directory)
    os.environ["PATH"] += os.pathsep + current_directory
    chrome_options = Options()
    chrome_options.add_argument('--headless')  # 注释这行以便观察
    driver = webdriver.Chrome(options=chrome_options)

    return driver


# 根据不同的特征进行爬取
def fetch_price_general(driver, url, selector, selector_type):
    start_time = time.time()  # 开始计时
    try_attempts = 2  # 尝试次数
    for attempt in range(try_attempts):
        try:
            if attempt > 0:  # 如果不是第一次尝试，先刷新页面
                print(f"Attempting to refresh and retry: {url}")
                driver.refresh()
                time.sleep(3)  # 给页面一些额外的时间来加载

            driver.get(url)
            # 等待JavaScript加载完成
            driver.implicitly_wait(5)
            if selector_type == "css":
                element = driver.find_element(By.CSS_SELECTOR, selector)
            elif selector_type == "xpath":
                element = driver.find_element(By.XPATH, selector)
            else:
                print(f"Unsupported selector type: {selector_type}")
                return None, None

            price_text = element.text
            if price_text:
                price = round(float(price_text.replace(',', '')), 2)  # 转换为浮点数并四舍五入到两位小数
                end_time = time.time()
                elapsed_time = end_time - start_time  # 计算耗时
                print(f"价格来源：{url}，价格：{price:.2f}，耗时：{elapsed_time:.2f}秒，开始时间：{start_time:.2f}秒, 结束时间：{end_time:.2f}秒")  # 打印信息
                return price, elapsed_time  # 返回价格和耗时
        except Exception as e:
            print(f"Error fetching from {url}")
    return None, None


# 某一个具体的爬取任务
def fetch_price_parallel(url, selector, selector_type):
    # 假设这里包含了webdriver的初始化逻辑，比如调用init_chrome()，或者直接在这里初始化
    driver = init_chrome()
    price, elapsed_time = fetch_price_general(driver, url, selector, selector_type)
    driver.quit()  # 确保每次使用后关闭webdriver
    return url, price, elapsed_time


# 针对第一个标的进行测试，选择爬取的优先级
def fetch_prices_for_code(code):
    urls_order = ["sina", "shangjia", "eastmoney", "baidu"]
    urls = get_urls(code)
    initial_code_results = parallel_fetch_prices(urls)
    print(f'{code}: {initial_code_results}')

    # 过滤出有效的结果（价格不为None且不为'--'）
    valid_results = [result for result in initial_code_results if result[1] is not None and result[1] != '--']

    # 找出最常见的价格
    prices = [result[1] for result in valid_results]
    common_prices = [price for price in set(prices) if prices.count(price) > 1]

    # 只保留具有最常见价格的结果，并按爬取耗时排序
    sorted_valid_results = sorted([result for result in valid_results if result[1] in common_prices],
                                  key=lambda x: x[2])

    # 使用url_to_source_name转换URL为来源简称，再获取索引
    return [urls_order.index(url_to_source_name(result[0])) for result in sorted_valid_results if url_to_source_name(result[0]) in urls_order], common_prices


def fetch_for_remaining_codes(code_list, valid_methods_order):
    final_prices = {}
    for code in code_list[1:]:  # Skip the first code, as it's already processed
        urls = get_urls(code)  # 为当前code生成URLs
        for method_index in valid_methods_order:  # 遍历有效方法的索引
            url = urls[method_index]  # 根据有效方法的索引选择URL
            selector, selector_type = method_to_details(url)  # 根据URL确定选择器和类型
            print(f"Fetching price for {code} from {url} with selector: {selector} and selector_type: {selector_type}")
            driver = init_chrome()
            price, elapsed_time = fetch_price_general(driver, url, selector, selector_type)
            driver.quit()
            if price is not None and price != '--':
                final_prices[code] = price
                print(f"Code: {code}, Price: {price} using {url}")
                break  # 成功获取到价格后跳出循环

    return final_prices


# 获取所有方案的爬取结果
def parallel_fetch_prices(urls):
    with ProcessPoolExecutor() as executor:
        futures = []
        for url in urls:
            selector, selector_type = method_to_details(url)  # 确定选择器和类型
            if selector and selector_type:  # 确保它们都不是None
                futures.append(executor.submit(fetch_price_parallel, url, selector, selector_type))

        results = []
        for future in as_completed(futures):
            try:
                results.append(future.result())
            except Exception as e:
                print(f"Parallel fetch encountered an error: {e}")
        return results


# 根据链接选择爬取特征
def method_to_details(url):
    # 根据get_urls函数返回的URL顺序确定选择器和选择器类型
    urls_order = ["sina", "shangjia", "eastmoney", "baidu"]
    css_selectors = ['td[class*="price"]',
                     '//span[text()="收盘价"]/following-sibling::strong',
                     '//div[@class="zxj"]/span/span',# 'div.zxj > span > span.price_up',
                     'span.b_price']
    selector_types = ['css', 'xpath', 'xpath', 'css']

    # 确定URL对应的索引
    index = None
    for i, key in enumerate(urls_order):
        if key in url:
            index = i
            break

    if index is not None:
        # 返回对应的选择器和选择器类型
        return css_selectors[index], selector_types[index]
    else:
        # 如果URL不匹配，返回None
        return None, None


# 根据链接选择类别
def url_to_source_name(url):
    if "sina.com.cn" in url:
        return "sina"
    elif "shangjia.com" in url:
        return "shangjia"
    elif "eastmoney.com" in url:
        return "eastmoney"
    elif "gushitong.baidu.com" in url:
        return "baidu"
    else:
        return None


def main():
    code_list = ["FU2405", "UR2405", "AO2405"]  # 示例code列表

    # Step 1: 对第一个code使用所有配置的爬取方法，并确定最优的爬取方法顺序
    valid_urls, common_prices = fetch_prices_for_code(code_list[0])
    print("Valid URLs:", valid_urls)

    # Step 2: 对剩余的code进行爬取，使用步骤1中确定的最优爬取方法
    final_prices = fetch_for_remaining_codes(code_list, valid_urls)

    # 打印最终获取到的价格信息
    print("Final prices:", final_prices)


if __name__ == '__main__':
    main()