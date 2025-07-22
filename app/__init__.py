"""
期货数据管理系统的Flask应用包
"""

import os
import yaml
import click
from flask import Flask
from app.database.db_manager import db, migrate, init_db
from app.routes.future_info import bp as future_info_bp
from app.routes.transaction import bp as transaction_bp
from app.routes.trade import bp as trade_bp
from app.routes.monitor import bp as monitor_bp
from app.routes.dimension import bp as dimension_bp

def create_app(test_config=None):
    """创建并配置Flask应用"""
    app = Flask(__name__, instance_relative_config=True)
    
    # 设置默认配置
    app.config.from_mapping(
        SECRET_KEY='dev',
        SQLALCHEMY_DATABASE_URI=f'sqlite:///{os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "financial_tools.db")}',
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
    )

    # 加载配置文件
    if test_config is None:
        # 尝试从config.yaml加载配置
        config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config.yaml')
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
                if config and 'flask' in config:
                    app.config.update(config['flask'])
    else:
        # 使用测试配置
        app.config.from_mapping(test_config)

    # 确保data文件夹存在
    data_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
    try:
        os.makedirs(data_path, exist_ok=True)
    except OSError:
        pass
        
    # 确保实例文件夹存在
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    # 初始化数据库
    init_db(app)

    # 注册蓝图
    register_blueprints(app)

    # 初始化数据更新服务
    from app.services.data_update import init_data_update_service
    init_data_update_service(app)
    
    # 注册命令行命令
    register_commands(app)

    # 注册首页路由
    @app.route('/')
    def index():
        from flask import render_template
        return render_template('index.html')

    return app

def register_blueprints(app):
    app.register_blueprint(future_info_bp)
    app.register_blueprint(transaction_bp)
    app.register_blueprint(trade_bp)
    app.register_blueprint(monitor_bp)
    app.register_blueprint(dimension_bp)

def register_commands(app):
    """注册Flask命令行命令"""
    @app.cli.command('update-future-data')
    @click.option('--mode', '-m', type=click.Choice(['daily', 'info', 'both']), default='both',
                  help='更新模式: daily=只更新future_daily表, info=只更新future_info表, both=两者都更新')
    def update_future_data(mode):
        """更新期货数据，包括future_daily和future_info表"""
        from app.models.future_info import FutureInfo, FutureDaily
        from app.services.data_scraper import FutureDataScraper
        
        click.echo(f"开始更新期货数据，模式: {mode}")
        
        scraper = FutureDataScraper()
        
        if mode in ['daily', 'both']:
            # 更新future_daily表
            click.echo("正在更新future_daily表...")
            records_count = scraper.update_future_daily(db.session, FutureDaily)
            click.echo(f"future_daily表更新完成，共{records_count}条记录")
        
        if mode in ['info', 'both']:
            if mode == 'both':
                # 根据future_daily表更新future_info表
                click.echo("正在根据future_daily表更新future_info表...")
                updated_count = scraper.update_future_info_from_daily(db.session, FutureInfo, FutureDaily)
            else:
                # 直接从网站更新future_info表
                click.echo("正在直接从网站更新future_info表...")
                updated_count = scraper.update_future_info(db.session, FutureInfo)
            click.echo(f"future_info表更新完成，共更新{updated_count}条记录")
            
        click.echo("期货数据更新任务完成")
    
    @app.cli.command('init-trend-info')
    @click.option('--force', '-f', is_flag=True, help='强制重新初始化，清空现有数据')
    def init_trend_info_cmd(force):
        """初始化trend_info表数据，从config/trend_list.csv导入"""
        from app.models.dimension import TrendInfo
        from app.database.init_trend_info import init_trend_info
        
        if force:
            # 如果强制初始化，先清空现有数据
            click.echo("正在清空trend_info表...")
            db.session.query(TrendInfo).delete()
            db.session.commit()
            click.echo("trend_info表已清空")
        
        # 初始化trend_info表
        click.echo("正在初始化trend_info表...")
        init_trend_info()
        count = db.session.query(TrendInfo).count()
        click.echo(f"trend_info表初始化完成，共{count}条记录")

    @app.cli.command('init-candle-info')
    @click.option('--force', '-f', is_flag=True, help='强制重新初始化，清空现有数据')
    def init_candle_info_cmd(force):
        """初始化candle_info表数据，从config/candle_info.csv导入"""
        from app.models.dimension import CandleInfo
        from app.database.init_trend_info import init_candle_info
        
        if force:
            # 如果强制初始化，先清空现有数据
            click.echo("正在清空candle_info表...")
            db.session.query(CandleInfo).delete()
            db.session.commit()
            click.echo("candle_info表已清空")
        
        # 初始化candle_info表
        click.echo("正在初始化candle_info表...")
        init_candle_info()
        count = db.session.query(CandleInfo).count()
        click.echo(f"candle_info表初始化完成，共{count}条记录") 