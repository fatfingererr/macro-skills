# 銅產量數據來源說明

## 唯一主要來源：MacroMicro (WBMS)

### 數據特性

| 項目 | 說明 |
|------|------|
| 來源 | MacroMicro (財經M平方) |
| 原始數據 | WBMS (World Bureau of Metal Statistics) |
| URL | https://en.macromicro.me/charts/91500/wbms-copper-mine-production-total-world |
| 口徑 | mined copper content（礦場產量的銅金屬含量） |
| 單位 | 千噸（圖表）→ 噸（轉換後） |
| 頻率 | 月度 |
| 歷史起點 | 約 1970 年 |

### 數據擷取方式

**推薦：Chrome CDP（繞過 Cloudflare）**

```bash
# Step 1: 啟動 Chrome 調試模式
"C:\Program Files\Google\Chrome\Application\chrome.exe" ^
  --remote-debugging-port=9222 ^
  --remote-allow-origins=* ^
  --user-data-dir="%USERPROFILE%\.chrome-debug-profile" ^
  "https://en.macromicro.me/charts/91500/wbms-copper-mine-production-total-world"

# Step 2: 等待頁面載入（圖表顯示），然後執行
cd scripts
python fetch_copper_production.py --cdp
```

**備選：Selenium**

```bash
python fetch_copper_production.py --selenium --no-headless
```

### 可用國家

圖表包含以下國家/地區的銅礦產量：

- World（全球總量）
- Chile（智利）
- Peru（秘魯）
- Democratic Republic of Congo（剛果民主共和國）
- China（中國）
- United States（美國）
- Russia（俄羅斯）
- Australia（澳洲）
- Mexico（墨西哥）
- Kazakhstan（哈薩克）
- Canada（加拿大）
- Indonesia（印尼）
- Zambia（尚比亞）

---

## 口徑說明

### 本技能使用口徑

| 口徑 | 說明 | 使用 |
|------|------|------|
| **mined_production** | 礦場產量（銅金屬含量） | ✅ 主要 |
| refined_production | 精煉產量 | ❌ 不使用 |
| reserves | 儲量 | ⚠️ 參考用 |

### 口徑差異警告

⚠️ **不同口徑不可直接比較**：

- **礦石噸數 vs 銅金屬含量**：礦石品位約 0.5-1.5%，1 噸銅金屬 ≈ 67-200 噸礦石
- **礦場產量 vs 精煉產量**：精煉產量包含二次銅（廢銅回收），通常精煉 > 礦場

---

## 快取策略

```python
CACHE_MAX_AGE_HOURS = 12  # 快取有效期
```

快取路徑：
- `scripts/cache/copper_production_cache.json` - 原始 Highcharts 數據
- `scripts/cache/copper_production.csv` - 標準化 DataFrame

---

## 數據標準化 Schema

```python
{
    "year": int,           # 年度
    "country": str,        # 國家（標準化名稱）
    "production": float,   # 產量（噸）
    "unit": "t_Cu_content",
    "source_id": "MacroMicro"
}
```
