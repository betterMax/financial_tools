"""
期货数据管理系统入口文件
"""

from app import create_app
import os
from app.database.schema import create_schemas
import logging

# 配置日志
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

app = create_app()

if __name__ == '__main__':
    # 设置数据库文件路径
    data_dir = os.path.join(os.getcwd(), "data")
    if not os.path.exists(data_dir):
        os.makedirs(data_dir, exist_ok=True)
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{os.path.join(data_dir, "financial_tools.db")}'
    
    # 确保表结构存在
    create_schemas(app)
    print("数据库表结构已验证!")
    
    app.run(debug=True, host='0.0.0.0', port=4950) 