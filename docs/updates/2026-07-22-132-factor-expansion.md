# 132 因子覆盖扩展

日期：2026-07-22（Asia/Shanghai）

## 本次更新

- 已注册并可批量导出的因子从 99 个扩展至 132 个。
- 新增注册：`Alpha4`、`Alpha19`、`Alpha22`、`Alpha23`、`Alpha28`、`Alpha38`、
  `Alpha49`、`Alpha50`、`Alpha51`、`Alpha55`、`Alpha78`、`Alpha86`、`Alpha94`、
  `Alpha98`、`Alpha112`、`Alpha127`、`Alpha128`、`Alpha129`、`Alpha137`、
  `Alpha143`、`Alpha146`、`Alpha159`、`Alpha160`、`Alpha162`、`Alpha164`、
  `Alpha165`、`Alpha166`、`Alpha167`、`Alpha172`、`Alpha174`、`Alpha183`、
  `Alpha186`、`Alpha187`。
- 补齐 `Alpha19`、`Alpha38`、`Alpha94`、`Alpha129`、`Alpha162`、`Alpha167`、
  `Alpha187` 的公式实现，并新增 `SUMAC`、`TR`、`HD`、`LD` 算子以支持本轮公式。
- 使用当前代码和 20 只研究股票的行情快照重新生成全部 132 份因子长表；每份固定包含
  24,173 条观测，字段为 `trade_date,trade_symbol,factor_value`。

## 数据与计算口径

- 横截面计算范围不变：`Alpha6`、`Alpha25`、`Alpha48`、`Alpha83`、`Alpha99`、
  `Alpha185` 在当前 20 只研究股票的每日有效观测上计算；其余因子逐股票计算。
- `run_factors.py` 读取 `data/price/` 下的 20 份行情文件，并将结果写入
  `data/factor/{FactorName}.csv`。

## 验证

- `python3 -m compileall -q factor.py factor_operators.py gat_data_akshare.py research_stocks.py run_factors.py` 通过。
- `python3 -m pytest -q`：95 passed。
- 已以当前代码逐项复算 132 份因子文件，确认文件数量、字段、行数、排序、联合键及数值均与行情快照一致。
- 已确认 132 个注册因子均为可调用实现，注册表中没有占位 `pass`。

## 当前边界

- 因子文件仍未补齐“日期并集 x 股票池”的完整观测网格。
- 当前数据是探索性的 `qfq` 行情快照，尚非严格的 point-in-time 复现。
- 横截面计算只覆盖当前研究股票池，不等同于报告中的全 A 非 ST 股票池。
- 其余 59 个国泰 191 因子和更多独立数值基准测试仍在后续计划中。
