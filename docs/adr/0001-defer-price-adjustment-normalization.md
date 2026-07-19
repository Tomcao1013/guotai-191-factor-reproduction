---
status: accepted
---

# Defer Price Adjustment Normalization

The first multi-stock factor-distribution milestone will continue using the
current AKShare qfq price input so that data-shape and export work can proceed
without changing the existing factor functions. Before implementing factors
that depend on VWAP or AMOUNT, or before any historical backtest, the market
data layer must preserve unadjusted OHLCVA, normalize volume units, store an
unambiguous price multiplier, and regenerate affected factor datasets.

## Consequences

Factor files produced before this work is completed are exploratory qfq
snapshots, not a strict point-in-time reproduction. They may need to be
regenerated later and must not be used to validate VWAP-dependent factors.
