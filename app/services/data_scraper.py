"""
数据爬取服务
用于从外部网站获取期货数据
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
import logging
from datetime import datetime
import re

logger = logging.getLogger(__name__)

class FutureDataScraper:
    """期货数据爬取类"""
    
    def __init__(self, url="http://121.37.80.177/fees.html"):
        """初始化爬虫"""
        self.url = url
    
    def fetch_future_daily(self):
        """
        从网页爬取期货每日数据
        返回一个包含期货数据的DataFrame
        """
        try:
            # 检查当前时间是否在交易时间内
            current_time = datetime.now().time()
            is_trading_hours = (
                current_time >= datetime.strptime('09:00', '%H:%M').time() and 
                current_time <= datetime.strptime('17:00', '%H:%M').time()
            )
            logger.debug(f"当前时间: {current_time}, 是否在交易时间内: {is_trading_hours}")
            
            # 如果不在交易时间内，获取当前的主力合约信息
            current_main_contracts = {}
            if not is_trading_hours:
                logger.debug("非交易时间，将保持现有主力合约不变")
                try:
                    from app.database.db_manager import db
                    from app.models.future_info import FutureDaily
                    # 获取现有的主力合约信息
                    main_contracts = FutureDaily.query.filter_by(is_main_contract=True).all()
                    for contract in main_contracts:
                        current_main_contracts[contract.product_code.upper()] = contract.contract_code
                    logger.debug(f"从数据库获取到的现有主力合约: {current_main_contracts}")
                except Exception as e:
                    logger.error(f"获取现有主力合约信息失败: {str(e)}")
            
            # 发送HTTP请求
            logger.debug(f"开始请求URL: {self.url}")
            response = requests.get(self.url)
            response.raise_for_status()  # 如果请求失败则抛出异常
            
            # 获取二进制内容，然后以GB2312编码解析
            content = response.content
            html_text = content.decode('GB2312', errors='replace')
            
            logger.debug(f"请求成功，状态码: {response.status_code}")
            logger.debug(f"响应内容长度: {len(html_text)}")
            
            # 使用BeautifulSoup解析HTML
            soup = BeautifulSoup(html_text, 'html.parser')
            
            # 查找表格
            table = soup.find('table')
            if not table:
                logger.error("未找到数据表格")
                logger.debug(f"页面内容前100字符: {html_text[:100]}")
                return None
            
            logger.debug("找到数据表格，开始解析")
            
            # 解析表格数据
            headers = []
            header_row = table.find('tr')
            if header_row:
                headers = [th.text.strip() for th in header_row.find_all('th')]
                logger.debug(f"表头: {headers}")
                
                # 检查表头是否包含预期的中文字段
                if not any(('交易所' in h or '合约' in h) for h in headers):
                    logger.warning("表头可能存在编码问题，没有找到预期的中文字段")
            else:
                logger.warning("未找到表头行")
            
            rows = []
            data_rows = table.find_all('tr')[1:]  # 跳过表头行
            logger.debug(f"找到 {len(data_rows)} 行数据")
            
            # 用于存储每个品种的所有合约数据
            product_contracts = {}
            
            # 第一遍遍历：收集所有合约数据
            for row in data_rows:
                cols = row.find_all('td')
                if not cols:
                    continue
                
                # 获取合约代码和品种代码
                contract_code = cols[1].text.strip()
                product_code = ''.join([c for c in contract_code if c.isalpha()]).upper()
                
                if is_trading_hours:
                    # 在交易时间内，使用实际成交量
                    volume_str = cols[20].text.strip() if len(cols) > 20 else '0'
                    try:
                        volume = int(volume_str)
                    except (ValueError, TypeError):
                        volume = 0
                        
                    # 将合约信息存储到对应品种的列表中
                    if product_code not in product_contracts:
                        product_contracts[product_code] = []
                    product_contracts[product_code].append((contract_code, volume))
            
            # 确定主力合约
            product_main_contracts = {}
            if is_trading_hours:
                # 在交易时间内，根据成交量确定主力合约
                for product_code, contracts in product_contracts.items():
                    if contracts:
                        # 按成交量排序，取成交量最大的合约
                        main_contract = max(contracts, key=lambda x: x[1])[0]
                        product_main_contracts[product_code] = main_contract
                        logger.debug(f"根据成交量确定主力合约: {product_code} {main_contract}")
            else:
                # 非交易时间，使用现有的主力合约
                product_main_contracts = current_main_contracts
                logger.debug("使用现有主力合约信息")
            
            # 第二遍遍历：处理所有数据行
            for row in data_rows:
                cols = row.find_all('td')
                if not cols:
                    continue
                
                # 获取合约代码和品种代码
                contract_code = cols[1].text.strip()
                product_code = ''.join([c for c in contract_code if c.isalpha()]).upper()
                
                # 判断是否为主力合约
                is_main = False
                if product_code in product_main_contracts:
                    if contract_code == product_main_contracts[product_code]:
                        is_main = True
                
                # 收集行数据
                row_data = [col.text.strip() for col in cols]
                row_data.append(is_main)  # 添加主力合约标志
                rows.append(row_data)
            
            # 创建DataFrame
            headers.append('is_main_contract')  # 添加主力合约标志列
            
            # 确保所有行的长度与表头一致
            for i, row in enumerate(rows):
                if len(row) != len(headers):
                    logger.warning(f"第{i+1}行数据长度({len(row)})与表头长度({len(headers)})不一致，进行调整")
                    # 如果行长度不够，用空字符串填充
                    if len(row) < len(headers):
                        row.extend([''] * (len(headers) - len(row)))
                    # 如果行长度超过，截断
                    elif len(row) > len(headers):
                        row = row[:len(headers)]
                        rows[i] = row
            
            df = pd.DataFrame(rows, columns=headers)
            
            # 记录日志
            logger.debug(f"成功获取期货数据，共{len(df)}条记录")
            logger.debug(f"数据前5行: {df.head()}")
            
            return df
            
        except Exception as e:
            logger.error(f"获取期货数据失败: {str(e)}", exc_info=True)
            return None
    
    def update_future_daily(self, db_session, FutureDaily):
        """
        更新数据库中的future_daily表
        参数:
            db_session: 数据库会话
            FutureDaily: 期货日数据模型类
        返回:
            更新的记录数量
        """
        try:
            # 获取数据
            df = self.fetch_future_daily()
            if df is None or df.empty:
                logger.error("无法更新期货日数据: 未获取到数据")
                return 0
            
            # 打印表头查看具体的字段名
            logger.debug(f"表格的字段名: {list(df.columns)}")
            
            # 清空当前数据表
            db_session.query(FutureDaily).delete()
            
            # 创建新记录
            records = []
            update_time = datetime.now()
            
            # 遍历DataFrame中的每一行
            for idx, row in df.iterrows():
                try:
                    # 提取合约代码和品种代码
                    contract_code = row.get('合约代码', '')
                    if not contract_code:
                        logger.warning(f"第{idx+1}行没有合约代码，跳过")
                        continue
                    
                    # 提取品种代码（合约代码中的字母部分）
                    product_code = ''.join([c for c in contract_code if c.isalpha()])
                    
                    # 记录处理的行号和关键字段
                    # logger.debug(f"处理第{idx+1}行，合约代码: {contract_code}, 产品代码: {product_code}")
                    
                    # 创建新记录
                    record = FutureDaily(
                        exchange=row.get('交易所', ''),
                        contract_code=contract_code,
                        contract_name=row.get('合约名称', ''),
                        product_code=product_code,
                        product_name=row.get('品种名称', ''),
                        contract_multiplier=self._safe_float(row.get('合约乘数', 0)),
                        price_tick=self._safe_float(row.get('最小跳动', 0)),
                        open_fee_rate=self._safe_float(row.get('开仓费率（按金额）', 0)),
                        open_fee=self._safe_float(row.get('开仓费用（按手）', 0)),
                        close_fee_rate=self._safe_float(row.get('平仓费率（按金额）', 0)),
                        close_fee=self._safe_float(row.get('平仓费用（按手）', 0)),
                        close_today_fee_rate=self._safe_float(row.get('平今费率（按金额）', 0)),
                        close_today_fee=self._safe_float(row.get('平今费用（按手）', 0)),
                        long_margin_rate=self._safe_float(row.get('做多保证金率（按金额）', 0)),
                        long_margin_fee=self._safe_float(row.get('做多保证金（按手）', 0)),
                        short_margin_rate=self._safe_float(row.get('做空保证金率（按金额）', 0)),
                        short_margin_fee=self._safe_float(row.get('做空保证金（按手）', 0)),
                        latest_price=self._safe_float(row.get('最新价', 0)),
                        open_interest=self._safe_int(row.get('持仓量', 0)),
                        volume=self._safe_int(row.get('成交量', 0)),
                        is_main_contract=row.get('is_main_contract', False),
                        update_time=update_time
                    )
                    records.append(record)
                    
                except Exception as e:
                    logger.error(f"解析期货日数据行失败(行号:{idx+1}): {str(e)}", exc_info=True)
                    continue
            
            # 批量添加记录
            if records:
                db_session.add_all(records)
                db_session.commit()
                logger.debug(f"成功更新期货日数据，共{len(records)}条记录")
                return len(records)
            else:
                logger.warning("无期货日数据可更新")
                return 0
                
        except Exception as e:
            logger.error(f"更新期货日数据失败: {str(e)}", exc_info=True)
            db_session.rollback()
            return 0
    
    def _normalize_contract_code(self, contract_code):
        """
        标准化合约代码格式
        例如：将 'AP505' 转换为 'AP2505'，同时确保字母部分为大写
        """
        try:
            if not contract_code:
                return contract_code
            
            # 提取字母部分和数字部分，并将字母转换为大写
            letters = ''.join(c for c in contract_code if c.isalpha()).upper()
            numbers = ''.join(c for c in contract_code if c.isdigit())
            
            # 如果数字部分是3位数，在前面加上2
            if len(numbers) == 3:
                numbers = '2' + numbers
            
            return letters + numbers
        except Exception as e:
            logger.error(f"合约代码格式转换失败: {str(e)}")
            return contract_code

    def update_future_info_from_daily(self, db_session, FutureInfo, FutureDaily):
        """
        根据future_daily表更新future_info表的数据
        参数:
            db_session: 数据库会话
            FutureInfo: 期货基础信息模型类
            FutureDaily: 期货日数据模型类
        返回:
            更新的记录数量
        """
        try:
            # 获取当前数据库中的所有期货基础信息
            # 将contract_letter转换为大写用于统一比较
            futures = {f.contract_letter.upper(): f for f in db_session.query(FutureInfo).all()}
            logger.debug(f"从future_info表获取到{len(futures)}个期货品种")
            
            # 获取最新的future_daily数据的所有产品代码
            product_data = {}
            
            # 为每个产品代码找出主力合约
            main_contracts = {}
            for daily in db_session.query(FutureDaily).filter(FutureDaily.is_main_contract == True).all():
                # 将product_code转换为大写
                product_code_upper = daily.product_code.upper()
                # 如果这个品种代码不在future_info中，才记录为主力合约
                if product_code_upper not in futures:
                    main_contracts[product_code_upper] = self._normalize_contract_code(daily.contract_code)
            
            logger.debug(f"找到{len(main_contracts)}个主力合约")
            
            # 记录每个品种的主力合约
            product_main_contracts = {}
            for daily in db_session.query(FutureDaily).filter(FutureDaily.is_main_contract == True).all():
                product_code_upper = daily.product_code.upper()
                if product_code_upper not in product_main_contracts:
                    product_main_contracts[product_code_upper] = self._normalize_contract_code(daily.contract_code)
            
            for daily in db_session.query(FutureDaily).all():
                # 将product_code转换为大写
                product_code_upper = daily.product_code.upper()
                if product_code_upper not in product_data:
                    product_data[product_code_upper] = daily
            
            logger.debug(f"从future_daily表获取到{len(product_data)}个品种的数据")
            
            # 更新计数器
            updated_count = 0
            not_found_count = 0
            
            # 更新期货基础信息
            for contract_letter, future in futures.items():
                contract_letter_upper = contract_letter.upper()
                if contract_letter_upper in product_data:
                    daily = product_data[contract_letter_upper]
                    
                    # 记录更新前的值
                    old_values = {
                        'exchange': future.exchange,
                        'contract_multiplier': future.contract_multiplier,
                        'long_margin_rate': future.long_margin_rate,
                        'short_margin_rate': future.short_margin_rate,
                        'open_fee': future.open_fee,
                        'close_fee': future.close_fee,
                        'close_today_rate': future.close_today_rate,
                        'close_today_fee': future.close_today_fee,
                        'current_main_contract': future.current_main_contract
                    }
                    
                    # # 打印平今费率的转换过程
                    # logger.debug(f"更新期货 {future.contract_letter} 的平今费率:")
                    # logger.debug(f"  - FutureDaily中的值: {daily.close_today_fee_rate}")
                    # logger.debug(f"  - 更新前FutureInfo中的值: {future.close_today_rate}")
                    
                    # 更新字段
                    future.exchange = daily.exchange
                    future.contract_multiplier = daily.contract_multiplier
                    future.long_margin_rate = daily.long_margin_rate
                    future.short_margin_rate = daily.short_margin_rate
                    future.open_fee = daily.open_fee
                    future.close_fee = daily.close_fee
                    future.close_today_rate = daily.close_today_fee_rate
                    future.close_today_fee = daily.close_today_fee
                    
                    # logger.debug(f"  - 更新后FutureInfo中的值: {future.close_today_rate}")
                    
                    # 更新主力合约
                    if contract_letter_upper in product_main_contracts:
                        future.current_main_contract = product_main_contracts[contract_letter_upper]
                    
                    # 检查是否有实际更新
                    has_changes = False
                    changes = []
                    for field, old_value in old_values.items():
                        new_value = getattr(future, field)
                        if old_value != new_value:
                            has_changes = True
                            changes.append(f"{field}: {old_value} -> {new_value}")
                    
                    if has_changes:
                        logger.debug(f"更新期货 {future.contract_letter} ({future.name}): {', '.join(changes)}")
                        updated_count += 1
                else:
                    not_found_count += 1
                    logger.warning(f"未找到期货 {future.contract_letter} ({future.name}) 的每日数据")
            
            # 更新不在future_info中的主力合约
            for product_code, contract_code in main_contracts.items():
                # 创建新的期货基础信息记录
                daily = product_data.get(product_code)
                if daily:
                    future_info = FutureInfo(
                        contract_letter=product_code,
                        name=daily.product_name,
                        market=0,  # 默认为国内市场
                        exchange=daily.exchange,
                        contract_multiplier=daily.contract_multiplier,
                        long_margin_rate=daily.long_margin_rate,
                        short_margin_rate=daily.short_margin_rate,
                        open_fee=daily.open_fee,
                        close_fee=daily.close_fee,
                        close_today_rate=daily.close_today_fee_rate,
                        close_today_fee=daily.close_today_fee,
                        current_main_contract=contract_code
                    )
                    db_session.add(future_info)
                    updated_count += 1
                    logger.debug(f"新增期货品种 {product_code} ({daily.product_name})")
            
            # 提交更改
            db_session.commit()
            
            logger.debug(f"根据期货日数据成功更新{updated_count}条期货基础信息，{not_found_count}个期货未找到对应数据")
            return updated_count
            
        except Exception as e:
            logger.error(f"根据期货日数据更新期货基础信息失败: {str(e)}")
            db_session.rollback()
            return 0
    
    def update_future_info(self, db_session, FutureInfo):
        """
        更新数据库中的期货基础信息 (直接从网页获取)
        参数:
            db_session: 数据库会话
            FutureInfo: 期货基础信息模型类
        返回:
            更新的记录数量
        """
        try:
            # 获取数据
            df = self.fetch_future_daily()
            if df is None or df.empty:
                logger.error("无法更新期货基础信息: 未获取到数据")
                return 0
            
            # 获取当前数据库中的所有期货基础信息
            futures = {f.contract_letter: f for f in db_session.query(FutureInfo).all()}
            
            # 更新计数器
            updated_count = 0
            
            # 遍历DataFrame中的每一行
            for _, row in df.iterrows():
                try:
                    # 提取合约字母
                    contract_code = row.get('合约代码', '')
                    if not contract_code:
                        continue
                    
                    # 假设合约代码的前1-2位是合约字母
                    contract_letter = ''.join([c for c in contract_code if c.isalpha()])
                    
                    # 如果合约字母在数据库中存在，则更新相应字段
                    if contract_letter in futures:
                        future = futures[contract_letter]
                        
                        # 更新字段
                        future.exchange = row.get('交易所', '')
                        future.contract_multiplier = self._safe_float(row.get('合约乘数', 0))
                        future.long_margin_rate = self._safe_float(row.get('做多保证金率（按金额）', 0))
                        future.short_margin_rate = self._safe_float(row.get('做空保证金率（按金额）', 0))
                        future.open_fee = self._safe_float(row.get('开仓费用（按手）', 0))
                        future.close_fee = self._safe_float(row.get('平仓费用（按手）', 0))
                        future.close_today_rate = self._safe_float(row.get('平今费率（按比例）', 0))
                        future.close_today_fee = self._safe_float(row.get('平今费用（按手）', 0))
                        
                        # 如果是主连合约，更新主力合约字段
                        if row.get('is_main_contract', False):
                            future.current_main_contract = contract_code
                        
                        updated_count += 1
                        
                except Exception as e:
                    logger.error(f"更新单个期货信息失败: {str(e)}")
                    continue
            
            # 提交更改
            db_session.commit()
            
            logger.debug(f"成功更新{updated_count}条期货基础信息")
            return updated_count
            
        except Exception as e:
            logger.error(f"更新期货基础信息失败: {str(e)}")
            db_session.rollback()
            return 0
    
    def _safe_float(self, value):
        """安全地转换为浮点数"""
        try:
            if pd.isna(value):
                return None
            return float(value)
        except (ValueError, TypeError):
            return None
    
    def _safe_int(self, value):
        """安全地转换为整数"""
        try:
            if pd.isna(value):
                return None
            return int(value)
        except (ValueError, TypeError):
            return None 