# 期货数据管理模块

## 1. 项目目录
```
financial_tools/
│
├── main.py                # 主程序入口
├── config_fake.yaml       # 配置文件模板
├── config.yaml            # 实际配置文件（git忽略）
├── README.md              # 项目说明文档
├── requirements.txt       # 项目依赖
│
├── app/                   # Web应用目录
│   ├── __init__.py
│   ├── routes/            # 路由定义
│   │   ├── __init__.py
│   │   ├── future_info.py # 期货基础信息相关路由
│   │   ├── transaction.py # 交易记录相关路由
│   │   ├── trade.py       # 交易汇总相关路由
│   │   └── monitor.py     # 监控记录相关路由
│   │
│   ├── models/            # 数据模型
│   │   ├── __init__.py
│   │   ├── future_info.py # 期货基础信息模型
│   │   ├── transaction.py # 交易记录模型
│   │   ├── trade.py       # 交易汇总模型
│   │   ├── monitor.py     # 监控记录模型
│   │   └── dimension.py   # 维度数据模型（策略、K线形态、趋势等）
│   │
│   ├── services/          # 业务逻辑服务
│   │   ├── __init__.py
│   │   ├── data_update.py # 数据更新服务
│   │   ├── data_scraper.py # 网页数据爬取
│   │   └── data_analysis.py # 数据分析服务
│   │
│   ├── static/            # 静态资源
│   │   ├── css/
│   │   ├── js/
│   │   └── img/
│   │
│   └── templates/         # 前端模板
│       ├── base.html      # 基础模板
│       ├── future_info/   # 期货基础信息页面
│       ├── transaction/   # 交易记录页面
│       ├── trade/         # 交易汇总页面
│       └── monitor/       # 监控记录页面
│
├── database/              # 数据库相关
│   ├── __init__.py
│   ├── db_manager.py      # 数据库管理器
│   ├── schema.py          # 数据库表结构定义
│   └── migrations/        # 数据库迁移脚本
│
├── scripts/               # 脚本工具
│   ├── data_importer.py   # 数据导入工具
│   ├── backup.py          # 数据备份脚本
│   └── data_validator.py  # 数据验证工具
│
├── data/                  # 数据文件目录
│   ├── raw/               # 原始数据
│   ├── processed/         # 处理后的数据
│   └── backup/            # 备份数据
│
├── tests/                 # 测试目录
│   ├── __init__.py
│   ├── test_models.py     # 模型测试
│   ├── test_services.py   # 服务测试
│   └── test_api.py        # API测试
│
└── utilities/             # 工具函数
    ├── __init__.py
    ├── logger.py          # 日志工具
    ├── validators.py      # 数据验证工具
    └── helpers.py         # 辅助函数
```

## 2. 核心功能

1. 数据管理：包括基础信息、监控的记录、虚拟和真实开仓平仓的记录、每一笔交易的记录（包含了关联性的开仓和平常以及可能涉及到的换月和未来可能有的加仓和减仓）。这部分是作为后期高级分析功能的数据基础
2. 数据更新：这部分涉及到从一些网络表格或者利用爬虫来按照一定结构更新指定部分的期货数据
3. 数据统计：针对现有的数据进行一些简单的分析，这部分细节待定
4. 数据查看及编辑：除了自动更新的数据以外，也需要一个网页可以进行访问，并进行数据新增和编辑

## 3. 数据表结构

### 3.1 维护期货标的及主连的基础信息

#### 3.1.1 "future_info"：维护期货标的基础信息，包含的字段有：
1. 序号：相当于是ID；表格导入
2. 合约字母：1位或者2位的英文字母，这是唯一的；表格导入
3. 名称：可能是中文（还可能包函数字），也可能是英文；表格导入
4. 市场：分为国内和国外，可以用数字对应；表格导入
5. 交易所：3-5位的英文字母；从"future_daily"用合约字母匹配
6. 合约乘数：数字；从"future_daily"用合约字母匹配
7. 做多保证金率（按金额）：数字；从"future_daily"用合约字母匹配
8. 做空保证金率（按金额）：数字；从"future_daily"用合约字母匹配
9. 开仓费用（按手）：数字；从"future_daily"用合约字母匹配
10. 平仓费用（按手）：数字；从"future_daily"用合约字母匹配
11. 平今费率（按金额）：数字；从"future_daily"用合约字母匹配
12. 平今费用（按手）：数字；从"future_daily"用合约字母匹配
13. 同花主力合约：是一个字符，是1位或者2位的英文字母加上4位数字，如PG2503或A2505，后面的数字代表了年份和月份，前面的字母则是合约字母；表格导入
14. 当前主力合约：同"同花主力合约"；表格导入
15. 同花顺顺序：数字；表格导入
16. 长期趋势：

#### 3.1.2 "transaction_records"：记录每一笔开仓平仓的具体数据，包含的字段有：
1. id：自动生成
2. 交易id：记录从属于哪个交易，对应"trade_records"里的id
3. 成交时间：年月日小时分；表格导入，目前只有年月日的数据，暂时小时分默认为14:30
4. 合约代码：格式和"同花主力合约"一致
5. 名称：和"名称"一致
6. 账户：中文，记录期货账户，默认为"华安期货"；表格导入
7. 操作策略ID：对应"strategy_info"里的序号
8. 操作策略：对应"strategy_info"里的名称
9. 多空仓位：0代表开多，1代表平多，2代表开空，3代表平空。0和2都是开仓，1和3都是平仓；
10. K线形态ID：代表了ID的列数据，对应"candle_info"
11. K线形态：类似"连续上跳+长阳突破"这样的数据；
12. 成交价格：1位小数；
13. 成交手数：实数；
14. 合约乘数：对应"future_info"的合约乘数；
15. 成交金额：等于本表内的`"成交价格*"成交手数"*"合约乘数"`
16. 手续费：
  a. 如果是开仓，则等于"future_info"的`"开仓费用（按手）"*本表内的"成交手数"`
  b. 如果是平仓，则等于"future_info"的`"平仓费用（按手）"*本表内的"成交手数"`
17. 手数变化：
  a. 如果是开仓，则等于本表内的`"成交手数"*1`
  b. 如果是平仓，则等于本表内的`"成交手数"*-1`
18. 现金流：
  a. 如果是开仓，则等于`(本表内的"成交金额"*-1)-本表内的"手续费"`
  b. 如果是平仓，则等于`(本表内的"成交金额"*1)-本表内的"手续费"`
19. 保证金：
  a. 如果是开仓，则等于本表内的`"成交金额"*"future_info"的"做多保证金率（按金额）"`
  b. 如果是平仓，则等于本表内的`"成交金额"*"future_info"的"做空保证金率（按金额）"`
20. 交易类别：0代表模拟交易，1代表真实交易
21. 交易状态：0代表进行，1代表暂停，2代表暂停进行，3代表结束
22. 最新价格：1位小数；
23. 实际收益率：百分比2位小数
  a. 如果是多仓，则等于`本表内的("最新价格"-"成交价格")/"成交价格"*1`
  b. 如果是空仓，则等于`本表内的("最新价格"-"成交价格")/"成交价格"*-1`
24. 实际收益：1位小数，等于`本表内的("最新价格"-"成交价格")*"手数变化"*"合约乘数"-2*手续费`
25. 止损价格：1位小数
26. 止损比例：1位小数
  a. 如果是多仓，则等于`本表内的("止损价格"-"成交价格")/"成交价格"*1`
  b. 如果是空仓，则等于`本表内的("止损价格"-"成交价格")/"成交价格"*-1`
27. 止损收益：1位小数，等于`本表内的("止损价格"-"成交价格")*"手数变化"*"合约乘数"-2*手续费`
28. 操作时间：默认为成交时间
29. 信心指数：0-2
30. 相似度评估：
31. 长期趋势id："trend_info"id的list
32. 长期趋势name："trend_info"id的多个name合并的字节如"长期大幅震荡上涨+短期高位中幅震荡"
33. 中期趋势id："trend_info"id的list
34. 中期趋势name："trend_info"id的多个name合并的字节如"长期大幅震荡上涨+短期高位中幅震荡"

#### 3.1.3 "trade_records"：对一组开仓平仓交易的汇总记录，从而评估一次交易的表现，包含的字段有：
1. id：如果在transaction里有指定则继续使用，没有则自动生成
2. 换月ID：可选，如果在transaction里有指定则继续使用，没有则自动生成
3. 合约代码：格式和"transaction_records"的"合约代码"一致，通过本表的id和"transaction_records"的交易id进行匹配，获得的第一条记录的"合约代码"；
4. 名称：格式和"transaction_records"的"名称"一致，通过本表的id和"transaction_records"的交易id进行匹配，获得的第一条记录的"名称"；
5. 账户：格式和"transaction_records"的"账户"一致，通过本表的id和"transaction_records"的交易id进行匹配，获得的第一条记录的"账户"；表格导入
6. 操作策略ID：格式和"transaction_records"的"操作策略ID"一致，通过本表的id和"transaction_records"的交易id进行匹配，获得的第一条记录的"操作策略ID"；
7. 操作策略：对应"strategy_info"里的名称
8. 多空仓位：0代表多头仓位，1代表空投仓位。通过本表的id和"transaction_records"的交易id进行匹配，获得的第一条记录的"多空仓位"如果是0或1则是多头，如果是2或3则是空头；
9. K线形态ID：格式和"transaction_records"的"K线形态ID"一致，通过本表的id和"transaction_records"的交易id进行匹配，获得的第一条记录的"K线形态ID"；
10. K线形态：类似"连续上跳+长阳突破"这样的数据；
11. 开仓时间：格式和"transaction_records"的"成交时间"一致，通过本表的id和"transaction_records"的交易id进行匹配，获得的第一条记录的"成交时间"；
12. 平仓时间：格式和"transaction_records"的"成交时间"一致，通过本表的id和"transaction_records"的交易id进行匹配，获得的最后一条记录的"成交时间"；
13. 持仓手数：格式和"transaction_records"的"持仓手数"一致，通过本表的id和"transaction_records"的交易id进行匹配，获得所有相关的transaction开仓记录，也就是"transaction_records"的"多空仓位"是0或者2；
14. 合约乘数：对应"future_info"的合约乘数；
15. 过往持仓成本：通过本表的id和"transaction_records"的交易id进行匹配，获得所有相关的transaction开仓记录，也就是"transaction_records"的"多空仓位"是0或者2，然后将他们的现金流绝对值进行求和。这个和/(本表内的"持仓手数"*"合约乘数")
16. 平均售价：通过本表的id和"transaction_records"的交易id进行匹配，获得所有相关的transaction平仓记录，也就是"transaction_records"的"多空仓位"是1或者3，然后将他们的现金流绝对值进行求和。这个和/(本表内的"持仓手数"*"合约乘数")
17. 单笔收益：通过本表的id和"transaction_records"的交易id进行匹配，获得所有相关的transaction记录，将他们的"现金流"进行求和
18. 投资收益：将本表内的"换月交易主id"一致的所有记录的"单笔收益"进行求和
19. 投资收益率：`本表内的"投资收益"/("持仓手数"*"合约乘数"*"过往持仓成本")`
20. 持仓天数：本表内的"平仓时间"和"开仓时间"之间的天数
21. 投资年化收益率：本表内的"投资收益率"计算而得
22. 交易类别：0代表模拟交易，1代表真实交易
23. 信心指数：0-2
24. 相似度评估：
25. 长期趋势ids：格式和"transaction_records"的"长期趋势ids"一致，通过本表的id和"transaction_records"的交易id进行匹配，获得的第一条记录的"长期趋势ids"
26. 长期趋势name："trend_info"id的多个name合并的字节如"长期大幅震荡上涨+短期高位中幅震荡"
27. 中期趋势ids：格式和"transaction_records"的"中期趋势ids"一致，通过本表的id和"transaction_records"的交易id进行匹配，获得的第一条记录的"中期趋势ids"
28. 中期趋势name："trend_info"id的多个name合并的字节如"长期大幅震荡上涨+短期高位中幅震荡"

#### 3.1.4 "monitor_records"：监控标的的信息
1. 序号：相当于是ID；表格导入
2. 合约：类似"future_info"的"同花主力合约"
3. 名称：可能是中文（还可能包函数字），也可能是英文；表格导入
4. 市场：分为国内和国外，可以用数字对应；表格导入
5. 机会：
6. 关键价格：1位小数
7. 开多价格：1位小数
8. 开空价格：1位小数
9. 状态：0代表有效，1代表失效，2代表虚拟多，3代表虚拟空，4代表真实多，5代表真实空
10. 最新价格：
11. 开多触发价格：1位小数
12. 开空触发价格：1位小数
13. 开多一手保证金：1位小数
14. 开空一手保证金：1位小数
15. K线形态ID：代表了ID的列数据，对应"candle_info"
16. K线形态：类似"连续上跳+长阳突破"这样的数据；
17. 长期趋势id："trend_info"id的list
18. 长期趋势name："trend_info"id的多个name合并的字节如"长期大幅震荡上涨+短期高位中幅震荡"
19. 中期趋势id："trend_info"id的list
20. 中期趋势name："trend_info"id的多个name合并的字节如"长期大幅震荡上涨+短期高位中幅震荡"
21. 相似度评估：
22. 可能触发价格：
23. 比例对照价格：0代表最新价格，1代表关键价格
24. 相应比例：等于(本表内的"比例对照价格"-"可能出发价格")/"可能出发价格"

#### 3.1.5 工具类表格
1. "future_daily"：这个网址http://121.37.80.177/fees.html里有一个表格，表格是每天都会更新的，里面有中国期货标的的一些基础信息。这部分只要可以每天从网页更新到数据库就可以。可以覆盖之前的数据，不需要单独保存。
  a. 在合约代码那一列标注了黄色填充色的是这个类别的主连合约
  b. 最新价格在盘中不是最新的
2. "transaction_records_copy"："transaction_records"每天备份
3. "roll_trade_records"：专门记录期货的换月交易记录
  a. id：
  b. 换月交易主id："trade_records"的换月交易主id
  c. 关联交易id："trade_records"中换月交易主id相同记录的所有id（去除掉"trade_records"的换月交易主id）
  d. 合约字母："future_info"的合约字母
  e. 关联合约："trade_records"中换月交易主id相同记录的所有合约代码
4. "strategy_info"：记录交易策略
  a. 序号：相当于是ID
  b. 名称：中文
  c. 开平仓类型：0代表开仓，1代表平仓
  d. 策略类型：0代表阻力位，1代表趋势
5. "candle_info"：记录K线形态
  a. 序号：相当于是ID
  b. 名称：中文
6. "trend_info"：走势类型的基本信息
  a. id：主键
  b. category：0代表上涨下跌类，1代表震荡类，2代表和压力位支撑位相关类
  c. name: 根据子表里id对应的name生成而得
    ⅰ. category为0：如"中期大幅震荡下跌"，子表对应的那么合并，dim_time_range+dim_amplitude+dim_speed+dim_trend_type
    ⅱ. category为1：如"长期高位中幅震荡且顶部下移"，dim_time_range+dim_position+dim_amplitude+dim_trend_type，如果有extra_info，那么就加上"且"+extra_info
    ⅲ. category为2：如"突破压力位",extra_info
  d. time_range_id：外键，关联dim_time_range
  e. amplitude_id：外键，关联dim_amplitude
  f. position_id：外键，关联dim_position
  g. dim_speed_type：外键，关联dim_speed
  h. trend_type_id：外键，关联dim_trend_type
  i. extra_info：可选字段，存例如"顶部下移""突破回踩"之类灵活描述
7. "dim_time_range"：走势类型的时间范围
  a. id: 
  b. name: 短期、中期、长期
8. "dim_amplitude"：走势类型的幅度范围
  a. id: 
  b. name: 小幅、中幅、大幅
9. "dim_position"：走势类型的位置范围
  a. id: 
  b. name: 低位、中位、高位
10. "dim_speed_type"：走势类型的位置范围
  a. id: 
  b. name: 急速、连续、震荡
11. "dim_trend_type"：走势类型的位置范围
  a. id: 
  b. name: 上涨、下跌、震荡

## 4. 前端页面
### 4.1 前端列表页面
#### 4.1.1 "future_info"对应的基础信息：
1. 功能：可以新增、编辑、删除、导出、排序
2. 列表字段：
  a. 合约字母：1位或者2位的英文字母，这是唯一的；"future_info"的"contract_letter"
  b. 名称：可能是中文（还可能包函数字），也可能是英文；"future_info"的"name"
  c. 市场：分为国内和国外，可以用数字对应；"future_info"的"market"
  d. 做多保证金率（按金额）：数字；"future_info"的"long_margin_rate"
  e. 做空保证金率（按金额）：数字；"future_info"的"short_margin_rate"
  f. 同花主力合约：是一个字符，是1位或者2位的英文字母加上4位数字，如PG2503或A2505，后面的数字代表了年份和月份，前面的字母则是合约字母；"future_info"的"th_main_contract"
  g. 当前主力合约："future_info"的"current_main_contract"
  h. 长期趋势："future_info"的"long_term_trend"
3. 筛选项：市场、名称（多选）、合约字母（多选）、长期趋势
4. 详情/编辑页面字段详情：
 a. 编号："future_info"的"id"；不可编辑
 b. 合约字母："future_info"的"contract_letter"；可以编辑，文本空格
 c. 名称："future_info"的"name"；可以编辑，文本空格
 d. 市场："future_info"的"market"；可以编辑，下拉选项（国内和国外两个选项）
 e. 交易所："future_info"的"exchange"；可以编辑，文本空格
 f. 合约乘数："future_info"的"contract_multiplier"；可以编辑，数字0位小数
 g. 做多保证金率（按金额）："future_info"的"long_margin_rate"；可以编辑，数字2位小数
 h. 做空保证金率（按金额）："future_info"的"short_margin_rate"；可以编辑，数字2位小数
 i. 开仓费用（按手）："future_info"的"open_fee"；可以编辑，数字2位小数
 j. 平仓费用（按手）："future_info"的"close_fee"；可以编辑，数字2位小数
 k. 平今费率（按金额）："future_info"的"close_today_rate"；可以编辑，数字6位小数
 l. 平今费用（按手）："future_info"的"close_today_fee"；可以编辑，数字2位小数
 m. 同花主力合约："future_info"的"th_main_contract"；可以编辑，文本空格
 n. 当前主力合约："future_info"的"current_main_contract"；可以编辑，文本空格
 o. 同花顺顺序："future_info"的"th_order"；可以编辑，数字0位小数
 p. 长期趋势："future_info"的"long_term_trend"；可以编辑，文本空格；要做数据检查，如果有“+”则把内容拆开和"trend_info"里的"name"比较要能匹配上；没有“+”则直接比较
 q. 最新每日数据：这部分只在查看里，不用改

#### 4.1.2 "transaction_records"：记录每一笔开仓平仓的具体数据，包含的字段有：
1. 功能：可以新增、编辑、删除、导出、排序
2. 字段：
  a. 交易id：记录从属于哪个交易，对应"trade_records"里的id
  b. 成交时间：年月日小时分；表格导入，目前只有年月日的数据，暂时小时分默认为14:30
  c. 合约代码：格式和"同花主力合约"一致
  d. 名称：和"名称"一致
  e. 账户：中文，记录期货账户，默认为"华安期货"；表格导入
  f. 操作策略：对应"strategy_info"里的名称
  g. 多空仓位：0代表开多，1代表平多，2代表开空，3代表平空。0和2都是开仓，1和3都是平仓；
  h. K线形态：类似"连续上跳+长阳突破"这样的数据；
  i. 成交价格：1位小数；
  j. 成交手数：实数；
  k. 成交金额：等于本表内的"成交价格"*"成交手数"*"合约乘数"
  l. 保证金：等于成交金额*利用这个“名称”和“多空仓位”的信息找到"future_info"里的"long_margin_rate"或者"short_margin_rate"
  m. 交易类别：0代表模拟交易，1代表真实交易
  n. 交易状态：0代表进行，1代表暂停，2代表暂停进行，3代表结束
  o. 最新价格：1位小数；
  p. 实际收益率：百分比2位小数
  q. 实际收益：1位小数，等于本表内的("最新价格"-"成交价格")*"手数变化"*"合约乘数"-2*手续费
  r. 止损价格：1位小数
  s. 止损比例：1位小数
  t. 止损收益：1位小数，等于本表内的("止损价格"-"成交价格")*"手数变化"*"合约乘数"-2*手续费
  u. 操作时间：默认为成交时间
  v. 信心指数：0-2
  w. 相似度评估：
  x. 长期趋势name："trend_info"id的多个name合并的字节如"长期大幅震荡上涨+短期高位中幅震荡"
  y. 中期趋势name："trend_info"id的多个name合并的字节如"长期大幅震荡上涨+短期高位中幅震荡"
3. 筛选项：成交时间范围、市场、名称（多选）、合约字母（多选）、操作策略（多选）、交易类别、交易状态（多选）
4. 列表显示字段：
  a. 合约代码："transaction_records"的"contract_code"
  b. 名称："transaction_records"的"name"
  c. 交易类别："transaction_records"的"trade_type"
  d. 操作策略："transaction_records"的"strategy_name"
  e. 多空仓位："transaction_records"的"position_type"
  f. K线形态："transaction_records"的"candle_pattern"
  g. 成交价格："transaction_records"的"price"
  h. 成交手数："transaction_records"的"volume"
  i. 保证金："transaction_records"的"margin"
  j. 最新价格："transaction_records"的"latest_price"
  k. 实际收益率："transaction_records"的"actual_profit_rate"
  l. 实际收益："transaction_records"的"actual_profit"
  m. 止损价格："transaction_records"的"stop_loss_price"
  o. 止损比例："transaction_records"的"stop_loss_rate"
  p. 止损收益："transaction_records"的"stop_loss_profit"
5. 详情/编辑字段：
  a. ID："transaction_records"的"contract_code"；不可编辑
  b. 交易id："transaction_records"的"trade_id"；可以编辑，同一个id的数据只能有两条
  b. 成交时间："transaction_records"的"transaction_time"；可以编辑，DATATIME格式
  c. 合约代码："transaction_records"的"contract_code"；可以编辑，文本空格
  d. 名称："transaction_records"的"name"；不可编辑，根据“合约代码”生成
  e. 账户："transaction_records"的"account"；可以编辑，默认为"华安期货"
  f. 操作策略："transaction_records"的"strategy_name"；可以编辑，多选项，以"strategy_info"表里的数据作为下拉选项
  g. 多空仓位：根据"transaction_records"的"position_type"进行匹配，0代表开多，1代表平多，2代表开空，3代表平空；可以编辑，4个文字就是下拉选项，注意选项里不是0,1的数字
  h. K线形态："transaction_records"的"candle_pattern"；可以编辑，多选项，以"candle_info"表里的数据作为下拉选项
  i. 成交价格："transaction_records"的"price"；可以编辑，2位小数
  j. 成交手数："transaction_records"的"volume"；可以编辑，0位小数
  k. 成交金额："transaction_records"的"amount"；不可编辑，1位小数
  l. 保证金："transaction_records"的"margin"；不可编辑，1位小数
  m. 交易类别：根据"transaction_records"的"trade_type"进行匹配，0代表模拟交易，1代表真实交易
  n. 交易状态：根据"transaction_records"的"trade_status"进行匹配，0代表进行，1代表暂停，2代表暂停进行，3代表结束
  o. 最新价格："transaction_records"的"latest_price"；可以编辑，3位小数
  p. 实际收益率："transaction_records"的"actual_profit_rate"；不可编辑，百分比2位小数
  q. 实际收益："transaction_records"的"actual_profit"；不可编辑，1位小数
  r. 止损价格："transaction_records"的"stop_loss_price"；可以编辑，3位小数
  s. 止损比例："transaction_records"的"stop_loss_rate"；不可编辑，不可编辑，百分比2位小数
  t. 止损收益："transaction_records"的"stop_loss_profit"；不可编辑，1位小数
  u. 操作时间："transaction_records"的"operation_time"；可以编辑
  v. 信心指数："transaction_records"的"confidence_index"；可以编辑，0位数字
  w. 相似度评估："transaction_records"的"similarity_evaluation"；可以编辑
  x. 长期趋势name："transaction_records"的"long_trend_name"；可以编辑
  y. 中期趋势name："transaction_records"的"short_trend_name"；可以编辑

