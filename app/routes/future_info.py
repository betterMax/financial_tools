"""
期货基础信息相关路由
"""

from flask import Blueprint, jsonify, request, render_template
from app import db
from app.models.future_info import FutureInfo

bp = Blueprint('future_info', __name__, url_prefix='/future_info')

@bp.route('/', methods=['GET'])
def index():
    """期货基础信息列表页面"""
    return render_template('future_info/index.html')

@bp.route('/list', methods=['GET'])
def get_list():
    """获取期货基础信息列表"""
    # 获取筛选参数
    market = request.args.get('market')
    names = request.args.getlist('name')
    contract_letters = request.args.getlist('contract_letter')
    long_term_trend = request.args.get('long_term_trend')
    
    # 构建查询
    query = FutureInfo.query
    
    if market is not None:
        query = query.filter(FutureInfo.market == int(market))
    
    if names:
        query = query.filter(FutureInfo.name.in_(names))
    
    if contract_letters:
        query = query.filter(FutureInfo.contract_letter.in_(contract_letters))
    
    if long_term_trend:
        query = query.filter(FutureInfo.long_term_trend.like(f'%{long_term_trend}%'))
    
    # 执行查询
    future_infos = query.all()
    
    # 返回结果
    return jsonify({
        'code': 0,
        'msg': '成功',
        'data': [future_info.to_dict() for future_info in future_infos]
    })

@bp.route('/detail/<int:id>', methods=['GET'])
def get_detail(id):
    """获取期货基础信息详情"""
    future_info = FutureInfo.query.get_or_404(id)
    return jsonify({
        'code': 0,
        'msg': '成功',
        'data': future_info.to_dict()
    })

@bp.route('/create', methods=['POST'])
def create():
    """创建期货基础信息"""
    data = request.json
    
    # 创建新记录
    future_info = FutureInfo(
        contract_letter=data.get('contract_letter'),
        name=data.get('name'),
        market=data.get('market'),
        exchange=data.get('exchange'),
        contract_multiplier=data.get('contract_multiplier'),
        long_margin_rate=data.get('long_margin_rate'),
        short_margin_rate=data.get('short_margin_rate'),
        open_fee=data.get('open_fee'),
        close_fee=data.get('close_fee'),
        close_today_rate=data.get('close_today_rate'),
        close_today_fee=data.get('close_today_fee'),
        th_main_contract=data.get('th_main_contract'),
        current_main_contract=data.get('current_main_contract'),
        th_order=data.get('th_order'),
        long_term_trend=data.get('long_term_trend')
    )
    
    # 保存到数据库
    db.session.add(future_info)
    db.session.commit()
    
    return jsonify({
        'code': 0,
        'msg': '创建成功',
        'data': future_info.to_dict()
    })

@bp.route('/update/<int:id>', methods=['PUT'])
def update(id):
    """更新期货基础信息"""
    future_info = FutureInfo.query.get_or_404(id)
    data = request.json
    
    # 更新字段
    if 'contract_letter' in data:
        future_info.contract_letter = data['contract_letter']
    if 'name' in data:
        future_info.name = data['name']
    if 'market' in data:
        future_info.market = data['market']
    if 'exchange' in data:
        future_info.exchange = data['exchange']
    if 'contract_multiplier' in data:
        future_info.contract_multiplier = data['contract_multiplier']
    if 'long_margin_rate' in data:
        future_info.long_margin_rate = data['long_margin_rate']
    if 'short_margin_rate' in data:
        future_info.short_margin_rate = data['short_margin_rate']
    if 'open_fee' in data:
        future_info.open_fee = data['open_fee']
    if 'close_fee' in data:
        future_info.close_fee = data['close_fee']
    if 'close_today_rate' in data:
        future_info.close_today_rate = data['close_today_rate']
    if 'close_today_fee' in data:
        future_info.close_today_fee = data['close_today_fee']
    if 'th_main_contract' in data:
        future_info.th_main_contract = data['th_main_contract']
    if 'current_main_contract' in data:
        future_info.current_main_contract = data['current_main_contract']
    if 'th_order' in data:
        future_info.th_order = data['th_order']
    if 'long_term_trend' in data:
        future_info.long_term_trend = data['long_term_trend']
    
    # 保存到数据库
    db.session.commit()
    
    return jsonify({
        'code': 0,
        'msg': '更新成功',
        'data': future_info.to_dict()
    })

@bp.route('/delete/<int:id>', methods=['DELETE'])
def delete(id):
    """删除期货基础信息"""
    future_info = FutureInfo.query.get_or_404(id)
    
    # 从数据库删除
    db.session.delete(future_info)
    db.session.commit()
    
    return jsonify({
        'code': 0,
        'msg': '删除成功'
    }) 