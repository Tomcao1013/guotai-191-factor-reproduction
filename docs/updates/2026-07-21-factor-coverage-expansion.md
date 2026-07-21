# 66 因子覆盖扩展

日期：2026-07-21（Asia/Shanghai）

## 本次更新

- 已注册的可批量导出因子从 20 个扩展到 66 个。
- 新增注册：`Alpha18`、`Alpha24`、`Alpha34`、`Alpha47`、`Alpha57`、`Alpha58`、
  `Alpha59`、`Alpha63`、`Alpha65`、`Alpha66`、`Alpha67`、`Alpha68`、`Alpha71`、
  `Alpha72`、`Alpha79`、`Alpha81`、`Alpha82`、`Alpha85`、`Alpha88`、`Alpha89`、
  `Alpha93`、`Alpha96`、`Alpha102`、`Alpha106`、`Alpha109`、`Alpha110`、`Alpha111`、
  `Alpha118`、`Alpha126`、`Alpha134`、`Alpha135`、`Alpha139`、`Alpha145`、
  `Alpha150`、`Alpha151`、`Alpha152`、`Alpha153`、`Alpha155`、`Alpha158`、`Alpha161`、
  `Alpha169`、`Alpha171`、`Alpha175`、`Alpha178`、`Alpha188`、`Alpha189`。
- 增加 `ABS`、`MAX`、`MIN` 算子，支持新增公式的时间序列计算。
- 新增 `factor_formula.md`，集中保存因子公式参考。
- 用当前实现重新生成全部 66 份因子长表，每份均为 24,173 条观测。

## 运行方式

```bash
python run_factors.py
```

脚本读取 `data/price/` 下的 20 份行情 CSV，并按每因子一文件的方式写入
`data/factor/{FactorName}.csv`。

## 验证

- `python3 -m pytest -q`：28 passed。
- 已逐项复算 66 份因子文件，确认其字段、排序、联合键唯一性和数值均与当前代码及行情快照一致。
- 已确认 66 个注册因子均没有占位 `pass` 实现。

## 当前边界

- `Alpha19`、`Alpha38`、`Alpha52`、`Alpha70`、`Alpha76`、`Alpha94`、`Alpha95`、`Alpha97`、`Alpha100`、`Alpha103`、`Alpha117`、`Alpha122`、`Alpha129`、`Alpha132`、`Alpha133`、`Alpha162`、`Alpha167`、`Alpha173`、`Alpha177`、`Alpha187` 仅保留公式占位，尚未注册到批量导出流程。
- 因子文件仍未补齐“日期并集 x 股票池”的完整观测网格。
- 当前使用探索性的 `qfq` 行情快照，尚非严格的 point-in-time 复现。
- 其余国泰 191 因子和更全面的数值基准测试仍在后续计划中。
