# 149 因子与横截面计算扩展

日期：2026-07-23（Asia/Shanghai）

## 本次更新

- 已注册并可批量导出的因子从 132 个扩展至 149 个。
- 新增注册：`Alpha8`、`Alpha12`、`Alpha37`、`Alpha41`、`Alpha42`、`Alpha54`、
  `Alpha62`、`Alpha90`、`Alpha105`、`Alpha107`、`Alpha120`、`Alpha136`、
  `Alpha141`、`Alpha148`、`Alpha163`、`Alpha170`、`Alpha184`。
- 使用横截面 `RANK` 的已实现因子从 6 个扩展到 23 个。新增因子和原有横截面
  因子均按 `trade_date` 对当前股票池排名；`DELAY`、滚动窗口、`CORR` 和
  `COVIANCE` 均按 `trade_symbol` 分别计算，避免窗口跨股票串行。
- `RANK` 同时支持独立向量排名和显式分组排名；`CORR` 增加索引一致性检查，
  `SMA` 增加正权重校验。
- 调整 `Alpha4` 的条件分支有效性判断，使价格条件已命中时不再错误依赖成交量
  窗口；同时明确 `Alpha9`、`Alpha21` 的窗口参数。
- 新增 `factor_operator.md`，整理报告中的变量、算子和原始公式疑点；
  `factor_plan.md` 更新为剩余 42 个因子的实施计划。
- 以当前实现重新生成全部 149 份因子长表。每份含 24,173 条观测，字段固定为
  `trade_date,trade_symbol,factor_value`。

## 数据与计算口径

- 当前横截面范围仍是 20 只研究股票，不等同于报告中的全 A 非 ST 股票池。
- `run_factors.py` 读取 `data/price/` 下的 20 份行情文件；横截面因子在完整
  面板上计算，其余因子逐股票计算，并输出至 `data/factor/{FactorName}.csv`。

## 验证

- `python3 -m compileall -q factor.py factor_operators.py gat_data_akshare.py research_stocks.py run_factors.py` 通过。
- `python3 -m pytest -q`：134 passed。
- 已按当前代码逐项复算 149 份注册因子 CSV，确认字段、行数、排序、联合键和数值
  均与行情快照一致，且注册表中的每个因子均有对应输出文件。
- 已确认所有 149 个注册因子均可调用，注册表中没有占位 `pass`。

## 当前边界

- 尚有 42 个国泰 191 因子未实现，其中部分需要先统一公式解释、补充 `PROD`、
  基准指数口径或 Fama-French 数据与回归算子。
- 因子文件仍未补齐“日期并集 x 股票池”的完整观测网格。
- 当前数据是探索性的 `qfq` 行情快照，尚非严格的 point-in-time 复现。
