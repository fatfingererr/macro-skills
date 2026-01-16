# 資料來源說明

## 主要資料來源

### Yahoo Finance (yfinance)

**免費、無需 API key**

```bash
pip install yfinance
```

#### 期貨代碼

| 商品   | 代碼       | 交易所         | 說明                 |
|--------|------------|----------------|----------------------|
| 白銀   | SI=F       | COMEX          | Silver Futures       |
| 鈀金   | PA=F       | NYMEX          | Palladium Futures    |
| 黃金   | GC=F       | COMEX          | Gold Futures         |
| 鉑金   | PL=F       | NYMEX          | Platinum Futures     |

#### 現貨/外匯代碼

| 商品   | 代碼       | 說明                 |
|--------|------------|----------------------|
| 白銀   | XAGUSD=X   | Silver Spot          |
| 黃金   | XAUUSD=X   | Gold Spot            |

#### 使用範例

```python
import yfinance as yf

# 取得白銀期貨數據
silver = yf.Ticker("SI=F")
silver_data = silver.history(period="2y", interval="1h")

# 取得鈀金期貨數據
palladium = yf.Ticker("PA=F")
palladium_data = palladium.history(period="2y", interval="1h")
```

#### 數據可用性

| 時間尺度 | 可用歷史 | 說明                 |
|----------|----------|----------------------|
| 1m       | 7 天     | 分鐘級數據限制       |
| 5m       | 60 天    |                      |
| 1h       | 730 天   | 約 2 年              |
| 1d       | 無限制   | 完整歷史             |

#### 注意事項

- yfinance 是非官方 API，可能有延遲或中斷
- 期貨數據為連續合約（front month roll）
- 小時數據可能有空缺（非交易時段）

---

## 替代資料來源

### Stooq

**免費 CSV 下載**

網址：https://stooq.com

```python
import pandas as pd

# 白銀
silver_url = "https://stooq.com/q/d/l/?s=xagusd&i=h"
silver_data = pd.read_csv(silver_url)
```

### Polygon.io

**付費 API**

```python
from polygon import RESTClient

client = RESTClient("YOUR_API_KEY")
aggs = client.get_aggs("C:XAGUSD", 1, "hour", "2024-01-01", "2024-12-31")
```

### Twelve Data

**免費額度 + 付費**

```python
from twelvedata import TDClient

td = TDClient(apikey="YOUR_API_KEY")
ts = td.time_series(symbol="XAG/USD", interval="1h", outputsize=1000)
```

---

## 宏觀濾鏡資料來源

### FRED (Federal Reserve Economic Data)

**免費，需 API key**

```bash
pip install pandas-datareader
```

#### 常用序列

| 序列 ID   | 說明                     | 更新頻率 |
|-----------|--------------------------|----------|
| DTWEXBGS  | 美元指數（廣義）         | 每日     |
| DFII10    | 10 年期實質利率          | 每日     |
| VIXCLS    | VIX 指數                 | 每日     |
| BAMLH0A0HYM2 | 高收益債利差          | 每日     |

```python
import pandas_datareader.data as web

# 取得美元指數
dxy = web.DataReader("DTWEXBGS", "fred", start="2024-01-01", end="2026-01-01")

# 取得實質利率
real_yield = web.DataReader("DFII10", "fred", start="2024-01-01", end="2026-01-01")
```

---

## 數據對齊

### 時間戳對齊

兩個標的的時間戳可能不完全一致，需要對齊：

```python
def align_data(ag_df: pd.DataFrame, pd_df: pd.DataFrame) -> pd.DataFrame:
    """
    對齊白銀和鈀金的時間序列。

    使用交集時間戳，forward fill 處理缺失值。
    """
    # 重新索引到共同時間
    common_index = ag_df.index.intersection(pd_df.index)

    ag_aligned = ag_df.reindex(common_index).ffill()
    pd_aligned = pd_df.reindex(common_index).ffill()

    # 合併
    df = pd.DataFrame({
        'ag_close': ag_aligned['Close'],
        'pd_close': pd_aligned['Close'],
        'ag_high': ag_aligned['High'],
        'ag_low': ag_aligned['Low'],
        'pd_high': pd_aligned['High'],
        'pd_low': pd_aligned['Low'],
    })

    # 計算報酬
    df['ag_ret'] = np.log(df['ag_close']).diff()
    df['pd_ret'] = np.log(df['pd_close']).diff()

    return df.dropna()
```

### 時區處理

- Yahoo Finance 返回 UTC 或交易所當地時間
- 建議統一轉換為 UTC

```python
df.index = df.index.tz_convert('UTC')
```

---

## 數據品質檢查

### 缺失值

```python
def check_data_quality(df: pd.DataFrame) -> dict:
    """檢查數據品質。"""
    return {
        'total_rows': len(df),
        'missing_ag': df['ag_close'].isna().sum(),
        'missing_pd': df['pd_close'].isna().sum(),
        'date_range': (df.index.min(), df.index.max()),
        'trading_days': df.index.nunique(),
    }
```

### 異常值

```python
def detect_outliers(df: pd.DataFrame, threshold: float = 5.0) -> pd.DataFrame:
    """偵測報酬率異常值（超過 N 個標準差）。"""
    ag_zscore = (df['ag_ret'] - df['ag_ret'].mean()) / df['ag_ret'].std()
    pd_zscore = (df['pd_ret'] - df['pd_ret'].mean()) / df['pd_ret'].std()

    outliers = df[(ag_zscore.abs() > threshold) | (pd_zscore.abs() > threshold)]
    return outliers
```

---

## 建議配置

### 快速原型

```python
# 使用 yfinance，免費快速
config = {
    'silver_symbol': 'SI=F',
    'palladium_symbol': 'PA=F',
    'source': 'yfinance',
}
```

### 生產環境

```python
# 使用付費 API 確保穩定性
config = {
    'silver_symbol': 'SI=F',
    'palladium_symbol': 'PA=F',
    'source': 'polygon',
    'api_key': 'YOUR_KEY',
    'backup_source': 'yfinance',  # 備用
}
```

---

## 常見問題

### Q: yfinance 數據中斷怎麼辦？

A: 使用備用來源（Stooq）或緩存本地數據。

### Q: 期貨換月會影響分析嗎？

A: 連續合約已處理換月，但價格可能有跳空。建議使用報酬率而非絕對價格。

### Q: 鈀金數據可用性差怎麼辦？

A: 鈀金流動性較低，小時數據可能有空缺。可嘗試 4h 或 1d 數據。
