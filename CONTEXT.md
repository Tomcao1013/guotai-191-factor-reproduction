# GTJA 191 Factor Research

This context describes the market observations produced while reproducing the
GTJA 191 factors. The current stage covers factor data and distributions, not
portfolio construction or trade execution.

## Language

**Factor Observation**:
The value of one factor for one security on one trading date.
_Avoid_: Trade, order, position

**Expected Factor Observation**:
The date-and-security slot that should exist in a factor dataset because the
date belongs to the research calendar and the security belongs to the research
universe, even when its factor value is unavailable.
_Avoid_: Optional row, executed trade

**Trading Date**:
The exchange trading session to which the source market data and factor
observation belong; it does not imply that an order was executed.
_Avoid_: Execution date, order date

**Security Symbol**:
A market-qualified identifier for the security whose factor value is observed.
_Avoid_: Position, traded asset

**Market Data Observation**:
The daily market facts for one security on one trading date from which factor
observations are calculated.
_Avoid_: Factor observation, trading signal

**Factor Dataset**:
The collection of observations for one factor across trading dates and the
research universe.
_Avoid_: Price dataset, multi-factor wide table

**Unavailable Factor Value**:
An expected factor observation whose value cannot be calculated, commonly
because the required historical window is not yet available. It is represented
as missing data, never as zero or an omitted observation.
_Avoid_: Zero factor value, absent security

**Cross-Sectional Factor Distribution**:
All available security-level observations of one factor on the same trading
date.
_Avoid_: Time-series distribution, trading signal

**Research Universe**:
The fixed set of securities included when producing and inspecting factor
observations during the current research stage.
_Avoid_: Portfolio, holdings, recommended stocks

**Trading Signal**:
A later-stage decision input derived from factor observations; it is outside
the current project stage.
_Avoid_: Factor value
