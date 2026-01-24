# 失敗模式與緩解策略

## 數據擷取失敗

### FM-001: OWID 數據不可用

**症狀**：
- HTTP 請求失敗（timeout, 404, 500）
- GitHub 服務中斷

**緩解策略**：
1. 使用本地快取（若存在）
2. 切換到 USGS 歷史數據（Tier 0 備援）
3. 通知用戶並建議稍後重試

```python
def fetch_with_fallback(primary_source, fallback_source, cache):
    try:
        return primary_source.fetch()
    except Exception as e:
        logger.warning(f"主要來源失敗: {e}")
        if cache.is_valid():
            logger.info("使用快取數據")
            return cache.load()
        logger.info("切換到備援來源")
        return fallback_source.fetch()
```

### FM-002: GDELT API 限流

**症狀**：
- 429 Too Many Requests
- 空回應

**緩解策略**：
1. 實作指數退避重試
2. 減少查詢頻率
3. 切換到 news_count 代理模式

```python
def gdelt_with_backoff(query, max_retries=3):
    for attempt in range(max_retries):
        try:
            return gdelt_query(query)
        except RateLimitError:
            wait_time = 2 ** attempt
            time.sleep(wait_time)
    return fallback_to_fixed_ratings()
```

---

## 數據品質問題

### FM-003: 國家名稱不一致

**症狀**：
- 同一國家有多種名稱
- 份額加總不等於 100%

**範例**：
- "Democratic Republic of the Congo" vs "DRC" vs "Congo, Dem. Rep."
- "United States" vs "USA" vs "United States of America"

**緩解策略**：
```python
COUNTRY_MAPPING = {
    "DRC": "Democratic Republic of Congo",
    "Congo, Dem. Rep.": "Democratic Republic of Congo",
    "USA": "United States",
    # ... 完整映射表
}

def normalize_country(name):
    return COUNTRY_MAPPING.get(name, name)
```

### FM-004: 缺失值處理

**症狀**：
- 某年某國數據缺失
- NaN 導致計算錯誤

**緩解策略**：

| 情況 | 策略 | 說明 |
|------|------|------|
| 單年缺失 | 線性插值 | `df.interpolate()` |
| 連續多年缺失 | 標記為缺失 | 不參與計算 |
| 最新年度缺失 | 使用上一年度 | 標記為 estimated |
| 國家完全缺失 | 歸入 "Other" | 不單獨計算份額 |

```python
def handle_missing_values(df, strategy="interpolate"):
    if strategy == "interpolate":
        return df.interpolate(method="linear", limit=2)
    elif strategy == "forward_fill":
        return df.ffill(limit=1)
    elif strategy == "drop":
        return df.dropna()
```

### FM-005: 口徑不一致

**症狀**：
- 混用 mined vs refined 數據
- 混用 ore tonnage vs metal content

**緩解策略**：
1. 數據擷取時強制標記 `unit` 欄位
2. 計算前驗證所有數據口徑一致
3. 若不一致，發出警告並拒絕計算

```python
def validate_unit_consistency(df):
    units = df["unit"].unique()
    if len(units) > 1:
        raise UnitMismatchError(
            f"數據口徑不一致: {units}。"
            f"請確保所有數據使用相同口徑。"
        )
```

---

## 計算邏輯問題

### FM-006: 除以零錯誤

**症狀**：
- 計算 replacement_ratio 時智利缺口為 0
- 計算 share 時全球產量為 0

**緩解策略**：
```python
def safe_divide(numerator, denominator, default=0):
    if denominator == 0 or pd.isna(denominator):
        return default
    return numerator / denominator

# 使用
replacement_ratio = safe_divide(
    peru_inc + drc_inc,
    chile_decline,
    default=float('inf')  # 無限大表示「無缺口」
)
```

### FM-007: 斷點偵測失敗

**症狀**：
- 數據過短無法偵測斷點
- 所有年份都返回 breakpoint

**緩解策略**：
```python
def detect_breakpoint_safe(series, min_segment=5):
    if len(series) < min_segment * 2:
        return {
            "detected": False,
            "reason": f"數據長度不足（需 {min_segment * 2} 年）"
        }

    breakpoint = find_breakpoint(series, min_segment)

    # 驗證斷點顯著性
    if not is_significant_break(series, breakpoint):
        return {
            "detected": False,
            "reason": "斷點不顯著"
        }

    return {"detected": True, "break_year": breakpoint}
```

---

## 外部依賴問題

### FM-008: 套件版本衝突

**症狀**：
- `ruptures` 與 `statsmodels` 版本衝突
- 某些函數簽名變更

**緩解策略**：
1. 固定版本在 `requirements.txt`
2. 提供無 `ruptures` 的備選實作

```python
try:
    import ruptures as rpt
    HAS_RUPTURES = True
except ImportError:
    HAS_RUPTURES = False

def find_breakpoint(series, method="auto"):
    if method == "ruptures" and HAS_RUPTURES:
        return find_breakpoint_ruptures(series)
    else:
        return find_breakpoint_simple(series)
```

### FM-009: 網路環境限制

**症狀**：
- 企業防火牆阻擋 API 請求
- 無網路環境

**緩解策略**：
1. 支援離線模式（使用預先下載的數據）
2. 提供手動數據輸入選項
3. 允許用戶指定本地數據路徑

```python
def load_data(source="auto", local_path=None):
    if local_path:
        return pd.read_csv(local_path)
    elif source == "offline":
        return load_bundled_data()
    else:
        return fetch_from_api()
```

---

## 輸出問題

### FM-010: 視覺化失敗

**症狀**：
- `matplotlib` backend 問題
- 圖片無法保存

**緩解策略**：
```python
import matplotlib
matplotlib.use('Agg')  # 非互動式 backend

def save_chart_safe(fig, filename):
    try:
        fig.savefig(filename, dpi=150, bbox_inches='tight')
        return {"status": "success", "path": filename}
    except Exception as e:
        logger.error(f"圖表保存失敗: {e}")
        return {"status": "failed", "error": str(e)}
```

### FM-011: 報告生成過長

**症狀**：
- Markdown 報告超過限制
- 用戶難以閱讀

**緩解策略**：
1. 提供摘要版與完整版
2. 使用折疊區塊
3. 分割為多個檔案

```python
def generate_report(results, detail_level="summary"):
    if detail_level == "summary":
        return generate_summary(results)
    elif detail_level == "full":
        return generate_full_report(results)
    elif detail_level == "split":
        return {
            "summary": generate_summary(results),
            "concentration": generate_concentration_detail(results),
            "trend": generate_trend_detail(results),
            # ...
        }
```

---

## 錯誤回報格式

當發生不可恢復的錯誤時，輸出標準化錯誤報告：

```json
{
  "status": "error",
  "error_code": "FM-003",
  "error_type": "DataQualityError",
  "message": "數據口徑不一致：發現 mined 和 refined 混用",
  "context": {
    "affected_countries": ["Chile", "Peru"],
    "affected_years": [2022, 2023]
  },
  "remediation": [
    "檢查數據來源設定",
    "確認使用相同口徑（建議 mined）",
    "若需混用，請使用轉換係數"
  ],
  "partial_results": null,
  "generated_at": "2026-01-24T10:30:00Z"
}
```

---

## 監控與日誌

```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('copper_analysis.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger('copper_supply_risk')

# 使用
logger.info("開始數據擷取")
logger.warning("OWID 請求超時，使用快取")
logger.error("計算失敗", exc_info=True)
```
