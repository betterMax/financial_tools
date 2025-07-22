"""
数据库表结构定义
定义所有表的基本结构和关系

根据BRD文档定义的表结构:
1. future_info - 期货标的基础信息表
2. transaction_records - 交易记录表，记录每一笔开仓平仓的具体数据
3. trade_records - 交易汇总表，对一组开仓平仓交易的汇总记录
4. monitor_records - 监控标的信息表
5. 维度相关表:
   - strategy_info - 交易策略表
   - candle_info - K线形态表
   - trend_info - 走势类型基本信息表
   - dim_time_range - 走势类型的时间范围
   - dim_amplitude - 走势类型的幅度范围
   - dim_position - 走势类型的位置范围
   - dim_speed_type - 走势类型的速度范围
   - dim_trend_type - 走势类型的趋势范围
6. future_daily - 每日期货数据更新表
7. roll_trade_records - 期货换月交易记录表
"""

from app.database.db_manager import db
from sqlalchemy import MetaData, text
import os
import pandas as pd

# 定义元数据，用于创建表
metadata = MetaData()

def create_schemas(app):
    """
    创建数据库表结构
    
    Args:
        app: Flask应用实例
    """
    with app.app_context():
        # 导入所有模型以确保它们被注册到元数据中
        import app.models.future_info
        import app.models.transaction
        import app.models.trade
        import app.models.monitor
        import app.models.dimension
        
        # 创建所有表
        db.create_all()
        
        # 初始化维度数据（如果需要）
        _initialize_dimension_data()
        
        # 添加表和列的注释
        _add_comments()

def _add_comments():
    """
    添加表和列的详细注释
    基于BRD文档中的描述
    """
    # 这里添加注释逻辑，SQLite不支持注释，所以这里只是作为文档记录
    # 如果之后切换到支持注释的数据库(如MySQL或PostgreSQL)，可以实现这部分逻辑
    
    # 例如在PostgreSQL中:
    # db.session.execute(text("COMMENT ON TABLE future_info IS '期货标的基础信息表';"))
    # db.session.execute(text("COMMENT ON COLUMN future_info.contract_letter IS '合约字母：1位或者2位的英文字母，这是唯一的';"))
    pass
        
def _initialize_dimension_data():
    """
    初始化维度数据
    创建基本的维度数据，如时间范围、幅度范围、位置范围等
    
    BRD文档中描述的维度数据:
    1. dim_time_range - 短期、中期、长期
    2. dim_amplitude - 小幅、中幅、大幅
    3. dim_position - 低位、中位、高位
    4. dim_speed_type - 急速、连续、震荡
    5. dim_trend_type - 上涨、下跌、震荡
    """
    from app.models.dimension import (
        DimTimeRange, DimAmplitude, DimPosition, 
        DimSpeedType, DimTrendType, StrategyInfo, CandleInfo
    )
    
    # 如果表中没有数据，添加初始数据
    if db.session.query(DimTimeRange).count() == 0:
        time_ranges = [
            DimTimeRange(name="短期"),
            DimTimeRange(name="中期"),
            DimTimeRange(name="长期")
        ]
        db.session.add_all(time_ranges)
    
    if db.session.query(DimAmplitude).count() == 0:
        amplitudes = [
            DimAmplitude(name="小幅"),
            DimAmplitude(name="中幅"),
            DimAmplitude(name="大幅")
        ]
        db.session.add_all(amplitudes)
    
    if db.session.query(DimPosition).count() == 0:
        positions = [
            DimPosition(name="低位"),
            DimPosition(name="中位"),
            DimPosition(name="高位")
        ]
        db.session.add_all(positions)
    
    if db.session.query(DimSpeedType).count() == 0:
        speed_types = [
            DimSpeedType(name="急速"),
            DimSpeedType(name="连续"),
            DimSpeedType(name="震荡")
        ]
        db.session.add_all(speed_types)
    
    if db.session.query(DimTrendType).count() == 0:
        trend_types = [
            DimTrendType(name="上涨"),
            DimTrendType(name="下跌"),
            DimTrendType(name="震荡")
        ]
        db.session.add_all(trend_types)
    
    # 添加基础策略数据
    if db.session.query(StrategyInfo).count() == 0:
        strategies = [
            StrategyInfo(name="趋势假突破", open_close_type=0, strategy_type=2),
            StrategyInfo(name="趋势真突破", open_close_type=0, strategy_type=2),
            StrategyInfo(name="趋势真跌破", open_close_type=0, strategy_type=2),
            StrategyInfo(name="趋势假跌破", open_close_type=0, strategy_type=2),
            StrategyInfo(name="压力位真突破", open_close_type=0, strategy_type=0),
            StrategyInfo(name="压力位假突破", open_close_type=0, strategy_type=0),
            StrategyInfo(name="支撑位真跌破", open_close_type=0, strategy_type=1),
            StrategyInfo(name="支撑位假跌破", open_close_type=0, strategy_type=1),
            StrategyInfo(name="换月", open_close_type=1, strategy_type=3),
            StrategyInfo(name="涨破5K", open_close_type=1, strategy_type=3),
            StrategyInfo(name="涨破10K", open_close_type=1, strategy_type=3),
            StrategyInfo(name="涨破20K", open_close_type=1, strategy_type=3),
            StrategyInfo(name="涨破30K", open_close_type=1, strategy_type=3),
            StrategyInfo(name="跌破5K", open_close_type=1, strategy_type=3),
            StrategyInfo(name="跌破10K", open_close_type=1, strategy_type=3),
            StrategyInfo(name="跌破20K", open_close_type=1, strategy_type=3),
            StrategyInfo(name="跌破30K", open_close_type=1, strategy_type=3),
            StrategyInfo(name="盘中比例止损", open_close_type=1, strategy_type=3),
            StrategyInfo(name="涨破支撑位", open_close_type=1, strategy_type=3),
            StrategyInfo(name="跌破支撑位", open_close_type=1, strategy_type=3),
            StrategyInfo(name="涨破压力位", open_close_type=1, strategy_type=3),
            StrategyInfo(name="跌破压力位", open_close_type=1, strategy_type=3),
            StrategyInfo(name="跌破手画压力位", open_close_type=1, strategy_type=3),
            StrategyInfo(name="换月不继续", open_close_type=1, strategy_type=3),
            StrategyInfo(name="比例止损", open_close_type=1, strategy_type=3),
        ]
        db.session.add_all(strategies)
    
    # 添加基础K线形态数据
    if db.session.query(CandleInfo).count() == 0:
        # 从CSV文件加载K线形态数据
        csv_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config', 'candle_info.csv')
        if os.path.exists(csv_path):
            df = pd.read_csv(csv_path)
            candle_patterns = []
            for _, row in df.iterrows():
                if pd.notna(row['name']):  # 只添加name不为空的记录
                    candle_patterns.append(CandleInfo(
                        id=row['id'],
                        name=row['name']
                    ))
            if candle_patterns:
                db.session.add_all(candle_patterns)
        else:
            # 如果CSV文件不存在，使用默认数据
            candle_patterns = [
                CandleInfo(name="连续阳线"),
                CandleInfo(name="连续阴线"),
                CandleInfo(name="长阳破位"),
                CandleInfo(name="长阴破位"),
                CandleInfo(name="上下影线"),
                CandleInfo(name="十字星")
            ]
            db.session.add_all(candle_patterns)
    
    # 提交事务
    db.session.commit()

def register_models():
    """
    注册所有模型
    确保所有模型都已导入并注册到SQLAlchemy
    """
    import app.models.future_info
    import app.models.transaction
    import app.models.trade
    import app.models.monitor
    import app.models.dimension

"""
BRD文档中表结构详细描述：

future_info表：
- id: 序号，主键
- contract_letter: 合约字母，1位或者2位的英文字母，唯一标识
- name: 名称，可能是中文（还可能包含数字），也可能是英文
- market: 市场，分为国内(0)和国外(1)
- exchange: 交易所，3-5位的英文字母
- contract_multiplier: 合约乘数，数字
- long_margin_rate: 做多保证金率（按金额），数字
- short_margin_rate: 做空保证金率（按金额），数字
- open_fee: 开仓费用（按手），数字
- close_fee: 平仓费用（按手），数字
- close_today_rate: 平今费率（按金额），数字
- close_today_fee: 平今费用（按手），数字
- th_main_contract: 同花主力合约，字母加上4位数字如PG2503
- current_main_contract: 当前主力合约，同"同花主力合约"
- th_order: 同花顺顺序，数字
- long_term_trend: 长期趋势

transaction_records表：
- id: 自动生成，主键
- trade_id: 记录从属于哪个交易，对应"trade_records"里的id
- transaction_time: 成交时间，年月日小时分
- contract_code: 合约代码，格式和"同花主力合约"一致
- name: 名称，和"名称"一致
- account: 账户，中文，记录期货账户，默认为"华安期货"
- strategy_ids: 操作策略ID，对应"strategy_info"里的序号
- strategy_name: 操作策略，对应"strategy_info"里的名称
- position_type: 多空仓位，0代表开多，1代表平多，2代表开空，3代表平空
- candle_pattern_id: K线形态ID，对应"candle_info"的id
- candle_pattern: K线形态，类似"连续上跳+长阳突破"这样的数据
- price: 成交价格，1位小数
- volume: 成交手数，实数
- contract_multiplier: 合约乘数，对应"future_info"的合约乘数
- transaction_amount: 成交金额，等于成交价格*成交手数*合约乘数
- fee: 手续费，根据开平仓类型计算
- volume_change: 手数变化，开仓为正，平仓为负
- cash_flow: 现金流，根据开平仓类型计算
- margin: 保证金，根据开平仓类型和合约规则计算
- trade_type: 交易类别，0代表模拟交易，1代表真实交易
- status: 交易状态，0代表进行，1代表暂停，2代表暂停进行，3代表结束
- latest_price: 最新价格，1位小数
- actual_yield_rate: 实际收益率，百分比2位小数
- actual_yield: 实际收益，1位小数
- stop_loss_price: 止损价格，1位小数
- stop_loss_ratio: 止损比例，1位小数
- stop_loss_yield: 止损收益，1位小数
- operation_time: 操作时间，默认为成交时间
- confidence: 信心指数，0-2
- similarity: 相似度评估
- long_term_trend_ids: 长期趋势id，"trend_info"id的list
- long_term_trend_name: 长期趋势name，多个name合并
- mid_term_trend_ids: 中期趋势id，"trend_info"id的list
- mid_term_trend_name: 中期趋势name，多个name合并

trade_records表：
- id: 自动生成
- roll_trade_main_id: 换月交易主id，可选
- contract_code: 合约代码，格式和"同花主力合约"一致
- name: 名称，格式和"transaction_records"的"名称"一致
- account: 账户，格式和"transaction_records"的"账户"一致
- strategy_ids: 操作策略ID，对应"strategy_info"里的序号
- strategy_name: 操作策略，对应"strategy_info"里的名称
- position_type: 多空仓位，0代表多头仓位，1代表空头仓位
- candle_pattern_id: K线形态ID
- candle_pattern: K线形态
- open_time: 开仓时间
- close_time: 平仓时间
- volume: 持仓手数
- contract_multiplier: 合约乘数
- cost_price: 过往持仓成本
- avg_sell_price: 平均售价
- single_profit: 单笔收益
- investment_profit: 投资收益
- investment_yield: 投资收益率
- hold_days: 持仓天数
- annual_yield: 投资年化收益率
- trade_type: 交易类别，0代表模拟交易，1代表真实交易
- confidence: 信心指数，0-2
- similarity: 相似度评估
- long_term_trend_ids: 长期趋势ids
- long_term_trend_name: 长期趋势name
- mid_term_trend_ids: 中期趋势ids
- mid_term_trend_name: 中期趋势name

monitor_records表：
- id: 序号，相当于ID
- contract: 合约，类似"future_info"的"同花主力合约"
- name: 名称
- market: 市场，分为国内和国外
- opportunity: 机会
- key_price: 关键价格，1位小数
- long_price: 开多价格，1位小数
- short_price: 开空价格，1位小数
- status: 状态，0代表有效，1代表失效，等
- latest_price: 最新价格
- long_trigger_price: 开多触发价格，1位小数
- short_trigger_price: 开空触发价格，1位小数
- long_margin: 开多一手保证金，1位小数
- short_margin: 开空一手保证金，1位小数
- candle_pattern_id: K线形态ID
- candle_pattern: K线形态
- long_term_trend_ids: 长期趋势id
- long_term_trend_name: 长期趋势name
- mid_term_trend_ids: 中期趋势id
- mid_term_trend_name: 中期趋势name
- similarity: 相似度评估
- possible_trigger_price: 可能触发价格
- ratio_ref_price: 比例对照价格，0代表最新价格，1代表关键价格
- ratio: 相应比例

工具类表格：
1. roll_trade_records - 专门记录期货的换月交易记录
2. strategy_info - 记录交易策略
3. candle_info - 记录K线形态
4. trend_info - 走势类型的基本信息
5. dim_time_range - 走势类型的时间范围
6. dim_amplitude - 走势类型的幅度范围
7. dim_position - 走势类型的位置范围
8. dim_speed_type - 走势类型的速度范围
9. dim_trend_type - 走势类型的趋势类型
""" 