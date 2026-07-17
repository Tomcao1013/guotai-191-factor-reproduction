from datetime import date
from pathlib import Path

import akshare as ak
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parent

symbol = "sz000001"
output_path = PROJECT_ROOT / "data" / "price" / "000001_SZ_5y_daily.csv"

end_date = pd.Timestamp(date.today())
start_date = end_date - pd.DateOffset(years=5)

data = ak.stock_zh_a_daily(
    symbol=symbol,
    start_date=start_date.strftime("%Y%m%d"),
    end_date=end_date.strftime("%Y%m%d"),
    adjust="qfq",
)


data = data.rename(
    columns={
        "date": "Date",
        "open": "Open",
        "high": "High",
        "low": "Low",
        "close": "Close",
        "volume": "Volume",
    }
)

data["Date"] = pd.to_datetime(data["Date"])
data = (
    data[["Date", "Open", "High", "Low", "Close", "Volume"]]
    .dropna()
    .drop_duplicates(subset="Date")
    .sort_values("Date")
    .set_index("Date")
)

output_path.parent.mkdir(parents=True, exist_ok=True)

data.to_csv(
    output_path,
    encoding="utf-8-sig",
    date_format="%Y-%m-%d",
)

print(data.tail())
