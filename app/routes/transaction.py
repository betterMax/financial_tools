"""
交易记录相关路由
"""

from flask import Blueprint, jsonify, request, render_template, send_file, make_response
from app import db
from app.models.transaction import TransactionRecord
from app.models.future_info import FutureInfo
from app.models.dimension import StrategyInfo, CandleInfo, TrendInfo
from datetime import datetime
import pandas as pd
import io
import os
from werkzeug.utils import secure_filename
from sqlalchemy import text
import uuid
import tempfile

bp = Blueprint('transaction', __name__, url_prefix='/transaction')

@bp.route('/', methods=['GET'])
def index():
    """交易记录列表页面"""
    return render_template('transaction/index.html')

@bp.route('/add', methods=['GET'])
def add():
    """添加交易记录页面"""
    return render_template('transaction/add.html')

@bp.route('/edit/<int:id>', methods=['GET'])
def edit(id):
    """编辑交易记录页面"""
    return render_template('transaction/edit.html', transaction_id=id)

@bp.route('/detail/view/<int:id>', methods=['GET'])
def detail(id):
    """查看交易记录详情页面"""
    transaction_obj = TransactionRecord.query.get_or_404(id)
    transaction_dict = transaction_obj.to_dict() # Convert to dictionary first
    print(f"transaction_dict: {transaction_dict}")
    return render_template('transaction/detail.html', transaction=transaction_dict)

@bp.route('/api/list', methods=['GET'])
def get_list():
    """获取交易记录列表"""
    try:
        # 获取分页参数
        page = request.args.get('page', 1, type=int)
        limit = request.args.get('limit', 10, type=int)
        
        # 获取筛选参数
        start_time = request.args.get('start_time')
        end_time = request.args.get('end_time')
        names = request.args.getlist('name')
        contract_letters = request.args.getlist('contract_letter')
        contract_code = request.args.get('contract_code')
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
        
        if contract_code:
            query = query.filter(TransactionRecord.contract_code.like(f'%{contract_code}%'))
        
        if strategy_ids:
            try:
                strategy_ids = [int(i) for i in strategy_ids if i.strip()]
                if strategy_ids:
                    query = query.filter(TransactionRecord.strategy_ids.in_(strategy_ids))
            except ValueError:
                pass
        
        if trade_type is not None and trade_type.strip():
            try:
                query = query.filter(TransactionRecord.trade_type == int(trade_type))
            except ValueError:
                pass
        
        if trade_statuses:
            try:
                trade_statuses = [int(i) for i in trade_statuses if i.strip()]
                if trade_statuses:
                    query = query.filter(TransactionRecord.trade_status.in_(trade_statuses))
            except ValueError:
                pass
        
        # 执行分页查询
        pagination = query.order_by(TransactionRecord.transaction_time.desc()).paginate(page=page, per_page=limit, error_out=False)
        transactions = pagination.items
        total = pagination.total
        
        # 返回结果
        return jsonify({
            'code': 0,
            'msg': '成功',
            'count': total, # 返回总记录数用于分页
            'data': [transaction.to_dict() for transaction in transactions]
        })
    except Exception as e:
        return jsonify({
            'code': 1,
            'msg': f'获取列表失败: {str(e)}',
            'count': 0,
            'data': []
        })

@bp.route('/api/future_info/by_letter/<string:letter>', methods=['GET'])
def get_future_info_by_letter(letter):
    """根据合约字母获取期货信息"""
    if not letter:
        return jsonify({'code': 1, 'msg': '缺少合约字母参数'})

    # 统一转为大写进行查询
    letter_upper = letter.upper()

    # 查找匹配的 FutureInfo 记录
    # 假设 future_info 表中有 contract_letter 字段存储纯字母（如 CU, ZC）
    # 使用 ilike 可能更健壮，如果 contract_letter 存储的是完整代码的前缀
    # future_info = FutureInfo.query.filter(FutureInfo.contract_letter.ilike(f'{letter_upper}%')).first()
    future_info = FutureInfo.query.filter_by(contract_letter=letter_upper).first()

    if future_info:
        return jsonify({
            'code': 0,
            'msg': '成功',
            'data': {
                'name': future_info.name,
                'open_fee': future_info.open_fee,
                'close_fee': future_info.close_fee,
                'contract_multiplier': future_info.contract_multiplier,
                'long_margin_rate': future_info.long_margin_rate,
                'short_margin_rate': future_info.short_margin_rate
            }
        })
    else:
        return jsonify({
            'code': 1,
            'msg': f'未找到合约字母为 {letter_upper} 的期货信息'
        })

@bp.route('/api/strategy_info/list', methods=['GET'])
def get_strategy_info_list():
    """获取所有策略信息列表"""
    try:
        strategies = StrategyInfo.query.order_by(StrategyInfo.id).all()
        strategy_list = [{'id': s.id, 'name': s.name} for s in strategies]
        return jsonify({
            'code': 0,
            'msg': '成功',
            'data': strategy_list
        })
    except Exception as e:
        return jsonify({
            'code': 1,
            'msg': f'获取策略列表失败: {str(e)}'
        })

@bp.route('/api/detail/<int:id>', methods=['GET'])
def get_detail(id):
    """获取交易记录详情"""
    transaction = TransactionRecord.query.get_or_404(id)
    # transaction_dict = transaction.to_dict()
    # # 尝试根据名称查找关联的 ID
    # account_id = None
    # future_info_id = None
    # if transaction.account:
    #     account_obj = Account.query.filter_by(account_name=transaction.account).first()
    #     if account_obj:
    #         account_id = account_obj.id
    # if transaction.name:
    #     # 优先按名称精确匹配
    #     future_obj = FutureInfo.query.filter_by(name=transaction.name).first()
    #     if not future_obj and transaction.contract_code:
    #         # 如果按名称找不到，尝试按合约字母匹配
    #         letter = ''.join(filter(str.isalpha, transaction.contract_code))[:2]
    #         if letter:
    #              future_obj = FutureInfo.query.filter(FutureInfo.contract_letter.ilike(f'{letter}%')).first()
    #     if future_obj:
    #         future_info_id = future_obj.id
    # # 将 ID 添加到返回的字典中
    # transaction_dict['account_id'] = account_id
    # transaction_dict['future_info_id'] = future_info_id

    return jsonify({
        'code': 0,
        'msg': '成功',
        'data': transaction.to_dict() # 直接返回 to_dict() 结果
    })

@bp.route('/api/create', methods=['POST'])
def create():
    """创建交易记录 (手动添加)"""
    # 在函数内部导入，避免循环依赖
    from app.models.trade import TradeRecord
    from app.services.trade_logic import update_trade_record

    data = request.json
    try:
        # --- 1. Process Input Data ---
        transaction_time = datetime.strptime(data.get('transaction_time', ''), '%Y-%m-%d %H:%M') if data.get('transaction_time') else datetime.now()
        operation_time = transaction_time
        if 'operation_time' in data and data['operation_time']:
             try:
                 operation_time = datetime.strptime(data['operation_time'], '%Y-%m-%d %H:%M')
             except ValueError:
                 pass

        # Basic data
        name = data.get('name')
        price = data.get('price')
        volume = data.get('volume')
        contract_multiplier = data.get('contract_multiplier')
        position_type = data.get('position_type')
        account = data.get('account', '华安期货')
        trade_type = data.get('trade_type', 0)
        trade_status = data.get('trade_status', 0)
        stop_loss_price = data.get('stop_loss_price')
        confidence_index = data.get('confidence_index')
        similarity_evaluation = data.get('similarity_evaluation')
        notes = data.get('notes')
        contract_code=data.get('contract_code')

        # Calculated financial data (from frontend)
        amount = data.get('amount')
        fee = data.get('fee')
        volume_change = data.get('volume_change')
        margin = data.get('margin')

        # Process names to IDs (Strategies, Candles, Trends)
        strategy_name = data.get('strategy_name', '').strip()
        strategy_ids, corrected_strategy_name = _get_ids_from_names(strategy_name, StrategyInfo)

        candle_pattern_name = data.get('candle_pattern_name', '').strip()
        candle_pattern_ids, corrected_candle_pattern_name = _get_ids_from_names(candle_pattern_name, CandleInfo)

        long_trend_name = data.get('long_trend_name', '').strip()
        long_trend_ids, corrected_long_trend_name = _get_ids_from_names(long_trend_name, TrendInfo)

        mid_trend_name = data.get('mid_trend_name', '').strip()
        mid_trend_ids, corrected_mid_trend_name = _get_ids_from_names(mid_trend_name, TrendInfo)

        # --- 2. Create TransactionRecord (trade_id is initially None) ---
        new_transaction = TransactionRecord(
            transaction_time=transaction_time,
            operation_time=operation_time,
            contract_code=contract_code,
            name=name,
            account=account,
            strategy_ids=strategy_ids,
            strategy_name=corrected_strategy_name,
            position_type=position_type,
            candle_pattern_ids=candle_pattern_ids,
            candle_pattern=corrected_candle_pattern_name,
            price=price,
            volume=volume,
            contract_multiplier=contract_multiplier,
            amount=amount,
            fee=fee,
            volume_change=volume_change,
            margin=margin,
            trade_type=trade_type,
            trade_status=trade_status,
            stop_loss_price=stop_loss_price,
            confidence_index=confidence_index,
            similarity_evaluation=similarity_evaluation,
            long_trend_ids=long_trend_ids,
            long_trend_name=corrected_long_trend_name,
            mid_trend_ids=mid_trend_ids,
            mid_trend_name=corrected_mid_trend_name,
            # notes=notes, # Add if model has notes field
            trade_id = None # Initial state
        )

        # --- 3. Handle Trade Logic (Find Match or Create New) ---
        target_trade_id = None
        final_trade_msg = ""

        # Only try to find a match if it's a closing transaction
        if position_type in [1, 3]: # 平多 or 平空
            print("处理平仓，尝试查找匹配的未平仓 Trade...")
            target_open_pos_type = 0 if position_type == 1 else 2
            # Find the latest open transaction of the opposite type for the same contract/account/strategy
            # that is linked to a TradeRecord which is currently open (close_time is null)
            matching_open_trans = db.session.query(TransactionRecord)\
                .join(TradeRecord, TransactionRecord.trade_id == TradeRecord.id)\
                .filter(
                    TradeRecord.close_time.is_(None), # Must be an open trade
                    TransactionRecord.contract_code == new_transaction.contract_code,
                    TransactionRecord.account == new_transaction.account,
                    TransactionRecord.strategy_ids == new_transaction.strategy_ids, # Strategy must match
                    TransactionRecord.position_type == target_open_pos_type
                )\
                .order_by(TransactionRecord.transaction_time.desc())\
                .first()

            if matching_open_trans:
                target_trade_id = matching_open_trans.trade_id
                new_transaction.trade_id = target_trade_id # Associate with the found trade
                print(f"找到匹配的未平仓 Trade ID: {target_trade_id}，关联此平仓记录。")
            else:
                print("未找到匹配的未平仓开仓记录，此平仓记录将创建新的 TradeRecord（可能表示孤立平仓或流程问题）。")
                # Proceed as if it's an opening transaction (will create new trade)

        # --- 4. Add Transaction to Session ---
        db.session.add(new_transaction)
        db.session.flush() # Get the ID for new_transaction

        # --- 5. Create or Update Trade Record ---
        if target_trade_id:
            # Update existing TradeRecord
            print(f"触发 TradeRecord 更新 ID: {target_trade_id}")
            update_result = update_trade_record(target_trade_id) # This function handles fetching all related trans and recalculating
            final_trade_msg = update_result.get('msg', f"尝试更新 TradeRecord ID: {target_trade_id}")
        else:
            # Create new TradeRecord (for opening transactions or unmatched closing ones)
            print("创建新的 TradeRecord...")
            # Use the helper that returns a data dictionary
            trade_data = generate_trade_from_transactions_data([new_transaction])
            if trade_data:
                 # Create TradeRecord instance using the dictionary
                 # Ensure TradeRecord's __init__ or a classmethod can handle this dict
                 # Or manually map fields if needed
                 # Example assuming direct mapping works:
                 try:
                     new_trade = TradeRecord(**trade_data)
                     db.session.add(new_trade)
                     db.session.flush() # Get the ID for the new trade
                     new_transaction.trade_id = new_trade.id # Backfill the trade_id
                     final_trade_msg = f"成功创建新的 TradeRecord ID: {new_trade.id}"
                     print(final_trade_msg)
                 except Exception as trade_create_e:
                     final_trade_msg = f"创建 TradeRecord 实例时出错: {trade_create_e}"
                     print(final_trade_msg)
                     # Consider what to do if trade creation fails - maybe rollback transaction?
            else:
                 final_trade_msg = "创建新的 TradeRecord 失败（无法计算数据）。"
                 print(final_trade_msg)

        # --- 6. Commit and Respond ---
        db.session.commit()

        return jsonify({
            'code': 0,
            'msg': f'操作成功。{final_trade_msg}',
            'data': new_transaction.to_dict() # Return the transaction, possibly with updated trade_id
        })

    except Exception as e:
        db.session.rollback()
        import traceback
        print(traceback.format_exc())
        return jsonify({
            'code': 1,
            'msg': f'创建交易记录时出错: {str(e)}'
        })

# Helper to convert names to IDs
def _get_ids_from_names(names_string, model):
    ids = None
    corrected_names = None
    if names_string:
        name_list = [name.strip() for name in names_string.split('+') if name.strip()]
        if name_list:
            records = model.query.filter(model.name.in_(name_list)).all()
            id_map = {r.name: r.id for r in records}
            id_list = [str(id_map[name]) for name in name_list if name in id_map]
            matched_names = [name for name in name_list if name in id_map]
            if id_list:
                ids = ','.join(id_list)
            if matched_names:
                corrected_names = '+'.join(matched_names)
    return ids, corrected_names

@bp.route('/api/update/<int:id>', methods=['PUT'])
def update(id):
    """更新交易记录"""
    # 在函数内部导入
    from app.services.trade_logic import update_trade_record

    transaction = TransactionRecord.query.get_or_404(id)
    original_trade_id = transaction.trade_id # 记录原始 trade_id
    data = request.json

    recalculate_financials = False
    trigger_trade_update = False # Flag to trigger trade update

    # 更新字段
    if 'transaction_time' in data:
        try:
            transaction.transaction_time = datetime.fromisoformat(data['transaction_time'])
        except ValueError:
            transaction.transaction_time = datetime.strptime(data['transaction_time'], '%Y-%m-%d %H:%M')
        recalculate_financials = True # 时间变化影响汇总
    if 'contract_code' in data:
        transaction.contract_code = data['contract_code']
        recalculate_financials = True
    if 'name' in data:
        transaction.name = data['name']
        recalculate_financials = True # name 变化影响 margin 计算和汇总
    if 'account' in data:
        transaction.account = data['account']
        recalculate_financials = True
    if 'strategy_ids' in data:
        transaction.strategy_ids = data['strategy_ids']
        recalculate_financials = True
    if 'strategy_name' in data:
        transaction.strategy_name = data['strategy_name']
    if 'position_type' in data:
        transaction.position_type = data['position_type']
        recalculate_financials = True # position_type 变化影响 volume_change 和 margin
    if 'candle_pattern_ids' in data:
        transaction.candle_pattern_ids = data['candle_pattern_ids']
    if 'candle_pattern' in data:
        transaction.candle_pattern = data['candle_pattern']
    if 'price' in data:
        transaction.price = data['price']
        recalculate_financials = True # price 变化影响 amount, margin
    if 'volume' in data:
        transaction.volume = data['volume']
        recalculate_financials = True # volume 变化影响 amount, volume_change, margin
    if 'contract_multiplier' in data and data['contract_multiplier'] is not None:
        transaction.contract_multiplier = data['contract_multiplier']
        recalculate_financials = True # multiplier 变化影响 amount, margin
    if 'fee' in data:
        transaction.fee = data['fee']
        # fee 变化本身不直接触发重算 amount/margin/volume_change, 但会影响最终利润计算
    if 'trade_type' in data:
        transaction.trade_type = data['trade_type']
    if 'trade_status' in data:
        transaction.trade_status = data['trade_status']
    if 'latest_price' in data:
        transaction.latest_price = data['latest_price']
        # latest_price 变化影响 to_dict 中的计算，不需要在此重算存储字段
    if 'stop_loss_price' in data:
        transaction.stop_loss_price = data['stop_loss_price']
        # stop_loss_price 变化影响 to_dict 中的计算
    # 移除 is_close_today, related_open_id, notes 的更新 (根据 BRD 要求)
    # if 'is_close_today' in data:
    #     transaction.is_close_today = data['is_close_today']
    # if 'related_open_id' in data:
    #     transaction.related_open_id = data['related_open_id']
    # if 'notes' in data:
    #     transaction.notes = data['notes']
    if 'operation_time' in data:
        try:
            transaction.operation_time = datetime.fromisoformat(data['operation_time'])
        except ValueError:
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

    # 重新计算相关字段
    if recalculate_financials:
        # 确保必要字段存在
        price = transaction.price
        volume = transaction.volume
        contract_multiplier = transaction.contract_multiplier
        position_type = transaction.position_type
        name = transaction.name

        if price is not None and volume is not None and contract_multiplier is not None:
            # 重新计算成交金额
            transaction.amount = price * volume * contract_multiplier

            # 重新计算手数变化
            if position_type in [0, 3]:
                transaction.volume_change = volume
            elif position_type in [1, 2]:
                transaction.volume_change = -volume
            else:
                transaction.volume_change = 0

            # 重新计算保证金
            margin = None
            future_info = None
            if name:
                future_info = FutureInfo.query.filter_by(name=name).first()

            if future_info and transaction.amount is not None:
                margin_rate = None
                if position_type in [0, 1]: # 多头
                    margin_rate = future_info.long_margin_rate
                elif position_type in [2, 3]: # 空头
                    margin_rate = future_info.short_margin_rate

                if margin_rate is not None:
                     # 假设 margin_rate 是百分比形式存储
                    margin = transaction.amount * (margin_rate / 100.0)
            transaction.margin = margin
        else:
            # 如果计算所需字段不全，将计算结果设为 None
            transaction.amount = None
            transaction.volume_change = None
            transaction.margin = None

    # 保存到数据库
    db.session.commit()

    # --- Update Trade Record(s) if needed ---
    trade_update_msg = ""
    if trigger_trade_update:
        ids_to_update = set()
        if original_trade_id:
            ids_to_update.add(original_trade_id)
        if transaction.trade_id and transaction.trade_id != original_trade_id:
             ids_to_update.add(transaction.trade_id)

        print(f"交易记录更新触发 Trade Record 更新 IDs: {ids_to_update}")
        for t_id in ids_to_update:
             if t_id: # Ensure not None
                 try:
                     update_result = update_trade_record(t_id)
                     trade_update_msg += f" Trade ID {t_id}: {update_result.get('msg', '尝试更新')}. "
                 except Exception as e:
                     trade_update_msg += f" Trade ID {t_id} 更新失败: {e}. "
                     print(f"更新 Trade ID {t_id} 失败: {e}")

    return jsonify({
        'code': 0,
        'msg': f'更新成功。{trade_update_msg}',
        'data': transaction.to_dict()
    })

@bp.route('/api/delete/<int:id>', methods=['DELETE'])
def delete(id):
    """删除交易记录"""
    # 在函数内部导入
    from app.services.trade_logic import update_trade_record

    transaction = TransactionRecord.query.get_or_404(id)
    associated_trade_id = transaction.trade_id

    db.session.delete(transaction)
    db.session.commit() # Commit deletion first

    # Trigger update for the associated trade record
    trade_update_msg = ""
    if associated_trade_id:
        print(f"删除交易记录 ID {id} 触发 Trade Record 更新 ID: {associated_trade_id}")
        try:
            update_result = update_trade_record(associated_trade_id)
            trade_update_msg = f"关联 Trade ID {associated_trade_id}: {update_result.get('msg', '尝试更新')}"
        except Exception as e:
            trade_update_msg = f"关联 Trade ID {associated_trade_id} 更新失败: {e}"
            print(f"更新 Trade ID {associated_trade_id} (因删除) 失败: {e}")
            # Consider if the trade should be deleted if it has no transactions left

    return jsonify({
        'code': 0,
        'msg': f'删除成功。{trade_update_msg}'
    })

@bp.route('/template', methods=['GET'])
def get_template():
    """获取交易记录的Excel导入模板"""
    # 创建DataFrame
    columns = [
        '交易ID', '换月ID', '成交时间', '合约代码', '合约名称', '账户', 
        '操作策略', '多空仓位', 'K线形态', '成交价格', '成交手数', '单位', 
        '成交金额', '手续费', '手数变化', '现金流', '保证金', '资金阈值判定',
        '交易类别', '交易状态', '止损点', '操作日期',
        '长期趋势名称', '中期趋势名称'
    ]
    
    # 创建示例数据
    data = [
        [1, 0, '2023-03-29 14:30', 'CU2305', '沪铜', '华安期货', 
         '趋势突破+均线突破', 0, '突破回踩+双底', 68000, 1, 5, 
         340000, 15, 1, -340015, 34000, 0,
         0, 0, 67500, '2023-03-29 14:30',
         '长期上涨+短期震荡', '中期下跌+短期震荡']
    ]
    
    df = pd.DataFrame(data, columns=columns)
    
    # 创建Excel文件
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, sheet_name='交易记录导入模板', index=False)
        
        # 自动调整列宽
        worksheet = writer.sheets['交易记录导入模板']
        for i, col in enumerate(df.columns):
            column_width = max(df[col].astype(str).map(len).max(), len(col) + 2)
            worksheet.set_column(i, i, column_width)
    
    output.seek(0)
    
    # 设置下载文件名
    filename = f'交易记录导入模板_{datetime.now().strftime("%Y%m%d%H%M%S")}.xlsx'
    
    return send_file(
        output,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name=filename
    )

@bp.route('/api/import', methods=['POST'])
def import_excel():
    """从Excel导入交易记录 (修改后)"""
    # 在函数内部导入
    from app.services.trade_logic import sync_trades_after_import

    if 'file' not in request.files:
        return jsonify({'code': 1,'msg': '没有上传文件'})
    file = request.files['file']
    if file.filename == '':
        return jsonify({'code': 1, 'msg': '没有选择文件'})
    if not file.filename.endswith('.xlsx'):
        return jsonify({'code': 1, 'msg': '请上传Excel文件(.xlsx)'})

    try:
        temp_dir = tempfile.gettempdir()
        cache_buster = str(uuid.uuid4())
        temp_path = os.path.join(temp_dir, f"transaction_import_{cache_buster}.xlsx")
        file.save(temp_path)
        df = pd.read_excel(temp_path)
        try:
            os.remove(temp_path)
        except Exception: pass

        print(f"Excel 列名: {df.columns.tolist()}")

        required_columns = ['交易ID', '合约代码', '合约名称', '多空仓位', '成交价格', '成交手数']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            return jsonify({'code': 1, 'msg': f'Excel文件缺少必填列: {", ".join(missing_columns)}'})

        # --- 验证 Trade ID 配对 ---
        trade_id_map = {}
        row_errors = {} # Store errors by row index

        for i, row in df.iterrows():
            row_num = i + 2 # Excel row number
            excel_trade_id = None
            pos_type = None
            try:
                 if '交易ID' in row and not pd.isna(row['交易ID']):
                      excel_trade_id = int(row['交易ID'])
                 else:
                      raise ValueError("缺少必需的 '交易ID'")

                 if '多空仓位' in row and not pd.isna(row['多空仓位']):
                     pos_type = int(row['多空仓位'])
                     if pos_type not in [0, 1, 2, 3]:
                         raise ValueError("无效的 '多空仓位' 值")
                 else:
                      raise ValueError("缺少必需的 '多空仓位'")

                 if excel_trade_id not in trade_id_map:
                     trade_id_map[excel_trade_id] = []
                 trade_id_map[excel_trade_id].append({'pos_type': pos_type, 'row_num': row_num})

            except Exception as e:
                 row_errors[row_num] = f"行预检错误: {str(e)}"

        # Check pairs
        for trade_id, items in trade_id_map.items():
             if len(items) > 2:
                  involved_rows = ", ".join([str(item['row_num']) for item in items])
                  error_msg = f"交易ID {trade_id} 在行 {involved_rows} 出现超过2次。"
                  for item in items: row_errors[item['row_num']] = error_msg # Mark all related rows
             elif len(items) == 2:
                  pos_types = {item['pos_type'] for item in items}
                  if not ((0 in pos_types and 1 in pos_types) or (2 in pos_types and 3 in pos_types)):
                       involved_rows = ", ".join([str(item['row_num']) for item in items])
                       error_msg = f"交易ID {trade_id} 在行 {involved_rows} 的仓位类型不是有效的开平仓对。"
                       for item in items: row_errors[item['row_num']] = error_msg
             # Single entry is allowed, will create/update trade based on that single entry

        # --- Process Rows ---
        transactions_to_add = []
        imported_trade_ids = set()
        error_count = len(row_errors)
        error_messages = list(row_errors.values()) # Collect pre-check errors

        # Load dimension maps once
        strategy_id_map, candle_pattern_id_map, trend_id_map = _load_dimension_maps()

        for i, row in df.iterrows():
            row_num = i + 2
            if row_num in row_errors: # Skip rows with pre-check errors
                continue

            try:
                excel_trade_id = int(row['交易ID']) # Already validated
                position_type = int(row['多空仓位']) # Already validated

                transaction_time, operation_time = _parse_excel_dates(row.get('成交时间'), row.get('操作日期'))

                price = float(row['成交价格'])
                volume = float(row['成交手数'])
                contract_multiplier = float(row.get('单位', 1)) if not pd.isna(row.get('单位')) else 1
                amount = float(row.get('成交金额', price * volume * contract_multiplier)) if not pd.isna(row.get('成交金额')) else price * volume * contract_multiplier
                fee = float(row.get('手续费', 0)) if not pd.isna(row.get('手续费')) else 0
                # Calculate volume_change based on position type
                volume_change = volume if position_type in [0, 3] else -volume

                # Margin needs calculation based on FutureInfo (similar to create logic)
                # margin = _calculate_margin(...) # Need a helper or repeat logic
                margin = float(row.get('保证金', 0)) if not pd.isna(row.get('保证金')) else None # Simplified: Take from Excel or None

                # Get IDs from names using preloaded maps
                strategy_ids, strategy_name = _resolve_names(row.get('操作策略', ''), strategy_id_map)
                candle_pattern_ids, candle_pattern = _resolve_names(row.get('K线形态', ''), candle_pattern_id_map)
                long_trend_ids, long_trend_name = _resolve_names(row.get('长期趋势名称', ''), trend_id_map)
                mid_trend_ids, mid_trend_name = _resolve_names(row.get('中期趋势名称', ''), trend_id_map)

                transaction = TransactionRecord(
                    trade_id=excel_trade_id,
                    roll_id=int(row.get('换月ID', 0)) if not pd.isna(row.get('换月ID')) else None,
                    transaction_time=transaction_time,
                    operation_time=operation_time,
                    contract_code=row['合约代码'],
                    name=row['合约名称'],
                    account=row.get('账户', '华安期货'),
                    strategy_ids=strategy_ids,
                    strategy_name=strategy_name,
                    position_type=position_type,
                    candle_pattern_ids=candle_pattern_ids,
                    candle_pattern=candle_pattern,
                    price=price,
                    volume=volume,
                    contract_multiplier=contract_multiplier,
                    amount=amount,
                    fee=fee,
                    volume_change=volume_change, # Use calculated value
                    # cash_flow=... # Not directly in simpler template?
                    margin=margin, # Use calculated or Excel value
                    # fund_threshold=...
                    trade_type=int(row.get('交易类别', 0)) if not pd.isna(row.get('交易类别')) else 0,
                    trade_status=int(row.get('交易状态', 0)) if not pd.isna(row.get('交易状态')) else 0,
                    stop_loss_price=float(row.get('止损点', 0)) if not pd.isna(row.get('止损点')) else None,
                    confidence_index=int(row.get('信心指数', 0)) if not pd.isna(row.get('信心指数')) else None,
                    similarity_evaluation=row.get('相似度评估'),
                    long_trend_ids=long_trend_ids,
                    long_trend_name=long_trend_name,
                    mid_trend_ids=mid_trend_ids,
                    mid_trend_name=mid_trend_name
                    # notes=...
                )
                transactions_to_add.append(transaction)
                imported_trade_ids.add(excel_trade_id)

            except Exception as e:
                error_count += 1
                row_data_str = ", ".join([f"{k}={v}" for k, v in row.items()])
                error_msg = f'第{row_num}行处理错误: {str(e)}\n行数据: {row_data_str[:200]}...' # Limit row data length
                print(error_msg)
                error_messages.append(error_msg)
                # No rollback needed here as we haven't added to session yet

        # --- Add valid transactions and sync trades ---
        sync_result = None # 初始化为 None
        if transactions_to_add:
            try:
                # Check for duplicates before adding (e.g., unique constraint on id?)
                # Add all valid Transaction Records
                db.session.add_all(transactions_to_add)
                db.session.flush() # Assign transaction IDs
                print(f"已添加 {len(transactions_to_add)} 条交易记录到 session。")
                final_success_count = len(transactions_to_add) # Update success count

                # Sync Trade Records
                print(f"开始同步 {len(imported_trade_ids)} 个关联的 Trade Records...")
                sync_result = sync_trades_after_import(list(imported_trade_ids))
                sync_msg = sync_result.get('msg', '交易汇总记录同步完成。')
                print(sync_msg) # 打印同步结果

                db.session.commit() # Commit transaction additions/updates and trade creations/updates

            except Exception as commit_sync_e:
                db.session.rollback() # Rollback if commit or sync fails
                import traceback
                print("Commit/Sync 阶段出错:")
                print(traceback.format_exc())
                final_success_count = 0 # Reset success count on final error
                error_count = len(df) # Mark all as failed if commit fails
                sync_msg = "数据库提交或同步失败，所有更改已回滚。"
                error_messages.append(f"数据库错误: {str(commit_sync_e)}")

        return jsonify({
            'code': 0 if error_count == 0 else 1, # Adjust code based on if errors occurred
            'msg': f'处理完成: {final_success_count} 条记录成功导入/更新, {error_count} 行存在错误。{sync_msg}',
            'data': {
                'success_count': final_success_count,
                'error_count': error_count,
                'error_messages': error_messages,
                'sync_details': sync_result # Optional: include sync details
            }
        })

    except Exception as e:
        # Catch errors during file reading or initial setup
        db.session.rollback()
        import traceback
        print(traceback.format_exc())
        return jsonify({
            'code': 1,
            'msg': f'导入过程中发生意外错误: {str(e)}'
        })

# --- Helper functions for import ---
def _load_dimension_maps():
    strategy_map = {s.name: s.id for s in StrategyInfo.query.all()}
    candle_map = {c.name: c.id for c in CandleInfo.query.all()}
    trend_map = {t.name: t.id for t in TrendInfo.query.all()}
    return strategy_map, candle_map, trend_map

def _parse_excel_dates(time_val, op_time_val):
    transaction_time = datetime.now() # Default
    if not pd.isna(time_val):
        try:
            # Handle various possible Excel date formats
            if isinstance(time_val, datetime): transaction_time = time_val
            else: transaction_time = pd.to_datetime(time_val).to_pydatetime()
        except Exception as e:
            print(f"无法解析成交时间 '{time_val}', 使用当前时间. 错误: {e}")

    operation_time = transaction_time # Default to transaction_time
    if not pd.isna(op_time_val):
         try:
             if isinstance(op_time_val, datetime): operation_time = op_time_val
             else: operation_time = pd.to_datetime(op_time_val).to_pydatetime()
         except Exception as e:
             print(f"无法解析操作时间 '{op_time_val}', 使用成交时间. 错误: {e}")

    return transaction_time, operation_time

def _resolve_names(names_string, id_map):
    ids = None
    corrected_names = None
    if isinstance(names_string, str) and names_string.strip():
        names_string = names_string.strip()
        name_list = [name.strip() for name in names_string.split('+') if name.strip()]
        if name_list:
            id_list = [str(id_map[name]) for name in name_list if name in id_map]
            matched_names = [name for name in name_list if name in id_map]
            if id_list:
                ids = ','.join(id_list)
            if matched_names:
                corrected_names = '+'.join(matched_names)
    return ids, corrected_names

@bp.route('/import', methods=['GET'])
def import_view():
    """导入交易记录页面"""
    return render_template('transaction/import.html')

# Remove the /generate_trades endpoint as it's replaced by logic within create/import/update
# @bp.route('/api/generate_trades', methods=['POST'])
# def generate_all_trades():
#     pass
"" 