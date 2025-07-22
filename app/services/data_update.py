"""
数据更新服务
负责定期更新期货数据
"""

import logging
import threading
import yaml
from pathlib import Path
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from app.database.db_manager import db
from app.models.future_info import FutureInfo, FutureDaily
from app.services.data_scraper import FutureDataScraper
from retrying import retry
import os

logger = logging.getLogger(__name__)

class DataUpdateService:
    """
    数据更新服务
    用于定期更新数据库中的期货数据
    """
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls, app=None):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance.app = None
                cls._instance.scraper = FutureDataScraper()
                cls._instance.scheduler = None  # 延迟初始化调度器
                cls._instance.config = None
                cls._instance._initialized = False
            return cls._instance
    
    def __init__(self, app=None):
        with self._lock:
            if not self._initialized:
                logger.info("初始化数据更新服务...")
                self.app = app
                self.config = self._load_config()
                self._initialized = True
                
                if app is not None:
                    self.init_app(app)
    
    def _load_config(self):
        """
        加载配置文件
        """
        config_path = Path("config.yaml")
        if not config_path.exists():
            # 创建默认配置
            default_config = {
                "data_update": {
                    "schedule": [
                        {"hour": "9", "minute": "0"},
                        {"hour": "15", "minute": "0"}
                    ]
                }
            }
            with open(config_path, "w", encoding="utf-8") as f:
                yaml.dump(default_config, f, allow_unicode=True)
            return default_config
        
        with open(config_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    
    def init_app(self, app):
        """
        初始化应用
        
        Args:
            app: Flask应用实例
        """
        logger.info(f"初始化应用到数据更新服务，应用ID: {id(app)}")
        self.app = app
        
        # 在主进程中初始化调度器
        if not self.scheduler:
            self.scheduler = BackgroundScheduler()
            if not app.debug or os.environ.get('WERKZEUG_RUN_MAIN') == 'true':
                logger.info("在主进程中启动调度器...")
                self.start_scheduler()
    
    def update_future_daily_data(self):
        """
        更新期货每日数据
        
        从网站爬取最新的期货数据，存入future_daily表，然后更新future_info表
        """
        try:
            with self.app.app_context():
                # 更新future_daily表
                records_count = self.scraper.update_future_daily(db.session, FutureDaily)
                if records_count > 0:
                    # 根据future_daily表更新future_info表
                    updated_count = self.scraper.update_future_info_from_daily(db.session, FutureInfo, FutureDaily)
                    logger.info(f"期货数据更新完成: 爬取{records_count}条记录，更新{updated_count}条期货基础信息")
                    return True
                else:
                    logger.warning("期货数据更新失败: 未能爬取任何数据")
                    return False
        except Exception as e:
            logger.error(f"期货数据更新出错: {str(e)}")
            raise
    
    def manual_update(self):
        """
        手动触发数据更新
        
        Returns:
            dict: 更新结果
        """
        try:
            logger.info("开始手动更新数据...")
            with self.app.app_context():
                # 1. 更新future_daily表
                logger.info("正在更新future_daily表...")
                records_count = self.scraper.update_future_daily(db.session, FutureDaily)
                
                if records_count > 0:
                    # 2. 更新future_info表
                    logger.info("正在根据future_daily表更新future_info表...")
                    updated_count = self.scraper.update_future_info_from_daily(db.session, FutureInfo, FutureDaily)
                    
                    return {
                        'code': 0,
                        'msg': f'数据更新成功：新增{records_count}条每日数据，更新{updated_count}条期货信息',
                        'data': {
                            'daily_count': records_count,
                            'info_count': updated_count
                        }
                    }
                else:
                    logger.warning("未能获取到新的每日数据")
                    return {
                        'code': 1,
                        'msg': '未能获取到新的数据，可能是网络问题或数据源未更新',
                        'data': None
                    }
                    
        except Exception as e:
            error_msg = f"手动更新数据失败: {str(e)}"
            logger.error(error_msg)
            return {
                'code': 1,
                'msg': error_msg,
                'data': None
            }
    
    def start_scheduler(self):
        """
        启动定时任务调度器
        """
        if self.scheduler.running:
            logger.warning(f"调度器已经在运行中，scheduler_id: {id(self.scheduler)}")
            return
        
        try:
            logger.info(f"开始启动调度器，scheduler_id: {id(self.scheduler)}")
            
            # 获取调度器配置
            scheduler_config = self.config.get("data_update", {}).get("scheduler", {})
            
            # 配置调度器
            self.scheduler.configure(
                timezone=scheduler_config.get("timezone", "Asia/Shanghai"),
                max_instances=scheduler_config.get("max_instances", 1),
                coalesce=scheduler_config.get("coalesce", True),
                misfire_grace_time=scheduler_config.get("misfire_grace_time", 60)
            )
            
            # 从配置文件读取定时设置
            schedule_config = self.config.get("data_update", {}).get("schedule", [])
            logger.info(f"读取到的定时配置: {schedule_config}")
            
            # 添加定时任务
            for schedule in schedule_config:
                try:
                    hour = schedule.get("hour", "*")
                    minute = schedule.get("minute", "0")
                    job_id = f"update_future_data_{hour}_{minute}"
                    
                    # 创建触发器
                    trigger = CronTrigger(
                        hour=hour,
                        minute=minute,
                        timezone=scheduler_config.get("timezone", "Asia/Shanghai")
                    )
                    
                    # 如果启用重试，创建重试装饰器
                    if schedule.get("retry", False):
                        max_retries = schedule.get("max_retries", 3)
                        retry_delay = schedule.get("retry_delay", 300)
                        
                        @retry(
                            stop_max_attempt_number=max_retries + 1,
                            wait_fixed=retry_delay * 1000,  # 毫秒
                            retry_on_exception=lambda e: isinstance(e, Exception)
                        )
                        def wrapped_task():
                            return self.update_future_daily_data()
                        
                        task_func = wrapped_task
                    else:
                        task_func = self.update_future_daily_data
                    
                    # 添加任务
                    job = self.scheduler.add_job(
                        task_func,
                        trigger=trigger,
                        id=job_id,
                        replace_existing=True,
                        max_instances=1,
                        coalesce=True
                    )
                    
                    # 安全地获取下次运行时间
                    next_run = job.next_run_time.strftime('%Y-%m-%d %H:%M:%S') if job and hasattr(job, 'next_run_time') and job.next_run_time else '未知'
                    logger.info(f"添加定时任务: {job_id}, 下次运行时间: {next_run}")
                    
                except Exception as e:
                    logger.error(f"添加定时任务失败: {str(e)}")
            
            # 启动调度器
            if not self.scheduler.running:
                self.scheduler.start()
                logger.info(f"数据更新调度器已启动，当前状态: {self.get_scheduler_status()}")
            
        except Exception as e:
            logger.error(f"启动调度器失败: {str(e)}")
            # 确保调度器被正确关闭
            if self.scheduler.running:
                self.scheduler.shutdown()
    
    def stop_scheduler(self):
        """
        停止定时任务调度器
        """
        if not self.scheduler.running:
            logger.warning(f"调度器未在运行，scheduler_id: {id(self.scheduler)}")
            return
        
        logger.info(f"开始停止调度器，scheduler_id: {id(self.scheduler)}")
        self.scheduler.shutdown()
        logger.info("数据更新调度器已停止")

    def get_scheduler_status(self):
        """
        获取调度器状态
        """
        if not self.scheduler:
            return {
                "status": "未初始化",
                "jobs": []
            }
        
        return {
            "status": "运行中" if self.scheduler.running else "已停止",
            "jobs": [{
                "id": job.id,
                "next_run_time": job.next_run_time.strftime("%Y-%m-%d %H:%M:%S") if job.next_run_time else None,
                "trigger": str(job.trigger)
            } for job in self.scheduler.get_jobs()]
        }

# 创建服务实例
data_update_service = DataUpdateService()

def init_data_update_service(app):
    """
    初始化数据更新服务
    
    Args:
        app: Flask应用实例
    """
    data_update_service.init_app(app)
    
    # 设置应用标记，用于跟踪是否已经初始化
    app._future_data_initialized = False
    
    # 在Flask 2.2+中，before_first_request被移除，使用after_request替代
    @app.after_request
    def after_request_handler(response):
        # 检查是否需要初始化数据
        if not app._future_data_initialized:
            app._future_data_initialized = True
            # 在后台线程中执行数据更新
            thread = threading.Thread(target=data_update_service.update_future_daily_data)
            thread.daemon = True
            thread.start()
        return response
    
    # 启动定时任务调度器
    data_update_service.start_scheduler()
    
    # 应用关闭时停止调度器
    @app.teardown_appcontext
    def stop_scheduler(exception=None):
        data_update_service.stop_scheduler() 