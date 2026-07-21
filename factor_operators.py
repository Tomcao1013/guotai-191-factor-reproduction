import pandas as pd
import numpy as np

def DELTA(series: pd.Series, periods: int = 1) -> pd.Series:
    return series - series.shift(periods)

def SUM(series: pd.Series, periods: int = 1) -> pd.Series:
    return series.rolling(window=periods, min_periods=periods).sum()

def DELAY(series: pd.Series, periods: int = 1) -> pd.Series:
    return series.shift(periods)

def ABS(series: pd.Series) -> pd.Series:
    return series.abs()

def TSMAX(series: pd.Series, periods: int = 1) -> pd.Series:
    return series.rolling(window=periods).max()

def TSMIN(series: pd.Series, periods: int = 1) -> pd.Series:
    return series.rolling(window=periods).min()

def TSRANK(series: pd.Series, periods: int = 1) -> pd.Series:
    return series.rolling(window=periods).rank(method='average', ascending=True, pct=False)

def CORR(series_a: pd.Series,
         series_b: pd.Series,
         periods: int
        ) -> pd.Series:
    if periods < 2:
        raise ValueError("CORR's periods value must be greater than 2")
    correlation = series_a.rolling(
        window=periods,
        min_periods=periods,
    ).corr(series_b)
    return correlation.replace(
        [float("inf"), float("-inf")],
        float("nan"),
    )

def REGBETA(
    series_a: pd.Series, series_b: pd.Series, periods: int) -> pd.Series:
    if periods < 2:
        raise ValueError("REGBETA's periods value must be at least 2")
    if not series_a.index.equals(series_b.index):
        raise ValueError("REGBETA inputs must have the same index")

    rolling_a = series_a.rolling(
        window=periods,
        min_periods=periods,
    )
    rolling_b = series_b.rolling(
        window=periods,
        min_periods=periods,
    )

    covariance = rolling_a.cov(series_b)
    variance = rolling_b.var(ddof=1)
    variance = variance.mask(variance.abs() <= np.finfo(float).eps)

    return covariance / variance

def SMA(
    series: pd.Series,
    periods: int,
    weight: int,
    ) -> pd.Series:
    if periods <= 0 or weight > periods:
        raise ValueError("0 < weight <= periods")
    alpha = weight / periods

    return series.ewm(alpha=alpha, adjust=False, min_periods=1).mean()

def STD(series: pd.Series, periods: int = 1) -> pd.Series:
    return series.rolling(
        window=periods,
        min_periods=periods,
    ).std(ddof=1)

def MEAN(series: pd.Series, periods: int = 1) -> pd.Series:
    return series.rolling(window=periods, min_periods=periods).mean()

def COUNT(series: pd.Series, periods: int = 1) -> pd.Series:
    return series.rolling(window=periods, min_periods=periods).sum()

def MAX(value1: pd.Series | int | float, value2: pd.Series | int | float,) -> pd.Series:
    return np.maximum(value1, value2)

def MIN(value1: pd.Series | int | float, value2: pd.Series | int | float,) -> pd.Series:
    return np.minimum(value1, value2)

def RET(close: pd.Series) -> pd.Series:
    previous_close = DELAY(close, periods=1)
    return close / previous_close - 1
