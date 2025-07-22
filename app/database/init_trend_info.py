"""
初始化trend_info表的脚本
从CSV文件中读取数据，按照规则生成存储趋势信息

根据规则：
1. 从"name"解析出对应的字段：
   1.1 首先获得"name"的长度，如果是13，"category"一定是1；如果长度是4或5，"category"一定是2；如果长度是8"category"可能是0或1
   1.2 如果是13，那么最后5个字符就是"extra_info"，剩下的就是8个字符
   1.3 如果长度是8，分析最后两个字符，如果是"上涨"或"下跌"，"category"是0，否则是1
   1.4 针对8个字符的部分，每两个字符为一组，如果"category"是0，对应的分别是"time_range", "amplitude", "speed_type", "trend_type"，然后根据内容找到id
   1.5 针对8个字符的部分，每两个字符为一组，如果"category"是1，对应的分别是"time_range", "position", "amplitude", "trend_type"，然后根据内容找到id
"""

import os
import csv
import logging
from pathlib import Path
from app import db, create_app
from app.models.dimension import (
    TrendInfo, DimTimeRange, DimAmplitude, 
    DimPosition, DimSpeedType, DimTrendType, CandleInfo
)
import pandas as pd

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_csv_data():
    """加载CSV文件数据"""
    csv_path = Path(__file__).parent.parent / 'config' / 'trend_info.csv'
    data = []
    
    if not csv_path.exists():
        logger.error(f"CSV文件不存在: {csv_path}")
        raise FileNotFoundError(f"CSV文件不存在: {csv_path}")
    
    try:
        with open(csv_path, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                data.append(row)
        
        logger.info(f"从CSV文件成功加载了{len(data)}条记录")
        return data
    except Exception as e:
        logger.error(f"加载CSV文件时出错: {e}")
        raise

def init_trend_info():
    """初始化trend_info表"""
    # 检查表中是否已有数据
    if db.session.query(TrendInfo).count() > 0:
        logger.info("trend_info表已有数据，跳过初始化")
        return
    
    # 加载CSV数据
    try:
        data = load_csv_data()
    except Exception as e:
        logger.error(f"加载CSV数据失败: {e}")
        return
    
    # 提前查询所有需要的维度数据
    time_ranges = {tr.name: tr for tr in db.session.query(DimTimeRange).all()}
    amplitudes = {a.name: a for a in db.session.query(DimAmplitude).all()}
    positions = {p.name: p for p in db.session.query(DimPosition).all()}
    speed_types = {s.name: s for s in db.session.query(DimSpeedType).all()}
    trend_types = {t.name: t for t in db.session.query(DimTrendType).all()}
    
    # 创建所有trend_info记录
    trend_records = []
    errors = []
    
    for i, row in enumerate(data, 1):
        try:
            name = row['name'].strip()
            if not name:
                logger.warning(f"第{i}行缺少name值，跳过")
                continue
                
            # 根据name的长度和特征确定category及其他字段
            category, time_range_id, amplitude_id, position_id, speed_type_id, trend_type_id, extra_info = parse_name(
                name, time_ranges, amplitudes, positions, speed_types, trend_types)
            
            # 创建TrendInfo对象
            trend_info = TrendInfo(
                category=category,
                name=name,
                time_range_id=time_range_id,
                position_id=position_id,
                amplitude_id=amplitude_id,
                speed_type_id=speed_type_id,
                trend_type_id=trend_type_id,
                extra_info=extra_info
            )
            
            trend_records.append(trend_info)
        except Exception as e:
            error_msg = f"处理第{i}行时出错: {e}, 行数据: {row}"
            logger.error(error_msg)
            errors.append(error_msg)
    
    if errors:
        logger.warning(f"初始化过程中有{len(errors)}个错误，请检查日志获取详情")
    
    try:
        # 批量添加记录并提交
        db.session.add_all(trend_records)
        db.session.commit()
        logger.info(f"成功初始化 {len(trend_records)} 条trend_info记录")
    except Exception as e:
        db.session.rollback()
        logger.error(f"提交数据到数据库时出错: {e}")
        raise

def parse_name(name, time_ranges, amplitudes, positions, speed_types, trend_types):
    """
    从name解析出category和其他字段的ID
    
    Args:
        name: 趋势名称
        time_ranges: 时间范围映射表 {name: object}
        amplitudes: 幅度范围映射表 {name: object}
        positions: 位置范围映射表 {name: object}
        speed_types: 速度类型映射表 {name: object}
        trend_types: 趋势类型映射表 {name: object}
        
    Returns:
        tuple: (category, time_range_id, amplitude_id, position_id, speed_type_id, trend_type_id, extra_info)
    """
    name_length = len(name)
    
    # 初始化所有字段为None
    category = None
    time_range_id = None
    amplitude_id = None
    position_id = None
    speed_type_id = None
    trend_type_id = None
    extra_info = None
    
    # 根据长度判断category
    if name_length == 13:
        # 长度为13，一定是category=1，带extra_info
        category = 1
        extra_info = name[-5:]
        main_part = name[:8]
    elif name_length in [4, 5]:
        # 长度为4或5，一定是category=2，其他字段为空
        category = 2
        return category, None, None, None, None, None, None
    elif name_length == 8:
        # 长度为8，需要进一步分析
        main_part = name
        if name.endswith('上涨') or name.endswith('下跌'):
            category = 0
        else:
            category = 1
    else:
        # 其他长度，出错
        raise ValueError(f"无法处理的名称长度: {name_length}, 名称: {name}")
    
    # 拆分main_part为4个两字符的部分
    parts = [main_part[i:i+2] for i in range(0, 8, 2)]
    
    if category == 0:
        # 对于category=0，顺序是：时间范围、幅度范围、速度类型、趋势类型
        time_range_name, amplitude_name, speed_type_name, trend_type_name = parts
        
        if time_range_name in time_ranges:
            time_range_id = time_ranges[time_range_name].id
        else:
            raise ValueError(f"找不到时间范围: {time_range_name}")
            
        if amplitude_name in amplitudes:
            amplitude_id = amplitudes[amplitude_name].id
        else:
            raise ValueError(f"找不到幅度范围: {amplitude_name}")
            
        if speed_type_name in speed_types:
            speed_type_id = speed_types[speed_type_name].id
        else:
            raise ValueError(f"找不到速度类型: {speed_type_name}")
            
        if trend_type_name in trend_types:
            trend_type_id = trend_types[trend_type_name].id
        else:
            raise ValueError(f"找不到趋势类型: {trend_type_name}")
    
    elif category == 1:
        # 对于category=1，顺序是：时间范围、位置范围、幅度范围、趋势类型(震荡)
        time_range_name, position_name, amplitude_name, trend_type_name = parts
        
        if time_range_name in time_ranges:
            time_range_id = time_ranges[time_range_name].id
        else:
            raise ValueError(f"找不到时间范围: {time_range_name}")
            
        if position_name in positions:
            position_id = positions[position_name].id
        else:
            raise ValueError(f"找不到位置范围: {position_name}")
            
        if amplitude_name in amplitudes:
            amplitude_id = amplitudes[amplitude_name].id
        else:
            raise ValueError(f"找不到幅度范围: {amplitude_name}")
            
        # 对于category=1，趋势类型固定为"震荡"
        if '震荡' in trend_types:
            trend_type_id = trend_types['震荡'].id
        else:
            raise ValueError("找不到趋势类型: 震荡")
    
    return category, time_range_id, amplitude_id, position_id, speed_type_id, trend_type_id, extra_info

if __name__ == "__main__":
    logger.info("开始执行trend_info表初始化")
    app = create_app()
    with app.app_context():
        try:
            init_trend_info()
            logger.info("trend_info表初始化完成")
        except Exception as e:
            logger.error(f"初始化trend_info表时发生错误: {e}")
            raise 