"""
交易汇总记录相关路由
"""

from flask import Blueprint, jsonify, request, render_template
from app import db
from app.models.trade import TradeRecord, RollTradeRecord
from datetime import datetime

bp = Blueprint('trade', __name__, url_prefix='/trade')

@bp.route('/', methods=['GET'])
def index():
    """交易汇总记录列表页面"""
    return render_template('trade/index.html')

@bp.route('/list', methods=['GET'])
def get_list():
    """获取交易汇总记录列表"""
    # 获取筛选参数
    # (可以添加类似transaction.py中的筛选参数)
    
    # 执行查询
    trades = TradeRecord.query.all()
    
    # 返回结果
    return jsonify({
        'code': 0,
        'msg': '成功',
        'data': [trade.to_dict() for trade in trades]
    })

@bp.route('/detail/<int:id>', methods=['GET'])
def get_detail(id):
    """获取交易汇总记录详情"""
    trade = TradeRecord.query.get_or_404(id)
    return jsonify({
        'code': 0,
        'msg': '成功',
        'data': trade.to_dict()
    })

@bp.route('/create', methods=['POST'])
def create():
    """创建交易汇总记录"""
    data = request.json
    
    # 处理日期时间
    open_time = datetime.strptime(data.get('open_time', ''), '%Y-%m-%d %H:%M') if data.get('open_time') else datetime.now()
    close_time = datetime.strptime(data.get('close_time', ''), '%Y-%m-%d %H:%M') if data.get('close_time') else None
    
    # 计算持仓天数
    holding_days = None
    if close_time and open_time:
        holding_days = (close_time - open_time).days
    
    # 创建新记录
    trade = TradeRecord(
        roll_trade_main_id=data.get('roll_trade_main_id'),
        contract_code=data.get('contract_code'),
        name=data.get('name'),
        account=data.get('account', '华安期货'),
        strategy_id=data.get('strategy_id'),
        strategy_name=data.get('strategy_name'),
        position_type=data.get('position_type'),
        candle_pattern_id=data.get('candle_pattern_id'),
        candle_pattern=data.get('candle_pattern'),
        open_time=open_time,
        close_time=close_time,
        position_volume=data.get('position_volume'),
        contract_multiplier=data.get('contract_multiplier'),
        past_position_cost=data.get('past_position_cost'),
        average_sale_price=data.get('average_sale_price'),
        single_profit=data.get('single_profit'),
        investment_profit=data.get('investment_profit'),
        investment_profit_rate=data.get('investment_profit_rate'),
        holding_days=holding_days,
        annual_profit_rate=data.get('annual_profit_rate'),
        trade_type=data.get('trade_type', 0),
        confidence_index=data.get('confidence_index'),
        similarity_evaluation=data.get('similarity_evaluation'),
        long_trend_ids=data.get('long_trend_ids'),
        long_trend_name=data.get('long_trend_name'),
        mid_trend_ids=data.get('mid_trend_ids'),
        mid_trend_name=data.get('mid_trend_name')
    )
    
    # 保存到数据库
    db.session.add(trade)
    db.session.commit()
    
    return jsonify({
        'code': 0,
        'msg': '创建成功',
        'data': trade.to_dict()
    })

@bp.route('/update/<int:id>', methods=['PUT'])
def update(id):
    """更新交易汇总记录"""
    trade = TradeRecord.query.get_or_404(id)
    data = request.json
    
    # 更新字段
    if 'roll_trade_main_id' in data:
        trade.roll_trade_main_id = data['roll_trade_main_id']
    if 'contract_code' in data:
        trade.contract_code = data['contract_code']
    if 'name' in data:
        trade.name = data['name']
    if 'account' in data:
        trade.account = data['account']
    if 'strategy_id' in data:
        trade.strategy_id = data['strategy_id']
    if 'strategy_name' in data:
        trade.strategy_name = data['strategy_name']
    if 'position_type' in data:
        trade.position_type = data['position_type']
    if 'candle_pattern_id' in data:
        trade.candle_pattern_id = data['candle_pattern_id']
    if 'candle_pattern' in data:
        trade.candle_pattern = data['candle_pattern']
    if 'open_time' in data:
        trade.open_time = datetime.strptime(data['open_time'], '%Y-%m-%d %H:%M')
    if 'close_time' in data:
        trade.close_time = datetime.strptime(data['close_time'], '%Y-%m-%d %H:%M')
    if 'position_volume' in data:
        trade.position_volume = data['position_volume']
    if 'contract_multiplier' in data:
        trade.contract_multiplier = data['contract_multiplier']
    if 'past_position_cost' in data:
        trade.past_position_cost = data['past_position_cost']
    if 'average_sale_price' in data:
        trade.average_sale_price = data['average_sale_price']
    if 'single_profit' in data:
        trade.single_profit = data['single_profit']
    if 'investment_profit' in data:
        trade.investment_profit = data['investment_profit']
    if 'investment_profit_rate' in data:
        trade.investment_profit_rate = data['investment_profit_rate']
    if 'annual_profit_rate' in data:
        trade.annual_profit_rate = data['annual_profit_rate']
    if 'trade_type' in data:
        trade.trade_type = data['trade_type']
    if 'confidence_index' in data:
        trade.confidence_index = data['confidence_index']
    if 'similarity_evaluation' in data:
        trade.similarity_evaluation = data['similarity_evaluation']
    if 'long_trend_ids' in data:
        trade.long_trend_ids = data['long_trend_ids']
    if 'long_trend_name' in data:
        trade.long_trend_name = data['long_trend_name']
    if 'mid_trend_ids' in data:
        trade.mid_trend_ids = data['mid_trend_ids']
    if 'mid_trend_name' in data:
        trade.mid_trend_name = data['mid_trend_name']
    
    # 重新计算持仓天数
    if 'open_time' in data or 'close_time' in data:
        if trade.close_time and trade.open_time:
            trade.holding_days = (trade.close_time - trade.open_time).days
    
    # 保存到数据库
    db.session.commit()
    
    return jsonify({
        'code': 0,
        'msg': '更新成功',
        'data': trade.to_dict()
    })

@bp.route('/delete/<int:id>', methods=['DELETE'])
def delete(id):
    """删除交易汇总记录"""
    trade = TradeRecord.query.get_or_404(id)
    
    # 从数据库删除
    db.session.delete(trade)
    db.session.commit()
    
    return jsonify({
        'code': 0,
        'msg': '删除成功'
    })

# 换月交易记录相关路由
@bp.route('/roll/list', methods=['GET'])
def get_roll_list():
    """获取换月交易记录列表"""
    roll_trades = RollTradeRecord.query.all()
    
    return jsonify({
        'code': 0,
        'msg': '成功',
        'data': [roll_trade.to_dict() for roll_trade in roll_trades]
    })

@bp.route('/roll/detail/<int:id>', methods=['GET'])
def get_roll_detail(id):
    """获取换月交易记录详情"""
    roll_trade = RollTradeRecord.query.get_or_404(id)
    return jsonify({
        'code': 0,
        'msg': '成功',
        'data': roll_trade.to_dict()
    })

@bp.route('/roll/create', methods=['POST'])
def create_roll():
    """创建换月交易记录"""
    data = request.json
    
    roll_trade = RollTradeRecord(
        roll_trade_main_id=data.get('roll_trade_main_id'),
        related_trade_ids=data.get('related_trade_ids'),
        contract_letter=data.get('contract_letter'),
        related_contracts=data.get('related_contracts')
    )
    
    db.session.add(roll_trade)
    db.session.commit()
    
    return jsonify({
        'code': 0,
        'msg': '创建成功',
        'data': roll_trade.to_dict()
    }) 