"""
维度数据模型文件
包含策略信息、K线形态、趋势类型等维度表
"""

from app import db

class StrategyInfo(db.Model):
    """
    交易策略信息表
    对应BRD文档中的"strategy_info"表
    """
    __tablename__ = 'strategy_info'

    id = db.Column(db.Integer, primary_key=True, comment='序号')
    name = db.Column(db.String(50), nullable=False, comment='名称')
    open_close_type = db.Column(db.Integer, nullable=False, comment='开平仓类型，0-开仓，1-平仓')
    strategy_type = db.Column(db.Integer, nullable=False, comment='策略类型，0-阻力位，1-趋势')
    
    def __repr__(self):
        return f'<StrategyInfo {self.id} - {self.name}>'

class CandleInfo(db.Model):
    """
    K线形态信息表
    对应BRD文档中的"candle_info"表
    """
    __tablename__ = 'candle_info'

    id = db.Column(db.Integer, primary_key=True, comment='序号')
    name = db.Column(db.String(100), nullable=False, comment='名称')
    
    def __repr__(self):
        return f'<CandleInfo {self.id} - {self.name}>'

class TrendInfo(db.Model):
    """
    走势类型基本信息表
    对应BRD文档中的"trend_info"表
    """
    __tablename__ = 'trend_info'

    id = db.Column(db.Integer, primary_key=True, comment='ID')
    category = db.Column(db.Integer, nullable=False, comment='类别，0-上涨下跌类，1-震荡类，2-和压力位支撑位相关类')
    name = db.Column(db.String(100), comment='名称')
    time_range_id = db.Column(db.Integer, db.ForeignKey('dim_time_range.id'), comment='时间范围ID')
    amplitude_id = db.Column(db.Integer, db.ForeignKey('dim_amplitude.id'), comment='幅度范围ID')
    position_id = db.Column(db.Integer, db.ForeignKey('dim_position.id'), comment='位置范围ID')
    speed_type_id = db.Column(db.Integer, db.ForeignKey('dim_speed_type.id'), comment='速度类型ID')
    trend_type_id = db.Column(db.Integer, db.ForeignKey('dim_trend_type.id'), comment='趋势类型ID')
    extra_info = db.Column(db.String(100), comment='额外信息')
    
    # 关联关系
    time_range = db.relationship('DimTimeRange', backref='trends')
    amplitude = db.relationship('DimAmplitude', backref='trends')
    position = db.relationship('DimPosition', backref='trends')
    speed_type = db.relationship('DimSpeedType', backref='trends')
    trend_type = db.relationship('DimTrendType', backref='trends')
    
    def __repr__(self):
        return f'<TrendInfo {self.id} - {self.name}>'

class DimTimeRange(db.Model):
    """
    走势类型的时间范围维度表
    对应BRD文档中的"dim_time_range"表
    """
    __tablename__ = 'dim_time_range'

    id = db.Column(db.Integer, primary_key=True, comment='ID')
    name = db.Column(db.String(20), nullable=False, comment='名称')
    
    def __repr__(self):
        return f'<DimTimeRange {self.id} - {self.name}>'

class DimAmplitude(db.Model):
    """
    走势类型的幅度范围维度表
    对应BRD文档中的"dim_amplitude"表
    """
    __tablename__ = 'dim_amplitude'

    id = db.Column(db.Integer, primary_key=True, comment='ID')
    name = db.Column(db.String(20), nullable=False, comment='名称')
    
    def __repr__(self):
        return f'<DimAmplitude {self.id} - {self.name}>'

class DimPosition(db.Model):
    """
    走势类型的位置范围维度表
    对应BRD文档中的"dim_position"表
    """
    __tablename__ = 'dim_position'

    id = db.Column(db.Integer, primary_key=True, comment='ID')
    name = db.Column(db.String(20), nullable=False, comment='名称')
    
    def __repr__(self):
        return f'<DimPosition {self.id} - {self.name}>'

class DimSpeedType(db.Model):
    """
    走势类型的速度类型维度表
    对应BRD文档中的"dim_speed_type"表
    """
    __tablename__ = 'dim_speed_type'

    id = db.Column(db.Integer, primary_key=True, comment='ID')
    name = db.Column(db.String(20), nullable=False, comment='名称')
    
    def __repr__(self):
        return f'<DimSpeedType {self.id} - {self.name}>'

class DimTrendType(db.Model):
    """
    走势类型的趋势类型维度表
    对应BRD文档中的"dim_trend_type"表
    """
    __tablename__ = 'dim_trend_type'

    id = db.Column(db.Integer, primary_key=True, comment='ID')
    name = db.Column(db.String(20), nullable=False, comment='名称')
    
    def __repr__(self):
        return f'<DimTrendType {self.id} - {self.name}>' 