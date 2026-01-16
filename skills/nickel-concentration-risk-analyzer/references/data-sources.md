# 數據來源詳細說明

<overview>
本文件詳細說明 nickel-concentration-risk-analyzer 使用的所有數據來源，
按可靠度分為 Tier 0-3，並說明每個來源的取得方式、口徑特性與潛在陷阱。
</overview>

<tier_0_sources>
**Tier 0: 免費、穩定、口徑一致（建議做 Baseline 主幹）**

<source name="USGS_MCS">
**USGS Mineral Commodity Summaries (Nickel)**

| 項目 | 說明 |
|------|------|
| URL | https://www.usgs.gov/centers/national-minerals-information-center/nickel-statistics-and-information |
| 更新頻率 | 每年 1 月/2 月 |
| 數據口徑 | Mine production (nickel content) |
| 單位 | Metric tons (鎳金屬含量) |
| 涵蓋範圍 | 全球 + 主要國家 |
| 取得方式 | PDF 下載 → 表格解析 |
| Confidence | 0.95 |

**關鍵表格：**
- Table: World Mine Production and Reserves
- Table: U.S. Salient Statistics

**解析注意事項：**
- PDF 表格可用 `camelot` 或 `tabula-py` 解析
- 數據單位為 metric tons（公噸），不是 short tons
- 部分國家數據標記 "e" (estimated) 或 "r" (revised)

**範例數據結構：**
```
Country         | 2020    | 2021    | 2022    | 2023    | 2024e
----------------|---------|---------|---------|---------|--------
Indonesia       | 760,000 | 1,000,000| 1,600,000| 1,900,000| 2,200,000
Philippines     | 320,000 | 370,000 | 330,000 | 400,000 | 400,000
Russia          | 250,000 | 250,000 | 220,000 | 220,000 | 210,000
...
World total     | 2,500,000| 2,800,000| 3,200,000| 3,500,000| 3,700,000
```
</source>

<source name="INSG">
**INSG (International Nickel Study Group)**

| 項目 | 說明 |
|------|------|
| URL | https://insg.org/ |
| 更新頻率 | 月報 + 年度報告 |
| 數據口徑 | Primary nickel production |
| 單位 | Thousand tonnes (kt) |
| 涵蓋範圍 | 全球供需平衡 |
| 取得方式 | 網頁/PDF（部分需會員） |
| Confidence | 0.90-0.95 |

**主要出版物：**
1. **Market Commentary** (月報): 供需摘要、價格趨勢
2. **World Nickel Factbook**: 年度綜合報告
3. **Statistics**: 歷史數據

**INSG vs USGS 口徑差異：**
- INSG "primary nickel" 可能包含部分 refined production
- USGS "mine production" 嚴格指礦場產量
- 差異通常在 5-10% 以內
</source>
</tier_0_sources>

<tier_1_sources>
**Tier 1: 免費但分散，需整合（Mine-level 最實用）**

<source name="Company_Reports">
**上市公司年報與財報**

| 公司 | Ticker | 主要產品 | 報告口徑 | URL |
|------|--------|----------|----------|-----|
| Nickel Industries | NIC.AX | NPI, nickel metal | Ni content | https://nickelindustries.com/investors/ |
| PT Vale Indonesia | INCO.JK | Nickel matte | Matte tonnes | https://www.vale.com/indonesia |
| Eramet (Weda Bay) | ERA.PA | Ore, ferronickel | Ore wet tonnes | https://www.eramet.com/en/investors |
| Antam | ANTM.JK | Ferronickel, ore | Various | https://www.antam.com/investor-relations |

**Nickel Industries (NIC.AX) 關鍵數據：**
```yaml
FY2024_guidance:
  NPI_production: ~100,000 t (產品噸)
  contained_nickel: ~13,000-15,000 t (按 ~13-15% Ni)
  RKEF_capacity: growing
```

**PT Vale Indonesia 關鍵數據：**
```yaml
quarterly_production:
  matte: ~X tonnes
  contained_nickel: ~75% Ni content
  notes: "Class 1 nickel, high purity"
```

**Eramet (Weda Bay) 關鍵數據：**
```yaml
sold_production:
  ore_wet_tonnes: ~X Mt
  grades: 1.5-1.8% Ni typical
  notes: "需轉換為 Ni content"
```

**⚠️ 公司報告陷阱：**
- 口徑常不一致（product tonnes vs contained Ni）
- 年度 vs 財年 vs 日曆年
- 速報 vs 審計數字可能微調
</source>

<source name="Industrial_Parks">
**印尼工業園區（IMIP/IWIP）**

| 園區 | 位置 | 主要產品 | 估計產能 |
|------|------|----------|----------|
| IMIP (Indonesia Morowali Industrial Park) | Central Sulawesi | NPI, stainless steel | ~X Mt NPI capacity |
| IWIP (Indonesia Weda Bay Industrial Park) | North Maluku | NPI, HPAL | ~X Mt capacity (growing) |

**⚠️ 產能 vs 產量：**
- 園區常報「設計產能」而非「實際產量」
- 新產線 ramp-up 期間產量可能只有產能的 60-80%
</source>
</tier_1_sources>

<tier_2_sources>
**Tier 2: 付費/半付費（更快、更完整）**

<source name="SP_Global">
**S&P Global Market Intelligence**

| 項目 | 說明 |
|------|------|
| URL | https://www.spglobal.com/marketintelligence/ |
| 訂閱費用 | 企業級訂閱 |
| 數據口徑 | Mine production (nickel content) |
| 關鍵數據點 | Indonesia 2024: 2.28 Mt, share 60.2% |
| Confidence | 0.90-0.95 |

**S&P 提供的關鍵錨點：**
```yaml
indonesia_2024:
  production: 2.28 Mt (2,280,000 tonnes)
  share: 60.2%  # up from 31.5% in 2020
  unit: nickel_content
  source: "S&P Global Market Intelligence"
```

**若無訂閱，可從以下管道取得 S&P 數據引用：**
- 投行研報（常引用 S&P）
- 新聞報導
- 公開演講/webinar

**⚠️ 注意：**
- 二手引用可能有轉述誤差
- 應盡可能追溯原始來源
</source>

<source name="Wood_Mackenzie">
**Wood Mackenzie**

| 項目 | 說明 |
|------|------|
| 訂閱費用 | 企業級訂閱 |
| 強項 | 長期供需預測、礦山級別數據 |
| Confidence | 0.85-0.90 |
</source>

<source name="Investment_Research">
**投行/券商研報**

| 來源 | 類型 | Confidence |
|------|------|------------|
| BTG Research | Sell-side | 0.70-0.80 |
| Morgan Stanley | Sell-side | 0.75-0.85 |
| Goldman Sachs | Sell-side | 0.75-0.85 |

**⚠️ 研報注意事項：**
- 常轉引 S&P/Wood Mac 數據，但可能不標來源
- 預測值 vs 實際值需區分
- "Our estimate" 需謹慎使用
</source>
</tier_2_sources>

<tier_3_sources>
**Tier 3: 政策/配額近期訊息**

<source name="Policy_News">
**印尼政策與配額**

| 資訊類型 | 來源 | 時效性 |
|----------|------|--------|
| RKAB 配額 | Indonesian government announcements | 即時 |
| 出口規則 | Ministry of Trade | 即時 |
| 減產傳聞 | Reuters, Bloomberg | 需驗證 |

**2026 RKAB 配額範例：**
```yaml
claim: "2026 ore quota 250 Mt vs 2025 target 379 Mt"
unit: ore_wet_tonnes  # ⚠️ 非 nickel content
source: various_news
confidence: 0.60
notes: "政策最終版本可能調整"
```

**⚠️ 政策資訊陷阱：**
- 配額常以 ore wet tonnes 計算
- 「目標」vs「實際配額」vs「執行量」差異大
- 政策可能在最後時刻調整
</source>
</tier_3_sources>

<data_source_priority>
**數據來源優先序**

```
建議流程：
1. Tier 0 (USGS + INSG) → 建立 baseline
2. Tier 1 (公司報告) → 補充 mine-level 細節
3. Tier 2 (S&P) → 驗證關鍵數據點
4. Tier 3 (政策新聞) → 情境分析輸入

若只有免費資源：
Tier 0 + Tier 1 已足夠做出穩健分析
```
</data_source_priority>

<url_registry>
**URL 清單**

| 來源 | URL |
|------|-----|
| USGS Nickel | https://www.usgs.gov/centers/national-minerals-information-center/nickel-statistics-and-information |
| USGS MCS 2025 | https://pubs.usgs.gov/periodicals/mcs2025/mcs2025-nickel.pdf |
| INSG Home | https://insg.org/ |
| INSG Market Commentary | https://insg.org/index.php/about-nickel/market-commentary/ |
| INSG Factbook | https://insg.org/index.php/publications/ |
| Nickel Industries IR | https://nickelindustries.com/investors/ |
| PT Vale Indonesia | https://www.vale.com/indonesia |
| Eramet IR | https://www.eramet.com/en/investors |
| Weda Bay Nickel | https://www.wedabaynickel.com/ |
| S&P Global MI | https://www.spglobal.com/marketintelligence/ |
</url_registry>
