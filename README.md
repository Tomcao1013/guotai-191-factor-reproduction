# 国泰 191 因子复现

基于 `pandas`、NumPy 和 AKShare 的国泰君安 191 因子复现项目。当前版本聚焦于
20 只 A 股研究样本上的单股票时间序列因子，并将每个因子导出为跨日期、跨证券的长表。

## 当前版本

- 固定研究窗口：`2021-07-19` 至 `2026-07-16`。
- 固定研究样本：20 只 A 股；每只股票一份前复权 `qfq` 日线 OHLCVA CSV。
- 已注册并可批量导出的因子：66 个。
- 因子数据采用一因子一文件的长表结构：`trade_date,trade_symbol,factor_value`。

当前注册表包含 66 个可批量导出的单股票时间序列因子。完整清单见
`factor.py` 中的 `FACTORS` 注册表，以及最新更新记录。

## 快速开始

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 重新下载固定窗口内的 20 只样本行情（需要网络）
python gat_data_akshare.py

# 基于 data/price/ 中的行情生成 66 份因子长表
python run_factors.py
```

行情文件写入 `data/price/{code}_{market}_5y_daily.csv`；因子文件写入
`data/factor/{FactorName}.csv`。

## 参考资料

- [最新 66 因子覆盖更新](docs/updates/2026-07-21-factor-coverage-expansion.md)
- [架构决策记录](docs/adr/)
- [因子公式目录](factor_formula.md)
- [191 因子依赖分类](factor_plan.md)

## 已知限制

- 当前是探索性的 `qfq` 数据快照，不是严格的 point-in-time 复现。
- 因子文件目前保留实际存在的行情日期，尚未补齐“日期并集 x 股票池”的完整观测网格。
- 66 个因子可运行，但大多数尚缺独立数值基准测试；其余 191 因子仍在规划或实现中。

本项目仅用于研究和学习，不构成投资建议。
