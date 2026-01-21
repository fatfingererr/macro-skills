<overview>
本文件定義技能使用的所有 FRED 數據系列代碼、頻率、轉換方式，以及數據抓取的技術細節。
</overview>

<fred_series>

<category name="labor_market">
**勞動市場指標**

| Series ID | 名稱                         | 頻率 | 單位 | 轉換  | 說明          |
|-----------|------------------------------|------|------|-------|---------------|
| UNRATE    | Unemployment Rate            | 月   | %    | level | 失業率（U-3） |
| UNEMPLOY  | Unemployed Level             | 月   | 千人 | level | 失業人數      |
| JTSJOL    | Job Openings: Total Nonfarm  | 月   | 千人 | level | JOLTS 職缺數  |
| ICSA      | Initial Claims               | 週   | 人   | 4w_ma | 初領失業救濟  |
| PAYEMS    | All Employees: Total Nonfarm | 月   | 千人 | yoy   | 非農就業      |
| U6RATE    | U-6 Unemployment Rate        | 月   | %    | level | 廣義失業率    |

**關鍵衍生指標**：
- **UJO** = UNEMPLOY / JTSJOL（失業/職缺比）
- **薩姆規則** = 3M_MA(UNRATE) - 12M_MIN(UNRATE)
- **ΔUR** = UNRATE(t) - UNRATE(t-6M)
</category>

<category name="gdp_macro">
**GDP 與宏觀指標**

| Series ID       | 名稱                   | 頻率 | 單位                  | 轉換  | 說明            |
|-----------------|------------------------|------|-----------------------|-------|-----------------|
| GDP             | Gross Domestic Product | 季   | 十億美元              | level | 名目 GDP        |
| GDPC1           | Real GDP               | 季   | 十億美元（2017 鏈價） | level | 實質 GDP        |
| A191RL1Q225SBEA | Real GDP Growth        | 季   | % SAAR                | level | 實質 GDP 成長率 |
| CPIAUCSL        | CPI: All Items         | 月   | 指數                  | yoy   | 消費者物價指數  |
| GDPDEF          | GDP Deflator           | 季   | 指數                  | yoy   | GDP 平減指數    |

**高 GDP 條件判定**：
- GDP_pctl > 70%（GDP 水平在 30 年歷史的 70 分位以上）
- 或 GDP_growth > 0（實質 GDP 仍正成長）
</category>

<category name="fiscal">
**財政指標**

| Series ID   | 名稱                                | 頻率 | 單位     | 轉換  | 說明                |
|-------------|-------------------------------------|------|----------|-------|---------------------|
| FYFSGDA188S | Federal Surplus/Deficit as % of GDP | 年   | %        | level | 聯邦盈餘/赤字占 GDP |
| FGEXPND     | Federal Government Expenditures     | 季   | 十億美元 | level | 聯邦支出            |
| FGRECPT     | Federal Government Receipts         | 季   | 十億美元 | level | 聯邦收入            |
| GFDEBTN     | Federal Debt: Total Public Debt     | 季   | 百萬美元 | level | 聯邦總債務          |
| GFDEGDQ188S | Federal Debt as % of GDP            | 季   | %        | level | 債務/GDP            |

**注意**：FYFSGDA188S 為負值時表示赤字（例如 -6.5 表示赤字占 GDP 6.5%）。
在分析中，我們通常取絕對值或乘以 -1 使赤字為正數。
</category>

<category name="financial_stress">
**金融壓力指標（用於 UST 風險分析）**

| Series ID    | 名稱                                      | 頻率 | 說明           |
|--------------|-------------------------------------------|------|----------------|
| BAMLC0A0CM   | ICE BofA US Corporate Master OAS          | 日   | 投資級信用利差 |
| BAMLH0A0HYM2 | ICE BofA US High Yield OAS                | 日   | 高收益債利差   |
| T10Y2Y       | 10Y-2Y Treasury Spread                    | 日   | 殖利率曲線     |
| DGS10        | 10-Year Treasury Rate                     | 日   | 10 年期殖利率  |
| VIXCLS       | VIX                                       | 日   | 波動率指數     |
| NFCI         | Chicago Fed National Financial Conditions | 週   | 金融壓力指數   |
</category>

</fred_series>

<data_fetching>

<method name="csv_endpoint">
**FRED CSV 端點（無需 API key）**

```python
import pandas as pd
from io import StringIO
import requests

def fetch_fred_csv(series_id: str, start_date: str = None) -> pd.Series:
    """
    從 FRED CSV 端點抓取數據（無需 API key）

    Parameters
    ----------
    series_id : str
        FRED 系列代碼
    start_date : str, optional
        起始日期 (YYYY-MM-DD)

    Returns
    -------
    pd.Series
        時間序列數據
    """
    url = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={series_id}"

    if start_date:
        url += f"&cosd={start_date}"

    response = requests.get(url, timeout=30)
    response.raise_for_status()

    df = pd.read_csv(StringIO(response.text), parse_dates=['DATE'], index_col='DATE')
    series = df[series_id].replace('.', pd.NA).astype(float)

    return series


def fetch_multiple_series(series_ids: list, years: int = 30) -> pd.DataFrame:
    """
    批量抓取多個 FRED 系列
    """
    from datetime import datetime, timedelta

    start_date = (datetime.now() - timedelta(days=years*365)).strftime('%Y-%m-%d')

    data = {}
    for sid in series_ids:
        try:
            data[sid] = fetch_fred_csv(sid, start_date)
            print(f"✓ {sid}")
        except Exception as e:
            print(f"✗ {sid}: {e}")

    return pd.DataFrame(data)
```
</method>

<method name="frequency_alignment">
**頻率對齊**

多數財政/GDP 數據為季頻，勞動數據為月頻。需要對齊處理：

```python
def align_to_quarterly(data: pd.DataFrame, method: str = 'quarter_end') -> pd.DataFrame:
    """
    將數據對齊到季度頻率

    Parameters
    ----------
    data : pd.DataFrame
        原始數據（可能包含不同頻率）
    method : str
        'quarter_end' - 取季末值
        'quarter_avg' - 取季度平均

    Returns
    -------
    pd.DataFrame
        季度頻率數據
    """
    if method == 'quarter_end':
        return data.resample('QE').last()
    elif method == 'quarter_avg':
        return data.resample('QE').mean()
    else:
        raise ValueError(f"Unknown method: {method}")
```
</method>

<method name="caching">
**快取策略**

建議使用本地快取減少重複請求：

```python
from pathlib import Path
import json
from datetime import datetime, timedelta

CACHE_DIR = Path('data/cache')
CACHE_MAX_AGE_HOURS = 12

def get_cached_data(series_id: str) -> pd.Series:
    """嘗試從快取讀取"""
    cache_file = CACHE_DIR / f"{series_id}.csv"

    if cache_file.exists():
        mtime = datetime.fromtimestamp(cache_file.stat().st_mtime)
        if datetime.now() - mtime < timedelta(hours=CACHE_MAX_AGE_HOURS):
            return pd.read_csv(cache_file, index_col=0, parse_dates=True).squeeze()

    return None

def save_to_cache(series_id: str, data: pd.Series):
    """保存到快取"""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    data.to_csv(CACHE_DIR / f"{series_id}.csv")
```
</method>

</data_fetching>

<data_quality>

<validation>
**數據驗證檢查**

抓取數據後應進行以下檢查：

1. **缺失值檢查**：
   ```python
   missing_pct = data.isna().sum() / len(data) * 100
   assert missing_pct < 10, f"Missing values too high: {missing_pct:.1f}%"
   ```

2. **時間範圍檢查**：
   ```python
   assert data.index.min().year <= start_year
   assert data.index.max() >= pd.Timestamp.now() - pd.Timedelta(days=90)
   ```

3. **數值範圍檢查**：
   ```python
   # 失業率應在 0-30% 之間
   assert 0 <= data['UNRATE'].min() and data['UNRATE'].max() <= 30
   # 赤字/GDP 應在 -30% 到 +10% 之間
   assert -30 <= data['FYFSGDA188S'].min() and data['FYFSGDA188S'].max() <= 10
   ```
</validation>

<known_issues>
**已知問題**

| 系列        | 問題              | 處理方式               |
|-------------|-------------------|------------------------|
| JTSJOL      | 2000 年以前無數據 | UJO 分析從 2001 年開始 |
| FYFSGDA188S | 年頻數據          | 需轉換或使用季頻替代   |
| ICSA        | 週頻高頻噪音      | 使用 4 週移動平均      |
</known_issues>

</data_quality>

<update_frequency>
**數據更新時間表**

| 數據類型           | 發布頻率 | 發布延遲 | 最佳抓取時機     |
|--------------------|----------|----------|------------------|
| 失業率 (UNRATE)    | 月       | ~5 天    | 每月第一個週五後 |
| JOLTS (JTSJOL)     | 月       | ~2 個月  | 每月中旬         |
| GDP                | 季       | ~1 個月  | 季末月底         |
| 財政 (FYFSGDA188S) | 年       | ~3 個月  | 年初更新         |

**建議**：每天最多抓取一次，快取有效期設為 12 小時。
</update_frequency>
