"""
监控记录相关路由
"""

from flask import Blueprint, jsonify, request, render_template
from app import db
from app.models.monitor import MonitorRecord

bp = Blueprint('monitor', __name__, url_prefix='/monitor')

@bp.route('/', methods=['GET'])
def index():
    """监控记录列表页面"""
    return render_template('monitor/index.html')

@bp.route('/list', methods=['GET'])
def get_list():
    """获取监控记录列表"""
    # 获取筛选参数
    status = request.args.get('status')
    market = request.args.get('market')
    names = request.args.getlist('name')
    contract_letters = request.args.getlist('contract_letter')
    
    # 构建查询
    query = MonitorRecord.query
    
    if status is not None:
        query = query.filter(MonitorRecord.status == int(status))
    
    if market is not None:
        query = query.filter(MonitorRecord.market == int(market))
    
    if names:
        query = query.filter(MonitorRecord.name.in_(names))
    
    if contract_letters:
        # 假设合约代码的前1-2位是合约字母
        query = query.filter(db.or_(*[MonitorRecord.contract.startswith(letter) for letter in contract_letters]))
    
    # 执行查询
    monitors = query.all()
    
    # 返回结果
    return jsonify({
        'code': 0,
        'msg': '成功',
        'data': [monitor.to_dict() for monitor in monitors]
    })

@bp.route('/detail/<int:id>', methods=['GET'])
def get_detail(id):
    """获取监控记录详情"""
    monitor = MonitorRecord.query.get_or_404(id)
    return jsonify({
        'code': 0,
        'msg': '成功',
        'data': monitor.to_dict()
    })

@bp.route('/create', methods=['POST'])
def create():
    """创建监控记录"""
    data = request.json
    
    # 创建新记录
    monitor = MonitorRecord(
        contract=data.get('contract'),
        name=data.get('name'),
        market=data.get('market'),
        opportunity=data.get('opportunity'),
        key_price=data.get('key_price'),
        open_long_price=data.get('open_long_price'),
        open_short_price=data.get('open_short_price'),
        status=data.get('status', 0),
        latest_price=data.get('latest_price'),
        open_long_trigger_price=data.get('open_long_trigger_price'),
        open_short_trigger_price=data.get('open_short_trigger_price'),
        open_long_margin_per_unit=data.get('open_long_margin_per_unit'),
        open_short_margin_per_unit=data.get('open_short_margin_per_unit'),
        candle_pattern_id=data.get('candle_pattern_id'),
        candle_pattern=data.get('candle_pattern'),
        long_trend_ids=data.get('long_trend_ids'),
        long_trend_name=data.get('long_trend_name'),
        mid_trend_ids=data.get('mid_trend_ids'),
        mid_trend_name=data.get('mid_trend_name'),
        similarity_evaluation=data.get('similarity_evaluation'),
        possible_trigger_price=data.get('possible_trigger_price'),
        reference_price_type=data.get('reference_price_type'),
        relative_ratio=data.get('relative_ratio')
    )
    
    # 保存到数据库
    db.session.add(monitor)
    db.session.commit()
    
    return jsonify({
        'code': 0,
        'msg': '创建成功',
        'data': monitor.to_dict()
    })

@bp.route('/update/<int:id>', methods=['PUT'])
def update(id):
    """更新监控记录"""
    monitor = MonitorRecord.query.get_or_404(id)
    data = request.json
    
    # 更新字段
    if 'contract' in data:
        monitor.contract = data['contract']
    if 'name' in data:
        monitor.name = data['name']
    if 'market' in data:
        monitor.market = data['market']
    if 'opportunity' in data:
        monitor.opportunity = data['opportunity']
    if 'key_price' in data:
        monitor.key_price = data['key_price']
    if 'open_long_price' in data:
        monitor.open_long_price = data['open_long_price']
    if 'open_short_price' in data:
        monitor.open_short_price = data['open_short_price']
    if 'status' in data:
        monitor.status = data['status']
    if 'latest_price' in data:
        monitor.latest_price = data['latest_price']
    if 'open_long_trigger_price' in data:
        monitor.open_long_trigger_price = data['open_long_trigger_price']
    if 'open_short_trigger_price' in data:
        monitor.open_short_trigger_price = data['open_short_trigger_price']
    if 'open_long_margin_per_unit' in data:
        monitor.open_long_margin_per_unit = data['open_long_margin_per_unit']
    if 'open_short_margin_per_unit' in data:
        monitor.open_short_margin_per_unit = data['open_short_margin_per_unit']
    if 'candle_pattern_id' in data:
        monitor.candle_pattern_id = data['candle_pattern_id']
    if 'candle_pattern' in data:
        monitor.candle_pattern = data['candle_pattern']
    if 'long_trend_ids' in data:
        monitor.long_trend_ids = data['long_trend_ids']
    if 'long_trend_name' in data:
        monitor.long_trend_name = data['long_trend_name']
    if 'mid_trend_ids' in data:
        monitor.mid_trend_ids = data['mid_trend_ids']
    if 'mid_trend_name' in data:
        monitor.mid_trend_name = data['mid_trend_name']
    if 'similarity_evaluation' in data:
        monitor.similarity_evaluation = data['similarity_evaluation']
    if 'possible_trigger_price' in data:
        monitor.possible_trigger_price = data['possible_trigger_price']
    if 'reference_price_type' in data:
        monitor.reference_price_type = data['reference_price_type']
    if 'relative_ratio' in data:
        monitor.relative_ratio = data['relative_ratio']
    
    # 保存到数据库
    db.session.commit()
    
    return jsonify({
        'code': 0,
        'msg': '更新成功',
        'data': monitor.to_dict()
    })

@bp.route('/delete/<int:id>', methods=['DELETE'])
def delete(id):
    """删除监控记录"""
    monitor = MonitorRecord.query.get_or_404(id)
    
    # 从数据库删除
    db.session.delete(monitor)
    db.session.commit()
    
    return jsonify({
        'code': 0,
        'msg': '删除成功'
    }) 