"""
期货基础信息模型文件
"""

from app import db

class FutureInfo(db.Model):
    """
    期货标的基础信息表
    对应BRD文档中的"future_info"表
    """
    __tablename__ = 'future_info'

    id = db.Column(db.Integer, primary_key=True, comment='序号')
    contract_letter = db.Column(db.String(2), unique=True, nullable=False, comment='合约字母')
    name = db.Column(db.String(50), nullable=False, comment='名称')
    market = db.Column(db.Integer, nullable=False, comment='市场，0-国内，1-国外')
    exchange = db.Column(db.String(5), comment='交易所')
    contract_multiplier = db.Column(db.Float, comment='合约乘数')
    long_margin_rate = db.Column(db.Float, comment='做多保证金率（按金额）')
    short_margin_rate = db.Column(db.Float, comment='做空保证金率（按金额）')
    open_fee = db.Column(db.Float, comment='开仓费用（按手）')
    close_fee = db.Column(db.Float, comment='平仓费用（按手）')
    close_today_rate = db.Column(db.Float, comment='平今费率（按金额）')
    close_today_fee = db.Column(db.Float, comment='平今费用（按手）')
    th_main_contract = db.Column(db.String(6), comment='同花主力合约')
    current_main_contract = db.Column(db.String(6), comment='当前主力合约')
    th_order = db.Column(db.Integer, comment='同花顺顺序')
    long_term_trend = db.Column(db.String(100), comment='长期趋势')
    
    def __repr__(self):
        return f'<FutureInfo {self.contract_letter} - {self.name}>'
    
    def to_dict(self):
        """转换为字典"""
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