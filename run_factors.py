from pathlib import Path

import pandas as pd

from factor import FACTORS


PROJECT_ROOT = Path(__file__).resolve().parent
DATA_DIR = PROJECT_ROOT / "data" / "price"
FACTOR_DIR = PROJECT_ROOT / "data" / "factor"


def main() -> None:
    price_paths = sorted(DATA_DIR.glob("*_5y_daily.csv"))
    FACTOR_DIR.mkdir(parents=True, exist_ok=True)

    for factor_name, factor_func in FACTORS.items():
        all_results = []

        for price_path in price_paths:
            data = pd.read_csv(
                price_path,
                parse_dates=["trade_date"],
            )

            result = data[["trade_date", "trade_symbol"]].copy()
            result["factor_value"] = factor_func(data)
            all_results.append(result)

        combined_result = pd.concat(
            all_results,
            ignore_index=True,
        )
        combined_result = combined_result.sort_values(
            ["trade_date", "trade_symbol"]
        ).reset_index(drop=True)

        output_path = FACTOR_DIR / f"{factor_name}.csv"
        combined_result.to_csv(
            output_path,
            index=False,
            encoding="utf-8-sig",
            date_format="%Y-%m-%d",
        )

        print(f"{factor_name}: 已保存 {len(combined_result)} 行到 {output_path}")


if __name__ == "__main__":
    main()
