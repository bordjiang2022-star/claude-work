# USDJPY 自动交易系统 EA 设计方案

**项目名称**：USDJPY Fast Scalping Expert Advisor
**目标平台**：Rakuten MT4（乐天证券）
**编程语言**：MQL4
**文档版本**：v1.0
**创建日期**：2025-11-21

---

## 文档目录

1. [项目概述](#1-项目概述)
2. [EA 整体架构设计](#2-ea-整体架构设计)
3. [策略参数定义方式](#3-策略参数定义方式)
4. [时间窗口内价格变动检测算法](#4-时间窗口内价格变动检测算法)
5. [MQL4 API 使用方案](#5-mql4-api-使用方案)
6. [关键技术要点](#6-关键技术要点)
7. [开发和测试流程](#7-开发和测试流程)
8. [潜在风险提示](#8-潜在风险提示)
9. [附录：技术参考](#9-附录技术参考)

---

## 1. 项目概述

### 1.1 项目目标

开发一个针对 USDJPY 货币对的高频自动交易系统，能够在极短时间窗口内（1秒级别）检测价格异常波动并自动执行交易。

### 1.2 核心需求

- **自动化交易**：基于价格变动阈值自动开仓
- **参数可配置**：通过 MT4 界面灵活调整策略参数
- **风险可控**：多层次风控机制，包括止损、日内限制等
- **高性能**：能够处理高频 Tick 数据
- **稳定可靠**：适用于 Demo 和真实账户

### 1.3 初始策略说明

**触发条件**：
- 时间窗口：1 秒
- 价格阈值：0.1 日元（约 10 pips）

**交易规则**：
- 当价格在 1 秒内上涨 ≥ 0.1 日元 → 买入（做多）
- 当价格在 1 秒内下跌 ≥ 0.1 日元 → 卖出（做空）

---

## 2. EA 整体架构设计

### 2.1 模块化分层架构

采用分层设计，每层职责明确，便于维护和扩展。

```
┌─────────────────────────────────────────────────────────┐
│                    配置层 (Configuration)                 │
│  • Input 参数定义                                         │
│  • 全局常量                                               │
│  • 魔术编号和EA标识                                       │
└─────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────┐
│                    数据层 (Data Layer)                    │
│  • 价格历史缓冲区（时间 + 价格）                          │
│  • 交易统计数据（盈亏、订单数）                           │
│  • 日内累计数据                                           │
└─────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────┐
│                   策略层 (Strategy Layer)                 │
│  • 价格变动检测器 (PriceChangeDetector)                  │
│  • 信号生成器 (SignalGenerator)                          │
│  • 趋势确认模块                                           │
└─────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────┐
│              风控层 (Risk Management Layer)               │
│  • 持仓管理 (Position Manager)                           │
│  • 手数计算器 (Lot Calculator)                           │
│  • 日内限制检查器 (Daily Limit Checker)                  │
│  • 止损止盈管理                                           │
└─────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────┐
│                 执行层 (Execution Layer)                  │
│  • 订单管理 (Order Manager)                              │
│  • 交易执行器 (Trade Executor)                           │
│  • 错误处理和重试机制                                     │
└─────────────────────────────────────────────────────────┘
```

### 2.2 核心模块说明

#### A. 配置层 (Configuration Layer)
**职责**：
- 定义所有可调参数（input 变量）
- 设置全局常量（如点值转换系数）
- 初始化魔术编号用于识别 EA 订单

**主要变量**：
- 策略参数（时间窗口、阈值）
- 交易参数（手数、滑点）
- 风控参数（止损、止盈、日限）

#### B. 数据层 (Data Layer)
**职责**：
- 维护价格历史记录
- 存储交易统计信息
- 管理时间序列数据

**数据结构**：
```cpp
// 价格历史数组
double priceHistory[];      // 存储价格
datetime timeHistory[];     // 存储时间戳
int historyIndex = 0;       // 当前索引

// 交易统计
double dailyProfit = 0;     // 当日盈亏
int dailyTradeCount = 0;    // 当日交易次数
int currentOpenOrders = 0;  // 当前持仓数
```

#### C. 策略层 (Strategy Layer)
**职责**：
- 检测价格变动
- 生成交易信号（买入/卖出/无信号）
- 过滤假信号

**核心函数**：
```cpp
// 检测价格变动
double DetectPriceChange()

// 生成交易信号
int GenerateSignal()  // 返回: 1=买入, -1=卖出, 0=无信号
```

#### D. 风控层 (Risk Management Layer)
**职责**：
- 计算合理的交易手数
- 检查日内限制（最大亏损、最大交易次数）
- 验证持仓是否超限
- 计算止损止盈价格

**核心函数**：
```cpp
// 检查是否允许交易
bool CanTrade()

// 计算手数
double CalculateLotSize()

// 计算止损价
double CalculateStopLoss(int orderType, double openPrice)

// 计算止盈价
double CalculateTakeProfit(int orderType, double openPrice)
```

#### E. 执行层 (Execution Layer)
**职责**：
- 执行开仓操作
- 管理现有订单
- 处理错误和异常
- 记录交易日志

**核心函数**：
```cpp
// 开仓
int OpenOrder(int orderType, double lotSize)

// 平仓
bool CloseOrder(int ticket)

// 检查现有持仓
void CheckOpenPositions()
```

### 2.3 架构优势

1. **模块化**：每个功能独立，便于单元测试
2. **可维护性**：代码结构清晰，易于定位问题
3. **可扩展性**：添加新策略或风控规则无需修改核心逻辑
4. **可读性**：符合 MQL4 最佳实践，便于团队协作

---

## 3. 策略参数定义方式

### 3.1 推荐方案：Input 参数

使用 MQL4 的 `input` 关键字定义参数，可以在 MT4 界面直接调整，无需重新编译。

### 3.2 参数分类和定义

#### A. 核心策略参数

```cpp
//+------------------------------------------------------------------+
//| 核心策略参数                                                        |
//+------------------------------------------------------------------+
input int    TimeWindowSeconds = 1;        // 时间窗口（秒）
input double ThresholdPips = 10.0;         // 触发阈值（pips）
input bool   EnableBuySignal = true;       // 启用买入信号
input bool   EnableSellSignal = true;      // 启用卖出信号
input double MinPriceChange = 5.0;         // 最小价格变动（pips，过滤噪音）
```

**说明**：
- `TimeWindowSeconds`：检测价格变动的时间窗口，默认 1 秒
- `ThresholdPips`：触发交易的价格变动阈值
- `EnableBuySignal/EnableSellSignal`：可单独禁用买入或卖出
- `MinPriceChange`：额外的过滤条件，防止微小波动触发

#### B. 交易执行参数

```cpp
//+------------------------------------------------------------------+
//| 交易执行参数                                                        |
//+------------------------------------------------------------------+
input double LotSize = 0.01;               // 交易手数
input int    Slippage = 3;                 // 最大滑点（点数）
input int    MagicNumber = 20251121;       // 魔术编号
input string OrderComment = "USDJPY_Fast"; // 订单备注
```

**说明**：
- `LotSize`：固定手数，初期建议 0.01
- `Slippage`：允许的最大滑点，3-5 点较合理
- `MagicNumber`：用于识别 EA 订单，避免与其他 EA 冲突

#### C. 风险控制参数

```cpp
//+------------------------------------------------------------------+
//| 风险控制参数                                                        |
//+------------------------------------------------------------------+
input double StopLossPips = 20.0;          // 止损（pips，0=不设置）
input double TakeProfitPips = 30.0;        // 止盈（pips，0=不设置）
input double MaxDailyLoss = 100.0;         // 单日最大亏损（账户货币，0=不限制）
input int    MaxDailyTrades = 10;          // 单日最大交易次数（0=不限制）
input int    MaxOpenOrders = 1;            // 最大同时持仓数
input double MaxSpreadPips = 2.0;          // 最大允许点差（pips）
```

**说明**：
- `StopLossPips/TakeProfitPips`：每笔订单的止损止盈
- `MaxDailyLoss`：达到此亏损后当日停止交易
- `MaxDailyTrades`：防止过度交易
- `MaxOpenOrders`：控制同时持仓数量
- `MaxSpreadPips`：点差过大时不交易（避免成本过高）

#### D. 时间过滤参数

```cpp
//+------------------------------------------------------------------+
//| 时间过滤参数                                                        |
//+------------------------------------------------------------------+
input int    TradingStartHour = 8;         // 允许交易开始时间（小时）
input int    TradingEndHour = 22;          // 允许交易结束时间（小时）
input bool   EnableMondayTrading = false;  // 周一是否交易
input bool   EnableFridayTrading = false;  // 周五是否交易
input bool   AvoidNewsTime = true;         // 避开新闻时间（需实现新闻日历）
```

**说明**：
- 可以限制交易时段，避开流动性低的时段
- 周一开盘和周五收盘容易出现异常波动，可选择关闭
- 重大新闻发布时波动剧烈，建议暂停交易

#### E. 调试和日志参数

```cpp
//+------------------------------------------------------------------+
//| 调试和日志参数                                                      |
//+------------------------------------------------------------------+
input bool   EnableDebugMode = false;      // 启用调试模式
input bool   PrintSignals = true;          // 打印交易信号
input bool   PrintPriceChanges = false;    // 打印价格变动
input int    LogLevel = 1;                 // 日志级别（0=关闭, 1=正常, 2=详细）
```

**说明**：
- 调试模式下可输出更多信息
- 回测时可关闭日志提高性能

### 3.3 参数组织建议

在 EA 代码中，使用注释分隔不同类别的参数，提高可读性：

```cpp
//+------------------------------------------------------------------+
//| Expert Advisor 输入参数                                            |
//+------------------------------------------------------------------+

//====== 核心策略参数 ======
input int    TimeWindowSeconds = 1;
input double ThresholdPips = 10.0;
// ...

//====== 交易执行参数 ======
input double LotSize = 0.01;
// ...

//====== 风险控制参数 ======
input double StopLossPips = 20.0;
// ...
```

### 3.4 可选：使用 .set 文件

对于不同的市场条件，可以准备多套参数配置：

- `USDJPY_Fast_Asian.set`：亚洲时段参数
- `USDJPY_Fast_London.set`：伦敦时段参数
- `USDJPY_Fast_NewYork.set`：纽约时段参数
- `USDJPY_Fast_Conservative.set`：保守策略参数
- `USDJPY_Fast_Aggressive.set`：激进策略参数

用户可以在 MT4 策略测试器或加载 EA 时选择不同的 .set 文件。

---

## 4. 时间窗口内价格变动检测算法

### 4.1 核心挑战

MQL4 的 `OnTick()` 是事件驱动，只在新报价到来时触发。要检测"N 秒内的价格变动"，需要：

1. **存储历史价格**：记录每个 Tick 的价格和时间
2. **维护时间窗口**：动态删除过期数据
3. **计算价格变化**：统计窗口内的最大最小值

### 4.2 推荐算法：滑动时间窗口

#### 算法概述

使用两个并行数组存储价格和时间戳：
```cpp
double priceHistory[];    // 价格序列
datetime timeHistory[];   // 时间戳序列
```

每次 Tick 到来时：
1. 添加新数据到数组
2. 删除超过时间窗口的旧数据
3. 计算窗口内价格变动
4. 判断是否达到阈值

#### 详细步骤

**步骤 1：初始化数组**

```cpp
// 在 OnInit() 中初始化
int maxHistorySize = 200;  // 最多存储 200 个价格点
ArrayResize(priceHistory, maxHistorySize);
ArrayResize(timeHistory, maxHistorySize);
```

**步骤 2：每次 Tick 到来时添加数据**

```cpp
void OnTick()
{
    // 获取当前价格（使用 Bid 或中间价）
    double currentPrice = (Bid + Ask) / 2.0;
    datetime currentTime = TimeCurrent();

    // 添加到数组
    AddPriceToHistory(currentPrice, currentTime);

    // 清理过期数据
    CleanOldData(TimeWindowSeconds);

    // 计算价格变动
    double priceChangePips = CalculatePriceChange();

    // 生成交易信号
    int signal = GenerateSignal(priceChangePips);

    // 执行交易
    if(signal != 0)
        ExecuteTrade(signal);
}
```

**步骤 3：添加价格到历史记录**

```cpp
void AddPriceToHistory(double price, datetime time)
{
    int size = ArraySize(priceHistory);

    // 检查是否需要扩展数组
    if(historyCount >= size)
    {
        // 数组已满，移除最旧的数据
        ArrayShift(priceHistory);
        ArrayShift(timeHistory);
        historyCount--;
    }

    // 添加新数据
    priceHistory[historyCount] = price;
    timeHistory[historyCount] = time;
    historyCount++;
}

// 辅助函数：移除数组第一个元素
void ArrayShift(double &arr[])
{
    int size = ArraySize(arr);
    for(int i = 0; i < size - 1; i++)
        arr[i] = arr[i + 1];
}
```

**步骤 4：清理过期数据**

```cpp
void CleanOldData(int windowSeconds)
{
    datetime cutoffTime = TimeCurrent() - windowSeconds;

    int deleteCount = 0;

    // 计算需要删除多少个旧数据
    for(int i = 0; i < historyCount; i++)
    {
        if(timeHistory[i] < cutoffTime)
            deleteCount++;
        else
            break;  // 时间是递增的，后面的都不需要删除
    }

    // 删除旧数据
    if(deleteCount > 0)
    {
        for(int i = 0; i < historyCount - deleteCount; i++)
        {
            priceHistory[i] = priceHistory[i + deleteCount];
            timeHistory[i] = timeHistory[i + deleteCount];
        }
        historyCount -= deleteCount;
    }
}
```

**步骤 5：计算价格变动**

```cpp
double CalculatePriceChange()
{
    if(historyCount < 2)
        return 0;  // 数据不足

    // 找到窗口内的最大值和最小值
    double maxPrice = priceHistory[0];
    double minPrice = priceHistory[0];

    for(int i = 1; i < historyCount; i++)
    {
        if(priceHistory[i] > maxPrice)
            maxPrice = priceHistory[i];
        if(priceHistory[i] < minPrice)
            minPrice = priceHistory[i];
    }

    // 计算变动幅度（转换为 pips）
    double changeInPrice = maxPrice - minPrice;
    double changeInPips = changeInPrice / Point / 10;  // USDJPY: 1 pip = 0.01

    return changeInPips;
}
```

**步骤 6：生成交易信号**

```cpp
int GenerateSignal(double priceChangePips)
{
    // 检查是否达到阈值
    if(priceChangePips < ThresholdPips)
        return 0;  // 无信号

    // 判断当前价格位置
    double currentPrice = (Bid + Ask) / 2.0;
    double avgPrice = CalculateAveragePrice();

    // 如果当前价格接近窗口内的最高点 → 上涨趋势 → 买入
    if(currentPrice > avgPrice && EnableBuySignal)
        return 1;  // 买入信号

    // 如果当前价格接近窗口内的最低点 → 下跌趋势 → 卖出
    if(currentPrice < avgPrice && EnableSellSignal)
        return -1;  // 卖出信号

    return 0;  // 无明确信号
}

double CalculateAveragePrice()
{
    if(historyCount == 0)
        return 0;

    double sum = 0;
    for(int i = 0; i < historyCount; i++)
        sum += priceHistory[i];

    return sum / historyCount;
}
```

### 4.3 性能优化技巧

#### A. 限制数组大小

```cpp
// 最多保存 100-200 个价格点
// 对于 1 秒窗口，假设每秒 10 个 Tick，最多 10 个元素
// 保留 200 个元素足够应对各种情况
int maxHistorySize = 200;
```

#### B. 使用 OnTimer() 辅助清理

```cpp
// 在 OnInit() 中设置定时器
void OnInit()
{
    EventSetTimer(1);  // 每秒触发一次
}

// 定时清理过期数据
void OnTimer()
{
    CleanOldData(TimeWindowSeconds);
    UpdateDailyStatistics();  // 更新日内统计
}
```

#### C. 避免重复计算

```cpp
// 缓存计算结果
double lastPriceChange = 0;
datetime lastCalculationTime = 0;

double CalculatePriceChange()
{
    datetime now = TimeCurrent();

    // 如果在同一秒内已经计算过，直接返回缓存结果
    if(now == lastCalculationTime)
        return lastPriceChange;

    // 执行计算
    // ...

    lastCalculationTime = now;
    lastPriceChange = result;
    return result;
}
```

### 4.4 算法示意图

```
时间轴 ──────────────────────────────────────────>
         [1秒时间窗口]
         ├─────────────┤
价格:    151.00  151.05  151.10  151.15  151.20
时间:    t-4     t-3     t-2     t-1     t0(现在)

步骤:
1. 存储: [(151.00, t-4), (151.05, t-3), ..., (151.20, t0)]
2. 删除 t-4 之前的数据（超过1秒窗口）
3. 计算: Max = 151.20, Min = 151.00
4. 变动: (151.20 - 151.00) / 0.001 / 10 = 20 pips
5. 判断: 20 pips >= 10 pips（阈值）→ 触发信号
6. 方向: 当前价格(151.20) > 平均价格 → 买入信号
```

---

## 5. MQL4 API 使用方案

### 5.1 核心事件函数

#### OnInit() - 初始化函数

**调用时机**：EA 加载到图表时

**任务清单**：
```cpp
int OnInit()
{
    // 1. 验证参数合法性
    if(TimeWindowSeconds <= 0)
    {
        Print("错误：时间窗口必须大于 0");
        return INIT_PARAMETERS_INCORRECT;
    }

    // 2. 初始化数组
    ArrayResize(priceHistory, 200);
    ArrayResize(timeHistory, 200);

    // 3. 设置定时器
    EventSetTimer(1);  // 每秒触发

    // 4. 初始化全局变量
    historyCount = 0;
    dailyProfit = 0;
    dailyTradeCount = 0;

    // 5. 打印启动信息
    Print("========================================");
    Print("USDJPY Fast Scalping EA 已启动");
    Print("时间窗口: ", TimeWindowSeconds, " 秒");
    Print("触发阈值: ", ThresholdPips, " pips");
    Print("========================================");

    return INIT_SUCCEEDED;
}
```

#### OnTick() - 报价更新函数

**调用时机**：每次收到新报价时（高频）

**任务清单**：
```cpp
void OnTick()
{
    // 1. 检查是否在允许交易的时间段
    if(!IsWithinTradingHours())
        return;

    // 2. 更新价格历史
    double currentPrice = (Bid + Ask) / 2.0;
    AddPriceToHistory(currentPrice, TimeCurrent());

    // 3. 清理过期数据
    CleanOldData(TimeWindowSeconds);

    // 4. 计算价格变动
    double priceChangePips = CalculatePriceChange();

    // 5. 检查风控条件
    if(!CanTrade())
        return;

    // 6. 生成交易信号
    int signal = GenerateSignal(priceChangePips);

    // 7. 执行交易
    if(signal == 1)  // 买入信号
        ExecuteBuy();
    else if(signal == -1)  // 卖出信号
        ExecuteSell();

    // 8. 管理现有持仓（可选：移动止损等）
    ManageOpenPositions();
}
```

#### OnTimer() - 定时器函数

**调用时机**：每隔指定时间触发（例如每秒）

**任务清单**：
```cpp
void OnTimer()
{
    // 1. 清理过期价格数据
    CleanOldData(TimeWindowSeconds);

    // 2. 更新每日统计
    UpdateDailyStatistics();

    // 3. 检查是否需要重置日内计数器（新的一天）
    CheckNewDay();

    // 4. 打印状态信息（可选）
    if(EnableDebugMode && TimeCurrent() % 10 == 0)  // 每10秒打印一次
        PrintStatus();
}
```

#### OnDeinit() - 卸载函数

**调用时机**：EA 从图表移除或关闭时

**任务清单**：
```cpp
void OnDeinit(const int reason)
{
    // 1. 关闭定时器
    EventKillTimer();

    // 2. 打印统计信息
    Print("========================================");
    Print("USDJPY Fast Scalping EA 已停止");
    Print("卸载原因代码: ", reason);
    Print("总交易次数: ", dailyTradeCount);
    Print("总盈亏: ", dailyProfit);
    Print("========================================");

    // 3. 清理资源（数组会自动释放）
}
```

### 5.2 价格和市场信息 API

```cpp
// 当前价格
double currentBid = Bid;           // 卖出价（做多时使用）
double currentAsk = Ask;           // 买入价（做空时使用）

// 品种信息
string symbol = Symbol();          // 当前品种（USDJPY）
double point = Point;              // 最小价格变动（0.001）
int digits = Digits;               // 小数位数（3）

// 点差
double spread = MarketInfo(Symbol(), MODE_SPREAD);  // 点差（点）
double spreadPips = spread / 10.0;                  // 转换为 pips

// 最小交易手数
double minLot = MarketInfo(Symbol(), MODE_MINLOT);  // 例如 0.01
double maxLot = MarketInfo(Symbol(), MODE_MAXLOT);  // 例如 100

// 止损水平限制
double stopLevel = MarketInfo(Symbol(), MODE_STOPLEVEL);  // 最小止损距离（点）
```

### 5.3 订单操作 API

#### 开仓 - OrderSend()

```cpp
int OpenBuyOrder()
{
    double price = Ask;  // 买入价
    double sl = CalculateStopLoss(OP_BUY, price);
    double tp = CalculateTakeProfit(OP_BUY, price);

    int ticket = OrderSend(
        Symbol(),           // 品种
        OP_BUY,             // 操作类型：买入
        LotSize,            // 手数
        price,              // 开仓价格
        Slippage,           // 滑点
        sl,                 // 止损价
        tp,                 // 止盈价
        OrderComment,       // 订单备注
        MagicNumber,        // 魔术编号
        0,                  // 订单过期时间（0=不过期）
        clrGreen            // 图表上的颜色
    );

    if(ticket > 0)
    {
        Print("买入订单成功，Ticket: ", ticket);
        dailyTradeCount++;
    }
    else
    {
        Print("买入订单失败，错误代码: ", GetLastError());
    }

    return ticket;
}

int OpenSellOrder()
{
    double price = Bid;  // 卖出价
    double sl = CalculateStopLoss(OP_SELL, price);
    double tp = CalculateTakeProfit(OP_SELL, price);

    int ticket = OrderSend(
        Symbol(),
        OP_SELL,            // 操作类型：卖出
        LotSize,
        price,
        Slippage,
        sl,
        tp,
        OrderComment,
        MagicNumber,
        0,
        clrRed
    );

    if(ticket > 0)
    {
        Print("卖出订单成功，Ticket: ", ticket);
        dailyTradeCount++;
    }
    else
    {
        Print("卖出订单失败，错误代码: ", GetLastError());
    }

    return ticket;
}
```

#### 平仓 - OrderClose()

```cpp
bool CloseOrder(int ticket)
{
    if(!OrderSelect(ticket, SELECT_BY_TICKET))
    {
        Print("选择订单失败: ", ticket);
        return false;
    }

    double closePrice;
    if(OrderType() == OP_BUY)
        closePrice = Bid;
    else
        closePrice = Ask;

    bool result = OrderClose(
        ticket,
        OrderLots(),        // 手数
        closePrice,
        Slippage,
        clrWhite
    );

    if(result)
        Print("订单 ", ticket, " 平仓成功");
    else
        Print("订单 ", ticket, " 平仓失败，错误: ", GetLastError());

    return result;
}
```

#### 修改止损止盈 - OrderModify()

```cpp
bool ModifyOrder(int ticket, double newSL, double newTP)
{
    if(!OrderSelect(ticket, SELECT_BY_TICKET))
        return false;

    bool result = OrderModify(
        ticket,
        OrderOpenPrice(),   // 开仓价（不修改）
        newSL,              // 新止损
        newTP,              // 新止盈
        0,                  // 过期时间
        clrBlue
    );

    return result;
}
```

#### 遍历现有订单

```cpp
int CountOpenOrders()
{
    int count = 0;

    for(int i = 0; i < OrdersTotal(); i++)
    {
        if(OrderSelect(i, SELECT_BY_POS, MODE_TRADES))
        {
            if(OrderSymbol() == Symbol() && OrderMagicNumber() == MagicNumber)
                count++;
        }
    }

    return count;
}

void ManageOpenPositions()
{
    for(int i = OrdersTotal() - 1; i >= 0; i--)
    {
        if(OrderSelect(i, SELECT_BY_POS, MODE_TRADES))
        {
            if(OrderSymbol() == Symbol() && OrderMagicNumber() == MagicNumber)
            {
                // 这里可以实现移动止损、部分平仓等逻辑
                // 例如：实现移动止损
                if(OrderType() == OP_BUY && Bid - OrderOpenPrice() > 20 * Point * 10)
                {
                    double newSL = Bid - 10 * Point * 10;  // 10 pips 移动止损
                    if(newSL > OrderStopLoss())
                        ModifyOrder(OrderTicket(), newSL, OrderTakeProfit());
                }
            }
        }
    }
}
```

### 5.4 时间和日期 API

```cpp
// 获取时间
datetime serverTime = TimeCurrent();    // 服务器时间
datetime localTime = TimeLocal();       // 本地时间

// 时间组成部分
int hour = TimeHour(serverTime);        // 小时 (0-23)
int minute = TimeMinute(serverTime);    // 分钟 (0-59)
int dayOfWeek = TimeDayOfWeek(serverTime);  // 星期几 (0=周日)

// 时间过滤示例
bool IsWithinTradingHours()
{
    int currentHour = TimeHour(TimeCurrent());

    // 检查时间段
    if(currentHour < TradingStartHour || currentHour >= TradingEndHour)
        return false;

    // 检查星期几
    int dow = TimeDayOfWeek(TimeCurrent());
    if(dow == 1 && !EnableMondayTrading)  // 周一
        return false;
    if(dow == 5 && !EnableFridayTrading)  // 周五
        return false;

    return true;
}
```

### 5.5 账户信息 API

```cpp
// 账户余额和净值
double balance = AccountBalance();      // 账户余额
double equity = AccountEquity();        // 账户净值
double freeMargin = AccountFreeMargin(); // 可用保证金

// 当前浮动盈亏
double floatingProfit = AccountProfit();

// 风险控制示例
bool CanTrade()
{
    // 1. 检查持仓数量
    if(CountOpenOrders() >= MaxOpenOrders)
    {
        if(EnableDebugMode)
            Print("已达到最大持仓数: ", MaxOpenOrders);
        return false;
    }

    // 2. 检查日内交易次数
    if(MaxDailyTrades > 0 && dailyTradeCount >= MaxDailyTrades)
    {
        if(EnableDebugMode)
            Print("已达到单日最大交易次数: ", MaxDailyTrades);
        return false;
    }

    // 3. 检查日内亏损
    if(MaxDailyLoss > 0 && dailyProfit <= -MaxDailyLoss)
    {
        if(EnableDebugMode)
            Print("已达到单日最大亏损: ", MaxDailyLoss);
        return false;
    }

    // 4. 检查点差
    double currentSpread = MarketInfo(Symbol(), MODE_SPREAD) / 10.0;
    if(currentSpread > MaxSpreadPips)
    {
        if(EnableDebugMode)
            Print("点差过大: ", currentSpread, " pips");
        return false;
    }

    // 5. 检查可用保证金
    double requiredMargin = MarketInfo(Symbol(), MODE_MARGINREQUIRED) * LotSize;
    if(freeMargin < requiredMargin * 2)  // 保留2倍保证金
    {
        if(EnableDebugMode)
            Print("可用保证金不足");
        return false;
    }

    return true;
}
```

### 5.6 数学和数组 API

```cpp
// 数组操作
int maxIndex = ArrayMaximum(priceHistory, 0, historyCount);  // 最大值索引
int minIndex = ArrayMinimum(priceHistory, 0, historyCount);  // 最小值索引
ArrayResize(priceHistory, newSize);                          // 调整大小

// 数学函数
double absValue = MathAbs(-10.5);       // 绝对值: 10.5
double maxValue = MathMax(10, 20);      // 最大值: 20
double minValue = MathMin(10, 20);      // 最小值: 10
double roundValue = MathRound(10.7);    // 四舍五入: 11
```

---

## 6. 关键技术要点

### 6.1 USDJPY 点值计算

#### 点值定义

对于 USDJPY（报价示例：151.234）：
- **1 pip = 0.01 日元**（第二位小数）
- 不是 0.001（这是 1 point）

#### 计算公式

```cpp
// MT4 中的 Point 是最小价格单位
// 对于 USDJPY: Point = 0.001, Digits = 3

// 将价格变动转换为 pips
double priceChange = 0.10;  // 0.10 日元
double pips = priceChange / Point / 10;  // 0.10 / 0.001 / 10 = 10 pips

// 将 pips 转换为价格
double pipsToPrice = 10 * Point * 10;  // 10 * 0.001 * 10 = 0.10 日元
```

#### 示例计算

```
价格变动示例：
从 151.000 涨到 151.100
变动: 0.100 日元
Pips: 0.100 / 0.001 / 10 = 10 pips ✓

从 151.234 跌到 151.184
变动: -0.050 日元
Pips: 0.050 / 0.001 / 10 = 5 pips ✓
```

#### 代码实现

```cpp
// 计算止损价格
double CalculateStopLoss(int orderType, double openPrice)
{
    if(StopLossPips == 0)
        return 0;  // 不设置止损

    double slDistance = StopLossPips * Point * 10;

    if(orderType == OP_BUY)
        return openPrice - slDistance;  // 买入：止损在下方
    else
        return openPrice + slDistance;  // 卖出：止损在上方
}

// 计算止盈价格
double CalculateTakeProfit(int orderType, double openPrice)
{
    if(TakeProfitPips == 0)
        return 0;  // 不设置止盈

    double tpDistance = TakeProfitPips * Point * 10;

    if(orderType == OP_BUY)
        return openPrice + tpDistance;  // 买入：止盈在上方
    else
        return openPrice - tpDistance;  // 卖出：止盈在下方
}
```

### 6.2 风控实现细节

#### A. 仓位管理

**固定手数模式**（推荐初期使用）：
```cpp
double lotSize = LotSize;  // 直接使用输入参数
```

**风险百分比模式**（进阶）：
```cpp
double CalculateLotSizeByRisk(double riskPercent, double stopLossPips)
{
    // 计算可承受的亏损金额
    double accountEquity = AccountEquity();
    double riskAmount = accountEquity * riskPercent / 100.0;

    // USDJPY 的点值计算
    double tickValue = MarketInfo(Symbol(), MODE_TICKVALUE);  // 每点价值
    double pipValue = tickValue * 10;  // 每 pip 价值

    // 计算手数
    double lotSize = riskAmount / (stopLossPips * pipValue);

    // 规范化手数（必须是 0.01 的倍数）
    double minLot = MarketInfo(Symbol(), MODE_MINLOT);
    double maxLot = MarketInfo(Symbol(), MODE_MAXLOT);
    double lotStep = MarketInfo(Symbol(), MODE_LOTSTEP);

    lotSize = MathFloor(lotSize / lotStep) * lotStep;

    // 限制在允许范围内
    if(lotSize < minLot) lotSize = minLot;
    if(lotSize > maxLot) lotSize = maxLot;

    return lotSize;
}
```

#### B. 日内限制

```cpp
// 全局变量
datetime lastTradeDate = 0;
double dailyProfit = 0;
int dailyTradeCount = 0;

void UpdateDailyStatistics()
{
    datetime today = TimeCurrent() - (TimeCurrent() % 86400);  // 当天零点

    // 检查是否新的一天
    if(today != lastTradeDate)
    {
        // 重置计数器
        dailyProfit = 0;
        dailyTradeCount = 0;
        lastTradeDate = today;

        Print("新的一天，重置日内统计");
    }

    // 计算当日盈亏
    double todayProfit = CalculateTodayProfit();
    dailyProfit = todayProfit;
}

double CalculateTodayProfit()
{
    double profit = 0;
    datetime todayStart = TimeCurrent() - (TimeCurrent() % 86400);

    // 统计已平仓订单
    for(int i = 0; i < OrdersHistoryTotal(); i++)
    {
        if(OrderSelect(i, SELECT_BY_POS, MODE_HISTORY))
        {
            if(OrderSymbol() == Symbol() &&
               OrderMagicNumber() == MagicNumber &&
               OrderCloseTime() >= todayStart)
            {
                profit += OrderProfit() + OrderSwap() + OrderCommission();
            }
        }
    }

    // 加上当前持仓的浮动盈亏
    for(int i = 0; i < OrdersTotal(); i++)
    {
        if(OrderSelect(i, SELECT_BY_POS, MODE_TRADES))
        {
            if(OrderSymbol() == Symbol() && OrderMagicNumber() == MagicNumber)
            {
                profit += OrderProfit() + OrderSwap() + OrderCommission();
            }
        }
    }

    return profit;
}
```

#### C. 时间过滤增强

```cpp
// 检查是否在新闻时间（示例：固定避开的时段）
bool IsNewsTime()
{
    int hour = TimeHour(TimeCurrent());
    int minute = TimeMinute(TimeCurrent());

    // 示例：避开美国非农就业数据发布时间（通常在周五 21:30 北京时间）
    int dow = TimeDayOfWeek(TimeCurrent());
    if(dow == 5 && hour == 21 && minute >= 25 && minute <= 35)
        return true;

    // 可以添加更多新闻时间

    return false;
}
```

### 6.3 滑点和延迟处理

#### 检查点差

```cpp
bool IsSpreadAcceptable()
{
    double currentSpread = (Ask - Bid) / Point / 10;  // 转换为 pips

    if(currentSpread > MaxSpreadPips)
    {
        if(EnableDebugMode)
            Print("当前点差过大: ", currentSpread, " pips");
        return false;
    }

    return true;
}
```

#### 处理订单错误

```cpp
int OpenOrderWithRetry(int orderType, int maxRetries = 3)
{
    int ticket = -1;

    for(int attempt = 0; attempt < maxRetries; attempt++)
    {
        if(orderType == OP_BUY)
            ticket = OpenBuyOrder();
        else
            ticket = OpenSellOrder();

        if(ticket > 0)
            return ticket;  // 成功

        // 获取错误代码
        int error = GetLastError();

        // 可重试的错误
        if(error == ERR_BROKER_BUSY ||
           error == ERR_TRADE_TIMEOUT ||
           error == ERR_REQUOTE)
        {
            Print("订单失败（可重试），等待1秒后重试...");
            Sleep(1000);
            RefreshRates();  // 刷新价格
            continue;
        }
        else
        {
            Print("订单失败（不可重试），错误代码: ", error);
            break;
        }
    }

    return -1;  // 失败
}
```

### 6.4 代码规范化

#### 价格规范化

```cpp
double NormalizePrice(double price)
{
    return NormalizeDouble(price, Digits);
}

double NormalizeLots(double lots)
{
    double minLot = MarketInfo(Symbol(), MODE_MINLOT);
    double maxLot = MarketInfo(Symbol(), MODE_MAXLOT);
    double lotStep = MarketInfo(Symbol(), MODE_LOTSTEP);

    lots = MathFloor(lots / lotStep) * lotStep;

    if(lots < minLot) lots = minLot;
    if(lots > maxLot) lots = maxLot;

    return NormalizeDouble(lots, 2);
}
```

---

## 7. 开发和测试流程

### 7.1 推荐开发步骤

#### 阶段 1：基础框架（1-2小时）

**任务**：
1. 创建 EA 文件结构
2. 定义所有 input 参数
3. 实现 OnInit/OnTick/OnTimer/OnDeinit 骨架
4. 添加基础日志输出

**验证**：
- EA 能在图表上加载
- 参数能在界面中显示和修改
- 能输出启动和关闭日志

#### 阶段 2：价格检测模块（2-3小时）

**任务**：
1. 实现价格历史数组
2. 实现时间窗口滑动算法
3. 实现价格变动计算
4. 使用 Print() 输出检测结果

**验证**：
- 能正确存储价格历史
- 能删除过期数据
- 能准确计算 pips 变动
- 日志输出符合预期

#### 阶段 3：信号生成（1-2小时）

**任务**：
1. 实现信号生成逻辑
2. 添加信号过滤条件
3. 使用图表对象标记信号（可选）

**验证**：
- 信号触发时机正确
- 信号方向（买/卖）正确
- 过滤条件生效

#### 阶段 4：订单执行（2-3小时）

**任务**：
1. 实现 OrderSend 封装函数
2. 实现止损止盈计算
3. 添加错误处理和重试机制

**验证**：
- 能成功开仓（在 Demo 账户）
- 止损止盈位置正确
- 订单备注和魔术编号正确

#### 阶段 5：风控模块（2-3小时）

**任务**：
1. 实现持仓数量检查
2. 实现日内限制检查
3. 实现点差过滤
4. 实现时间过滤

**验证**：
- 达到限制时停止交易
- 点差过大时不交易
- 时间段外不交易

#### 阶段 6：优化和完善（3-5小时）

**任务**：
1. 代码重构和优化
2. 添加详细注释
3. 实现高级功能（移动止损等）
4. 完善日志系统

**验证**：
- 代码清晰易读
- 性能良好（OnTick 执行快）
- 功能完整

### 7.2 测试策略

#### A. 策略测试器回测（Strategy Tester）

**步骤**：
1. 打开 MT4 策略测试器（Ctrl+R）
2. 选择 EA 文件
3. 设置测试参数：
   - 品种：USDJPY
   - 周期：M1（1分钟图）
   - 日期范围：最近1个月
   - 模式：每个点（最精确）
4. 优化参数（可选）：
   - 时间窗口：1-5秒
   - 触发阈值：5-20 pips
5. 运行测试

**评估指标**：
- **总盈利**：净利润
- **胜率**：盈利订单 / 总订单
- **最大回撤**：最大亏损幅度
- **盈亏比**：平均盈利 / 平均亏损
- **交易频率**：每天交易次数

**目标标准**：
- 胜率 > 50%
- 盈亏比 > 1.2
- 最大回撤 < 账户的 20%
- 交易频率合理（不过度交易）

#### B. Demo 账户实盘测试

**步骤**：
1. 在 Rakuten MT4 Demo 账户加载 EA
2. 使用最小手数（0.01 lot）
3. 运行 1-2 周
4. 每天记录：
   - 交易次数
   - 盈亏情况
   - 异常事件

**观察重点**：
- 信号触发频率是否合理
- 滑点和点差的影响
- 风控机制是否生效
- 是否出现异常订单

**调整策略**：
- 如果交易过于频繁 → 提高阈值或增加过滤条件
- 如果很少触发 → 降低阈值或放宽条件
- 如果胜率低 → 检查信号逻辑或增加确认条件

#### C. 真实账户小资金测试

**步骤**：
1. 使用真实账户但小资金（例如 1000 USD）
2. 使用最小手数（0.01 lot）
3. 严格遵守风控规则
4. 运行 1 个月以上
5. 逐步增加仓位（如果表现良好）

**心理准备**：
- 真实账户交易有心理压力
- 可能出现意外亏损
- 需要严格遵守计划，不随意修改参数

### 7.3 回测数据示例

假设回测结果如下：

```
========== 回测报告 ==========
测试周期: 2024-10-01 至 2024-10-31 (1个月)
品种: USDJPY
参数: TimeWindow=1秒, Threshold=10pips, Lot=0.01

总交易次数: 87
盈利订单: 52 (59.8%)
亏损订单: 35 (40.2%)

总盈利: +$245.60
总亏损: -$168.30
净利润: +$77.30

平均盈利: $4.72
平均亏损: $4.81
盈亏比: 0.98

最大回撤: $32.40 (账户的 3.2%)
最大连续亏损: 5 笔

日均交易: 3.9 笔
================================
```

**分析**：
- ✓ 胜率 59.8% > 50%（良好）
- ✗ 盈亏比 0.98 < 1.2（需改进）
- ✓ 最大回撤 3.2% < 20%（优秀）
- ✓ 日均交易 3.9 笔（合理）

**改进建议**：
- 提高盈亏比：增加止盈距离或优化出场策略
- 或者：调整阈值，选择更高质量的信号

---

## 8. 潜在风险提示

### 8.1 高频策略的挑战

#### A. 信号过多导致过度交易

**问题**：
- 1秒时间窗口非常短，可能在波动市场产生大量信号
- 频繁交易导致累积交易成本高（点差+佣金）

**解决方案**：
- 增加过滤条件（例如：趋势过滤、成交量确认）
- 设置信号冷却期（例如：5秒内只触发一次）
- 限制日内最大交易次数

#### B. 噪音信号

**问题**：
- 短期价格波动可能是市场噪音，不代表真实趋势
- 追涨杀跌可能在震荡行情中反复止损

**解决方案**：
- 增加确认条件（例如：价格突破移动平均线）
- 使用更长的时间窗口（例如：3-5秒）
- 添加波动率过滤（ATR）

### 8.2 成本累积

#### A. 点差成本

**USDJPY 典型点差**：
- 低点差经纪商：0.3-0.5 pips
- 一般经纪商：1-2 pips
- 高点差时段：3-5 pips

**影响**：
- 每笔交易都要支付点差
- 例如：每天10笔，点差1 pip，0.01手
  - 日成本 = 10 × 1 pip × $0.10 = $1.00
  - 月成本 = $1.00 × 22天 = $22.00

**建议**：
- 选择低点差经纪商
- 避开点差扩大的时段（如亚洲午夜）
- 设置最大点差限制（参数 MaxSpreadPips）

#### B. 滑点成本

**问题**：
- 高频策略中，实际成交价可能偏离预期价格
- 滑点会降低策略盈利能力

**建议**：
- 设置合理的滑点参数（3-5点）
- 避开流动性低的时段
- 使用 ECN 账户类型（更好的执行）

### 8.3 市场条件变化

#### A. 波动率变化

**问题**：
- 不同时段波动率差异大
- 固定阈值可能在低波动时几乎不触发，高波动时过于频繁

**解决方案**：
- 使用动态阈值（基于 ATR）
- 根据时段调整参数
- 添加波动率过滤

#### B. 趋势 vs 震荡

**问题**：
- 策略在趋势市场表现好，在震荡市场可能亏损
- 需要识别市场状态

**解决方案**：
- 添加趋势识别指标（例如：ADX）
- 只在趋势明显时交易
- 或者：开发震荡市场专用策略

### 8.4 技术风险

#### A. 网络延迟

**问题**：
- VPS 或本地电脑网络不稳定
- 延迟导致错过最佳入场时机

**建议**：
- 使用低延迟 VPS（最好在经纪商服务器附近）
- 监控 EA 运行状态
- 设置异常告警

#### B. EA 逻辑错误

**问题**：
- 代码 bug 导致异常订单
- 未充分测试导致真实账户亏损

**建议**：
- 充分回测和 Demo 测试
- 代码审查和单元测试
- 初期使用小资金

### 8.5 心理和纪律风险

#### A. 过度干预

**问题**：
- 看到亏损时手动关闭 EA
- 盈利时调整参数"优化"

**建议**：
- 信任系统，让 EA 运行足够长时间
- 只在固定时间（例如每周）评估和调整
- 记录所有修改和原因

#### B. 参数过度优化

**问题**：
- 回测中找到"完美"参数
- 实盘中完全不适用（过拟合）

**建议**：
- 使用样本外数据验证
- 参数保持简单和稳健
- 接受合理的回撤

---

## 9. 附录：技术参考

### 9.1 MQL4 常用错误代码

| 错误代码 | 常量名 | 说明 | 处理方式 |
|---------|--------|------|----------|
| 0 | ERR_NO_ERROR | 无错误 | - |
| 4 | ERR_SERVER_BUSY | 服务器繁忙 | 等待后重试 |
| 6 | ERR_NO_CONNECTION | 无连接 | 检查网络 |
| 8 | ERR_TOO_FREQUENT_REQUESTS | 请求过于频繁 | 减少请求频率 |
| 128 | ERR_TRADE_TIMEOUT | 交易超时 | 重试 |
| 129 | ERR_INVALID_PRICE | 无效价格 | 刷新价格后重试 |
| 130 | ERR_INVALID_STOPS | 无效止损 | 检查止损距离 |
| 131 | ERR_INVALID_TRADE_VOLUME | 无效手数 | 检查手数范围 |
| 134 | ERR_NOT_ENOUGH_MONEY | 资金不足 | 减少手数 |
| 136 | ERR_OFF_QUOTES | 无报价 | 等待后重试 |
| 138 | ERR_REQUOTE | 重新报价 | 刷新价格后重试 |
| 145 | ERR_TRADE_MODIFY_DENIED | 禁止修改 | 检查订单状态 |

### 9.2 USDJPY 交易规格（乐天证券参考）

| 项目 | 值 | 说明 |
|------|---|------|
| 合约大小 | 100,000 | 1标准手 = 100,000 USD |
| 最小手数 | 0.01 | 1000 USD |
| 最大手数 | 100 | 根据经纪商不同 |
| 点值 | 0.001 | 第三位小数 |
| Pip | 0.01 | 第二位小数（1 pip = 10 points） |
| 典型点差 | 0.3-1 pip | 根据时段和流动性 |
| 杠杆 | 25:1 - 500:1 | 根据账户类型 |
| 保证金要求 | 约 $400-$4000 | 1手，根据杠杆 |

**计算示例**（1手，杠杆100:1）：
```
合约价值 = 100,000 USD
当前汇率 = 151.00
所需保证金 = 100,000 / 100 = $1,000

1 pip 价值 = 100,000 × 0.01 / 151.00 ≈ $6.62
0.01手 1 pip 价值 = $0.0662 ≈ $0.07
```

### 9.3 推荐的交易时段（UTC+8 北京时间）

| 时段 | 时间 | 特点 | 建议 |
|------|------|------|------|
| 亚洲早盘 | 06:00-12:00 | 波动较小，点差正常 | 可交易 |
| 亚洲午盘 | 12:00-15:00 | 流动性低，点差可能扩大 | 谨慎 |
| 欧洲开盘 | 15:00-18:00 | 波动增加 | 适合交易 |
| 伦敦-纽约重叠 | 20:00-24:00 | 流动性最高，波动最大 | 最佳时段 |
| 美国收盘 | 01:00-05:00 | 波动减少 | 可交易 |
| 亚洲午夜 | 02:00-05:00 | 流动性极低 | 避免交易 |

### 9.4 相关技术指标建议

可以考虑在 EA 中集成以下指标增强策略：

#### A. ATR（平均真实波幅）
```cpp
double atr = iATR(Symbol(), PERIOD_M1, 14, 0);
double dynamicThreshold = atr / Point / 10 * 0.5;  // ATR 的 50% 作为阈值
```

#### B. 移动平均线（趋势过滤）
```cpp
double ma20 = iMA(Symbol(), PERIOD_M1, 20, 0, MODE_SMA, PRICE_CLOSE, 0);
bool isBullish = Bid > ma20;  // 价格在 MA 上方 → 多头趋势
```

#### C. RSI（超买超卖）
```cpp
double rsi = iRSI(Symbol(), PERIOD_M1, 14, PRICE_CLOSE, 0);
bool isOversold = rsi < 30;   // 超卖 → 可能反弹
bool isOverbought = rsi > 70; // 超买 → 可能回调
```

### 9.5 参考资料

- **MQL4 官方文档**: https://docs.mql4.com/
- **MT4 用户指南**: https://www.metatrader4.com/en/trading-platform/help
- **乐天证券 MT4**: https://www.rakuten-sec.co.jp/web/fx/mt4/
- **MQL4 社区**: https://www.mql5.com/en/forum/172923

### 9.6 EA 文件结构示例

```
USDJPY_FastScalping_EA.mq4
├── 头部注释（版权、描述、版本）
├── #property 声明
├── input 参数定义
│   ├── 核心策略参数
│   ├── 交易执行参数
│   ├── 风险控制参数
│   ├── 时间过滤参数
│   └── 调试参数
├── 全局变量定义
├── OnInit() - 初始化
├── OnDeinit() - 清理
├── OnTick() - 主逻辑
├── OnTimer() - 定时任务
├── 策略模块函数
│   ├── AddPriceToHistory()
│   ├── CleanOldData()
│   ├── CalculatePriceChange()
│   └── GenerateSignal()
├── 风控模块函数
│   ├── CanTrade()
│   ├── UpdateDailyStatistics()
│   ├── CalculateLotSize()
│   └── IsWithinTradingHours()
├── 交易执行函数
│   ├── OpenBuyOrder()
│   ├── OpenSellOrder()
│   ├── CloseOrder()
│   └── ManageOpenPositions()
├── 工具函数
│   ├── CalculateStopLoss()
│   ├── CalculateTakeProfit()
│   ├── NormalizePrice()
│   └── PrintStatus()
└── 结束
```

---

## 结语

本设计方案详细规划了 USDJPY 自动交易系统的各个方面，从架构设计到具体实现，从参数配置到风险控制。

### 核心要点总结

1. **模块化架构**：分层设计，便于维护和扩展
2. **灵活参数**：使用 input 参数，可视化调整
3. **滑动窗口算法**：高效检测时间窗口内的价格变动
4. **多层风控**：持仓限制、日内限制、点差过滤等
5. **严格测试**：回测 → Demo → 真实小资金
6. **风险意识**：了解高频策略的挑战和成本

### 下一步建议

1. **审阅设计方案**，确认是否符合需求
2. **决定开发方式**：
   - 选项 A：我可以为你编写完整的 MQL4 代码
   - 选项 B：你基于此方案自行开发
   - 选项 C：我们逐步实现，分阶段交付
3. **准备测试环境**：确保 Rakuten MT4 Demo 账户可用
4. **设定目标**：明确回测和实盘的评估标准

---

**文档版本**: v1.0
**最后更新**: 2025-11-21
**作者**: Claude Code AI Assistant
**联系方式**: 通过 GitHub Issues 反馈

---
