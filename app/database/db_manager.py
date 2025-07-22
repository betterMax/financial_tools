"""
数据库管理器
负责数据库连接及会话管理
"""

from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import os

# 初始化数据库对象
db = SQLAlchemy()
migrate = Migrate()

def init_db(app):
    """
    初始化数据库连接
    
    Args:
        app: Flask应用实例
    """
    # 确保数据目录存在
    data_dir = os.path.join(os.getcwd(), "data")
    if not os.path.exists(data_dir):
        os.makedirs(data_dir, exist_ok=True)
    
    # 设置数据库URI
    sqlite_path = os.path.join(data_dir, "financial_tools.db")
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{sqlite_path}'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # 初始化SQLAlchemy和Migrate
    db.init_app(app)
    migrate.init_app(app, db)
    
    # 初始化数据库表结构和基础数据
    with app.app_context():
        from app.database.schema import create_schemas
        create_schemas(app)
        
        # 初始化trend_info表数据
        from app.database.init_trend_info import init_trend_info
        init_trend_info()
    
    return db

def get_db():
    """
    获取数据库实例
    
    Returns:
        SQLAlchemy实例
    """
    return db

def close_db():
    """
    关闭数据库连接
    """
    db.session.close() 