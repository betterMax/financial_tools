from flask import Blueprint, jsonify
from app.models.dimension import StrategyInfo, CandleInfo, TrendInfo
from app import db

bp = Blueprint('dimension', __name__, url_prefix='/api/dimension')

@bp.route('/strategy/list_all', methods=['GET'])
def list_all_strategies():
    """获取所有策略信息"""
    try:
        strategies = StrategyInfo.query.all()
        strategy_list = [{'id': s.id, 'name': s.name} for s in strategies]
        return jsonify({'code': 0, 'msg': 'Success', 'data': strategy_list})
    except Exception as e:
        return jsonify({'code': 500, 'msg': f'Error fetching strategies: {str(e)}', 'data': []}), 500

@bp.route('/candle/list_all', methods=['GET'])
def list_all_candles():
    """获取所有K线形态信息"""
    try:
        candles = CandleInfo.query.all()
        candle_list = [{'id': c.id, 'name': c.name} for c in candles]
        return jsonify({'code': 0, 'msg': 'Success', 'data': candle_list})
    except Exception as e:
        return jsonify({'code': 500, 'msg': f'Error fetching candles: {str(e)}', 'data': []}), 500

@bp.route('/trend/list_all', methods=['GET'])
def list_all_trends():
    """获取所有趋势类型信息"""
    try:
        trends = TrendInfo.query.all()
        trend_list = [{'id': t.id, 'name': t.name} for t in trends]
        return jsonify({'code': 0, 'msg': 'Success', 'data': trend_list})
    except Exception as e:
        return jsonify({'code': 500, 'msg': f'Error fetching trends: {str(e)}', 'data': []}), 500 