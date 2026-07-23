# 190 因子覆盖扩展

日期：2026-07-23（Asia/Shanghai）

## 本次更新

- 当前 `FACTORS` 注册表从 149 个扩展至 190 个因子。
- 新增注册：`Alpha1`、`Alpha7`、`Alpha10`、`Alpha16`、`Alpha17`、`Alpha32`、
  `Alpha33`、`Alpha35`、`Alpha36`、`Alpha39`、`Alpha45`、`Alpha56`、`Alpha61`、
  `Alpha64`、`Alpha73`、`Alpha74`、`Alpha77`、`Alpha87`、`Alpha91`、`Alpha92`、
  `Alpha101`、`Alpha104`、`Alpha108`、`Alpha113`、`Alpha114`、`Alpha115`、
  `Alpha119`、`Alpha121`、`Alpha123`、`Alpha124`、`Alpha125`、`Alpha130`、
  `Alpha131`、`Alpha138`、`Alpha140`、`Alpha142`、`Alpha156`、`Alpha157`、
  `Alpha176`、`Alpha179`、`Alpha181`。
- 当前横截面因子数量为 63 个；其余注册因子按单股票时间序列计算。
- 新增 `PROD` 滚动累乘算子，支持 `Alpha157`。
- 当前工作区包含 190 份已注册因子的长表输出，每份字段为
  `trade_date,trade_symbol,factor_value`。

## 当前边界

- `Alpha30` 仍未实现，依赖 Fama-French 因子数据与 `REGRESI` 回归残差算子。
- 当前股票池固定为 20 只研究样本；横截面结果不等同于全 A 非 ST 股票池。
- 当前数据是探索性的 `qfq` 行情快照，尚非严格的 point-in-time 复现。
- 本次发布步骤仅同步现有工作区内容并更新文档，未改动任何因子实现或生成数据。

## 验证状态

- 已确认注册表包含 190 个因子，且每个注册因子均有对应 CSV 输出。
- 现有本地面板因子测试有 34 项失败，集中在横截面排名和按股票时序窗口的断言；
  本次按发布要求未对实现做修复。
