"""
监控记录模型文件
"""

from app import db

class MonitorRecord(db.Model):
    """
    监控标的信息表
    对应BRD文档中的"monitor_records"表
    """
    __tablename__ = 'monitor_records'

    id = db.Column(db.Integer, primary_key=True, comment='序号')
    contract = db.Column(db.String(6), nullable=False, comment='合约')
    name = db.Column(db.String(50), nullable=False, comment='名称')
    market = db.Column(db.Integer, nullable=False, comment='市场，0-国内，1-国外')
    opportunity = db.Column(db.String(200), comment='机会')
    key_price = db.Column(db.Float, comment='关键价格')
    open_long_price = db.Column(db.Float, comment='开多价格')
    open_short_price = db.Column(db.Float, comment='开空价格')
    status = db.Column(db.Integer, nullable=False, default=0, comment='状态，0-有效，1-失效，2-虚拟多，3-虚拟空，4-真实多，5-真实空')
    latest_price = db.Column(db.Float, comment='最新价格')
    open_long_trigger_price = db.Column(db.Float, comment='开多触发价格')
    open_short_trigger_price = db.Column(db.Float, comment='开空触发价格')
    open_long_margin_per_unit = db.Column(db.Float, comment='开多一手保证金')
    open_short_margin_per_unit = db.Column(db.Float, comment='开空一手保证金')
    candle_pattern_id = db.Column(db.Integer, db.ForeignKey('candle_info.id'), comment='K线形态ID')
    candle_pattern = db.Column(db.String(100), comment='K线形态')
    long_trend_ids = db.Column(db.String(200), comment='长期趋势IDs')
    long_trend_name = db.Column(db.String(200), comment='长期趋势名称')
    mid_trend_ids = db.Column(db.String(200), comment='中期趋势IDs')
    mid_trend_name = db.Column(db.String(200), comment='中期趋势名称')
    similarity_evaluation = db.Column(db.String(200), comment='相似度评估')
    possible_trigger_price = db.Column(db.Float, comment='可能触发价格')
    reference_price_type = db.Column(db.Integer, comment='比例对照价格类型，0-最新价格，1-关键价格')
    relative_ratio = db.Column(db.Float, comment='相应比例')
    
    # 关联关系
    candle = db.relationship('CandleInfo', backref='monitors')
    
    def __repr__(self):
        return f'<MonitorRecord {self.id} - {self.contract}>'
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'contract': self.contract,
            'name': self.name,
            'market': self.market,
            'opportunity': self.opportunity,
            'key_price': self.key_price,
            'open_long_price': self.open_long_price,
            'open_short_price': self.open_short_price,
            'status': self.status,
            'latest_price': self.latest_price,
            'open_long_trigger_price': self.open_long_trigger_price,
            'open_short_trigger_price': self.open_short_trigger_price,
            'open_long_margin_per_unit': self.open_long_margin_per_unit,
            'open_short_margin_per_unit': self.open_short_margin_per_unit,
            'candle_pattern_id': self.candle_pattern_id,
            'candle_pattern': self.candle_pattern,
            'long_trend_ids': self.long_trend_ids,
            'long_trend_name': self.long_trend_name,
            'mid_trend_ids': self.mid_trend_ids,
            'mid_trend_name': self.mid_trend_name,
            'similarity_evaluation': self.similarity_evaluation,
            'possible_trigger_price': self.possible_trigger_price,
            'reference_price_type': self.reference_price_type,
            'relative_ratio': self.relative_ratio
        } 