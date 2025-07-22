"""
监控记录相关路由
"""

from flask import Blueprint, jsonify, request, render_template, send_file, make_response
from app import db
from app.models.monitor import MonitorRecord
from app.models.future_info import FutureInfo
import pandas as pd
import io
import os
from datetime import datetime
from werkzeug.utils import secure_filename
from io import BytesIO
from openpyxl.utils import get_column_letter

bp = Blueprint('monitor', __name__, url_prefix='/monitor')

@bp.route('/', methods=['GET'])
def index():
    """监控记录列表页面"""
    return render_template('monitor/index.html')

@bp.route('/add', methods=['GET'])
def add():
    """添加监控记录页面"""
    return render_template('monitor/add.html')

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

@bp.route('/add', methods=['POST'])
def add_post():
    """创建监控记录（通过add路由）"""
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

@bp.route('/import', methods=['GET'])
def import_view():
    """导入监控记录页面"""
    return render_template('monitor/import.html')

@bp.route('/get_template', methods=['GET'])
def get_template():
    """Generate and return an Excel template for data import."""
    # 创建一个DataFrame，包含需要的列
    df = pd.DataFrame(columns=[
        '合约代码', '名称', '市场类型', '关注原因', '关注状态', '备注'
    ])
    
    # 添加示例数据（可选）
    df.loc[0] = ['IF2212', '沪深300期货2212', '0', '价格突破', '1', '重点关注']
    df.loc[1] = ['CL2301', '原油期货2301', '1', '季节性变化', '0', '暂时观察']
    
    # 创建一个字节流
    output = BytesIO()
    
    # 使用ExcelWriter以便于设置列宽
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='监控记录导入模板')
        worksheet = writer.sheets['监控记录导入模板']
        
        # 调整列宽
        for i, col in enumerate(df.columns):
            column_width = max(len(col) * 2, 15)
            worksheet.column_dimensions[get_column_letter(i + 1)].width = column_width
    
    output.seek(0)
    
    # 返回Excel文件
    return send_file(
        output,
        as_attachment=True,
        download_name='监控记录导入模板.xlsx',
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )

@bp.route('/import', methods=['POST'])
def import_excel():
    """Import monitor records from Excel file."""
    if 'file' not in request.files:
        return jsonify({
            'code': 1,
            'msg': '没有上传文件'
        })
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({
            'code': 1,
            'msg': '未选择文件'
        })
    
    if not file.filename.endswith('.xlsx'):
        return jsonify({
            'code': 1,
            'msg': '请上传Excel文件(.xlsx)'
        })
    
    try:
        # 读取Excel文件
        df = pd.read_excel(file)
        
        # 检查必需的列
        required_columns = ['合约代码', '名称', '市场类型']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            return jsonify({
                'code': 1,
                'msg': f'缺少必要的列: {", ".join(missing_columns)}'
            })
        
        # 准备导入数据
        success_count = 0
        error_count = 0
        error_messages = []
        
        for index, row in df.iterrows():
            try:
                # 检查必填字段
                if pd.isna(row['合约代码']) or pd.isna(row['名称']) or pd.isna(row['市场类型']):
                    error_count += 1
                    error_messages.append(f"第{index+2}行: 合约代码、名称和市场类型为必填项")
                    continue
                
                # 创建监控记录
                monitor = MonitorRecord(
                    contract=row['合约代码'],
                    name=row['名称'],
                    market=int(row['市场类型']),
                    opportunity=row['关注原因'] if not pd.isna(row['关注原因']) else None,
                    status=int(row['关注状态']) if not pd.isna(row['关注状态']) else 0
                )
                
                db.session.add(monitor)
                success_count += 1
                
            except Exception as e:
                error_count += 1
                error_messages.append(f"第{index+2}行: {str(e)}")
        
        # 提交事务
        db.session.commit()
        
        return jsonify({
            'code': 0,
            'msg': f'成功导入{success_count}条记录',
            'data': {
                'success_count': success_count,
                'error_count': error_count,
                'error_messages': error_messages
            }
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'code': 1,
            'msg': f'导入失败: {str(e)}'
        })

# 新增 API 端点：根据 future_info_id 或 contract_code 查询 FutureInfo
@bp.route('/api/future_info/lookup', methods=['GET'])
def lookup_future_info():
    future_info_id = request.args.get('future_info_id', type=int)
    contract_code = request.args.get('contract_code')

    future = None
    if future_info_id:
        future = FutureInfo.query.get(future_info_id)
    elif contract_code:
        # 尝试通过合约代码查找，可能需要更复杂的逻辑来匹配
        # 这里假设 FutureInfo 有 contract_letter 字段，并且合约代码以它开头
        # 或者 FutureInfo 有一个字段直接存储了常见的合约代码
        # 此处仅为示例，您可能需要根据实际模型调整
        # 例如，如果 FutureInfo 有 name 或 symbol 字段可以匹配
        letter = ''.join(filter(str.isalpha, contract_code))[:2] # 提取字母部分
        if letter:
            future = FutureInfo.query.filter(
                FutureInfo.contract_letter.ilike(f'{letter}%')
            ).first() # 简单示例：按合约字母模糊匹配

    if future:
        return jsonify({
            'code': 0,
            'msg': '成功',
            'data': {
                'name': future.name,
                'market_type': future.market_type # 假设 FutureInfo 有 market_type 字段
            }
        })
    else:
        return jsonify({'code': 1, 'msg': '未找到匹配的期货信息', 'data': None}) 