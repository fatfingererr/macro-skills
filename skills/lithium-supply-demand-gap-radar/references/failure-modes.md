# 失敗模式與緩解策略

本文件記錄 Skill 執行過程中可能遇到的失敗模式及其緩解策略。

---

## 數據擷取失敗

### FM-001: USGS 頁面結構變更

**症狀**
- 無法解析 USGS 頁面
- 選擇器找不到目標元素

**原因**
- USGS 網站改版
- 數據發布路徑變更

**緩解策略**
1. 使用多層備用選擇器
2. 嘗試直接下載 PDF/Excel
3. 使用緩存的歷史數據
4. 標記 `confidence = 0.5`

```python
def ingest_usgs_with_fallback():
    try:
        return scrape_usgs_html()
    except SelectorError:
        try:
            return download_usgs_pdf()
        except:
            return load_cached_usgs()
```

---

### FM-002: 價格數據不可得

**症狀**
- Fastmarkets/SMM 無法訪問
- API 返回錯誤或空值

**原因**
- 付費牆限制
- API 配額耗盡
- 網站維護

**緩解策略**
1. 切換到 CME 期貨 proxy
2. 使用股票籃子 proxy
3. 向前填充最近有效價格
4. 標記 `data_level = "proxy"`

```python
def load_price_with_fallback(data_level):
    if data_level in ["paid_low", "paid_high"]:
        price = try_fastmarkets() or try_smm()
        if price:
            return price

    # Fallback 到免費 proxy
    return try_cme_futures() or compute_stock_proxy()
```

---

### FM-003: ETF 持股載入失敗

**症狀**
- Global X 頁面無法解析
- 持股數據為空

**原因**
- 頁面動態載入
- factsheet 格式變更

**緩解策略**
1. 使用 Selenium 等待動態內容
2. 嘗試解析 PDF factsheet
3. 使用靜態備份（上次成功抓取）
4. 標記 `asof_date = "static"`

```python
def load_holdings_with_fallback(ticker):
    # 優先：動態抓取
    holdings = scrape_globalx_dynamic(ticker)

    if not holdings:
        # 備用：PDF factsheet
        holdings = parse_factsheet_pdf(ticker)

    if not holdings:
        # 最後：靜態備份
        holdings = load_static_backup(ticker)
        holdings["source"] = "static_backup"

    return holdings
```

---

## 計算邏輯失敗

### FM-101: 數據對齊失敗

**症狀**
- 時間序列長度不一致
- 合併後出現大量 NaN

**原因**
- 數據源更新頻率不同（年度 vs 月度）
- 日期格式不一致

**緩解策略**
1. 標準化日期格式
2. 使用適當的重採樣策略
3. 明確標記缺失值處理

```python
def align_series(series_list, freq="weekly"):
    """對齊多個時間序列"""

    # 1. 標準化日期格式
    for s in series_list:
        s.index = pd.to_datetime(s.index)

    # 2. 重採樣到目標頻率
    resampled = [s.resample(freq).last().ffill() for s in series_list]

    # 3. 取交集時間範圍
    common_start = max(s.index.min() for s in resampled)
    common_end = min(s.index.max() for s in resampled)

    aligned = [s.loc[common_start:common_end] for s in resampled]

    return aligned
```

---

### FM-102: 回歸計算異常

**症狀**
- Beta 值異常（極大或極小）
- R² 接近 0 或負值

**原因**
- 數據點太少
- 多重共線性
- 異常值影響

**緩解策略**
1. 最低數據點要求（>= 30）
2. 異常值檢測與處理
3. 穩健回歸方法

```python
def rolling_beta_robust(y, X, window=52, min_obs=30):
    """穩健的滾動 beta 計算"""

    results = []

    for i in range(window, len(y)):
        y_window = y.iloc[i-window:i]
        X_window = X.iloc[i-window:i]

        # 檢查有效數據點
        valid_mask = ~(y_window.isna() | X_window.isna().any(axis=1))
        if valid_mask.sum() < min_obs:
            results.append({"date": y.index[i], "beta": np.nan, "valid": False})
            continue

        # 異常值處理
        y_clean, X_clean = remove_outliers(y_window[valid_mask], X_window[valid_mask])

        # 回歸
        try:
            model = sm.OLS(y_clean, sm.add_constant(X_clean)).fit()
            results.append({
                "date": y.index[i],
                "beta": model.params[1:].to_dict(),
                "r_squared": model.rsquared,
                "valid": True
            })
        except Exception as e:
            results.append({"date": y.index[i], "beta": np.nan, "valid": False, "error": str(e)})

    return pd.DataFrame(results)
```

---

### FM-103: 單位轉換錯誤

**症狀**
- 數值異常大或異常小
- 供需計算結果不合理

**原因**
- 混用不同單位（Li vs LCE vs ore）
- 轉換係數錯誤

**緩解策略**
1. 強制單位標註
2. 範圍檢查
3. 轉換前後驗證

```python
def validate_conversion(value, source_unit, target_unit, context=""):
    """驗證單位轉換結果"""

    # 合理範圍定義
    ranges = {
        "kt_LCE": {"global_production": (500, 2000), "country_production": (0, 500)},
        "kt_Li": {"global_production": (100, 400), "country_production": (0, 100)},
        "GWh": {"global_battery": (500, 5000), "country_battery": (0, 1000)}
    }

    expected_range = ranges.get(target_unit, {}).get(context, (0, float("inf")))

    if not expected_range[0] <= value <= expected_range[1]:
        return {
            "status": "warning",
            "message": f"轉換結果 {value} {target_unit} 超出預期範圍 {expected_range}",
            "suggestion": f"請檢查 {source_unit} → {target_unit} 轉換是否正確"
        }

    return {"status": "ok"}
```

---

## 輸出格式失敗

### FM-201: JSON 序列化錯誤

**症狀**
- TypeError: Object of type X is not JSON serializable
- 輸出為空或格式錯誤

**原因**
- pandas 對象未轉換
- numpy 類型未處理
- 日期對象未格式化

**緩解策略**
1. 自定義 JSON encoder
2. 序列化前轉換

```python
class LithiumEncoder(json.JSONEncoder):
    """處理 numpy/pandas 類型的 JSON encoder"""

    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        if isinstance(obj, np.floating):
            return float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        if isinstance(obj, pd.Timestamp):
            return obj.isoformat()
        if isinstance(obj, pd.DataFrame):
            return obj.to_dict(orient="records")
        if isinstance(obj, pd.Series):
            return obj.to_dict()
        return super().default(obj)
```

---

### FM-202: Markdown 格式錯亂

**症狀**
- 表格不對齊
- 代碼塊未正確渲染

**原因**
- 特殊字符未轉義
- 中英文混排寬度問題

**緩解策略**
1. 使用 ASCII 表格（如示例）
2. 轉義特殊字符
3. 固定寬度格式化

```python
def format_table_ascii(headers, rows, widths=None):
    """生成 ASCII 表格（避免 Markdown 渲染問題）"""

    if widths is None:
        widths = [max(len(str(h)), max(len(str(r[i])) for r in rows))
                  for i, h in enumerate(headers)]

    # 頂部邊框
    top = "┌" + "┬".join("─" * (w + 2) for w in widths) + "┐"

    # 標題行
    header_row = "│" + "│".join(f" {h:<{w}} " for h, w in zip(headers, widths)) + "│"

    # 分隔線
    sep = "├" + "┼".join("─" * (w + 2) for w in widths) + "┤"

    # 數據行
    data_rows = []
    for row in rows:
        data_rows.append("│" + "│".join(f" {str(r):<{w}} " for r, w in zip(row, widths)) + "│")

    # 底部邊框
    bottom = "└" + "┴".join("─" * (w + 2) for w in widths) + "┘"

    return "\n".join([top, header_row, sep] + data_rows + [bottom])
```

---

## 預防性檢查

### 執行前檢查清單

```python
def pre_execution_check(params):
    """執行前檢查"""

    checks = []

    # 1. 參數驗證
    required_params = ["etf_ticker", "lookback_years", "price_freq"]
    for p in required_params:
        if p not in params:
            checks.append({"check": f"param_{p}", "status": "fail", "message": f"缺少必要參數: {p}"})
        else:
            checks.append({"check": f"param_{p}", "status": "pass"})

    # 2. 數據源可達性
    sources = ["usgs", "iea", "globalx"]
    for source in sources:
        if is_source_reachable(source):
            checks.append({"check": f"source_{source}", "status": "pass"})
        else:
            checks.append({"check": f"source_{source}", "status": "warning", "message": f"{source} 可能不可達"})

    # 3. 依賴庫
    required_libs = ["pandas", "numpy", "yfinance", "statsmodels"]
    for lib in required_libs:
        try:
            __import__(lib)
            checks.append({"check": f"lib_{lib}", "status": "pass"})
        except ImportError:
            checks.append({"check": f"lib_{lib}", "status": "fail", "message": f"缺少依賴: {lib}"})

    return {
        "all_pass": all(c["status"] == "pass" for c in checks),
        "checks": checks
    }
```

---

## 錯誤報告格式

當發生錯誤時，輸出以下格式的錯誤報告：

```markdown
# 執行錯誤報告

## 錯誤摘要
- 錯誤代碼: [FM-XXX]
- 錯誤類型: [類型]
- 發生位置: [函數/模塊]
- 時間: [YYYY-MM-DD HH:MM:SS]

## 錯誤詳情
[詳細描述]

## 受影響的功能
- [功能1]
- [功能2]

## 緩解措施
1. [措施1]
2. [措施2]

## 降級輸出
[如果仍有部分結果可用，在此顯示]

## 建議行動
- [ ] [用戶應採取的行動]
```
