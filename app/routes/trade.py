"""
交易汇总记录相关路由
"""

from flask import Blueprint, jsonify, request, render_template, send_file, make_response
from app import db
from app.models.trade import TradeRecord, RollTradeRecord
from app.models.transaction import TransactionRecord
from datetime import datetime
import pandas as pd
import io
import os
from openpyxl.utils import get_column_letter
from io import BytesIO
from sqlalchemy import func

bp = Blueprint('trade', __name__, url_prefix='/trade')

@bp.route('/', methods=['GET'])
def index():
    """交易汇总记录列表页面"""
    return render_template('trade/index.html')

@bp.route('/list', methods=['GET'])
def get_list():
    """获取交易汇总记录列表"""
    try:
        print("获取交易汇总记录列表...")
        # 获取分页参数
        page = request.args.get('page', 1, type=int)
        limit = request.args.get('limit', 10, type=int)
        
        # 获取筛选参数
        start_time = request.args.get('start_time')
        end_time = request.args.get('end_time')
        names = request.args.getlist('name')
        contract_letters = request.args.getlist('contract_letter')
        contract_code = request.args.get('contract_code')
        strategy_ids = request.args.getlist('strategy_ids')
        trade_type = request.args.get('trade_type')
        position_type = request.args.get('position_type')
        
        # 构建查询
        query = TradeRecord.query
        
        if start_time:
            query = query.filter(TradeRecord.open_time >= datetime.strptime(start_time, '%Y-%m-%d'))
        
        if end_time:
            query = query.filter(TradeRecord.open_time <= datetime.strptime(end_time, '%Y-%m-%d'))
        
        if names:
            query = query.filter(TradeRecord.name.in_(names))
        
        if contract_letters:
            # 假设合约代码的前1-2位是合约字母
            query = query.filter(db.or_(*[TradeRecord.contract_code.startswith(letter) for letter in contract_letters]))
        
        if contract_code:
            query = query.filter(TradeRecord.contract_code.like(f'%{contract_code}%'))
        
        if strategy_ids:
            try:
                strategy_ids = [int(i) for i in strategy_ids if i.strip()]
                if strategy_ids:
                    query = query.filter(TradeRecord.strategy_ids.in_(strategy_ids))
            except ValueError:
                pass
        
        if trade_type is not None and trade_type.strip():
            try:
                query = query.filter(TradeRecord.trade_type == int(trade_type))
            except ValueError:
                pass
        
        if position_type is not None and position_type.strip():
            try:
                query = query.filter(TradeRecord.position_type == int(position_type))
            except ValueError:
                pass
        
        # 执行分页查询
        pagination = query.order_by(TradeRecord.open_time.desc()).paginate(page=page, per_page=limit, error_out=False)
        trades = pagination.items
        total = pagination.total
        print(f"找到{len(trades)}条交易汇总记录，总共{total}条")
        
        # 返回结果
        return jsonify({
            'code': 0,
            'msg': '成功',
            'count': total,
            'data': [trade.to_dict() for trade in trades]
        })
    except Exception as e:
        print(f"获取交易汇总记录列表失败: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return jsonify({
            'code': 1,
            'msg': f'获取列表失败: {str(e)}',
            'count': 0,
            'data': []
        })

@bp.route('/detail/<int:id>', methods=['GET'])
def get_detail(id):
    """获取交易汇总记录详情，改为渲染模板"""
    trade = TradeRecord.query.get_or_404(id)
    # 如果需要关联查询其他信息（如策略、K线形态、趋势名称），可以在这里进行
    # 例如，查询策略名称
    # strategy = StrategyInfo.query.get(trade.strategy_id) if trade.strategy_id else None
    # trade_data = trade.to_dict()
    # trade_data['strategy_name'] = strategy.name if strategy else trade.strategy_name # 优先使用查询到的名称
    
    return render_template('trade/detail.html', trade=trade)

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

@bp.route('/export', methods=['GET'])
def export():
    """导出交易汇总记录为Excel文件"""
    # 获取所有交易记录
    trades = TradeRecord.query.all()
    
    # 转换为DataFrame
    data = []
    for trade in trades:
        data.append({
            '合约代码': trade.contract_code,
            '名称': trade.name,
            '账户': trade.account,
            '策略': trade.strategy_name,
            '持仓类型': trade.position_type,
            'K线形态': trade.candle_pattern,
            '开仓时间': trade.open_time.strftime('%Y-%m-%d %H:%M') if trade.open_time else '',
            '平仓时间': trade.close_time.strftime('%Y-%m-%d %H:%M') if trade.close_time else '',
            '持仓量': trade.position_volume,
            '合约乘数': trade.contract_multiplier,
            '持仓成本': trade.past_position_cost,
            '平均售价': trade.average_sale_price,
            '单笔利润': trade.single_profit,
            '投资利润': trade.investment_profit,
            '投资收益率': trade.investment_profit_rate,
            '持仓天数': trade.holding_days,
            '年化收益率': trade.annual_profit_rate,
            '交易类型': trade.trade_type,
            '置信指数': trade.confidence_index,
            '相似度评价': trade.similarity_evaluation,
            '长期趋势': trade.long_trend_name,
            '中期趋势': trade.mid_trend_name,
        })
    
    df = pd.DataFrame(data)
    
    # 创建Excel文件
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, sheet_name='交易汇总', index=False)
        
        # 自动调整列宽
        worksheet = writer.sheets['交易汇总']
        for i, col in enumerate(df.columns):
            column_width = max(df[col].astype(str).map(len).max(), len(col) + 2)
            worksheet.set_column(i, i, column_width)
    
    output.seek(0)
    
    # 设置下载文件名
    filename = f'交易汇总_{datetime.now().strftime("%Y%m%d%H%M%S")}.xlsx'
    
    return send_file(
        output,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name=filename
    )

@bp.route('/template', methods=['GET'])
def get_template():
    """获取交易汇总记录的Excel导入模板"""
    # 创建DataFrame
    columns = [
        '换月交易主ID', '合约代码', '名称', '账户', 
        '操作策略ID', '操作策略', '多空仓位(0-多头,1-空头)', 
        'K线形态ID', 'K线形态', '开仓时间', '平仓时间', 
        '持仓手数', '合约乘数', '过往持仓成本', '平均售价', 
        '单笔收益', '投资收益', '投资收益率', '持仓天数', '年化收益率', 
        '交易类别(0-模拟,1-真实)', '信心指数', '相似度评估', 
        '长期趋势IDs', '长期趋势名称', '中期趋势IDs', '中期趋势名称'
    ]
    
    # 创建示例数据
    data = [
        [None, 'CU2305', '沪铜', '华安期货', 
         1, '趋势突破', 0, 
         1, '突破回踩', '2023-03-29 14:30', '2023-03-30 14:30', 
         1, 5, 68000, 68500, 
         2500, 2500, 0.0735, 1, 26.86, 
         0, 1.5, '80%相似', 
         '1,2', '长期上涨+短期震荡', '3,4', '中期下跌+短期震荡']
    ]
    
    df = pd.DataFrame(data, columns=columns)
    
    # 创建Excel文件
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, sheet_name='交易汇总导入模板', index=False)
        
        # 自动调整列宽
        worksheet = writer.sheets['交易汇总导入模板']
        for i, col in enumerate(df.columns):
            column_width = max(df[col].astype(str).map(len).max(), len(col) + 2)
            worksheet.set_column(i, i, column_width)
    
    output.seek(0)
    
    # 设置下载文件名
    filename = f'交易汇总导入模板_{datetime.now().strftime("%Y%m%d%H%M%S")}.xlsx'
    
    return send_file(
        output,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name=filename
    )

@bp.route('/import_page', methods=['GET'])
def import_page():
    """Display the import page."""
    return render_template('trade/import.html')

@bp.route('/import', methods=['POST'])
def import_excel():
    """从Excel导入交易汇总记录"""
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
        required_columns = ['合约代码', '名称', '多空仓位(0-多头,1-空头)', '开仓时间', '持仓手数', '合约乘数']
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
                # 处理日期时间
                open_time = None
                if '开仓时间' in row and not pd.isna(row['开仓时间']):
                    if isinstance(row['开仓时间'], str):
                        open_time = datetime.strptime(row['开仓时间'], '%Y-%m-%d %H:%M')
                    else:
                        open_time = row['开仓时间']
                else:
                    open_time = datetime.now()
                
                close_time = None
                if '平仓时间' in row and not pd.isna(row['平仓时间']):
                    if isinstance(row['平仓时间'], str):
                        close_time = datetime.strptime(row['平仓时间'], '%Y-%m-%d %H:%M')
                    else:
                        close_time = row['平仓时间']
                
                # 计算持仓天数
                holding_days = None
                if close_time and open_time:
                    holding_days = (close_time - open_time).days
                
                # 创建新记录
                trade = TradeRecord(
                    roll_trade_main_id=int(row['换月交易主ID']) if not pd.isna(row.get('换月交易主ID')) else None,
                    contract_code=row['合约代码'],
                    name=row['名称'],
                    account=row.get('账户', '华安期货'),
                    strategy_ids=row.get('操作策略ID'),
                    strategy_name=row.get('操作策略'),
                    position_type=int(row['多空仓位(0-多头,1-空头)']),
                    candle_pattern_ids=row.get('K线形态ID'),
                    candle_pattern=row.get('K线形态'),
                    open_time=open_time,
                    close_time=close_time,
                    position_volume=float(row['持仓手数']),
                    contract_multiplier=float(row['合约乘数']),
                    past_position_cost=float(row.get('过往持仓成本', 0)) if not pd.isna(row.get('过往持仓成本')) else None,
                    average_sale_price=float(row.get('平均售价', 0)) if not pd.isna(row.get('平均售价')) else None,
                    single_profit=float(row.get('单笔收益', 0)) if not pd.isna(row.get('单笔收益')) else None,
                    investment_profit=float(row.get('投资收益', 0)) if not pd.isna(row.get('投资收益')) else None,
                    investment_profit_rate=float(row.get('投资收益率', 0)) if not pd.isna(row.get('投资收益率')) else None,
                    holding_days=holding_days,
                    annual_profit_rate=float(row.get('年化收益率', 0)) if not pd.isna(row.get('年化收益率')) else None,
                    trade_type=int(row.get('交易类别(0-模拟,1-真实)', 0)) if not pd.isna(row.get('交易类别(0-模拟,1-真实)')) else 0,
                    confidence_index=float(row.get('信心指数', 0)) if not pd.isna(row.get('信心指数')) else None,
                    similarity_evaluation=row.get('相似度评估'),
                    long_trend_ids=row.get('长期趋势IDs'),
                    long_trend_name=row.get('长期趋势名称'),
                    mid_trend_ids=row.get('中期趋势IDs'),
                    mid_trend_name=row.get('中期趋势名称')
                )
                
                # 保存到数据库
                db.session.add(trade)
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