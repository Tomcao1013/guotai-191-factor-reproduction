---
status: accepted
---

# Store One Long-Format Dataset per Factor

Each factor is stored in its own CSV across all dates and securities, while raw
market data remains one file per security. A factor row contains only
`trade_date`, `trade_symbol`, and `factor_value`; the first two columns form a
unique key, and the factor identity comes from the filename. This keeps the
existing single-security factor functions intact while making daily
cross-sectional distributions easy to construct.

## Consequences

Factor datasets must be sorted by `trade_date` and `trade_symbol`. Market data,
security names, returns, positions, and trading signals do not belong in these
files. Rows backed by available market data are retained even when the factor
cannot yet be calculated; `factor_value` is missing rather than zero, and the
row is not deleted. Daily distribution statistics are computed from the factor
dataset when needed and are not persisted as a second summary CSV.

The expected row set is the Cartesian product of the research universe and the
union of trading dates found across its market-data files. Missing market data,
suspensions, and unavailable calculations therefore produce rows with missing
`factor_value` instead of removing the date-security pair.

The first reproducible dataset snapshot uses the fixed inclusive research
window from `2021-07-19` through `2026-07-16`. Updating that window is a later
operation and is not tied to the date on which the scripts happen to run.

`trade_symbol` uses the canonical six-digit, exchange-qualified format such as
`000001.SZ` and `600030.SH`. Vendor-specific forms such as `sz000001` are
created only inside the market-data adapter.
