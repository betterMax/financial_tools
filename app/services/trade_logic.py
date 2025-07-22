# app/services/trade_logic.py
"""
Business logic related to TradeRecord generation and synchronization.
"""
from app import db
from app.models.trade import TradeRecord
from app.models.transaction import TransactionRecord
from datetime import datetime
import traceback

def generate_trade_from_transactions(transactions):
    """从交易记录生成交易汇总记录对象 (但不写入数据库)"""
    if not transactions:
        # print("没有交易记录可用于生成汇总")
        return None

    # print(f"从{len(transactions)}条交易记录尝试生成交易汇总")

    open_trans = None
    close_trans = []

    # 找到开仓交易
    for trans in transactions:
        if trans.position_type is None:
            print(f"  警告: 交易ID={trans.id}缺少position_type")
            continue

        if trans.position_type in [0, 2]:  # 开多 or 开空
            if not open_trans:  # 只取第一个开仓交易
                open_trans = trans
        elif trans.position_type in [1, 3]: # 平多 or 平空
             close_trans.append(trans)
        else:
            print(f"  警告: 交易ID={trans.id}的仓位类型{trans.position_type}无效")

    if not open_trans:
        # print("  没有找到有效的开仓交易")
        return None

    # 确保开仓和平仓交易匹配
    valid_close_trans = []
    for trans in close_trans:
        if (open_trans.position_type == 0 and trans.position_type == 1) or \
           (open_trans.position_type == 2 and trans.position_type == 3):
            valid_close_trans.append(trans)

    close_trans = valid_close_trans

    # 计算平均售价和收益
    total_close_amount = sum(t.price * t.volume for t in close_trans if t.price is not None and t.volume is not None)
    total_close_volume = sum(t.volume for t in close_trans if t.volume is not None)
    average_sale_price = total_close_amount / total_close_volume if total_close_volume > 0 else None

    # 计算收益
    single_profit = None
    if average_sale_price is not None and open_trans.contract_multiplier is not None and open_trans.price is not None and total_close_volume is not None:
        try:
            if open_trans.position_type == 0:  # 多头
                single_profit = (average_sale_price - open_trans.price) * total_close_volume * open_trans.contract_multiplier
            else:  # 空头
                single_profit = (open_trans.price - average_sale_price) * total_close_volume * open_trans.contract_multiplier
        except TypeError as e:
            print(f"  计算收益时发生类型错误: {e}. Open price: {open_trans.price}, Avg sale price: {average_sale_price}, Vol: {total_close_volume}, Multiplier: {open_trans.contract_multiplier}")
            single_profit = None

    # 计算投资额 (开仓成本)
    investment_amount = None
    if open_trans.price is not None and open_trans.volume is not None and open_trans.contract_multiplier is not None:
        try:
            investment_amount = open_trans.price * open_trans.volume * open_trans.contract_multiplier
        except TypeError:
             print(f"  计算投资额时发生类型错误: Price: {open_trans.price}, Vol: {open_trans.volume}, Multiplier: {open_trans.contract_multiplier}")
             investment_amount = None

    # 计算投资收益率
    investment_profit_rate = single_profit / investment_amount if single_profit is not None and investment_amount and investment_amount != 0 else None

    # 计算持仓天数
    close_time = max(t.transaction_time for t in close_trans if t.transaction_time) if close_trans else None
    holding_days = (close_time - open_trans.transaction_time).days if close_time and open_trans.transaction_time else None

    # 计算年化收益率
    annual_profit_rate = investment_profit_rate * 365 / holding_days if investment_profit_rate is not None and holding_days and holding_days > 0 else None

    # 创建交易汇总记录对象
    try:
        roll_trade_main_id = getattr(open_trans, 'roll_id', None)

        trade = TradeRecord(
            roll_trade_main_id=roll_trade_main_id,
            contract_code=open_trans.contract_code,
            name=open_trans.name,
            account=open_trans.account,
            strategy_ids=open_trans.strategy_ids,
            strategy_name=open_trans.strategy_name,
            position_type=0 if open_trans.position_type == 0 else 1,
            candle_pattern_id=open_trans.candle_pattern_ids,
            candle_pattern=open_trans.candle_pattern,
            open_time=open_trans.transaction_time,
            close_time=close_time,
            position_volume=open_trans.volume,
            contract_multiplier=open_trans.contract_multiplier,
            past_position_cost=investment_amount,
            average_sale_price=average_sale_price,
            single_profit=single_profit,
            investment_profit=single_profit,
            investment_profit_rate=investment_profit_rate,
            holding_days=holding_days,
            annual_profit_rate=annual_profit_rate,
            trade_type=open_trans.trade_type,
            confidence_index=open_trans.confidence_index,
            similarity_evaluation=open_trans.similarity_evaluation,
            long_trend_ids=getattr(open_trans, 'long_trend_ids', None),
            long_trend_name=getattr(open_trans, 'long_trend_name', None),
            mid_trend_ids=getattr(open_trans, 'mid_trend_ids', None),
            mid_trend_name=getattr(open_trans, 'mid_trend_name', None)
        )
        return trade

    except Exception as e:
        print(f"  创建交易汇总记录对象时出错: {str(e)}")
        print(traceback.format_exc())
        return None

def update_trade_record(trade_id):
    """
    根据关联的 TransactionRecords 重新计算并更新 TradeRecord。
    如果计算结果有效，则更新或创建 TradeRecord。
    如果计算结果无效（例如，没有开仓交易），则删除现有的 TradeRecord。
    """
    if trade_id is None:
        print("  update_trade_record 收到 None trade_id。跳过。")
        return

    print(f"正在更新 trade_id: {trade_id} 的 TradeRecord")
    try:
        existing_trade = TradeRecord.query.get(trade_id) # 使用 get 获取主键

        transactions = TransactionRecord.query.filter_by(trade_id=trade_id)\
                                            .order_by(TransactionRecord.transaction_time)\
                                            .all()

        if not transactions:
            print(f"  未找到 trade_id {trade_id} 的交易记录。")
            if existing_trade:
                print(f"  正在删除现有的 TradeRecord {trade_id} (因无交易记录)。")
                db.session.delete(existing_trade)
            else:
                print(f"  无需删除，TradeRecord {trade_id} 不存在。")
            db.session.commit() # 提交删除或不执行任何操作
            return

        # 根据交易记录生成理论状态
        generated_trade_obj = generate_trade_from_transactions(transactions)

        if generated_trade_obj:
            print(f"  为 {trade_id} 生成了有效的交易数据。")
            if existing_trade:
                print(f"  正在更新现有的 TradeRecord {trade_id}。")
                # 从生成的对象更新现有记录的字段
                existing_trade.roll_trade_main_id = generated_trade_obj.roll_trade_main_id
                existing_trade.contract_code = generated_trade_obj.contract_code
                existing_trade.name = generated_trade_obj.name
                existing_trade.account = generated_trade_obj.account
                existing_trade.strategy_ids = generated_trade_obj.strategy_ids
                existing_trade.strategy_name = generated_trade_obj.strategy_name
                existing_trade.position_type = generated_trade_obj.position_type
                existing_trade.candle_pattern_id = generated_trade_obj.candle_pattern_id
                existing_trade.candle_pattern = generated_trade_obj.candle_pattern
                existing_trade.open_time = generated_trade_obj.open_time
                existing_trade.close_time = generated_trade_obj.close_time
                existing_trade.position_volume = generated_trade_obj.position_volume
                existing_trade.contract_multiplier = generated_trade_obj.contract_multiplier
                existing_trade.past_position_cost = generated_trade_obj.past_position_cost
                existing_trade.average_sale_price = generated_trade_obj.average_sale_price
                existing_trade.single_profit = generated_trade_obj.single_profit
                existing_trade.investment_profit = generated_trade_obj.investment_profit
                existing_trade.investment_profit_rate = generated_trade_obj.investment_profit_rate
                existing_trade.holding_days = generated_trade_obj.holding_days
                existing_trade.annual_profit_rate = generated_trade_obj.annual_profit_rate
                existing_trade.trade_type = generated_trade_obj.trade_type
                existing_trade.confidence_index = generated_trade_obj.confidence_index
                existing_trade.similarity_evaluation = generated_trade_obj.similarity_evaluation
                existing_trade.long_trend_ids = generated_trade_obj.long_trend_ids
                existing_trade.long_trend_name = generated_trade_obj.long_trend_name
                existing_trade.mid_trend_ids = generated_trade_obj.mid_trend_ids
                existing_trade.mid_trend_name = generated_trade_obj.mid_trend_name
            else:
                print(f"  正在为 trade_id {trade_id} 创建新的 TradeRecord。")
                generated_trade_obj.id = trade_id # 显式设置 ID
                db.session.add(generated_trade_obj)
        else:
            # 无法从交易记录生成有效的交易
            print(f"  为 {trade_id} 生成了无效/不完整的交易数据。")
            if existing_trade:
                print(f"  正在删除现有的 TradeRecord {trade_id} (因数据无效/不完整)。")
                db.session.delete(existing_trade)
            else:
                print(f"  无需删除，TradeRecord {trade_id} 不存在。")

        db.session.commit() # 提交更新、创建或删除
        print(f"  成功提交 TradeRecord {trade_id} 的更改。")

    except Exception as e:
        db.session.rollback()
        print(f"  处理 TradeRecord {trade_id} 时出错: {e}")
        print(traceback.format_exc())

def sync_trades_after_import(trade_ids):
    """
    为给定的 trade_id 列表同步 TradeRecords。
    为每个唯一的 trade_id 调用 update_trade_record。
    """
    if not trade_ids:
        print("未提供用于同步的 trade ID。")
        return

    valid_trade_ids = set()
    for tid in trade_ids:
        if tid is not None:
            try:
                valid_trade_ids.add(int(tid))
            except (ValueError, TypeError):
                 print(f"  跳过无效的 trade_id: {tid}")

    if not valid_trade_ids:
        print("过滤后未找到有效的 trade ID。")
        return

    print(f"正在为 {len(valid_trade_ids)} 个唯一的 trade ID 同步 TradeRecords...")
    errors = []
    success_count = 0
    for trade_id in valid_trade_ids:
        try:
            update_trade_record(trade_id)
            success_count += 1
        except Exception as e:
            error_msg = f"同步 trade_id {trade_id} 时发生严重错误: {e}"
            print(f"  {error_msg}")
            print(traceback.format_exc())
            errors.append(error_msg)

    sync_status = "同步完成。"
    if errors:
        sync_status = f"同步完成，但有 {len(errors)} 个错误。"
        print(f"同步期间的错误: {errors}")

    print(sync_status)
    # 返回同步结果
    return {'code': 1 if errors else 0, 'msg': sync_status, 'errors': errors, 'success_count': success_count} 