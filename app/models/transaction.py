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
    trade_id = db.Column(db.Integer, db.ForeignKey('trade_records.id'), comment='交易ID')
    roll_id = db.Column(db.Integer, comment='换月ID')
    transaction_time = db.Column(db.DateTime, nullable=False, default=datetime.datetime.now, comment='成交时间')
    contract_code = db.Column(db.String(6), nullable=False, comment='合约代码')
    name = db.Column(db.String(50), nullable=False, comment='名称')
    account = db.Column(db.String(20), nullable=False, default='华安期货', comment='账户')
    strategy_ids = db.Column(db.String(200), comment='操作策略IDs')
    strategy_name = db.Column(db.String(200), comment='操作策略，多个策略用+号连接')
    position_type = db.Column(db.Integer, nullable=False, comment='多空仓位，0-开多，1-平多，2-开空，3-平空')
    candle_pattern_ids = db.Column(db.String(200), comment='K线形态IDs')
    candle_pattern = db.Column(db.String(200), comment='K线形态，多个形态用+号连接')
    price = db.Column(db.Float, nullable=False, comment='成交价格')
    volume = db.Column(db.Float, nullable=False, comment='成交手数')
    contract_multiplier = db.Column(db.Float, nullable=False, comment='合约乘数')
    amount = db.Column(db.Float, comment='成交金额')
    fee = db.Column(db.Float, comment='手续费')
    volume_change = db.Column(db.Float, comment='手数变化')
    cash_flow = db.Column(db.Float, comment='现金流')
    margin = db.Column(db.Float, comment='保证金')
    fund_threshold = db.Column(db.Integer, comment='资金阈值判定，0-可以，1-不可以')
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
    similarity_evaluation = db.Column(db.Float, comment='相似度评估，百分比数值')
    long_trend_ids = db.Column(db.String(200), comment='长期趋势IDs')
    long_trend_name = db.Column(db.String(200), comment='长期趋势名称')
    mid_trend_ids = db.Column(db.String(200), comment='中期趋势IDs')
    mid_trend_name = db.Column(db.String(200), comment='中期趋势名称')
    
    # 关联关系
    trade = db.relationship('TradeRecord', backref=db.backref('transactions', lazy='dynamic'))
    
    def __repr__(self):
        return f'<TransactionRecord {self.id} - {self.contract_code}>'
    
    def to_dict(self):
        """转换为字典"""
        
        # Helper function for safe division
        def safe_division(numerator, denominator):
            if denominator is None or denominator == 0 or numerator is None:
                return None
            try:
                return numerator / denominator
            except ZeroDivisionError:
                return None

        # Helper function for profit/rate calculation direction multiplier
        def get_direction_multiplier(position_type):
            # 0=开多, 1=平多 -> Long (+)
            # 2=开空, 3=平空 -> Short (-)
            if position_type in [2, 3]:
                return -1.0
            return 1.0

        direction_multiplier = get_direction_multiplier(self.position_type)

        # Calculate actual profit rate
        actual_profit_rate = None
        if self.latest_price is not None:
             rate = safe_division(self.latest_price - self.price, self.price)
             if rate is not None:
                 actual_profit_rate = direction_multiplier * rate

        # Calculate actual profit
        actual_profit = None
        if self.latest_price is not None and self.volume_change is not None and self.contract_multiplier is not None:
            actual_profit = (self.latest_price - self.price) * self.volume_change * self.contract_multiplier
            # 根据BRD，实际收益还需要减去手续费，假设开平仓手续费相同
            if self.fee is not None:
                 # 乘以2代表开仓和平仓的总手续费，但列表显示的是单条记录，此处逻辑可能需调整
                 # 暂时按BRD公式 q 计算（假设这是平仓记录且包含了开仓手续费信息或fee字段代表总手续费）
                 # 或者更合理的做法是仅在汇总记录(TradeRecord)中计算包含手续费的净收益
                 # 这里暂时不减去fee，保持公式一致性: (最新价格 - 成交价格) * 手数变化 * 合约乘数
                 # actual_profit = actual_profit - (2 * self.fee) # 暂时注释掉
                 pass


        # Calculate stop loss rate
        stop_loss_rate = None
        if self.stop_loss_price is not None:
            rate = safe_division(self.stop_loss_price - self.price, self.price)
            if rate is not None:
                stop_loss_rate = direction_multiplier * rate

        # Calculate stop loss profit
        stop_loss_profit = None
        if self.stop_loss_price is not None and self.volume_change is not None and self.contract_multiplier is not None:
            stop_loss_profit = (self.stop_loss_price - self.price) * self.volume_change * self.contract_multiplier
            # 同样，根据BRD公式 t，止损收益也应考虑手续费
            # if self.fee is not None:
            #    stop_loss_profit = stop_loss_profit - (2 * self.fee) # 暂时注释掉
            #    pass
        
        return {
            'id': self.id,
            'trade_id': self.trade_id,
            'roll_id': self.roll_id,
            'transaction_time': self.transaction_time.strftime('%Y-%m-%d %H:%M') if self.transaction_time else None,
            'contract_code': self.contract_code,
            'name': self.name,
            'account': self.account,
            'strategy_ids': self.strategy_ids,
            'strategy_name': self.strategy_name,
            'position_type': self.position_type,
            'candle_pattern_ids': self.candle_pattern_ids,
            'candle_pattern': self.candle_pattern,
            'price': self.price,
            'volume': self.volume,
            'contract_multiplier': self.contract_multiplier,
            'amount': self.amount,
            'fee': self.fee,
            'volume_change': self.volume_change,
            'cash_flow': self.cash_flow,
            'margin': self.margin, # margin 在创建/更新时计算并存储
            'fund_threshold': self.fund_threshold,
            'trade_type': self.trade_type,
            'trade_status': self.trade_status,
            'latest_price': self.latest_price,
            'actual_profit_rate': actual_profit_rate, # Calculated
            'actual_profit': actual_profit,           # Calculated
            'stop_loss_price': self.stop_loss_price,
            'stop_loss_rate': stop_loss_rate,         # Calculated
            'stop_loss_profit': stop_loss_profit,       # Calculated
            'operation_time': self.operation_time.strftime('%Y-%m-%d %H:%M') if self.operation_time else None,
            'confidence_index': self.confidence_index,
            'similarity_evaluation': self.similarity_evaluation,
            'long_trend_ids': self.long_trend_ids,
            'long_trend_name': self.long_trend_name,
            'mid_trend_ids': self.mid_trend_ids,
            'mid_trend_name': self.mid_trend_name
        } 