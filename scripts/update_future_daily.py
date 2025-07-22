#!/usr/bin/env python
"""
手动更新期货每日数据脚本
用于从命令行手动触发期货数据的更新
"""

import os
import sys
import logging
import click

# 添加项目根目录到系统路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from app.database.db_manager import db
from app.models.future_info import FutureInfo, FutureDaily
from app.services.data_scraper import FutureDataScraper

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger('update_future_daily')

@click.command()
@click.option('--update-mode', '-m', type=click.Choice(['daily', 'info', 'both']), default='both',
              help='指定更新模式: daily=只更新future_daily表, info=只更新future_info表, both=两者都更新')
def update_future_daily(update_mode):
    """更新期货每日数据和基础信息"""
    logger.info(f"开始更新期货数据，模式: {update_mode}")
    
    # 创建Flask应用实例
    app = create_app()
    
    with app.app_context():
        scraper = FutureDataScraper()
        
        if update_mode in ['daily', 'both']:
            # 更新future_daily表
            logger.info("正在更新future_daily表...")
            records_count = scraper.update_future_daily(db.session, FutureDaily)
            logger.info(f"future_daily表更新完成，共{records_count}条记录")
        
        if update_mode in ['info', 'both']:
            if update_mode == 'both':
                # 根据future_daily表更新future_info表
                logger.info("正在根据future_daily表更新future_info表...")
                updated_count = scraper.update_future_info_from_daily(db.session, FutureInfo, FutureDaily)
                logger.info(f"future_info表更新完成，共更新{updated_count}条记录")
            else:
                # 直接从网站更新future_info表
                logger.info("正在直接从网站更新future_info表...")
                updated_count = scraper.update_future_info(db.session, FutureInfo)
                logger.info(f"future_info表更新完成，共更新{updated_count}条记录")
    
    logger.info("期货数据更新任务完成")

if __name__ == '__main__':
    update_future_daily() 