from pathlib import Path

import akshare as ak
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parent
RESEARCH_UNIVERSE = (
    "sz000001",
    "sz000333",
    "sz000858",
    "sz002027",
    "sz002230",
    "sz002415",
    "sz002594",
    "sz002714",
    "sz300015",
    "sz300124",
    "sz300750",
    "sh600030",
    "sh600050",
    "sh600276",
    "sh600309",
    "sh600900",
    "sh601088",
    "sh601318",
    "sh601668",
    "sh688008",
)

def main() -> None:
    start_date = pd.Timestamp("2021-07-19")
    end_date = pd.Timestamp("2026-07-16")

    price_dir = PROJECT_ROOT / "data" / "price"
    price_dir.mkdir(parents=True, exist_ok=True)

    for symbol in RESEARCH_UNIVERSE:
        market = symbol[:2].upper()
        code = symbol[2:]
        trade_symbol = f"{code}.{market}"

        output_path = price_dir / f"{code}_{market}_5y_daily.csv"

        data = ak.stock_zh_a_daily(
            symbol=symbol,
            start_date=start_date.strftime("%Y%m%d"),
            end_date=end_date.strftime("%Y%m%d"),
            adjust="qfq",
        )

        data = data.rename(columns={"date": "trade_date"})
        data["trade_date"] = pd.to_datetime(data["trade_date"])
        data["trade_symbol"] = trade_symbol

        data = (
            data[
                [
                    "trade_date",
                    "trade_symbol",
                    "open",
                    "high",
                    "low",
                    "close",
                    "volume",
                    "amount",
                ]
            ]
            .dropna()
            .drop_duplicates(subset="trade_date")
            .sort_values("trade_date")
        )

        data.to_csv(
            output_path,
            index=False,
            encoding="utf-8-sig",
            date_format="%Y-%m-%d",
        )

        print(f"{trade_symbol}: 已保存 {len(data)} 行到 {output_path}")

if __name__ == "__main__":
    main()
