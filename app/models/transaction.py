"""
交易记录模型文件
"""

from app import db
import datetime

class TransactionRecord(db.Model):
    """
    开仓平仓交易记录表
    对应BRD文档中的"transaction_records"表
    """
    __tablename__ = 'transaction_records'

    id = db.Column(db.Integer, primary_key=True, comment='ID')
    trade_id = db.Column(db.Integer, db.ForeignKey('trade_records.id'), nullable=False, comment='交易ID')
    transaction_time = db.Column(db.DateTime, nullable=False, default=datetime.datetime.now, comment='成交时间')
    contract_code = db.Column(db.String(6), nullable=False, comment='合约代码')
    name = db.Column(db.String(50), nullable=False, comment='名称')
    account = db.Column(db.String(20), nullable=False, default='华安期货', comment='账户')
    strategy_id = db.Column(db.Integer, db.ForeignKey('strategy_info.id'), comment='操作策略ID')
    strategy_name = db.Column(db.String(50), comment='操作策略')
    position_type = db.Column(db.Integer, nullable=False, comment='多空仓位，0-开多，1-平多，2-开空，3-平空')
    candle_pattern_id = db.Column(db.Integer, db.ForeignKey('candle_info.id'), comment='K线形态ID')
    candle_pattern = db.Column(db.String(100), comment='K线形态')
    price = db.Column(db.Float, nullable=False, comment='成交价格')
    volume = db.Column(db.Float, nullable=False, comment='成交手数')
    contract_multiplier = db.Column(db.Float, nullable=False, comment='合约乘数')
    amount = db.Column(db.Float, comment='成交金额')
    fee = db.Column(db.Float, comment='手续费')
    volume_change = db.Column(db.Float, comment='手数变化')
    cash_flow = db.Column(db.Float, comment='现金流')
    margin = db.Column(db.Float, comment='保证金')
    trade_type = db.Column(db.Integer, nullable=False, default=0, comment='交易类别，0-模拟交易，1-真实交易')
    trade_status = db.Column(db.Integer, nullable=False, default=0, comment='交易状态，0-进行，1-暂停，2-暂停进行，3-结束')
    latest_price = db.Column(db.Float, comment='最新价格')
    actual_profit_rate = db.Column(db.Float, comment='实际收益率')
    actual_profit = db.Column(db.Float, comment='实际收益')
    stop_loss_price = db.Column(db.Float, comment='止损价格')
    stop_loss_rate = db.Column(db.Float, comment='止损比例')
    stop_loss_profit = db.Column(db.Float, comment='止损收益')
    operation_time = db.Column(db.DateTime, default=datetime.datetime.now, comment='操作时间')
    confidence_index = db.Column(db.Float, comment='信心指数，0-2')
    similarity_evaluation = db.Column(db.String(200), comment='相似度评估')
    long_trend_ids = db.Column(db.String(200), comment='长期趋势IDs')
    long_trend_name = db.Column(db.String(200), comment='长期趋势名称')
    mid_trend_ids = db.Column(db.String(200), comment='中期趋势IDs')
    mid_trend_name = db.Column(db.String(200), comment='中期趋势名称')
    
    # 关联关系
    trade = db.relationship('TradeRecord', backref=db.backref('transactions', lazy='dynamic'))
    strategy = db.relationship('StrategyInfo', backref='transactions')
    candle = db.relationship('CandleInfo', backref='transactions')
    
    def __repr__(self):
        return f'<TransactionRecord {self.id} - {self.contract_code}>'
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'trade_id': self.trade_id,
            'transaction_time': self.transaction_time.strftime('%Y-%m-%d %H:%M') if self.transaction_time else None,
            'contract_code': self.contract_code,
            'name': self.name,
            'account': self.account,
            'strategy_id': self.strategy_id,
            'strategy_name': self.strategy_name,
            'position_type': self.position_type,
            'candle_pattern_id': self.candle_pattern_id,
            'candle_pattern': self.candle_pattern,
            'price': self.price,
            'volume': self.volume,
            'contract_multiplier': self.contract_multiplier,
            'amount': self.amount,
            'fee': self.fee,
            'volume_change': self.volume_change,
            'cash_flow': self.cash_flow,
            'margin': self.margin,
            'trade_type': self.trade_type,
            'trade_status': self.trade_status,
            'latest_price': self.latest_price,
            'actual_profit_rate': self.actual_profit_rate,
            'actual_profit': self.actual_profit,
            'stop_loss_price': self.stop_loss_price,
            'stop_loss_rate': self.stop_loss_rate,
            'stop_loss_profit': self.stop_loss_profit,
            'operation_time': self.operation_time.strftime('%Y-%m-%d %H:%M') if self.operation_time else None,
            'confidence_index': self.confidence_index,
            'similarity_evaluation': self.similarity_evaluation,
            'long_trend_ids': self.long_trend_ids,
            'long_trend_name': self.long_trend_name,
            'mid_trend_ids': self.mid_trend_ids,
            'mid_trend_name': self.mid_trend_name
        } 