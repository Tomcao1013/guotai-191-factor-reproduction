# 横截面、基准数据与 99 因子扩展

日期：2026-07-21（Asia/Shanghai）

## 本次更新

- 可批量导出的因子从 70 个扩展到 99 个。
- 新增注册：`Alpha6`、`Alpha21`、`Alpha25`、`Alpha27`、`Alpha44`、`Alpha48`、`Alpha52`、`Alpha70`、`Alpha75`、`Alpha76`、`Alpha83`、`Alpha95`、`Alpha99`、`Alpha100`、`Alpha103`、`Alpha116`、`Alpha117`、`Alpha122`、`Alpha132`、`Alpha133`、`Alpha144`、`Alpha147`、`Alpha149`、`Alpha173`、`Alpha177`、`Alpha180`、`Alpha182`、`Alpha185`、`Alpha190`。
- 新增 `RANK`、`WMA`、`DECAYLINEAR`、`COVIANCE`、`LOG`、`SUMIF`、`FILTER`、`SIGN`、`HIGHDAY`、`LOWDAY` 等算子，并扩展 `REGBETA` 以支持固定序列窗口。
- 新增横截面因子分流：`Alpha6`、`Alpha25`、`Alpha48`、`Alpha83`、`Alpha99`、`Alpha185` 在完整股票面板上计算；其余注册因子仍逐股票计算。
- 行情数据增加 `benchmark_open`、`benchmark_close`，来源为沪深 300（`sh000300`）日线；下载入口在写入每只股票文件时按交易日合并基准数据。
- `run_factors.py` 改为先加载完整面板，再按因子类型选择横截面或单股票计算路径。
- 使用当前实现重生成全部 99 份因子长表，每份包含 24,173 条观测。

## 数据口径

- 横截面 `RANK` 在每日当前 20 只研究股票的有效观测内计算，采用百分比排名。
- 基准指数开收盘价复制到同一交易日的每个股票行情文件，仅服务需要基准指数的因子。
- 研究股票池与报告中的全 A 非 ST 股票池不同，因此横截面类因子是当前研究样本上的近似实现。

## 验证

- `python3 -m pytest -q`：38 passed。
- 已验证 20 份行情文件均含有效的基准指数开收盘字段。
- 已按面板/单股票分流规则逐项复算 99 份因子文件，确认字段、排序、联合键唯一性和数值均与当前代码及行情快照一致。

## 当前边界

- 因子文件仍未补齐“日期并集 x 股票池”的完整观测网格。
- 当前数据仍是探索性的 `qfq` 快照，尚非严格 point-in-time 复现。
- 横截面股票池、基准指数数据、VWAP 和价格复权口径在完整回测或严格复现前仍需进一步校验。
