"""
交易汇总记录和换月交易记录模型文件
"""

from app import db
import datetime

class TradeRecord(db.Model):
    """
    交易汇总记录表
    对应BRD文档中的"trade_records"表
    """
    __tablename__ = 'trade_records'

    id = db.Column(db.Integer, primary_key=True, comment='ID')
    roll_trade_main_id = db.Column(db.Integer, comment='换月交易主ID')
    contract_code = db.Column(db.String(6), nullable=False, comment='合约代码')
    name = db.Column(db.String(50), nullable=False, comment='名称')
    account = db.Column(db.String(20), nullable=False, default='华安期货', comment='账户')
    strategy_id = db.Column(db.Integer, db.ForeignKey('strategy_info.id'), comment='操作策略ID')
    strategy_name = db.Column(db.String(50), comment='操作策略')
    position_type = db.Column(db.Integer, nullable=False, comment='多空仓位，0-多头，1-空头')
    candle_pattern_id = db.Column(db.Integer, db.ForeignKey('candle_info.id'), comment='K线形态ID')
    candle_pattern = db.Column(db.String(100), comment='K线形态')
    open_time = db.Column(db.DateTime, nullable=False, comment='开仓时间')
    close_time = db.Column(db.DateTime, comment='平仓时间')
    position_volume = db.Column(db.Float, nullable=False, comment='持仓手数')
    contract_multiplier = db.Column(db.Float, nullable=False, comment='合约乘数')
    past_position_cost = db.Column(db.Float, comment='过往持仓成本')
    average_sale_price = db.Column(db.Float, comment='平均售价')
    single_profit = db.Column(db.Float, comment='单笔收益')
    investment_profit = db.Column(db.Float, comment='投资收益')
    investment_profit_rate = db.Column(db.Float, comment='投资收益率')
    holding_days = db.Column(db.Integer, comment='持仓天数')
    annual_profit_rate = db.Column(db.Float, comment='投资年化收益率')
    trade_type = db.Column(db.Integer, nullable=False, default=0, comment='交易类别，0-模拟交易，1-真实交易')
    confidence_index = db.Column(db.Float, comment='信心指数，0-2')
    similarity_evaluation = db.Column(db.String(200), comment='相似度评估')
    long_trend_ids = db.Column(db.String(200), comment='长期趋势IDs')
    long_trend_name = db.Column(db.String(200), comment='长期趋势名称')
    mid_trend_ids = db.Column(db.String(200), comment='中期趋势IDs')
    mid_trend_name = db.Column(db.String(200), comment='中期趋势名称')
    
    # 关联关系
    strategy = db.relationship('StrategyInfo', backref='trades')
    candle = db.relationship('CandleInfo', backref='trades')
    
    def __repr__(self):
        return f'<TradeRecord {self.id} - {self.contract_code}>'
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'roll_trade_main_id': self.roll_trade_main_id,
            'contract_code': self.contract_code,
            'name': self.name,
            'account': self.account,
            'strategy_id': self.strategy_id,
            'strategy_name': self.strategy_name,
            'position_type': self.position_type,
            'candle_pattern_id': self.candle_pattern_id,
            'candle_pattern': self.candle_pattern,
            'open_time': self.open_time.strftime('%Y-%m-%d %H:%M') if self.open_time else None,
            'close_time': self.close_time.strftime('%Y-%m-%d %H:%M') if self.close_time else None,
            'position_volume': self.position_volume,
            'contract_multiplier': self.contract_multiplier,
            'past_position_cost': self.past_position_cost,
            'average_sale_price': self.average_sale_price,
            'single_profit': self.single_profit,
            'investment_profit': self.investment_profit,
            'investment_profit_rate': self.investment_profit_rate,
            'holding_days': self.holding_days,
            'annual_profit_rate': self.annual_profit_rate,
            'trade_type': self.trade_type,
            'confidence_index': self.confidence_index,
            'similarity_evaluation': self.similarity_evaluation,
            'long_trend_ids': self.long_trend_ids,
            'long_trend_name': self.long_trend_name,
            'mid_trend_ids': self.mid_trend_ids,
            'mid_trend_name': self.mid_trend_name
        }

class RollTradeRecord(db.Model):
    """
    换月交易记录表
    对应BRD文档中的"roll_trade_records"表
    """
    __tablename__ = 'roll_trade_records'

    id = db.Column(db.Integer, primary_key=True, comment='ID')
    roll_trade_main_id = db.Column(db.Integer, nullable=False, comment='换月交易主ID')
    related_trade_ids = db.Column(db.String(200), nullable=False, comment='关联交易IDs')
    contract_letter = db.Column(db.String(2), nullable=False, comment='合约字母')
    related_contracts = db.Column(db.String(200), nullable=False, comment='关联合约')
    
    def __repr__(self):
        return f'<RollTradeRecord {self.id} - {self.contract_letter}>'
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'roll_trade_main_id': self.roll_trade_main_id,
            'related_trade_ids': self.related_trade_ids,
            'contract_letter': self.contract_letter,
            'related_contracts': self.related_contracts
        } 