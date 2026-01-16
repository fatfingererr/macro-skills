# 集中度指標計算方法

<overview>
本文件詳細說明鎳供給集中度分析中使用的各項指標，
包括計算方法、解讀標準與應用場景。
</overview>

<metric name="country_share">
**Country Share（國家市佔率）**

<definition>
單一國家在全球供給中的佔比。

```
Country Share = Country_Production / Global_Production
```
</definition>

<calculation>
```python
def calculate_country_share(df, country, year):
    """
    計算特定國家的市場份額

    Args:
        df: 供給數據 DataFrame
        country: 目標國家
        year: 目標年份

    Returns:
        float: 市場份額 (0-1)
    """
    year_data = df[(df.year == year) & (df.supply_type == "mined")]

    country_prod = year_data[year_data.country == country].value.sum()
    global_prod = year_data.value.sum()

    if global_prod == 0:
        return 0

    return country_prod / global_prod
```
</calculation>

<interpretation>
| 份額 | 解讀 | 風險等級 |
|------|------|----------|
| < 10% | 小型供給國 | 低 |
| 10-30% | 重要供給國 | 中 |
| 30-50% | 主要供給國 | 高 |
| > 50% | 主導供給國 | 極高 |

**印尼案例：**
- 2020: ~31.5% → 主要供給國
- 2024: ~60.2% → **主導供給國**
</interpretation>
</metric>

<metric name="CRn">
**CR_n（n 國集中率）**

<definition>
前 n 個最大供給國/礦的累積市場份額。

```
CR_n = Σ(top_n_shares)
```

常用指標：
- **CR1**: 最大單一供給者份額
- **CR3**: 前三大累積份額
- **CR5**: 前五大累積份額
</definition>

<calculation>
```python
def calculate_CRn(df, year, n=5):
    """
    計算前 N 大供給者集中率

    Args:
        df: 供給數據 DataFrame
        year: 目標年份
        n: 前 N 大（預設 5）

    Returns:
        dict: CR1, CR3, CR5 等指標
    """
    year_data = df[(df.year == year) & (df.supply_type == "mined")]

    # 計算各國份額
    country_prod = year_data.groupby("country").value.sum()
    total_prod = country_prod.sum()
    shares = (country_prod / total_prod).sort_values(ascending=False)

    return {
        "CR1": shares.iloc[0] if len(shares) >= 1 else 0,
        "CR3": shares.head(3).sum() if len(shares) >= 3 else shares.sum(),
        "CR5": shares.head(5).sum() if len(shares) >= 5 else shares.sum(),
        f"CR{n}": shares.head(n).sum() if len(shares) >= n else shares.sum(),
        "top_countries": shares.head(n).to_dict()
    }
```
</calculation>

<interpretation>
| CR4 | 市場結構 | 說明 |
|-----|----------|------|
| < 40% | 競爭型 | 多元供給來源 |
| 40-60% | 鬆散寡佔 | 數個主要供給者 |
| 60-80% | 緊密寡佔 | 少數供給者主導 |
| > 80% | 高度集中 | 極少數供給者控制 |

**鎳市場 (2024 估計)：**
- CR1 (Indonesia): ~60%
- CR3 (Indonesia + Philippines + Russia): ~75%
- CR5: ~85%
- 判定：**高度集中市場**
</interpretation>
</metric>

<metric name="HHI">
**HHI（赫芬達爾-赫希曼指數）**

<definition>
衡量市場集中程度的標準指標，由各供給者市場份額的平方和構成。

```
HHI = Σ(share_i² × 10000)
```

其中 share_i 為第 i 個供給者的市場份額（0-1）。
乘以 10000 是為了得到 0-10000 的標準範圍。
</definition>

<calculation>
```python
def calculate_HHI(df, year, by="country"):
    """
    計算 HHI 指數

    Args:
        df: 供給數據 DataFrame
        year: 目標年份
        by: 分組依據 ("country" 或 "company")

    Returns:
        float: HHI 指數 (0-10000)
    """
    year_data = df[(df.year == year) & (df.supply_type == "mined")]

    # 計算份額
    group_prod = year_data.groupby(by).value.sum()
    total_prod = group_prod.sum()
    shares = group_prod / total_prod

    # HHI = Σ(share² × 10000)
    hhi = (shares ** 2).sum() * 10000

    return round(hhi, 0)
```
</calculation>

<interpretation>
**美國司法部 / FTC 標準：**

| HHI | 市場結構 | 說明 |
|-----|----------|------|
| < 1500 | 低集中 (Unconcentrated) | 競爭充分 |
| 1500-2500 | 中等集中 (Moderately Concentrated) | 需關注 |
| > 2500 | 高集中 (Highly Concentrated) | 壟斷風險 |

**計算範例：**

假設 2024 年各國份額：
- Indonesia: 60%
- Philippines: 10%
- Russia: 6%
- Canada: 5%
- Australia: 4%
- Others: 15%

```
HHI = (0.60² + 0.10² + 0.06² + 0.05² + 0.04² + 0.15²) × 10000
    = (0.36 + 0.01 + 0.0036 + 0.0025 + 0.0016 + 0.0225) × 10000
    = 0.4002 × 10000
    = 4002

結論：HHI ≈ 4000，屬於 **高集中市場**
```
</interpretation>

<special_cases>
**極端情況：**

| 情境 | HHI | 說明 |
|------|-----|------|
| 完全壟斷 (1家 100%) | 10000 | 理論最大值 |
| 雙寡頭 (2家各 50%) | 5000 | |
| 10家各 10% | 1000 | 低集中 |
| 100家各 1% | 100 | 高度分散 |
</special_cases>
</metric>

<metric name="policy_leverage">
**Policy Leverage（政策槓桿）**

<definition>
衡量政策變動對全球供給的潛在影響力。

```
Policy Leverage = Affected_Supply / Global_Supply
```
</definition>

<calculation>
```python
def calculate_policy_leverage(scenario, baseline):
    """
    計算政策槓桿

    Args:
        scenario: 政策情境 (含 cut_value, cut_type, target_country)
        baseline: 基準數據 (含 country_prod, global_prod)

    Returns:
        dict: 政策槓桿指標
    """
    # 確定受影響供給量
    if scenario.cut_type == "pct_country":
        affected = baseline.country_prod * scenario.cut_value
    elif scenario.cut_type == "pct_global":
        affected = baseline.global_prod * scenario.cut_value
    else:  # absolute
        affected = scenario.cut_value

    # 計算槓桿
    leverage = affected / baseline.global_prod

    return {
        "affected_supply_kt": affected / 1000,
        "global_hit_pct": leverage,
        "equivalent_days": leverage * 365,  # 相當於多少天全球消費
        "risk_level": classify_leverage(leverage)
    }

def classify_leverage(leverage):
    if leverage < 0.02:
        return "低風險"
    elif leverage < 0.05:
        return "中等風險"
    elif leverage < 0.10:
        return "高風險"
    else:
        return "極高風險"
```
</calculation>

<interpretation>
| 槓桿 (%) | 相當於 | 風險等級 | 說明 |
|----------|--------|----------|------|
| < 2% | < 1 週消費 | 低 | 市場可吸收 |
| 2-5% | 1-3 週消費 | 中 | 短期價格波動 |
| 5-10% | 3-5 週消費 | 高 | 顯著供給衝擊 |
| > 10% | > 5 週消費 | 極高 | 市場重大混亂 |

**印尼減產 20% 情境：**
- Indonesia share: 60%
- Cut: 20% of Indonesia = 12% of global
- Risk level: **極高風險**
</interpretation>
</metric>

<metric name="mine_CRn">
**Mine CR_n（礦區集中率）**

<definition>
前 n 個最大礦區/園區的累積產量份額。
用於評估「掐脖子」風險。

```
Mine_CR5 = Σ(top_5_mine_production) / Global_Production
```
</definition>

<calculation>
```python
def calculate_mine_CRn(mine_data, year, n=5):
    """
    計算礦區集中率

    Note: 需要 mine-level 數據（Tier 1）

    Args:
        mine_data: 礦區產量數據
        year: 目標年份
        n: 前 N 大礦區
    """
    year_data = mine_data[mine_data.year == year]

    mine_prod = year_data.groupby("mine_name").value.sum()
    total_prod = mine_prod.sum()
    shares = (mine_prod / total_prod).sort_values(ascending=False)

    return {
        f"Mine_CR{n}": shares.head(n).sum(),
        "top_mines": shares.head(n).to_dict(),
        "concentration_risk": "若 Mine_CR5 > 20%，單一事件可影響顯著供給"
    }
```
</calculation>

<data_availability>
**數據可用性說明：**

Mine-level 數據較難取得：
- 公開來源有限
- 口徑不一致（ore vs content）
- 需整合多家公司報告

**可用錨點：**
| 礦區/園區 | 估計產量 | 全球佔比 | 來源 |
|-----------|----------|----------|------|
| Weda Bay | ~X kt | ~X% | Eramet |
| IMIP | ~X kt | ~X% | 產業報告 |
| IWIP | ~X kt | ~X% | 產業報告 |
| PT Vale | ~X kt | ~X% | 公司財報 |
| Ramu | ~X kt | ~X% | 公司財報 |
</data_availability>
</metric>

<time_series_analysis>
**時序分析**

追蹤集中度指標隨時間的變化：

```python
def analyze_concentration_trend(df, years, metric="HHI"):
    """
    分析集中度趨勢

    Returns:
        DataFrame: 各年份集中度指標
    """
    results = []
    for year in years:
        if metric == "HHI":
            value = calculate_HHI(df, year)
        elif metric == "CR5":
            value = calculate_CRn(df, year, n=5)["CR5"]
        elif metric == "indonesia_share":
            value = calculate_country_share(df, "Indonesia", year)

        results.append({"year": year, "metric": metric, "value": value})

    return pd.DataFrame(results)
```

**印尼市佔趨勢（2015-2024）：**

| 年份 | Indonesia Share | HHI | 判讀 |
|------|-----------------|-----|------|
| 2015 | ~15% | ~1200 | 低集中 |
| 2018 | ~25% | ~1800 | 中等集中 |
| 2020 | ~31% | ~2100 | 中等集中 |
| 2022 | ~48% | ~3000 | 高集中 |
| 2024 | ~60% | ~4000 | 高集中 |

**趨勢觀察：**
- 印尼市佔 10 年間增長 4 倍
- HHI 從低集中跨入高集中
- 增長主要來自 NPI 產能擴張
</time_series_analysis>

<risk_matrix>
**集中度風險矩陣**

| | HHI < 1500 | HHI 1500-2500 | HHI > 2500 |
|---|---|---|---|
| **CR1 < 30%** | 低風險 | 中風險 | 中高風險 |
| **CR1 30-50%** | 中風險 | 中高風險 | 高風險 |
| **CR1 > 50%** | 中高風險 | 高風險 | **極高風險** |

**2024 鎳市場定位：**
- CR1 (Indonesia): ~60%
- HHI: ~4000
- **風險評級：極高**
</risk_matrix>
