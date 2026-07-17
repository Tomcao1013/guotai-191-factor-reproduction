# 国泰 191 因子复现

基于 `pandas`、`NumPy` 和 AKShare 的国泰君安 191 因子复现项目。当前实现聚焦于仅依赖单只股票 OHLCV 日线数据的时间序列因子，仍在持续完善中。

## 项目内容

- `factor.py`：已注册因子的计算与批量导出。
- `factor_operators.py`：`DELAY`、`SUM`、`CORR`、`SMA` 等公式算子。
- `gat_data_akshare.py`：下载平安银行（`sz000001`）近五年的前复权日线数据。
- `factor_plan.md`：191 个因子的依赖分类及实现计划。
- `data/price/`：示例 OHLCV 输入数据和计算结果。
- `国泰191因子.pdf`：因子公式参考资料。

## 快速开始

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 可选：重新下载近五年数据
python gat_data_akshare.py

# 计算当前已注册的因子
python factor.py
```

计算结果会写入 `data/price/000001_SZ_5y_daily_with_factors.csv`。

## 当前状态

当前已注册并参与批量计算的因子包括：`Alpha2`、`Alpha5`、`Alpha9`、`Alpha11`、`Alpha14`、`Alpha15`、`Alpha20`、`Alpha29`、`Alpha31`、`Alpha46`、`Alpha60`、`Alpha80`、`Alpha168`、`Alpha191`。

其余待实现因子和数据依赖说明见 [factor_plan.md](factor_plan.md)。本项目仅用于研究和学习，不构成投资建议。
