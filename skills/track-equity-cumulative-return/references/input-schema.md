# 完整輸入參數定義

本文檔定義累積報酬率追蹤技能的所有輸入參數。

---

## 1. cumulative_return_analyzer.py

### 必要參數

| 參數     | 類型     | 說明               |
|----------|----------|--------------------|
| --ticker | str list | 股票代碼（可多個） |

### 選用參數

| 參數        | 類型 | 預設值 | 說明               |
|-------------|------|--------|--------------------|
| --year      | int  | 2022   | 起始年份           |
| --benchmark | str  | ^GSPC  | 基準指數代碼       |
| --output    | str  | None   | 輸出 JSON 檔案路徑 |

### 使用範例

```bash
# 單一標的
python cumulative_return_analyzer.py --ticker NVDA --year 2022

# 多標的比較
python cumulative_return_analyzer.py --ticker NVDA AMD GOOGL --year 2022

# 自訂基準
python cumulative_return_analyzer.py --ticker NVDA AMD --year 2022 --benchmark ^NDX

# 輸出 JSON
python cumulative_return_analyzer.py --ticker NVDA --year 2022 --output result.json
```

---

## 2. index_component_analyzer.py

### 必要參數

無（有預設值）

### 選用參數

| 參數     | 類型 | 預設值    | 說明               |
|----------|------|-----------|--------------------|
| --index  | str  | nasdaq100 | 指數類型           |
| --year   | int  | 2022      | 起始年份           |
| --top    | int  | 20        | 取前 N 名          |
| --output | str  | None      | 輸出 JSON 檔案路徑 |

### 支援的指數

| 代碼      | 名稱              |
|-----------|-------------------|
| nasdaq100 | 納斯達克 100 指數 |
| sp100     | 標普 100 指數     |
| dow30     | 道瓊工業 30 指數  |
| sox       | 費城半導體指數    |

### 使用範例

```bash
# Nasdaq 100 Top N
python index_component_analyzer.py --index nasdaq100 --year 2022

# S&P 100 Top 30
python index_component_analyzer.py --index sp100 --year 2022 --top 30

# 費城半導體
python index_component_analyzer.py --index sox --year 2023

# 輸出 JSON
python index_component_analyzer.py --index nasdaq100 --year 2022 --output result.json
```

---

## 3. visualize_cumulative.py

### 必要參數

無（有預設值）

### 選用參數

| 參數        | 類型     | 預設值    | 說明                     |
|-------------|----------|-----------|--------------------------|
| --mode      | str      | compare   | 模式 (compare/top20)     |
| --ticker    | str list | NVDA AMD  | 股票代碼（compare 模式） |
| --index     | str      | nasdaq100 | 指數類型（top20 模式）   |
| --year      | int      | 2022      | 起始年份                 |
| --benchmark | str      | ^GSPC     | 基準指數代碼             |
| --output    | str      | auto      | 輸出 PNG 檔案路徑        |
| --top       | int      | 20        | Top N（top20 模式）      |

### 使用範例

```bash
# 多標的比較圖
python visualize_cumulative.py --ticker NVDA AMD --year 2022

# 指定輸出路徑
python visualize_cumulative.py --ticker NVDA AMD GOOGL --year 2022 --output output/my_chart.png

# Top N 圖表
python visualize_cumulative.py --mode top20 --index nasdaq100 --year 2022

# 費城半導體 Top 10
python visualize_cumulative.py --mode top20 --index sox --year 2023 --top 10
```

---

## 4. fetch_price_data.py

### 必要參數

| 參數     | 類型     | 說明               |
|----------|----------|--------------------|
| --ticker | str list | 股票代碼（可多個） |

### 選用參數

| 參數          | 類型 | 預設值     | 說明                  |
|---------------|------|------------|-----------------------|
| --start       | str  | 2022-01-01 | 起始日期 (YYYY-MM-DD) |
| --end         | str  | 今日       | 結束日期 (YYYY-MM-DD) |
| --no-cache    | flag | False      | 不使用快取            |
| --clear-cache | flag | False      | 清除所有快取          |
| --summary     | flag | False      | 顯示摘要              |

### 使用範例

```bash
# 抓取單一標的
python fetch_price_data.py --ticker NVDA --start 2022-01-01

# 抓取多標的
python fetch_price_data.py --ticker NVDA AMD GOOGL --start 2022-01-01

# 不使用快取
python fetch_price_data.py --ticker NVDA --start 2022-01-01 --no-cache

# 清除快取
python fetch_price_data.py --clear-cache

# 顯示摘要
python fetch_price_data.py --ticker NVDA --start 2022-01-01 --summary
```

---

## 5. 參數驗證規則

### ticker

- 必須是有效的 Yahoo Finance 代碼
- 大小寫不敏感（會自動轉大寫）
- 指數以 ^ 開頭（如 ^GSPC）

### year

- 必須是整數
- 建議範圍：2000 - 當前年份
- 太早的年份可能缺少部分股票數據

### index

- 必須是預定義的指數代碼之一
- 區分大小寫（使用小寫）

### output

- 若提供，必須是有效的檔案路徑
- 目錄會自動建立
- JSON 副檔名：.json
- PNG 副檔名：.png
