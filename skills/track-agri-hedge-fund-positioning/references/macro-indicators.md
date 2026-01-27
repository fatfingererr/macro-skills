# 宏觀指標定義與代理序列

## 1. 核心宏觀指標

### 1.1 美元指數（USD）

| 指標       | 來源          | 代碼/符號     | 頻率 | 說明                     |
|------------|---------------|---------------|------|--------------------------|
| DXY        | ICE           | DX=F          | 日   | 美元指數期貨             |
| UUP        | Yahoo Finance | UUP           | 日   | Invesco DB US Dollar ETF |
| DTWEXBGS   | FRED          | DTWEXBGS      | 日   | Trade Weighted USD Broad |
| DTWEXAFEGS | FRED          | DTWEXAFEGS    | 日   | Trade Weighted USD AFE   |

**推薦**：Yahoo Finance `UUP`（簡單）或 FRED `DTWEXBGS`（官方）

**訊號解讀**：
- 美元走弱（負報酬）→ 利於農產品價格
- 美元走強（正報酬）→ 壓抑農產品價格

### 1.2 原油（Crude Oil）

| 指標       | 來源          | 代碼/符號     | 頻率 | 說明                     |
|------------|---------------|---------------|------|--------------------------|
| WTI        | Yahoo Finance | CL=F          | 日   | WTI 原油期貨             |
| Brent      | Yahoo Finance | BZ=F          | 日   | Brent 原油期貨           |
| USO        | Yahoo Finance | USO           | 日   | 原油 ETF                 |
| DCOILWTICO | FRED          | DCOILWTICO    | 日   | WTI 原油現貨             |

**推薦**：Yahoo Finance `CL=F`

**訊號解讀**：
- 原油走強 → 風險偏好上升，能源成本傳導
- 原油走弱 → 需求疑慮，可能拖累商品

### 1.3 金屬（Metals）

| 指標       | 來源          | 代碼/符號     | 頻率 | 說明                     |
|------------|---------------|---------------|------|--------------------------|
| XME        | Yahoo Finance | XME           | 日   | SPDR S&P Metals & Mining |
| COPX       | Yahoo Finance | COPX          | 日   | 銅礦 ETF                 |
| GDX        | Yahoo Finance | GDX           | 日   | 黃金礦業 ETF             |
| HG=F       | Yahoo Finance | HG=F          | 日   | 銅期貨                   |

**推薦**：Yahoo Finance `XME`（廣義金屬）

**訊號解讀**：
- 金屬走強 → 循環需求樂觀，工業活動擴張
- 金屬走弱 → 需求轉弱，通縮疑慮

---

## 2. 輔助宏觀指標

### 2.1 商品綜合指數

| 指標       | 來源          | 代碼/符號     | 頻率 | 說明                     |
|------------|---------------|---------------|------|--------------------------|
| DBC        | Yahoo Finance | DBC           | 日   | Invesco DB Commodity ETF |
| GSG        | Yahoo Finance | GSG           | 日   | iShares S&P GSCI ETF     |
| DBA        | Yahoo Finance | DBA           | 日   | 農產品 ETF               |

### 2.2 風險偏好指標

| 指標       | 來源          | 代碼/符號     | 頻率 | 說明                     |
|------------|---------------|---------------|------|--------------------------|
| VIX        | FRED          | VIXCLS        | 日   | CBOE VIX                 |
| SPY        | Yahoo Finance | SPY           | 日   | S&P 500 ETF              |
| HYG        | Yahoo Finance | HYG           | 日   | 高收益債 ETF             |

### 2.3 利率指標

| 指標       | 來源          | 代碼/符號     | 頻率 | 說明                     |
|------------|---------------|---------------|------|--------------------------|
| DGS10      | FRED          | DGS10         | 日   | 10Y 國債殖利率           |
| DGS2       | FRED          | DGS2          | 日   | 2Y 國債殖利率            |
| T10Y2Y     | FRED          | T10Y2Y        | 日   | 10Y-2Y 利差              |

---

## 3. 宏觀順風評分計算

### 3.1 標準計算

```python
def calculate_macro_tailwind(macro_df, lookback_days=5):
    """
    計算宏觀順風評分

    Parameters:
    -----------
    macro_df : pd.DataFrame
        包含 usd, crude, metals 欄位的日頻資料
    lookback_days : int
        回看天數（預設 5 天）

    Returns:
    --------
    float
        宏觀順風評分 (0-1)
    """
    recent = macro_df.iloc[-lookback_days:]

    # 計算各指標報酬
    usd_ret = (recent['usd'].iloc[-1] / recent['usd'].iloc[0]) - 1
    crude_ret = (recent['crude'].iloc[-1] / recent['crude'].iloc[0]) - 1
    metals_ret = (recent['metals'].iloc[-1] / recent['metals'].iloc[0]) - 1

    # 判斷順風條件
    flags = [
        usd_ret < 0,      # 美元走弱
        crude_ret > 0,    # 原油走強
        metals_ret > 0    # 金屬走強
    ]

    return sum(flags) / len(flags)
```

### 3.2 加權計算（可選）

```python
def calculate_macro_tailwind_weighted(macro_df, lookback_days=5,
                                       weights=None):
    """加權版本的宏觀順風評分"""
    if weights is None:
        weights = {
            'usd': 0.4,     # 美元權重最高
            'crude': 0.35,  # 原油次之
            'metals': 0.25  # 金屬
        }

    recent = macro_df.iloc[-lookback_days:]

    scores = {}
    for indicator, weight in weights.items():
        ret = (recent[indicator].iloc[-1] / recent[indicator].iloc[0]) - 1

        if indicator == 'usd':
            # 美元反向
            scores[indicator] = (1 if ret < -0.005 else
                                0.5 if abs(ret) < 0.005 else
                                0) * weight
        else:
            # 其他正向
            scores[indicator] = (1 if ret > 0.005 else
                                0.5 if abs(ret) < 0.005 else
                                0) * weight

    return sum(scores.values())
```

---

## 4. 指標獲取範例

### 4.1 使用 Yahoo Finance

```python
import yfinance as yf
import pandas as pd

def fetch_macro_indicators(start_date, end_date):
    """抓取宏觀指標"""
    symbols = {
        'usd': 'UUP',
        'crude': 'CL=F',
        'metals': 'XME'
    }

    data = {}
    for name, symbol in symbols.items():
        try:
            df = yf.download(symbol, start=start_date, end=end_date,
                            progress=False)
            data[name] = df['Adj Close']
        except Exception as e:
            print(f"Error fetching {symbol}: {e}")
            data[name] = pd.Series(dtype=float)

    return pd.DataFrame(data)
```

### 4.2 使用 FRED

```python
import requests
from io import StringIO

def fetch_fred_series(series_id, start_date, end_date):
    """從 FRED 抓取序列"""
    url = "https://fred.stlouisfed.org/graph/fredgraph.csv"
    params = {
        "id": series_id,
        "cosd": start_date,
        "coed": end_date
    }

    response = requests.get(url, params=params, timeout=30)
    response.raise_for_status()

    df = pd.read_csv(StringIO(response.text))
    df.columns = ["DATE", series_id]
    df["DATE"] = pd.to_datetime(df["DATE"])
    df[series_id] = pd.to_numeric(
        df[series_id].replace(".", pd.NA),
        errors="coerce"
    )

    return df.dropna().set_index("DATE")[series_id]
```

---

## 5. 解讀指南

### 5.1 宏觀順風評分解讀

| 評分區間    | 意義           | 對農產品含義                 |
|-------------|----------------|------------------------------|
| 0.67 - 1.00 | 強順風         | 風險偏好高，商品需求樂觀     |
| 0.33 - 0.66 | 中性           | 方向不明確，謹慎對待         |
| 0.00 - 0.33 | 逆風           | 風險規避，商品承壓           |

### 5.2 與資金流的交叉解讀

| 資金流   | 宏觀順風 | 解讀                               |
|----------|----------|-----------------------------------|
| 流入     | 高       | 敘事一致，順勢做多                |
| 流入     | 低       | 資金流與宏觀背離，謹慎            |
| 流出     | 高       | 宏觀利好但資金離場，觀望          |
| 流出     | 低       | 敘事一致，避險情緒主導            |

---

## 6. 注意事項

1. **資料延遲**：部分 FRED 序列有 1 天延遲
2. **時區**：Yahoo Finance 使用美東時間
3. **假日**：需處理非交易日的缺值
4. **ETF 追蹤誤差**：ETF 價格可能與標的指數有差異
5. **季節性**：部分指標有明顯季節性（如農產品 ETF）
