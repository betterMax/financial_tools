"""
数据爬取服务
用于从外部网站获取期货数据
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
import logging
from datetime import datetime

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
            # 发送HTTP请求
            response = requests.get(self.url)
            response.raise_for_status()  # 如果请求失败则抛出异常
            
            # 使用BeautifulSoup解析HTML
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 查找表格
            table = soup.find('table')
            if not table:
                logger.error("未找到数据表格")
                return None
            
            # 解析表格数据
            headers = []
            header_row = table.find('tr')
            if header_row:
                headers = [th.text.strip() for th in header_row.find_all('th')]
            
            rows = []
            data_rows = table.find_all('tr')[1:]  # 跳过表头行
            for row in data_rows:
                cols = row.find_all('td')
                
                # 检查此行是否有黄色背景（主连合约）
                is_main_contract = False
                if cols and 'background-color: yellow' in cols[0].get('style', ''):
                    is_main_contract = True
                
                row_data = [col.text.strip() for col in cols]
                
                # 添加一个标志来标识主连合约
                row_data.append(is_main_contract)
                
                rows.append(row_data)
            
            # 创建DataFrame
            headers.append('is_main_contract')  # 添加主连合约标志列
            df = pd.DataFrame(rows, columns=headers)
            
            # 记录日志
            logger.info(f"成功获取期货数据，共{len(df)}条记录")
            
            return df
            
        except Exception as e:
            logger.error(f"获取期货数据失败: {str(e)}")
            return None
    
    def update_future_info(self, db_session, FutureInfo):
        """
        更新数据库中的期货基础信息
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
                        future.contract_multiplier = float(row.get('合约乘数', 0))
                        future.long_margin_rate = float(row.get('多头保证金率', 0))
                        future.short_margin_rate = float(row.get('空头保证金率', 0))
                        future.open_fee = float(row.get('开仓手续费', 0))
                        future.close_fee = float(row.get('平仓手续费', 0))
                        future.close_today_rate = float(row.get('平今手续费率', 0))
                        future.close_today_fee = float(row.get('平今手续费', 0))
                        
                        # 如果是主连合约，更新主力合约字段
                        if row.get('is_main_contract', False):
                            future.th_main_contract = contract_code
                        
                        updated_count += 1
                        
                except Exception as e:
                    logger.error(f"更新单个期货信息失败: {str(e)}")
                    continue
            
            # 提交更改
            db_session.commit()
            
            logger.info(f"成功更新{updated_count}条期货基础信息")
            return updated_count
            
        except Exception as e:
            logger.error(f"更新期货基础信息失败: {str(e)}")
            db_session.rollback()
            return 0 