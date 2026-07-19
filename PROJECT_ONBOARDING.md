# 国泰 191 因子复现：项目上手指南

> 面向第一次接手本仓库的新 session。
>
> 本文按当前工作区实际代码、测试和数据核对，最后验证日期为
> **2026-07-19（Asia/Shanghai）**。接手时仍应先运行 `git status` 和测试，
> 不要把本文当成不会变化的事实。

## 1. 先看结论

这是一个用 `pandas`、NumPy 和 AKShare 复现国泰君安 191 个短周期价量因子的
研究项目。

当前真正落地的范围不是完整 191 因子，而是：

- 固定 20 只 A 股研究样本。
- 固定日期范围 `2021-07-19` 至 `2026-07-16`。
- 每只股票一份前复权 `qfq` 日线 OHLCVA CSV。
- 14 个已注册、可运行的单股票时间序列因子。
- 每个因子一份跨日期、跨股票的长表 CSV。

当前主链路可以离线运行并生成 14 个因子文件，但项目还不能视为完成：

- 完整 `pytest` 在测试收集阶段失败。
- 因子输出尚未补齐 ADR 约定的完整日期和股票笛卡尔积。
- 大多数因子只有 smoke-level 运行验证，没有独立数值基准测试。
- 6 个第一阶段候选因子仍未完成或存在已知错误。
- 当前数据口径是探索性 `qfq` 快照，不是严格 point-in-time 复现。

本项目当前只处理 **Factor Observation**，不处理交易信号、订单、持仓、组合和
回测。领域词汇以 `CONTEXT.md` 为准。

## 2. 信息来源与优先级

接手时按以下方式理解仓库，避免被旧文档误导：

1. **实际运行行为**：以当前 `factor.py`、`factor_operators.py`、
   `gat_data_akshare.py`、测试和 CSV 为准。
2. **目标数据契约**：以 `docs/adr/` 为准。当前实现可能尚未满足 ADR。
3. **领域术语**：以 `CONTEXT.md` 为准。
4. **公式来源**：以 `国泰191因子.pdf` 为准，尤其是公式表和附录函数定义。
5. **更新历史**：`CHANGELOG.md`。
6. **历史计划和讨论**：`HANDOFF.md`、`factor_plan.md`。
7. **基础介绍**：`README.md`。README 已覆盖当前多股票数据流；精确的实现边界仍以本指南和 ADR 为准。

`HANDOFF.md` 记录的是上一阶段讨论和推荐实施顺序，其中“只有一只样例股票”
等描述已经被当前 20 股票数据实现取代。它仍然适合了解项目目标和协作背景，
但需要用当前代码重新核对。

## 3. 仓库结构

```text
.
├── README.md
├── PROJECT_ONBOARDING.md       # 本文，当前项目地图和接手入口
├── CONTEXT.md                  # 领域词汇及明确排除的交易语义
├── HANDOFF.md                  # 上一阶段讨论、教学协作方式和实施路线
├── factor_plan.md              # 191 因子按数据依赖分类
├── 国泰191因子.pdf              # 原始研报和 191 因子公式参考
├── requirements.txt           # akshare / numpy / pandas / pytest，未锁版本
├── gat_data_akshare.py         # 20 股票行情下载入口
├── factor_operators.py         # 时间序列公式算子
├── factor.py                   # 因子函数、注册表、批量计算和导出入口
├── data/
│   ├── price/                  # 一只股票一份行情 CSV
│   └── factor/                 # 一个因子一份长表 CSV
├── docs/
│   └── adr/
│       ├── 0001-defer-price-adjustment-normalization.md
│       └── 0002-one-long-format-dataset-per-factor.md
└── tests/
    ├── test_factor.py
    ├── test_factor_operators.py
    └── operator_CORR.py        # 当前为空文件
```

仓库没有 Python package、`pyproject.toml`、CLI 参数层或配置文件。脚本直接从项目
根目录运行。

## 4. 当前数据流

```text
AKShare stock_zh_a_daily(adjust="qfq")
                |
                v
data/price/{code}_{market}_5y_daily.csv
一只股票一份，20 份
                |
                v
factor.py 中 FACTORS 注册表
按股票读取，按因子函数计算
                |
                v
data/factor/{FactorName}.csv
一个因子一份，当前 14 份
```

当前没有独立的数据加载层、校验层或导出模块，编排逻辑直接写在
`factor.main()` 中。

需要特别区分两个接口：

- `calculate_factors(data)`：把所有注册因子追加到一只股票的 DataFrame，
  是早期“单股票宽表”流程留下的 helper，当前批量导出入口没有使用它。
- `main()`：遍历行情文件和 `FACTORS`，输出“一因子一长表”，这是当前实际主线。

## 5. 核心模块

### 5.1 `gat_data_akshare.py`

职责：

- 在 `RESEARCH_UNIVERSE` 中硬编码 20 个 AKShare symbol。
- 固定请求 `2021-07-19` 至 `2026-07-16`。
- 调用 `ak.stock_zh_a_daily(..., adjust="qfq")`。
- 将 AKShare symbol 转为项目标准 `trade_symbol`，例如：
  `sz000001 -> 000001.SZ`。
- 保留 `trade_date, trade_symbol, open, high, low, close, volume, amount`。
- `dropna()`、按日期去重、排序后覆盖写入对应行情文件。

当前研究样本：

```text
000001.SZ  000333.SZ  000858.SZ  002027.SZ  002230.SZ
002415.SZ  002594.SZ  002714.SZ  300015.SZ  300124.SZ
300750.SZ  600030.SH  600050.SH  600276.SH  600309.SH
600900.SH  601088.SH  601318.SH  601668.SH  688008.SH
```

已知限制：

- 没有 retry、限速、断点续跑和单股票失败隔离。
- 任意一个网络请求失败会中止整个批次。
- 运行会覆盖已有行情 CSV。
- `.dropna()` 会直接删除任意字段缺失的行情行。
- 没有在写入前验证 OHLC 关系、正成交量、日期范围和证券代码一致性。
- 固定日期和股票池只能修改源码，不能通过 CLI 或配置传入。

### 5.2 `factor_operators.py`

当前已实现：

```text
DELTA  SUM  DELAY  TSMAX  TSMIN  TSRANK  CORR  SMA  MEAN
```

当前未实现：

```text
COUNT
```

实现语义主要依赖 `pandas.Series.shift`、`rolling`、`rolling.rank`、
`rolling.corr` 和 `ewm`。

注意事项：

- `SUM`、`MEAN` 等使用完整窗口 `min_periods=periods`，初始窗口会产生空值。
- `CORR` 会把正负无穷替换为 `NaN`，但没有独立数值测试。
- `CORR` 允许 `periods=2`，错误文案却写着必须 greater than 2。
- `SMA` 使用 `ewm(alpha=weight/periods, adjust=False)` 实现研报递推公式。
- `SMA` 的校验没有显式拒绝 `weight <= 0`，与错误文案不完全一致。
- 模块只暴露大写函数名；现有测试错误地导入小写 `delta`。

### 5.3 `factor.py`

文件包含三类职责：

1. 20 个第一阶段候选因子函数。
2. `FACTORS` 注册表。
3. 多股票批量读取、计算、合并和导出。

所有因子函数都假设输入字段为小写：

```text
open, high, low, close, volume
```

函数不负责验证：

- 必需字段是否存在。
- 日期是否升序。
- 输入是否只属于一只股票。
- 索引是否唯一。
- 数据类型是否为数值。

`main()` 当前行为：

1. 匹配 `data/price/*_5y_daily.csv`。
2. 对每个已注册因子遍历全部行情文件。
3. 保留行情中实际存在的 `trade_date, trade_symbol`。
4. 计算 `factor_value`。
5. 合并并按 `trade_date, trade_symbol` 排序。
6. 写入 UTF-8 BOM 编码的 `data/factor/{FactorName}.csv`。

当前实现没有构造“日期并集 x 20 股票”的完整观测网格，所以停牌或缺行情日期
对应的行会直接消失。这与 ADR 0002 的目标契约不一致。

## 6. 因子实现状态

### 6.1 已注册并参与批量计算的 14 个因子

| 因子 | 当前实现的核心依赖 | 主要窗口 |
|---|---|---:|
| `Alpha2` | 收盘位置值的负一阶差分 | 1 |
| `Alpha5` | `TSRANK(VOLUME/HIGH)`、`CORR`、`TSMAX` | 5/5/3 |
| `Alpha9` | 中间价变化、振幅、成交量、递推 `SMA` | 7 |
| `Alpha11` | 成交量加权收盘位置值之和 | 6 |
| `Alpha14` | `CLOSE - DELAY(CLOSE, 5)` | 5 |
| `Alpha15` | 隔夜开盘缺口 | 1 |
| `Alpha20` | 6 日收盘收益率百分比 | 6 |
| `Alpha29` | 6 日收盘收益率乘成交量 | 6 |
| `Alpha31` | 收盘价相对 12 日均值偏离 | 12 |
| `Alpha46` | 3/6/12/24 日均价组合 | 24 |
| `Alpha60` | 成交量加权收盘位置值之和 | 20 |
| `Alpha80` | 5 日成交量变化率 | 5 |
| `Alpha168` | 负成交量相对 20 日均量 | 20 |
| `Alpha191` | 20 日均量与最低价的 5 日相关性 | 20+5 |

这 14 个因子已经验证能对当前全部 20 只股票运行并生成 CSV。这里的“可运行”
只表示不抛异常，不等于每个数学公式已经由独立基准确认。

### 6.2 候选但未注册的 6 个因子

| 因子 | 当前状态 |
|---|---|
| `Alpha3` | `pass` |
| `Alpha40` | 有代码但已知错误，`previous_close` 错存为 `.notna` 方法 |
| `Alpha43` | `pass` |
| `Alpha53` | `pass`，同时依赖尚未实现的 `COUNT` |
| `Alpha69` | `pass` |
| `Alpha84` | `pass` |

不要把这些函数加入 `FACTORS`，也不要为它们生成形式上完整但无有效实现的 CSV。

### 6.3 完整 191 因子的依赖分类

`factor_plan.md` 已做初步分类：

- 115 个仅用单股 OHLCV 即可计算。
- 63 个需要当日股票横截面 `RANK`。
- 4 个额外需要真实 VWAP。
- 4 个需要 `AMOUNT`。
- 4 个需要基准指数日线。
- `Alpha30` 需要 Fama-French 三因子。

这里的分类只表示字段依赖，不表示公式不存在排版歧义，也不表示相应算子已经
实现。

## 7. 数据契约

### 7.1 行情文件

位置和命名：

```text
data/price/{six_digit_code}_{SZ|SH}_5y_daily.csv
```

固定字段：

```csv
trade_date,trade_symbol,open,high,low,close,volume,amount
```

当前约定：

- 一只股票一个文件。
- `trade_symbol` 使用 `000001.SZ` 形式。
- 日期升序。
- 同一文件内 `trade_date` 唯一。
- 因子值不再追加到行情文件。

### 7.2 因子文件

位置和命名：

```text
data/factor/{FactorName}.csv
```

固定字段：

```csv
trade_date,trade_symbol,factor_value
```

ADR 0002 约定：

- `(trade_date, trade_symbol)` 联合唯一。
- 按 `trade_date, trade_symbol` 排序。
- 因子名称由文件名表达。
- 缺少历史窗口或行情时，保留行并令 `factor_value` 为空。
- 理论行集合为“全部行情日期并集 x 固定研究股票池”。
- 不保存价格、股票名称、未来收益、信号、持仓或订单。

## 8. 已验证的数据快照

### 8.1 行情数据

截至 2026-07-18 的本地文件检查结果：

- 行情文件：20 个。
- 日期并集：1210 个交易日。
- 总实际行情行数：24,173。
- 完整网格理论行数：`1210 x 20 = 24,200`。
- 所有行情文件字段一致。
- 所有文件内日期无重复、字段无空值、证券代码唯一。
- 所有文件日期范围均从 `2021-07-19` 到 `2026-07-16`。
- 只有 3 只股票存在相对日期并集的缺行情记录，共 27 行：

| 股票 | 缺少行数 | 缺少日期 |
|---|---:|---|
| `600030.SH` | 6 | `2022-01-19` 至 `2022-01-26` |
| `600900.SH` | 11 | `2021-11-29` 至 `2021-12-10`，另有 `2022-10-26` |
| `601088.SH` | 10 | `2025-08-04` 至 `2025-08-15` |

基础 OHLC 检查没有发现高低价包络错误、非正成交量或非正成交额。
`600030.SH` 有 1 行 `high == low`，依赖日内振幅的因子会合理产生空值。

### 8.2 因子数据

- 因子文件：14 个，与 `FACTORS` 注册表一致。
- 每个文件都是 24,173 行，而不是 ADR 目标的 24,200 行。
- 每个文件字段均为 `trade_date, trade_symbol, factor_value`。
- 每个文件联合键无重复，覆盖 20 只股票和 1210 个日期。
- 已存在的非空因子值都是有限数，没有正负无穷。
- 14 个本地因子文件的键和值均与当前代码重新计算结果一致。

这说明生成数据没有明显“代码和缓存不一致”，但仍缺少完整网格中的 27 行。

因子文件中的 `NaN` 不一定只来自初始 lookback：

- 初始滚动窗口不足会产生 `NaN`。
- `high == low` 等分母为零会产生 `NaN`。
- 滚动相关窗口中序列退化为常数时也可能产生 `NaN`。

不要把空值填成 0，也不要在没有解释原因时直接删除。

### 8.3 遗留文件

`data/price/000001_SZ_5y_daily_with_factors.csv` 是早期单股票宽表产物，字段仍为
大写 `Date/Open/High/Low/Close/Volume/Alpha2`。它不属于当前长表主链路，
不要拿它作为新数据契约的依据。

Git 中原来还跟踪过根目录 `data/000001_SZ_5y_daily_with_factors.csv`，当前工作区
显示为删除状态。除非用户明确要求，不要恢复或清理这些已有变更。

## 9. 环境与运行

### 9.1 安装

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

`requirements.txt` 当前没有版本锁。最近一次实际验证环境：

```text
Python   3.10.14
akshare  1.18.64
numpy    1.23.5
pandas   2.3.3
pytest   9.1.1
```

### 9.2 下载或覆盖行情

```bash
python3 gat_data_akshare.py
```

这是联网操作，会请求 20 只股票并覆盖 `data/price/` 下同名文件。普通代码阅读、
因子调试和测试不需要先运行它。

### 9.3 生成因子文件

```bash
python3 factor.py
```

这是离线操作，读取现有行情并覆盖 `data/factor/Alpha*.csv`。当前会生成 14 个
文件，每个 24,173 行。

### 9.4 测试和静态语法检查

```bash
python3 -m pytest -q
python3 -m compileall -q factor.py factor_operators.py gat_data_akshare.py tests
```

截至本文验证时：

- `compileall` 通过。
- `pytest` 在收集 `tests/test_factor_operators.py` 时失败，因为测试导入
  `factor_operators.delta`，实现只有 `DELTA`。
- 单独运行 `tests/test_factor.py` 的结果是 `20 passed, 4 failed`。
- 4 个失败都首先暴露出测试仍使用大写行情字段，而代码已经迁移到小写字段。
- 即使修正字段大小写，部分测试仍假设注册表只有 `Alpha2`，也需要同步更新。

因此当前测试红灯主要是测试与数据契约迁移不同步，但不能据此推断因子数值都
正确。修复测试时应补充真实契约测试，而不是只让旧断言机械通过。

## 10. 当前已知缺口

按优先级理解：

1. **测试套件不可用**
   - 大小写字段和算子命名已漂移。
   - `calculate_factors` 的断言仍停留在只有 `Alpha2` 的阶段。
   - 除 `Alpha2` 外几乎没有独立数值测试。

2. **完整观测网格未实现**
   - ADR 要求 24,200 行。
   - 当前导出只有行情中真实存在的 24,173 行。
   - 缺行情、停牌和计算不可用三类情况尚未在统一网格中表达。

3. **数据和输入校验薄弱**
   - `factor.main()` 不验证 schema、排序、重复键或单股票约束。
   - 没有行情文件时，`pd.concat([])` 会报错。
   - 下载脚本没有失败隔离和数据质量报告。

4. **数学正确性验证不足**
   - 当前“14 个可运行”是运行级结论，不是严格复现结论。
   - 公式排版、滚动窗口、`NaN` 传播和 `SMA` 初值都需要逐因子确认。

5. **未完成因子和算子**
   - 5 个函数是 `pass`。
   - `Alpha40` 已知错误。
   - `COUNT` 未实现。

6. **文档漂移**
   - README 仍描述单股票下载和旧宽表输出。
   - HANDOFF 混合了实施前状态和目标设计。

7. **复权与严格可复现性**
   - 当前使用 `qfq`，只适合第一阶段数据管道和分布探索。
   - 在实现 VWAP/AMOUNT 因子或任何回测前，必须处理 ADR 0001 中的复权、
     成交量单位和价格 multiplier 问题。

## 11. 推荐接手顺序

不要一开始扩展到全部 191 因子。推荐按下面顺序推进：

1. 先运行 `git status`，确认并保护当前未提交修改。
2. 阅读本文、`CONTEXT.md`、两份 ADR、核心 Python 文件和相关 PDF 公式。
3. 重现当前 `pytest` 失败，修复测试与小写数据契约的漂移。
4. 为 `DELTA/SUM/DELAY/CORR/SMA/TSRANK` 增加明确的算子测试。
5. 先用 `Alpha2` 建立完整网格、空值和导出契约测试。
6. 将“1210 日期 x 20 股票”的网格补齐到每个因子输出。
7. 增加某日横截面分布统计，验证有效数、缺失率、均值、标准差和分位数。
8. 把同一导出流程推广到现有 14 个注册因子。
9. 对每个因子增加独立公式复算或可信参考实现对照。
10. 最后再逐个实现 `Alpha3/40/43/53/69/84`，每次只加入一个已验证因子。

当前阶段合理的最小完成标准：

- 20 份行情结构可靠。
- `Alpha2.csv` 满足三字段和完整网格契约。
- 空值被保留且原因可解释。
- 可以展示任意交易日 20 股票的 Alpha2 横截面。
- 有独立公式测试证明 Alpha2 数值正确。
- 完整测试套件通过。

## 12. Git 工作区注意事项

本文生成时工作区已有用户或上一 session 的未提交工作，包括：

- `factor.py`、`factor_operators.py`、`gat_data_akshare.py` 的修改。
- `data/price/000001_SZ_5y_daily.csv` 的修改。
- 一个旧宽表文件的删除。
- `CONTEXT.md`、`HANDOFF.md`、`docs/`、20 股票数据和因子数据等未跟踪内容。

接手时：

- 不要使用 `git reset --hard` 或 `git checkout --` 清理工作区。
- 不要把未跟踪 CSV 当成可随意删除的缓存。
- 修改前先看 `git diff`，区分基线代码与当前进行中的改造。
- 除非用户明确要求，不要 commit、push、删除历史文件或重新下载全部数据。

## 13. 新 session 的首轮检查清单

```bash
git status --short --branch
git diff -- factor.py factor_operators.py gat_data_akshare.py
python3 --version
python3 -m pytest -q
python3 -m compileall -q factor.py factor_operators.py gat_data_akshare.py tests
```

然后回答用户以下问题再开始较大修改：

1. 当前代码实际输入和输出是什么。
2. 14 个注册因子与 6 个未完成因子的边界是什么。
3. 测试为什么失败。
4. 24,173 行和 24,200 行的差异来自哪里。
5. 本次任务应修改哪一层，哪些已有因子公式可以保持不动。

## 14. 可直接给新 session 的提示词

```text
请先阅读 PROJECT_ONBOARDING.md，并用当前代码、测试和数据重新核对其中结论。
先运行 git status、pytest 和 compileall，不要立即清理工作区或重新下载数据。
请向我说明当前数据流、14 个注册因子、6 个未完成因子、测试失败原因，以及
24,173 行实际输出和 24,200 行完整网格契约之间的差异。
后续修改以 docs/adr/ 的目标契约为准，优先修复测试和 Alpha2 完整网格，
不要直接扩展到全部 191 因子，也不要引入交易、组合或回测范围。
```
