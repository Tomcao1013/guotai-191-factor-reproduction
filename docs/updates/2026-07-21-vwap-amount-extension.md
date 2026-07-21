# VWAP/AMOUNT 数据层与 70 因子扩展

日期：2026-07-21（Asia/Shanghai）

## 本次更新

- 行情数据从 OHLCVA 扩展为 `trade_date,trade_symbol,open,high,low,close,vwap,volume,amount`。
- 下载脚本同时读取前复权和未复权日线：以未复权 `amount / volume` 计算每日 `vwap_raw`，再使用每日前复权比例转换为与 `open/high/low/close` 一致的 `vwap` 价格尺度。
- 将 20 只研究股票池抽取到 `research_stocks.py`，供下载入口复用。
- 新增并注册 `Alpha13`、`Alpha26`、`Alpha97`、`Alpha154`，可批量导出的因子数量从 66 个增至 70 个。
- 新增 `REGBETA`、`STD`、`RET` 算子，并修正 `Alpha52` 与 `Alpha117` 的可调用性。
- 使用当前行情数据重生成全部 70 份因子长表；每份包含 24,173 条观测。

## 数据口径

- `open`、`high`、`low`、`close` 继续使用 AKShare 前复权 `qfq` 价格。
- `volume` 与 `amount` 使用未复权日线中的真实成交量和成交额。
- `vwap` 是“日成交额 / 日成交量”经前复权比例换算后的日频价格，并非逐笔成交重建的 VWAP。

## 验证

- `python3 -m pytest -q`：32 passed。
- 已检查 20 份行情文件的 `vwap`、`volume`、`amount` 均为有效正值。
- 已逐项复算 70 份因子文件，确认字段、排序、联合键唯一性和数值均与当前代码及行情快照一致。

## 当前边界

- 因子文件仍未补齐“日期并集 x 股票池”的完整观测网格。
- 当前数据仍是探索性的 `qfq` 快照，尚非严格 point-in-time 复现。
- 需要真正交易所口径 VWAP、横截面 RANK、基准指数或 Fama-French 数据的因子，仍需后续扩展数据层。
