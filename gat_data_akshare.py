from pathlib import Path

import akshare as ak
import pandas as pd

from research_stocks import RESEARCH_UNIVERSE


PROJECT_ROOT = Path(__file__).resolve().parent


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

        # 1. 获取前复权价格
        qfq_data = ak.stock_zh_a_daily(
            symbol=symbol,
            start_date=start_date.strftime("%Y%m%d"),
            end_date=end_date.strftime("%Y%m%d"),
            adjust="qfq",
        )

        # 2. 获取未复权价格和真实成交数据
        raw_data = ak.stock_zh_a_daily(
            symbol=symbol,
            start_date=start_date.strftime("%Y%m%d"),
            end_date=end_date.strftime("%Y%m%d"),
            adjust="",
        )

        qfq_data = qfq_data.rename(columns={"date": "trade_date"})

        raw_data = raw_data.rename(
            columns={
                "date": "trade_date",
                "close": "close_raw",
                "volume": "volume_raw",
                "amount": "amount_raw",
            }
        )

        qfq_data["trade_date"] = pd.to_datetime(qfq_data["trade_date"])
        raw_data["trade_date"] = pd.to_datetime(raw_data["trade_date"])

        # 3. 按交易日合并
        data = qfq_data.merge(
            raw_data[
                [
                    "trade_date",
                    "close_raw",
                    "volume_raw",
                    "amount_raw",
                ]
            ],
            on="trade_date",
            how="inner",
        )

        data["trade_symbol"] = trade_symbol

        # 4. 未复权 VWAP：成交额 / 成交股数
        data["vwap_raw"] = data["amount_raw"].div(
            data["volume_raw"].where(data["volume_raw"] > 0)
        )

        # 5. 计算每日前复权比例
        data["qfq_ratio"] = data["close"].div(
            data["close_raw"].where(data["close_raw"] != 0)
        )

        # 6. 将 VWAP 调整到前复权价格尺度
        data["vwap"] = data["vwap_raw"] * data["qfq_ratio"]

        # 使用真实成交量和成交额
        data["volume"] = data["volume_raw"]
        data["amount"] = data["amount_raw"]

        data = (
            data[
                [
                    "trade_date",
                    "trade_symbol",
                    "open",
                    "high",
                    "low",
                    "close",
                    "vwap",
                    "volume",
                    "amount",
                ]
            ]
            .replace([float("inf"), float("-inf")], pd.NA)
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
