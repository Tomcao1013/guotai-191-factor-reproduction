# 国泰 191 因子实现计划

更新日期：2026-07-23

## 当前状态

- `FACTORS` 已注册 149 个因子。
- 尚未实现 42 个因子。
- 当前 23 个已实现因子使用股票横截面 `RANK`。
- 剩余因子中，40 个需要横截面 `RANK`；完成后 `PANEL_FACTORS`
  理论上应包含 63 个因子。
- 当前行情已包含 `open`、`high`、`low`、`close`、`volume`、
  `amount`、`vwap`、`benchmark_open` 和 `benchmark_close`。
- 当前 20 只股票已经可以用于开发和验证横截面因子，但其排名结果只代表
  当前研究股票池，不等同于全 A 非 ST 股票池。

剩余 42 个因子：

```text
Alpha1, Alpha7, Alpha10, Alpha16, Alpha17, Alpha30,
Alpha32, Alpha33, Alpha35, Alpha36, Alpha39, Alpha45,
Alpha56, Alpha61, Alpha64, Alpha73, Alpha74, Alpha77,
Alpha87, Alpha91, Alpha92, Alpha101, Alpha104, Alpha108,
Alpha113, Alpha114, Alpha115, Alpha119, Alpha121, Alpha123,
Alpha124, Alpha125, Alpha130, Alpha131, Alpha138, Alpha140,
Alpha142, Alpha156, Alpha157, Alpha176, Alpha179, Alpha181
```

## 分类一：可直接实现的优先批

共 12 个。现有数据、`RANK`、时序算子和 Panel 辅助函数已经能够支持，
公式结构也没有明显缺失，适合下一批完成：

```text
Alpha1, Alpha16, Alpha32, Alpha33,
Alpha45, Alpha73, Alpha74, Alpha101,
Alpha104, Alpha123, Alpha176, Alpha179
```

主要覆盖：

- 横截面 `RANK` 后进行逐股票 `CORR`、`SUM` 或 `TSMAX`。
- 逐股票计算完成后再做横截面排名。
- 多个横截面排名结果之间的乘法、加法或条件比较。

## 分类二：可直接实现的复杂嵌套批

共 17 个。现有数据和算子已经支持，但公式包含较多层
`CORR`、`DECAYLINEAR`、`TSRANK`、`DELAY` 或多次 `RANK`，
实现后需要重点检查运算顺序和索引对齐：

```text
Alpha35, Alpha39, Alpha56, Alpha61,
Alpha77, Alpha87, Alpha92, Alpha113,
Alpha114, Alpha115, Alpha124, Alpha125,
Alpha130, Alpha138, Alpha140, Alpha142,
Alpha156
```

这批因子不需要新行情字段，也不需要新增核心算子。

## 分类三：公式解释需要先统一

共 10 个。它们使用了与项目算子定义不一致或存在拼写问题的表达式，
不建议在确认口径前直接实现：

| 因子 | 需要确认的问题 |
|---|---|
| `Alpha7` | `MAX(VWAP-CLOSE,3)` 和 `MIN(VWAP-CLOSE,3)` 是否分别表示 `TSMAX`、`TSMIN` |
| `Alpha10` | `MAX(conditional_value,5)` 是否表示五日 `TSMAX` |
| `Alpha17` | `MAX(VWAP,15)` 是否表示 `TSMAX(VWAP,15)`；负底数参与幂运算时如何处理 |
| `Alpha36` | `RANK(SUM(...),2)` 中额外的参数 `2` 属于 `RANK`、`SUM` 还是原公式排版错误 |
| `Alpha64` | `MAX(CORR(...),13)` 是否表示十三日 `TSMAX` |
| `Alpha91` | `MAX(CLOSE,5)` 是否表示 `TSMAX(CLOSE,5)` |
| `Alpha108` | `MIN(HIGH,2)` 是否表示 `TSMIN(HIGH,2)`；幂运算的定义域如何处理 |
| `Alpha119` | `MIN(CORR(...),9)` 是否表示九日 `TSMIN` |
| `Alpha121` | `MIN(VWAP,12)` 是否表示 `TSMIN(VWAP,12)`；幂运算的定义域如何处理 |
| `Alpha131` | `DELAT(VWAP,1)` 应确认是 `DELTA(VWAP,1)`，并确认幂运算口径 |

建议把最终确认后的规范公式同步写回 `factor_formula.md`，避免代码、
docstring 和公式文件采用不同解释。

## 分类四：需要新增算子

### Alpha157

`Alpha157` 需要新增：

```text
PROD(series, periods)
```

该算子表示过去 `periods` 期的滚动累乘。公式还包含多层
`RANK`、`TSMIN`、`LOG`、`SUM`、`DELAY` 和 `TSRANK`，
应在 `PROD` 独立验证后再实现因子。

## 分类五：需要基准指数并确认公式

### Alpha181

当前数据已经具有 `benchmark_close`，因此数据字段不是阻塞项。但原公式中的
括号和指数位置存在歧义，而且股票收益率与基准指数价格偏差直接相减的量纲
不一致。

实现前需要确认：

- 基准项应使用指数价格还是指数收益率。
- 平方和立方分别作用于哪个完整表达式。
- 两个 `SUM` 的窗口是否都为 20。

## 分类六：需要外部数据和回归算子

### Alpha30

`Alpha30` 暂时放在最后实现，需要：

- 日频 `MKT`、`SMB`、`HML` Fama-French 三因子数据。
- 与股票交易日和复权口径对齐的数据处理。
- 新增多因子滚动回归残差算子 `REGRESI`。
- 明确回归是否包含截距以及缺失样本处理规则。

现有 `WMA` 已经可以支持回归残差平方后的二十日加权平均。

## 推荐实施顺序

1. 完成分类一的 12 个因子，注册因子数达到 161。
2. 完成分类二的 17 个因子，注册因子数达到 178。
3. 统一分类三的公式解释并完成 10 个因子，注册因子数达到 188。
4. 新增 `PROD` 并完成 `Alpha157`，注册因子数达到 189。
5. 确认基准公式并完成 `Alpha181`，注册因子数达到 190。
6. 准备 Fama-French 数据、实现 `REGRESI`，最后完成 `Alpha30`。

## 横截面因子实现规则

剩余 40 个横截面因子都应遵守：

1. 公式中的 `RANK` 必须按 `trade_date` 对股票横截面排名。
2. `DELAY`、`SUM`、`MEAN`、`STD`、`TSRANK`、`TSMAX`、
   `TSMIN` 和 `DECAYLINEAR` 必须按 `trade_symbol` 分别计算。
3. `CORR` 和 `COVIANCE` 必须按股票分别执行滚动计算。
4. 不能直接对拼接后的完整 Panel 使用普通 rolling，否则窗口可能跨股票。
5. 每完成一个横截面因子，都要同步加入 `PANEL_FACTORS` 和 `FACTORS`。

## 全部完成的验收标准

- `FACTORS` 包含 191 个因子。
- `PANEL_FACTORS` 包含全部 63 个横截面因子。
- 所有因子能够在当前 20 只股票数据上运行且保持原索引。
- 因子结果不存在整列全空或意外无穷值。
- 横截面因子每天只对非空信号进行排名。
- 批量导出结果与 `FACTORS` 注册表数量一致。
- 公式歧义、`RANK` 输出尺度、`STD` 自由度和缺失值规则有明确记录。
