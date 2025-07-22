"""
期货基础信息相关路由
包括期货品种信息的查询、创建、更新等
"""

from flask import Blueprint, jsonify, request, render_template, send_file, make_response, current_app
from app.database.db_manager import db
from app.models.future_info import FutureInfo, FutureDaily
from app.models.dimension import TrendInfo
from app.services.data_scraper import FutureDataScraper
from app.services.data_update import data_update_service
import pandas as pd
import io
import os
from datetime import datetime
from werkzeug.utils import secure_filename
import threading
import logging

logger = logging.getLogger(__name__)

# 创建蓝图
bp = Blueprint('future_info', __name__, url_prefix='/api/future_info')

@bp.route('/', methods=['GET'])
def index():
    """期货基础信息列表页面 (仅渲染骨架)"""
    # # 获取查询参数 (不再需要从后端传递数据)
    # search = request.args.get('search', '')
    # page = request.args.get('page', 1, type=int)
    # limit = request.args.get('limit', 10, type=int)
    
    # # 构建查询 (不再需要从后端传递数据)
    # query = FutureInfo.query
    
    # # 应用查询条件 (不再需要从后端传递数据)
    # if search:
    #     query = query.filter(
    #         db.or_(
    #             FutureInfo.contract_letter.like(f'%{search}%'),
    #             FutureInfo.name.like(f'%{search}%')
    #         )
    #     )
    
    # # 执行分页查询 (不再需要从后端传递数据)
    # pagination = query.order_by(FutureInfo.id.asc()).paginate(page=page, per_page=limit, error_out=False)
    # futures = pagination.items
    # total = pagination.total
    
    # 只渲染模板，数据由前端AJAX获取
    return render_template('future_info/index.html')
                           # futures=futures, 
                           # pagination=pagination, 
                           # total=total, 
                           # search=search,
                           # limit=limit # 传递limit到模板，以便选择器知道当前值
                           

@bp.route('/add', methods=['GET'])
def add():
    """添加期货基础信息页面"""
    return render_template('future_info/add.html')

@bp.route('/edit/<int:id>', methods=['GET'])
def edit(id):
    """编辑期货基础信息页面"""
    return render_template('future_info/edit.html', future_id=id)

@bp.route('/get/<int:future_id>', methods=['GET'])
def get_future_info_detail(future_id):
    """获取期货基础信息详情"""
    future = FutureInfo.query.get_or_404(future_id)
    
    return jsonify({
        'code': 0, 
        'msg': '获取成功',
        'data': future.to_dict()
    })

@bp.route('/list', methods=['GET'])
def get_future_info_list():
    """获取期货基础信息列表 (支持分页和搜索)"""
    # 获取查询参数
    page = request.args.get('page', 1, type=int)
    limit = request.args.get('limit', 10, type=int)
    search = request.args.get('search', '')
    # 保留旧的过滤参数，如果需要的话
    market = request.args.get('market', type=int)
    contract_letter = request.args.get('contract_letter')
    name = request.args.get('name')
    long_term_trend = request.args.get('long_term_trend')
    future_id = request.args.get('id', type=int)
    
    # 构建查询
    query = FutureInfo.query
    
    # 应用过滤条件
    if market is not None:
        query = query.filter(FutureInfo.market == market)
    if contract_letter:
        query = query.filter(FutureInfo.contract_letter.like(f'%{contract_letter}%'))
    if name:
        query = query.filter(FutureInfo.name.like(f'%{name}%'))
    if long_term_trend:
        query = query.filter(FutureInfo.long_term_trend.like(f'%{long_term_trend}%'))
    if future_id is not None:
        query = query.filter(FutureInfo.id == future_id)
    
    # 添加搜索逻辑 (合并contract_letter和name搜索)
    if search:
        query = query.filter(
            db.or_(
                FutureInfo.contract_letter.like(f'%{search}%'),
                FutureInfo.name.like(f'%{search}%')
            )
        )
    
    # 执行分页查询并获取结果
    pagination = query.order_by(FutureInfo.id.asc()).paginate(page=page, per_page=limit, error_out=False)
    futures = pagination.items
    total = pagination.total
    
    # 将查询结果转换为JSON格式
    result = {
        'code': 0,
        'msg': '获取成功',
        'count': total, # 返回总数以供分页
        'data': [future.to_dict() for future in futures]
    }
    
    return jsonify(result)

@bp.route('/update/<int:future_id>', methods=['PUT'])
def update_future_info(future_id):
    """更新期货基础信息"""
    future = FutureInfo.query.get_or_404(future_id)
    data = request.json
    
    # 更新字段
    if 'contract_letter' in data:
        future.contract_letter = data['contract_letter']
    if 'name' in data:
        future.name = data['name']
    if 'market' in data:
        future.market = data['market']
    if 'exchange' in data:
        future.exchange = data['exchange']
    if 'contract_multiplier' in data:
        future.contract_multiplier = data['contract_multiplier']
    if 'long_margin_rate' in data:
        future.long_margin_rate = data['long_margin_rate']
    if 'short_margin_rate' in data:
        future.short_margin_rate = data['short_margin_rate']
    if 'open_fee' in data:
        future.open_fee = data['open_fee']
    if 'close_fee' in data:
        future.close_fee = data['close_fee']
    if 'close_today_rate' in data:
        future.close_today_rate = data['close_today_rate']
    if 'close_today_fee' in data:
        future.close_today_fee = data['close_today_fee']
    if 'th_main_contract' in data:
        future.th_main_contract = data['th_main_contract']
    if 'current_main_contract' in data:
        future.current_main_contract = data['current_main_contract']
    if 'th_order' in data:
        future.th_order = data['th_order']
    if 'long_term_trend' in data:
        future.long_term_trend = data['long_term_trend']
    
    # 保存到数据库
    db.session.commit()
    
    return jsonify({
        'code': 0,
        'msg': '更新成功',
        'data': future.to_dict()
    })

@bp.route('/add', methods=['POST'])
def create_future_info():
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

@bp.route('/delete/<int:future_id>', methods=['DELETE'])
def delete_future_info(future_id):
    """删除期货基础信息"""
    future = FutureInfo.query.get_or_404(future_id)
    
    # 从数据库中删除
    db.session.delete(future)
    db.session.commit()
    
    return jsonify({
        'code': 0,
        'msg': '删除成功'
    })

@bp.route('/template', methods=['GET'])
def get_template():
    """获取期货基础信息的Excel导入模板"""
    # 创建DataFrame
    columns = [
        '合约字母', '名称', '市场(0-国内,1-国外)', '交易所', '合约乘数', 
        '做多保证金率', '做空保证金率', '开仓费用', '平仓费用', 
        '平今费率', '平今费用', '同花主力合约', '当前主力合约', 
        '同花顺顺序', '长期趋势'
    ]
    
    # 创建示例数据
    data = [
        ['CU', '沪铜', 0, 'SHFE', 5, 
         0.1, 0.1, 3, 3, 
         0, 0, 'CU2305', 'CU2305', 
         1, '长期上涨']
    ]
    
    df = pd.DataFrame(data, columns=columns)
    
    # 创建Excel文件
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, sheet_name='期货基础信息导入模板', index=False)
        
        # 自动调整列宽
        worksheet = writer.sheets['期货基础信息导入模板']
        for i, col in enumerate(df.columns):
            column_width = max(df[col].astype(str).map(len).max(), len(col) + 2)
            worksheet.set_column(i, i, column_width)
    
    output.seek(0)
    
    # 设置下载文件名
    filename = f'期货基础信息导入模板_{datetime.now().strftime("%Y%m%d%H%M%S")}.xlsx'
    
    return send_file(
        output,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name=filename
    )

@bp.route('/import', methods=['POST'])
def import_excel():
    """从Excel导入期货基础信息"""
    if 'file' not in request.files:
        return jsonify({
            'code': 1,
            'msg': '没有上传文件'
        })
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({
            'code': 1,
            'msg': '没有选择文件'
        })
    
    if not file.filename.endswith('.xlsx'):
        return jsonify({
            'code': 1,
            'msg': '请上传Excel文件(.xlsx)'
        })
    
    try:
        # 读取Excel文件
        df = pd.read_excel(file)
        
        # 验证必填列
        required_columns = ['合约字母', '名称', '市场(0-国内,1-国外)']
        for col in required_columns:
            if col not in df.columns:
                return jsonify({
                    'code': 1,
                    'msg': f'Excel文件缺少必填列: {col}'
                })
        
        # 导入数据
        success_count = 0
        error_count = 0
        error_messages = []
        
        for i, row in df.iterrows():
            try:
                # 检查是否已存在相同合约字母
                existing = FutureInfo.query.filter_by(contract_letter=row['合约字母']).first()
                if existing:
                    # 更新现有记录
                    existing.name = row['名称']
                    existing.market = int(row.get('市场(0-国内,1-国外)', 0))
                    existing.exchange = row.get('交易所')
                    existing.contract_multiplier = float(row.get('合约乘数', 0)) if not pd.isna(row.get('合约乘数')) else None
                    existing.long_margin_rate = float(row.get('做多保证金率', 0)) if not pd.isna(row.get('做多保证金率')) else None
                    existing.short_margin_rate = float(row.get('做空保证金率', 0)) if not pd.isna(row.get('做空保证金率')) else None
                    existing.open_fee = float(row.get('开仓费用', 0)) if not pd.isna(row.get('开仓费用')) else None
                    existing.close_fee = float(row.get('平仓费用', 0)) if not pd.isna(row.get('平仓费用')) else None
                    existing.close_today_rate = float(row.get('平今费率', 0)) if not pd.isna(row.get('平今费率')) else None
                    existing.close_today_fee = float(row.get('平今费用', 0)) if not pd.isna(row.get('平今费用')) else None
                    existing.th_main_contract = row.get('同花主力合约')
                    existing.current_main_contract = row.get('当前主力合约')
                    existing.th_order = int(row.get('同花顺顺序', 0)) if not pd.isna(row.get('同花顺顺序')) else None
                    existing.long_term_trend = row.get('长期趋势')
                else:
                    # 创建新记录
                    future_info = FutureInfo(
                        contract_letter=row['合约字母'],
                        name=row['名称'],
                        market=int(row.get('市场(0-国内,1-国外)', 0)),
                        exchange=row.get('交易所'),
                        contract_multiplier=float(row.get('合约乘数', 0)) if not pd.isna(row.get('合约乘数')) else None,
                        long_margin_rate=float(row.get('做多保证金率', 0)) if not pd.isna(row.get('做多保证金率')) else None,
                        short_margin_rate=float(row.get('做空保证金率', 0)) if not pd.isna(row.get('做空保证金率')) else None,
                        open_fee=float(row.get('开仓费用', 0)) if not pd.isna(row.get('开仓费用')) else None,
                        close_fee=float(row.get('平仓费用', 0)) if not pd.isna(row.get('平仓费用')) else None,
                        close_today_rate=float(row.get('平今费率', 0)) if not pd.isna(row.get('平今费率')) else None,
                        close_today_fee=float(row.get('平今费用', 0)) if not pd.isna(row.get('平今费用')) else None,
                        th_main_contract=row.get('同花主力合约'),
                        current_main_contract=row.get('当前主力合约'),
                        th_order=int(row.get('同花顺顺序', 0)) if not pd.isna(row.get('同花顺顺序')) else None,
                        long_term_trend=row.get('长期趋势')
                    )
                    db.session.add(future_info)
                success_count += 1
                
            except Exception as e:
                error_count += 1
                error_messages.append(f'第{i+2}行出错: {str(e)}')
        
        # 提交所有更改
        db.session.commit()
        
        return jsonify({
            'code': 0,
            'msg': f'成功导入{success_count}条记录，失败{error_count}条',
            'data': {
                'success_count': success_count,
                'error_count': error_count,
                'error_messages': error_messages
            }
        })
        
    except Exception as e:
        return jsonify({
            'code': 1,
            'msg': f'导入失败: {str(e)}'
        })

@bp.route('/import', methods=['GET'])
def import_view():
    """导入期货基础信息页面"""
    return render_template('future_info/import.html')

@bp.route('/update-data', methods=['POST'])
def update_future_data():
    """手动触发期货数据更新"""
    # 获取更新模式
    data = request.json
    update_mode = data.get('update_mode', 'both')
    
    if update_mode not in ['daily', 'info', 'both']:
        return jsonify({
            'code': 1,
            'msg': '无效的更新模式，有效的选项为: daily, info, both'
        })
    
    # 在后台线程中执行更新，避免阻塞请求
    def update_data_thread():
        try:
            scraper = FutureDataScraper()
            with current_app.app_context():
                if update_mode in ['daily', 'both']:
                    # 更新future_daily表
                    records_count = scraper.update_future_daily(db.session, FutureDaily)
                    logger.info(f"future_daily表更新完成，共{records_count}条记录")
                
                if update_mode in ['info', 'both']:
                    if update_mode == 'both':
                        # 根据future_daily表更新future_info表
                        updated_count = scraper.update_future_info_from_daily(db.session, FutureInfo, FutureDaily)
                    else:
                        # 直接从网站更新future_info表
                        updated_count = scraper.update_future_info(db.session, FutureInfo)
                    logger.info(f"future_info表更新完成，共更新{updated_count}条记录")
                    # 在这里可以添加一个标记，表示更新完成
                    current_app.config['DATA_UPDATE_COMPLETE'] = True 
        except Exception as e:
            logger.error(f"更新期货数据时出错: {str(e)}")
            # 更新失败时也设置标记，或者设置不同的标记
            current_app.config['DATA_UPDATE_COMPLETE'] = False
            current_app.config['DATA_UPDATE_ERROR'] = str(e)
        finally:
            # 确保即使出错也重置标记
            pass # 可以在这里执行一些清理操作，但目前不需要
    
    # 启动后台线程执行更新
    thread = threading.Thread(target=update_data_thread)
    thread.daemon = True
    thread.start()
    
    # 重置完成标记和错误信息 (启动时重置)
    current_app.config['DATA_UPDATE_COMPLETE'] = None
    current_app.config['DATA_UPDATE_ERROR'] = None
    
    return jsonify({
        'code': 0,
        'msg': '期货数据更新已在后台启动，请稍后查看结果或等待页面自动刷新'
    })

@bp.route('/update-status', methods=['GET'])
def get_update_status():
    """检查后台数据更新的状态"""
    complete = current_app.config.get('DATA_UPDATE_COMPLETE')
    error = current_app.config.get('DATA_UPDATE_ERROR')
    
    status = {
        'code': 0,
        'data': {
            'complete': complete,
            'error': error
        }
    }
    
    # 如果已完成或出错，清除标记，避免重复通知
    if complete is not None:
        # 清除标记的操作移到实际获取状态之后，确保前端能至少获取一次结果
        # current_app.config['DATA_UPDATE_COMPLETE'] = None
        # current_app.config['DATA_UPDATE_ERROR'] = None
        pass
        
    return jsonify(status)

@bp.route('/daily-list', methods=['GET'])
def get_future_daily_list():
    """获取期货每日数据列表"""
    # 获取查询参数
    exchange = request.args.get('exchange')
    product_code = request.args.get('product_code')
    contract_code = request.args.get('contract_code')
    is_main_contract = request.args.get('is_main_contract', type=int)
    
    # 构建查询
    query = FutureDaily.query
    
    # 应用过滤条件
    if exchange:
        query = query.filter(FutureDaily.exchange.like(f'%{exchange}%'))
    if product_code:
        query = query.filter(FutureDaily.product_code.like(f'%{product_code}%'))
    if contract_code:
        query = query.filter(FutureDaily.contract_code.like(f'%{contract_code}%'))
    if is_main_contract is not None:
        query = query.filter(FutureDaily.is_main_contract == bool(is_main_contract))
    
    # 执行查询并获取结果
    daily_data = query.all()
    
    # 将查询结果转换为JSON格式
    result = {
        'code': 0,
        'msg': '获取成功',
        'count': len(daily_data),
        'data': [daily.to_dict() for daily in daily_data]
    }
    
    return jsonify(result)

@bp.route('/manual_update', methods=['POST'])
def manual_update():
    """手动触发数据更新"""
    return jsonify(data_update_service.manual_update())

@bp.route('/trends', methods=['GET'])
def get_trend_info_list():
    """获取趋势信息列表，用于在编辑期货信息时选择长期趋势特征"""
    
    # 获取查询参数
    category = request.args.get('category', type=int)
    
    # 构建查询
    query = TrendInfo.query
    
    # 应用过滤条件
    if category is not None:
        query = query.filter(TrendInfo.category == category)
    
    # 执行查询并获取结果
    trends = query.all()
    
    # 将查询结果转换为JSON格式
    trend_list = []
    for trend in trends:
        trend_data = {
            'id': trend.id,
            'category': trend.category,
            'name': trend.name,
            'time_range_id': trend.time_range_id,
            'amplitude_id': trend.amplitude_id,
            'position_id': trend.position_id,
            'speed_type_id': trend.speed_type_id,
            'trend_type_id': trend.trend_type_id,
            'extra_info': trend.extra_info
        }
        trend_list.append(trend_data)
    
    result = {
        'code': 0,
        'msg': '获取成功',
        'count': len(trends),
        'data': trend_list
    }
    
    return jsonify(result)

@bp.route('/validate-trends', methods=['POST'])
def validate_trend_names():
    """验证趋势特征名称是否有效"""
    data = request.json
    
    if not data or 'trend_names' not in data:
        return jsonify({
            'code': 1,
            'msg': '缺少趋势特征名称',
            'data': {'invalid_trends': []}
        })
    
    trend_names = data['trend_names']
    
    # 如果为空字符串，视为有效
    if not trend_names.strip():
        return jsonify({
            'code': 0,
            'msg': '验证成功',
            'data': {'invalid_trends': []}
        })
    
    # 分割趋势特征名称
    trend_names_list = [name.strip() for name in trend_names.split('+') if name.strip()]
    
    # 查询所有有效的趋势特征名称
    valid_trends = {trend.name for trend in TrendInfo.query.all()}
    
    # 找出无效的趋势特征名称
    invalid_trends = [name for name in trend_names_list if name not in valid_trends]
    
    if invalid_trends:
        return jsonify({
            'code': 1,
            'msg': '存在无效的趋势特征名称',
            'data': {'invalid_trends': invalid_trends}
        })
    
    return jsonify({
        'code': 0,
        'msg': '所有趋势特征名称均有效',
        'data': {'invalid_trends': []}
    }) 