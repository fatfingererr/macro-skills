# 銅產量數據來源說明

## 數據分層策略

| Tier | 特性 | 來源 | 用途 | 成本 |
|------|------|------|------|------|
| 0 | 免費、穩定、長序列 | OWID, USGS | 主幹 baseline | 免費 |
| 1 | 免費但分散 | 公司年報 | mine-level 錨點 | 免費 |
| 2 | 付費、更即時 | S&P Global, Wood Mac | 精度驗證 | 付費 |
| 3 | 事件驅動 | GDELT, 新聞 | 地緣風險指數 | 免費 |

---

## Tier 0: 主要數據來源

### OWID Minerals Explorer

**優點**：
- 免費開放取用
- 長序列數據（1900年起）
- 一致的統計口徑
- GitHub 直接下載

**數據內容**：
- Copper mine production by country（銅礦場產量）
- 單位：tonnes of copper content（銅金屬含量）

**URL**：
```
https://ourworldindata.org/minerals
https://github.com/owid/owid-datasets/tree/master/datasets/Copper%20mine%20production%20(USGS%20%26%20BGS)
```

**直接下載 CSV**：
```
https://raw.githubusercontent.com/owid/owid-datasets/master/datasets/Copper%20mine%20production%20(USGS%20%26%20BGS)/Copper%20mine%20production%20(USGS%20%26%20BGS).csv
```

**欄位說明**：
| 欄位 | 說明 |
|------|------|
| Entity | 國家名稱（含 "World"） |
| Year | 年份 |
| Copper mine production (USGS & BGS) | 產量（公噸銅金屬含量） |

---

### USGS Mineral Commodity Summaries

**優點**：
- 美國官方統計機構
- 權威性高
- 包含儲量、進出口等補充資訊

**數據內容**：
- Mine production by country（最新 2 年）
- Reserves by country（儲量）
- 全球供需摘要

**URL**：
```
https://www.usgs.gov/centers/national-minerals-information-center/copper-statistics-and-information
```

**下載方式**：
1. 年度 Mineral Commodity Summaries（PDF）
2. Historical Statistics for Mineral Commodities（Excel）

**歷史數據**：
```
https://www.usgs.gov/centers/national-minerals-information-center/historical-statistics-mineral-and-material-commodities
```

---

## Tier 1: 公司年報

用於 mine-level 數據補充。

### 主要銅礦公司

| 公司 | 主要資產 | 年報來源 |
|------|----------|----------|
| Codelco | Chuquicamata, El Teniente | codelco.com |
| BHP | Escondida (與 Rio Tinto 合資) | bhp.com |
| Freeport-McMoRan | Grasberg, Cerro Verde | fcx.com |
| Southern Copper | Buenavista, IMMSA | southerncoppercorp.com |
| Glencore | Katanga, Collahuasi | glencore.com |
| First Quantum | Cobre Panama, Kansanshi | first-quantum.com |

---

## Tier 2: 付費數據

### S&P Global Market Intelligence

- 礦山級產量與成本數據
- 項目進度追蹤
- 品位與產能數據

### Wood Mackenzie

- 供需預測
- 成本曲線分析
- 項目評估

---

## Tier 3: 地緣風險數據

### GDELT (Global Database of Events, Language, and Tone)

**用途**：計算地緣風險指數

**優點**：
- 免費開放
- 全球覆蓋
- 即時更新

**API**：
```
https://api.gdeltproject.org/api/v2/doc/doc
```

**篩選關鍵字**（銅礦相關）：
- 衝突類：strike, protest, conflict, violence
- 政策類：mining tax, export ban, nationalization
- 環境類：water, pollution, environmental

---

## 口徑說明

### 本 Skill 使用口徑

| 口徑 | 說明 | 使用 |
|------|------|------|
| **mined_production** | 礦場產量（銅金屬含量） | ✅ 主要 |
| refined_production | 精煉產量 | ❌ 不使用 |
| reserves | 儲量 | ⚠️ 參考用 |
| ore_grades | 礦石品位 | ⚠️ 間接代理 |

### 口徑轉換警告

⚠️ **不同口徑不可直接比較**：

- **礦石噸數 vs 銅金屬含量**：
  - 礦石品位 0.5-1.5%
  - 1 噸銅金屬 ≈ 67-200 噸礦石

- **礦場產量 vs 精煉產量**：
  - 精煉產量包含二次銅（廢銅回收）
  - 通常精煉產量 > 礦場產量

---

## 數據更新頻率

| 來源 | 更新頻率 | 延遲 |
|------|----------|------|
| OWID | 年度 | T+6-12 個月 |
| USGS | 年度 | T+2-3 個月 |
| 公司年報 | 季度/年度 | T+1-2 個月 |
| GDELT | 即時 | T+1 天 |

---

## 快取策略

```python
CACHE_TTL = {
    "owid": 7,      # 7 天
    "usgs": 30,     # 30 天（年度更新）
    "gdelt": 1,     # 1 天（即時數據）
    "company": 90   # 90 天（季報週期）
}
```
