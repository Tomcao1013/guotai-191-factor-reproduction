# 因子扩展更新

日期：2026-07-20（Asia/Shanghai）

## 本次更新

- 新增 `Alpha3`、`Alpha40`、`Alpha43`、`Alpha53`、`Alpha69`、`Alpha84` 的实现并注册到 `FACTORS`。
- 实现 `COUNT` 算子，用于滚动统计布尔条件为真的次数。
- 将多股票批量导出入口拆分为 `run_factors.py`，因子定义保留在 `factor.py`。
- 使用当前实现重生成全部 20 份因子长表；每份包含 24,173 条观测，字段固定为
  `trade_date,trade_symbol,factor_value`。

## 使用方式

```bash
python run_factors.py
```

脚本读取 `data/price/` 下的 20 份行情文件，并将每个已注册因子的结果写入
`data/factor/{FactorName}.csv`。

## 验证

- 独立的循环参考实现已覆盖新增的 6 个因子公式。
- 20 份因子文件与当前 `FACTORS` 注册表和行情快照逐项比对一致。
- `python3 -m pytest -q` 通过。

## 仍待完善

- 因子数据尚未补齐“日期并集 x 股票池”的完整观测网格。
- 当前使用探索性 `qfq` 行情快照，尚非严格的 point-in-time 复现。
- 其余国泰 191 因子及更全面的数值基准测试仍在后续计划中。
