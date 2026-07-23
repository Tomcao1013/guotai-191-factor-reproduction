import pandas as pd
import numpy as np


def DELTA(series: pd.Series, periods: int = 1) -> pd.Series:
    return series - series.shift(periods)


def SUM(series: pd.Series, periods: int = 1) -> pd.Series:
    return series.rolling(window=periods, min_periods=periods).sum()


def SUMAC(
    series: pd.Series,
    periods: int | None = None,
) -> pd.Series:
    """Return a cumulative sum, or a rolling sum when a window is given."""
    if periods is None:
        return series.cumsum()
    if periods <= 0:
        raise ValueError("SUMAC periods must be positive")

    return series.rolling(
        window=periods,
        min_periods=periods,
    ).sum()


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


def RANK(
    series: pd.Series,
    groups: pd.Series | None = None,
) -> pd.Series:
    if groups is None:
        return series.rank(
            method="average",
            ascending=True,
            pct=True,
        )

    if not series.index.equals(groups.index):
        raise ValueError("RANK inputs must have the same index")

    return series.groupby(
        groups,
        sort=False,
    ).rank(
        method="average",
        ascending=True,
        pct=True,
    )


def CORR(series_a: pd.Series,
         series_b: pd.Series,
         periods: int
        ) -> pd.Series:
    if periods < 2:
        raise ValueError("CORR periods must be at least 2")
    if not series_a.index.equals(series_b.index):
        raise ValueError("CORR inputs must have the same index")

    correlation = series_a.rolling(
        window=periods,
        min_periods=periods,
    ).corr(series_b)
    return correlation.replace(
        [float("inf"), float("-inf")],
        float("nan"),
    )


def SEQUENCE(periods: int) -> np.ndarray:
    if periods <= 0:
        raise ValueError("SEQUENCE periods must be positive")

    return np.arange(1, periods + 1, dtype=float)


def REGBETA(
    series_a: pd.Series,
    series_b: pd.Series | np.ndarray,
    periods: int | None = None,
) -> pd.Series:
    if isinstance(series_b, pd.Series):
        if periods is None:
            raise ValueError(
                "REGBETA periods is required for two aligned Series"
            )
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
        variance = variance.mask(
            variance.abs() <= np.finfo(float).eps
        )

        return covariance / variance

    sequence = np.asarray(series_b, dtype=float)
    if sequence.ndim != 1:
        raise ValueError("REGBETA sequence must be one-dimensional")

    inferred_periods = len(sequence)
    if periods is None:
        periods = inferred_periods
    if periods < 2:
        raise ValueError("REGBETA's periods value must be at least 2")
    if inferred_periods != periods:
        raise ValueError(
            "REGBETA sequence length must equal periods"
        )

    centered_sequence = sequence - sequence.mean()
    denominator = np.dot(centered_sequence, centered_sequence)
    if denominator <= np.finfo(float).eps:
        return pd.Series(np.nan, index=series_a.index)

    return series_a.rolling(
        window=periods,
        min_periods=periods,
    ).apply(
        lambda values: np.dot(
            values - values.mean(),
            centered_sequence,
        ) / denominator,
        raw=True,
    )


def SMA(
    series: pd.Series,
    periods: int,
    weight: int,
    ) -> pd.Series:
    if periods <= 0 or weight <= 0 or weight > periods:
        raise ValueError("0 < weight <= periods")
    alpha = weight / periods

    return series.ewm(alpha=alpha, adjust=False, min_periods=1).mean()


def WMA(series: pd.Series, periods: int) -> pd.Series:
    if periods <= 0:
        raise ValueError("WMA periods must be positive")

    weights = np.power(
        0.9,
        np.arange(periods - 1, -1, -1, dtype=float),
    )
    weights = weights / weights.sum()

    return series.rolling(
        window=periods,
        min_periods=periods,
    ).apply(
        lambda values: np.dot(values, weights),
        raw=True,
    )


def DECAYLINEAR(series: pd.Series, periods: int) -> pd.Series:
    if periods <= 0:
        raise ValueError("DECAYLINEAR periods must be positive")

    weights = np.arange(1, periods + 1, dtype=float)
    weights = weights / weights.sum()

    return series.rolling(
        window=periods,
        min_periods=periods,
    ).apply(
        lambda values: np.dot(values, weights),
        raw=True,
    )


def STD(series: pd.Series, periods: int = 1) -> pd.Series:
    return series.rolling(
        window=periods,
        min_periods=periods,
    ).std(ddof=1)


def COVIANCE(
    series_a: pd.Series,
    series_b: pd.Series,
    periods: int,
) -> pd.Series:
    if periods < 2:
        raise ValueError("COVIANCE periods must be at least 2")
    if not series_a.index.equals(series_b.index):
        raise ValueError("COVIANCE inputs must have the same index")

    return series_a.rolling(
        window=periods,
        min_periods=periods,
    ).cov(series_b)


def LOG(series: pd.Series) -> pd.Series:
    return np.log(series.where(series > 0))


def MEAN(series: pd.Series, periods: int = 1) -> pd.Series:
    return series.rolling(window=periods, min_periods=periods).mean()


def COUNT(series: pd.Series, periods: int = 1) -> pd.Series:
    return series.rolling(window=periods, min_periods=periods).sum()


def SUMIF(
    series: pd.Series,
    periods: int,
    condition: pd.Series,
) -> pd.Series:
    if not series.index.equals(condition.index):
        raise ValueError("SUMIF inputs must have the same index")

    selected = series.where(condition.fillna(False), 0.0)
    return selected.rolling(
        window=periods,
        min_periods=periods,
    ).sum()


def FILTER(
    series: pd.Series,
    condition: pd.Series,
) -> pd.Series:
    if not series.index.equals(condition.index):
        raise ValueError("FILTER inputs must have the same index")

    return series.loc[condition.fillna(False)]


def SIGN(series: pd.Series) -> pd.Series:
    return pd.Series(
        np.sign(series),
        index=series.index,
        name=series.name,
    )


def _extreme_day(
    series: pd.Series,
    periods: int,
    find_maximum: bool,
) -> pd.Series:
    if periods <= 0:
        raise ValueError("extreme-day periods must be positive")

    def distance(values: np.ndarray) -> float:
        target = np.max(values) if find_maximum else np.min(values)
        positions = np.flatnonzero(values == target)
        most_recent_position = positions[-1]
        return float(len(values) - 1 - most_recent_position)

    return series.rolling(
        window=periods,
        min_periods=periods,
    ).apply(distance, raw=True)


def HIGHDAY(series: pd.Series, periods: int) -> pd.Series:
    return _extreme_day(series, periods, find_maximum=True)


def LOWDAY(series: pd.Series, periods: int) -> pd.Series:
    return _extreme_day(series, periods, find_maximum=False)


def MAX(value1: pd.Series | int | float, value2: pd.Series | int | float,) -> pd.Series:
    return np.maximum(value1, value2)


def MIN(value1: pd.Series | int | float, value2: pd.Series | int | float,) -> pd.Series:
    return np.minimum(value1, value2)


def RET(close: pd.Series) -> pd.Series:
    previous_close = DELAY(close, periods=1)
    return close / previous_close - 1


def TR(
    high: pd.Series,
    low: pd.Series,
    close: pd.Series,
) -> pd.Series:
    previous_close = DELAY(close, 1)
    return MAX(
        MAX(
            high - low,
            ABS(high - previous_close),
        ),
        ABS(low - previous_close),
    )


def HD(high: pd.Series) -> pd.Series:
    return high - DELAY(high, 1)


def LD(low: pd.Series) -> pd.Series:
    return DELAY(low, 1) - low


def _require_panel_columns(data: pd.DataFrame) -> None:
    required_columns = {"trade_date", "trade_symbol"}
    missing_columns = required_columns - set(data.columns)
    if missing_columns:
        raise ValueError(
            "Cross-sectional factors require columns: "
            + ", ".join(sorted(missing_columns))
        )


def _by_symbol(
    data: pd.DataFrame,
    series: pd.Series,
    transform,
) -> pd.Series:
    _require_panel_columns(data)
    return series.groupby(
        data["trade_symbol"],
        sort=False,
    ).transform(transform)


def _by_symbol_pair(
    data: pd.DataFrame,
    series_a: pd.Series,
    series_b: pd.Series,
    transform,
) -> pd.Series:
    _require_panel_columns(data)
    result = pd.Series(np.nan, index=data.index, dtype=float)

    for _, group_index in data.groupby(
        "trade_symbol",
        sort=False,
    ).groups.items():
        result.loc[group_index] = transform(
            series_a.loc[group_index],
            series_b.loc[group_index],
        )

    return result
