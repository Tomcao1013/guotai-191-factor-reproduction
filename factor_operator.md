# 国泰 191 因子变量及函数说明

来源：`国泰191因子.pdf`，5.1“附录 2 表 6 相关变量及函数说明”，表 15（PDF 第 30-31 页）。

以下内容按原表提取。为便于阅读，仅统一了空格、半角标点和公式排版；原表中的名称拼写及定义含义均予以保留。

## 变量及特殊变量

| 变量/算子名 | 定义 |
| --- | --- |
| `OPEN` | 开盘价 |
| `HIGH` | 最高价 |
| `LOW` | 最低价 |
| `CLOSE` | 收盘价 |
| `VWAP` | 均价 |
| `VOLUME` | 成交量 |
| `AMOUNT` | 成交额 |
| `BANCHMARKINDEXCLOSE` | 基准指数的开盘价 |
| `BANCHMARKINDEXOPEN` | 基准指数的收盘价 |
| `RET` | 每日收益率（收盘 / 前收盘 - 1） |
| `DTM` | `OPEN <= DELAY(OPEN, 1) ? 0 : MAX((HIGH - OPEN), (OPEN - DELAY(OPEN, 1)))` |
| `DBM` | `OPEN >= DELAY(OPEN, 1) ? 0 : MAX((OPEN - LOW), (OPEN - DELAY(OPEN, 1)))` |
| `TR` | `MAX(MAX(HIGH - LOW, ABS(HIGH - DELAY(CLOSE, 1))), ABS(LOW - DELAY(CLOSE, 1)))` |
| `HD` | `HIGH - DELAY(HIGH, 1)` |
| `LD` | `DELAY(LOW, 1) - LOW` |
| `HML`、`SMB`、`MKE` | Fama French 三因子 |
| `SELF` | 特殊变量，出现在 Alpha143，表示 t-1 日的 Alpha143 因子计算结果 |

## 函数及逻辑算子

| 函数/算子名 | 定义 |
| --- | --- |
| `RANK(A)` | 向量 A 升序排序 |
| `MAX(A, B)` | 在 A、B 中选择最大的数 |
| `MIN(A, B)` | 在 A、B 中选择最小的数 |
| `STD(A, n)` | 序列 A 过去 n 天标准差 |
| `CORR(A, B, n)` | 序列 A、B 过去 n 天相关系数 |
| `DELTA(A, n)` | $A_i - A_{i-n}$ |
| `LOG(A)` | 自然对数函数 |
| `SUM(A, n)` | 序列 A 过去 n 天求和 |
| `ABS(A)` | 绝对值函数 |
| `MEAN(A, n)` | 序列 A 过去 n 天均值 |
| `TSRANK(A, n)` | 序列 A 的末位值在过去 n 天的顺序排位 |
| `SIGN(A)` | 符号函数：A > 0 时取 1；A = 0 时取 0；A < 0 时取 -1 |
| `COVIANCE(A, B, n)` | 序列 A、B 过去 n 天协方差 |
| `DELAY(A, n)` | $A_{i-n}$ |
| `TSMIN(A, n)` | 序列 A 过去 n 天的最小值 |
| `TSMAX(A, n)` | 序列 A 过去 n 天的最大值 |
| `PROD(A, n)` | 序列 A 过去 n 天累乘 |
| `COUNT(condition, n)` | 计算前 n 期满足条件 `condition` 的样本个数 |
| `REGBETA(A, B, n)` | 前 n 期样本 A 对 B 做回归所得回归系数 |
| `REGRESI(A, B, n)` | 前 n 期样本 A 对 B 做回归所得的残差 |
| `SMA(A, n, m)` | $\hat{Y}_{i+1} = (A_i m + \hat{Y}_i(n-m))/n$，其中 $\hat{Y}$ 表示最终结果 |
| `SUMIF(A, n, condition)` | 对 A 前 n 项条件求和，其中 `condition` 表示选择条件 |
| `WMA(A, n)` | 计算 A 前 n 期样本加权平均值，权重为 0.9i（i 表示样本距离当前时点的间隔） |
| `DECAYLINEAR(A, d)` | 对 A 序列计算移动平均加权，其中权重对应 d、d-1、...、1（权重和为 1） |
| `FILTER(A, condition)` | 对 A 筛选出符合选择条件 `condition` 的样本 |
| `HIGHDAY(A, n)` | 计算 A 前 n 期时间序列中最大值距离当前时点的间隔 |
| `LOWDAY(A, n)` | 计算 A 前 n 期时间序列中最大值距离当前时点的间隔 |
| `SEQUENCE(n)` | 生成 1~n 的等差序列 |
| `SUMAC(A, n)` | 计算 A 的前 n 项的累加 |
| `&` | 逻辑运算与 |
| <code>&#124;&#124;</code> | 逻辑运算或 |
| `A ? B : C` | 若 A 成立，则为 B，否则为 C |

## 原表疑点

以下内容是原表本身的疑点，本文件未在上表中擅自修正：

1. `BANCHMARK` 很可能是 `BENCHMARK` 的拼写错误。
2. `BANCHMARKINDEXCLOSE` 被定义为“基准指数的开盘价”，`BANCHMARKINDEXOPEN` 被定义为“基准指数的收盘价”，名称与定义看起来互换。
3. 原表列出 `HML SMB MKE`，其中 `MKE` 很可能是 `MKT`；报告的 Alpha30 公式使用的是 `MKT`。
4. `COVIANCE` 很可能是 `COVARIANCE` 的拼写错误。
5. `LOWDAY(A, n)` 的定义与 `HIGHDAY(A, n)` 相同，都写成“最大值距离当前时点的间隔”；按名称推测，前者可能应为“最小值距离当前时点的间隔”。
6. `WMA(A, n)` 的权重在原表中排为 `0.9i`，此处按原文保留。
