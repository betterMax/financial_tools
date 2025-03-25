"""
交易记录相关路由
"""

from flask import Blueprint, jsonify, request, render_template
from app import db
from app.models.transaction import TransactionRecord
from datetime import datetime

bp = Blueprint('transaction', __name__, url_prefix='/transaction')

@bp.route('/', methods=['GET'])
def index():
    """交易记录列表页面"""
    return render_template('transaction/index.html')

@bp.route('/list', methods=['GET'])
def get_list():
    """获取交易记录列表"""
    # 获取筛选参数
    start_time = request.args.get('start_time')
    end_time = request.args.get('end_time')
    names = request.args.getlist('name')
    contract_letters = request.args.getlist('contract_letter')
    strategy_ids = request.args.getlist('strategy_id')
    trade_type = request.args.get('trade_type')
    trade_statuses = request.args.getlist('trade_status')
    
    # 构建查询
    query = TransactionRecord.query
    
    if start_time:
        query = query.filter(TransactionRecord.transaction_time >= datetime.strptime(start_time, '%Y-%m-%d'))
    
    if end_time:
        query = query.filter(TransactionRecord.transaction_time <= datetime.strptime(end_time, '%Y-%m-%d'))
    
    if names:
        query = query.filter(TransactionRecord.name.in_(names))
    
    if contract_letters:
        # 假设合约代码的前1-2位是合约字母
        query = query.filter(db.or_(*[TransactionRecord.contract_code.startswith(letter) for letter in contract_letters]))
    
    if strategy_ids:
        query = query.filter(TransactionRecord.strategy_id.in_([int(i) for i in strategy_ids]))
    
    if trade_type is not None:
        query = query.filter(TransactionRecord.trade_type == int(trade_type))
    
    if trade_statuses:
        query = query.filter(TransactionRecord.trade_status.in_([int(i) for i in trade_statuses]))
    
    # 执行查询
    transactions = query.all()
    
    # 返回结果
    return jsonify({
        'code': 0,
        'msg': '成功',
        'data': [transaction.to_dict() for transaction in transactions]
    })

@bp.route('/detail/<int:id>', methods=['GET'])
def get_detail(id):
    """获取交易记录详情"""
    transaction = TransactionRecord.query.get_or_404(id)
    return jsonify({
        'code': 0,
        'msg': '成功',
        'data': transaction.to_dict()
    })

@bp.route('/create', methods=['POST'])
def create():
    """创建交易记录"""
    data = request.json
    
    # 处理日期时间
    transaction_time = datetime.strptime(data.get('transaction_time', ''), '%Y-%m-%d %H:%M') if data.get('transaction_time') else datetime.now()
    operation_time = datetime.strptime(data.get('operation_time', ''), '%Y-%m-%d %H:%M') if data.get('operation_time') else transaction_time
    
    # 计算一些字段
    position_type = data.get('position_type')
    price = data.get('price', 0)
    volume = data.get('volume', 0)
    contract_multiplier = data.get('contract_multiplier', 0)
    
    # 成交金额
    amount = price * volume * contract_multiplier
    
    # 创建新记录
    transaction = TransactionRecord(
        trade_id=data.get('trade_id'),
        transaction_time=transaction_time,
        contract_code=data.get('contract_code'),
        name=data.get('name'),
        account=data.get('account', '华安期货'),
        strategy_id=data.get('strategy_id'),
        strategy_name=data.get('strategy_name'),
        position_type=position_type,
        candle_pattern_id=data.get('candle_pattern_id'),
        candle_pattern=data.get('candle_pattern'),
        price=price,
        volume=volume,
        contract_multiplier=contract_multiplier,
        amount=amount,
        # 其他计算字段
        volume_change=volume if position_type in [0, 2] else -volume,
        operation_time=operation_time,
        trade_type=data.get('trade_type', 0),
        trade_status=data.get('trade_status', 0),
        latest_price=data.get('latest_price'),
        stop_loss_price=data.get('stop_loss_price'),
        confidence_index=data.get('confidence_index'),
        similarity_evaluation=data.get('similarity_evaluation'),
        long_trend_ids=data.get('long_trend_ids'),
        long_trend_name=data.get('long_trend_name'),
        mid_trend_ids=data.get('mid_trend_ids'),
        mid_trend_name=data.get('mid_trend_name')
    )
    
    # 保存到数据库
    db.session.add(transaction)
    db.session.commit()
    
    return jsonify({
        'code': 0,
        'msg': '创建成功',
        'data': transaction.to_dict()
    })

@bp.route('/update/<int:id>', methods=['PUT'])
def update(id):
    """更新交易记录"""
    transaction = TransactionRecord.query.get_or_404(id)
    data = request.json
    
    # 更新字段
    if 'trade_id' in data:
        transaction.trade_id = data['trade_id']
    if 'transaction_time' in data:
        transaction.transaction_time = datetime.strptime(data['transaction_time'], '%Y-%m-%d %H:%M')
    if 'contract_code' in data:
        transaction.contract_code = data['contract_code']
    if 'name' in data:
        transaction.name = data['name']
    if 'account' in data:
        transaction.account = data['account']
    if 'strategy_id' in data:
        transaction.strategy_id = data['strategy_id']
    if 'strategy_name' in data:
        transaction.strategy_name = data['strategy_name']
    if 'position_type' in data:
        transaction.position_type = data['position_type']
    if 'candle_pattern_id' in data:
        transaction.candle_pattern_id = data['candle_pattern_id']
    if 'candle_pattern' in data:
        transaction.candle_pattern = data['candle_pattern']
    if 'price' in data:
        transaction.price = data['price']
    if 'volume' in data:
        transaction.volume = data['volume']
    if 'contract_multiplier' in data:
        transaction.contract_multiplier = data['contract_multiplier']
    if 'trade_type' in data:
        transaction.trade_type = data['trade_type']
    if 'trade_status' in data:
        transaction.trade_status = data['trade_status']
    if 'latest_price' in data:
        transaction.latest_price = data['latest_price']
    if 'stop_loss_price' in data:
        transaction.stop_loss_price = data['stop_loss_price']
    if 'operation_time' in data:
        transaction.operation_time = datetime.strptime(data['operation_time'], '%Y-%m-%d %H:%M')
    if 'confidence_index' in data:
        transaction.confidence_index = data['confidence_index']
    if 'similarity_evaluation' in data:
        transaction.similarity_evaluation = data['similarity_evaluation']
    if 'long_trend_ids' in data:
        transaction.long_trend_ids = data['long_trend_ids']
    if 'long_trend_name' in data:
        transaction.long_trend_name = data['long_trend_name']
    if 'mid_trend_ids' in data:
        transaction.mid_trend_ids = data['mid_trend_ids']
    if 'mid_trend_name' in data:
        transaction.mid_trend_name = data['mid_trend_name']
    
    # 重新计算一些字段
    if 'price' in data or 'volume' in data or 'contract_multiplier' in data:
        transaction.amount = transaction.price * transaction.volume * transaction.contract_multiplier
        transaction.volume_change = transaction.volume if transaction.position_type in [0, 2] else -transaction.volume
    
    # 保存到数据库
    db.session.commit()
    
    return jsonify({
        'code': 0,
        'msg': '更新成功',
        'data': transaction.to_dict()
    })

@bp.route('/delete/<int:id>', methods=['DELETE'])
def delete(id):
    """删除交易记录"""
    transaction = TransactionRecord.query.get_or_404(id)
    
    # 从数据库删除
    db.session.delete(transaction)
    db.session.commit()
    
    return jsonify({
        'code': 0,
        'msg': '删除成功'
    }) 