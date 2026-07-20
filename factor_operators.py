import pandas as pd


def DELTA(series: pd.Series, periods: int = 1) -> pd.Series:
    return series - series.shift(periods)

def SUM(series: pd.Series, periods: int = 1) -> pd.Series:
    return series.rolling(window=periods, min_periods=periods).sum()

def DELAY(series: pd.Series, periods: int = 1) -> pd.Series:
    return series.shift(periods)

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

def SMA(
    series: pd.Series,
    periods: int,
    weight: int,
    ) -> pd.Series:
    if periods <= 0 or weight > periods:
        raise ValueError("0 < weight <= periods")
    alpha = weight / periods

    return series.ewm(alpha=alpha, adjust=False, min_periods=1).mean()

def MEAN(series: pd.Series, periods: int = 1) -> pd.Series:
    return series.rolling(window=periods, min_periods=periods).mean()

def COUNT(series: pd.Series, periods: int = 1) -> pd.Series:
    return series.rolling(window=periods, min_periods=periods).sum()
