"""
数据库初始化脚本
用于创建数据库和初始化表结构
"""

from app import create_app
from app.database.db_manager import db
from app.database.schema import create_schemas, register_models

def init_db():
    """
    初始化数据库
    创建所有定义的表结构
    """
    # 创建Flask应用实例
    flask_app = create_app()
    
    # 确保所有模型都已注册
    register_models()
    
    # 创建表结构并初始化基础数据
    create_schemas(flask_app)
    
    print("数据库表结构已成功创建!")

if __name__ == "__main__":
    init_db() 