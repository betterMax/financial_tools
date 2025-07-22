"""
期货基础信息模型文件

定义期货标的的基础信息表结构，包括合约字母、名称、交易所、保证金率等
"""

from app.database.db_manager import db
from datetime import datetime

class FutureInfo(db.Model):
    """
    期货标的基础信息表
    对应BRD文档中的"future_info"表
    
    维护期货标的及主连的基础信息，记录合约的保证金、手续费等交易参数
    """
    __tablename__ = 'future_info'

    id = db.Column(db.Integer, primary_key=True, comment='序号：相当于是ID')
    contract_letter = db.Column(db.String(2), unique=True, nullable=False, comment='合约字母：1位或者2位的英文字母，这是唯一的')
    name = db.Column(db.String(50), nullable=False, comment='名称：可能是中文（还可能包含数字），也可能是英文')
    market = db.Column(db.Integer, nullable=False, comment='市场：分为国内(0)和国外(1)')
    exchange = db.Column(db.String(5), comment='交易所：3-5位的英文字母，从"future_daily"用合约字母匹配')
    contract_multiplier = db.Column(db.Float, comment='合约乘数：数字，从"future_daily"用合约字母匹配')
    long_margin_rate = db.Column(db.Float, comment='做多保证金率（按金额）：数字，从"future_daily"用合约字母匹配')
    short_margin_rate = db.Column(db.Float, comment='做空保证金率（按金额）：数字，从"future_daily"用合约字母匹配')
    open_fee = db.Column(db.Float, comment='开仓费用（按手）：数字，从"future_daily"用合约字母匹配')
    close_fee = db.Column(db.Float, comment='平仓费用（按手）：数字，从"future_daily"用合约字母匹配')
    close_today_rate = db.Column(db.Float, comment='平今费率（按金额）：数字，从"future_daily"用合约字母匹配')
    close_today_fee = db.Column(db.Float, comment='平今费用（按手）：数字，从"future_daily"用合约字母匹配')
    th_main_contract = db.Column(db.String(6), comment='同花主力合约：字母加上4位数字，如PG2503')
    current_main_contract = db.Column(db.String(6), comment='当前主力合约：同"同花主力合约"')
    th_order = db.Column(db.Integer, comment='同花顺顺序：数字')
    long_term_trend = db.Column(db.String(100), comment='长期趋势：记录期货品种的长期趋势特征')
    
    def __repr__(self):
        return f'<FutureInfo {self.contract_letter} - {self.name}>'
    
    def to_dict(self):
        """转换为字典，用于API返回"""
        return {
            'id': self.id,
            'contract_letter': self.contract_letter,
            'name': self.name,
            'market': self.market,
            'exchange': self.exchange,
            'contract_multiplier': self.contract_multiplier,
            'long_margin_rate': self.long_margin_rate,
            'short_margin_rate': self.short_margin_rate,
            'open_fee': self.open_fee,
            'close_fee': self.close_fee,
            'close_today_rate': self.close_today_rate,
            'close_today_fee': self.close_today_fee, 
            'th_main_contract': self.th_main_contract,
            'current_main_contract': self.current_main_contract,
            'th_order': self.th_order,
            'long_term_trend': self.long_term_trend
        }

class FutureDaily(db.Model):
    """
    期货每日数据表
    存储从网页爬取的期货每日数据
    
    该表每日更新，覆盖之前的数据
    """
    __tablename__ = 'future_daily'
    
    id = db.Column(db.Integer, primary_key=True, comment='自增ID')
    exchange = db.Column(db.String(10), nullable=False, comment='交易所')
    contract_code = db.Column(db.String(20), index=True, nullable=False, comment='合约代码')
    contract_name = db.Column(db.String(50), nullable=False, comment='合约名称')
    product_code = db.Column(db.String(10), index=True, nullable=False, comment='品种代码')
    product_name = db.Column(db.String(50), nullable=False, comment='品种名称')
    contract_multiplier = db.Column(db.Float, nullable=False, comment='合约乘数')
    price_tick = db.Column(db.Float, nullable=False, comment='跳动变动')
    open_fee_rate = db.Column(db.Float, comment='开仓费率（按金额）')
    open_fee = db.Column(db.Float, comment='开仓费用（按手）')
    close_fee_rate = db.Column(db.Float, comment='平仓费率（按金额）')
    close_fee = db.Column(db.Float, comment='平仓费用（按手）')
    close_today_fee_rate = db.Column(db.Float, comment='平今费率（按金额）')
    close_today_fee = db.Column(db.Float, comment='平今费用（按手）')
    long_margin_rate = db.Column(db.Float, comment='做多保证金率（按金额）')
    long_margin_fee = db.Column(db.Float, comment='做多保证金（按手）')
    short_margin_rate = db.Column(db.Float, comment='做空保证金率（按金额）')
    short_margin_fee = db.Column(db.Float, comment='做空保证金（按手）')
    latest_price = db.Column(db.Float, comment='最新价')
    open_interest = db.Column(db.Integer, comment='持仓量')
    volume = db.Column(db.Integer, comment='成交量')
    is_main_contract = db.Column(db.Boolean, default=False, comment='是否是主力合约')
    update_time = db.Column(db.DateTime, default=datetime.now, comment='更新时间')
    
    def __repr__(self):
        return f'<FutureDaily {self.contract_code} - {self.product_name}>'
    
    def to_dict(self):
        """转换为字典，用于API返回"""
        return {
            'id': self.id,
            'exchange': self.exchange,
            'contract_code': self.contract_code,
            'contract_name': self.contract_name,
            'product_code': self.product_code,
            'product_name': self.product_name,
            'contract_multiplier': self.contract_multiplier,
            'price_tick': self.price_tick,
            'open_fee_rate': self.open_fee_rate,
            'open_fee': self.open_fee,
            'close_fee_rate': self.close_fee_rate,
            'close_fee': self.close_fee,
            'close_today_fee_rate': self.close_today_fee_rate,
            'close_today_fee': self.close_today_fee,
            'long_margin_rate': self.long_margin_rate,
            'long_margin_fee': self.long_margin_fee,
            'short_margin_rate': self.short_margin_rate,
            'short_margin_fee': self.short_margin_fee,
            'latest_price': self.latest_price,
            'open_interest': self.open_interest,
            'volume': self.volume,
            'is_main_contract': self.is_main_contract,
            'update_time': self.update_time.strftime('%Y-%m-%d %H:%M:%S') if self.update_time else None
        } 