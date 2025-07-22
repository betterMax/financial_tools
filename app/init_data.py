import os
import pandas as pd
from app import db
from app.models.dimension import CandleInfo

def init_candle_info():
    """
    初始化K线形态信息表
    如果表为空，则从CSV文件导入数据
    """
    # 检查表是否为空
    if CandleInfo.query.first() is None:
        # 获取CSV文件的绝对路径
        csv_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'app', 'config', 'candle_info.csv')
        
        # 读取CSV文件
        df = pd.read_csv(csv_path)
        
        # 遍历数据并插入到数据库
        for _, row in df.iterrows():
            if pd.notna(row['name']):  # 只插入name不为空的记录
                candle = CandleInfo(
                    id=row['id'],
                    name=row['name']
                )
                db.session.add(candle)
        
        try:
            db.session.commit()
            print("K线形态数据初始化成功")
        except Exception as e:
            db.session.rollback()
            print(f"K线形态数据初始化失败: {str(e)}") 