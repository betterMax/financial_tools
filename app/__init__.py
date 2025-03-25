"""
期货数据管理系统的Flask应用包
"""

import os
import yaml
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

# 初始化数据库
db = SQLAlchemy()
migrate = Migrate()

def create_app(test_config=None):
    """创建并配置Flask应用"""
    app = Flask(__name__, instance_relative_config=True)
    
    # 设置默认配置
    app.config.from_mapping(
        SECRET_KEY='dev',
        SQLALCHEMY_DATABASE_URI='sqlite:///:memory:',
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

    # 确保实例文件夹存在
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    # 初始化数据库
    db.init_app(app)
    migrate.init_app(app, db)

    # 注册蓝图
    from app.routes import future_info, transaction, trade, monitor
    app.register_blueprint(future_info.bp)
    app.register_blueprint(transaction.bp)
    app.register_blueprint(trade.bp)
    app.register_blueprint(monitor.bp)

    # 注册首页路由
    @app.route('/')
    def index():
        return 'Hello, 期货数据管理系统!'

    return app 