# Workflow: 數據抓取

<required_reading>
**執行前請先閱讀：**
1. references/data-sources.md - SGE/SHFE 資料來源與抓取方法
</required_reading>

<process>

## Step 1: 環境準備

確認依賴套件已安裝：

```bash
pip install selenium webdriver-manager beautifulsoup4 pdfplumber pandas numpy
```

確認 Chrome 瀏覽器已安裝（Selenium 需要）。

## Step 2: 抓取 SGE 庫存數據

SGE（上海黃金交易所）庫存數據來自「行情周報」PDF：

```bash
cd skills/detect-shanghai-silver-stock-drain

python scripts/fetch_sge_stock.py \
  --start 2020-01-01 \
  --end 2026-01-16 \
  --output data/sge_stock.csv
```

**抓取流程：**
1. 訪問 SGE 官網行情周報頁面
2. 下載週報 PDF 檔案
3. 使用 pdfplumber 解析 PDF 表格
4. 提取「指定倉庫庫存周報」中的白銀庫存數據
5. 轉換為 CSV 格式儲存

**反偵測策略：**
- 隨機延遲 1-3 秒
- 隨機 User-Agent
- 模擬人類瀏覽器行為

## Step 3: 抓取 SHFE 庫存數據

SHFE（上海期貨交易所）庫存數據來自「倉單日報」或「Weekly Inventory」：

```bash
python scripts/fetch_shfe_stock.py \
  --start 2020-01-01 \
  --end 2026-01-16 \
  --output data/shfe_stock.csv
```

**抓取流程：**
1. 訪問 SHFE 官網倉單查詢頁面
2. 選擇白銀品種
3. 等待頁面完全載入（使用 WebDriverWait）
4. 解析 HTML 表格提取庫存數據
5. 轉換為 CSV 格式儲存

## Step 4: 數據驗證

檢查抓取的數據是否完整：

```python
import pandas as pd

# 讀取數據
sge = pd.read_csv("data/sge_stock.csv", parse_dates=["date"])
shfe = pd.read_csv("data/shfe_stock.csv", parse_dates=["date"])

# 檢查數據範圍
print(f"SGE: {sge['date'].min()} ~ {sge['date'].max()}, {len(sge)} 筆")
print(f"SHFE: {shfe['date'].min()} ~ {shfe['date'].max()}, {len(shfe)} 筆")

# 檢查缺失值
print(f"SGE 缺失: {sge['stock_kg'].isna().sum()}")
print(f"SHFE 缺失: {shfe['stock_kg'].isna().sum()}")
```

## Step 5: 快取管理

數據會快取在 `data/` 目錄：

```
data/
├── sge_stock.csv         # SGE 庫存時間序列
├── shfe_stock.csv        # SHFE 庫存時間序列
├── combined_stock.csv    # 合併庫存（自動生成）
└── cache_meta.json       # 快取元資料
```

快取有效期預設為 12 小時。超過有效期後會自動重新抓取。

強制更新快取：

```bash
python scripts/fetch_sge_stock.py --force-update
python scripts/fetch_shfe_stock.py --force-update
```

## Step 6: 錯誤處理

**常見錯誤與解決方案：**

| 錯誤 | 原因 | 解決方案 |
|------|------|----------|
| `TimeoutException` | 頁面載入超時 | 增加等待時間或重試 |
| `NoSuchElementException` | 選擇器失效 | 更新選擇器（網站改版） |
| PDF 解析失敗 | PDF 格式變更 | 更新解析規則 |
| 403 Forbidden | 被網站封鎖 | 增加延遲、降低頻率 |

**Debug 模式：**

```bash
python scripts/fetch_sge_stock.py --debug
```

Debug 模式會：
- 保存原始 HTML/PDF 到 `data/debug/`
- 輸出詳細日誌
- 不使用 headless 模式（可視化瀏覽器）

</process>

<success_criteria>
此工作流程完成時應產出：

- [ ] `data/sge_stock.csv` - SGE 庫存時間序列
- [ ] `data/shfe_stock.csv` - SHFE 庫存時間序列
- [ ] 數據欄位：date, stock_kg
- [ ] 數據範圍覆蓋指定時間區間
- [ ] 缺失值比例 < 5%
- [ ] 快取元資料已更新
</success_criteria>
