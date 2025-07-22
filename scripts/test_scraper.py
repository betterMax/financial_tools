#!/usr/bin/env python3
"""
测试期货数据爬取功能
"""

import os
import sys
import logging
import requests
from bs4 import BeautifulSoup
import chardet

# 配置日志
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger()

def test_direct_fetch():
    """直接测试网页爬取，不依赖其他组件"""
    url = "http://121.37.80.177/fees.html"
    
    print(f"开始直接请求URL: {url}")
    
    try:
        # 发送HTTP请求
        response = requests.get(url)
        response.raise_for_status()
        
        # 检测内容编码
        content = response.content
        detected = chardet.detect(content)
        print(f"检测到的编码: {detected}")
        
        # 尝试几种不同的编码
        encodings = ['utf-8', 'gbk', 'gb2312', 'gb18030', 'big5', detected['encoding']]
        
        for encoding in encodings:
            if not encoding:
                continue
                
            print(f"\n尝试使用 {encoding} 编码解析内容")
            try:
                html_text = content.decode(encoding)
                soup = BeautifulSoup(html_text, 'html.parser')
                
                # 查找表格
                table = soup.find('table')
                if not table:
                    print(f"使用 {encoding} 编码未找到数据表格")
                    continue
                
                print(f"使用 {encoding} 编码找到数据表格，开始解析")
                
                # 解析表格数据
                headers = []
                header_row = table.find('tr')
                if header_row:
                    headers = [th.text.strip() for th in header_row.find_all('th')]
                    print(f"表头: {headers}")
                    
                    # 如果表头看起来不像乱码，则继续处理
                    if any('交易所' in h for h in headers) or any('合约' in h for h in headers):
                        print(f"\n使用 {encoding} 编码成功解析表头！")
                        
                        rows = []
                        data_rows = table.find_all('tr')[1:]  # 跳过表头行
                        print(f"找到 {len(data_rows)} 行数据")
                        
                        # 只处理前3行作为示例
                        for i, row in enumerate(data_rows[:3]):
                            cols = row.find_all('td')
                            row_data = [col.text.strip() for col in cols]
                            rows.append(row_data)
                            
                            print(f"\n第{i+1}行数据:")
                            for j, cell in enumerate(row_data):
                                if j < len(headers):
                                    print(f"  {headers[j]}: {cell}")
                                    
                        # 找到正确编码，不需要继续尝试
                        break
                    
                else:
                    print(f"使用 {encoding} 编码未找到表头行")
                
            except Exception as e:
                print(f"使用 {encoding} 编码解析失败: {str(e)}")
        
        print("\n测试完成")
        
    except Exception as e:
        print(f"测试失败: {str(e)}")

if __name__ == '__main__':
    print("=== 测试直接爬取数据 ===")
    test_direct_fetch() 