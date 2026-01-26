# 資料來源說明

## 1. 主要數據來源：JSDA

### 1.1 來源資訊

| 項目 | 內容 |
|------|------|
| 機構 | 日本證券業協會（Japan Securities Dealers Association, JSDA） |
| 網址 | https://www.jsda.or.jp/ |
| 數據類型 | Trends in Bond Transactions (by investor type) |
| 格式 | Excel (XLS/XLSX) |
| 頻率 | 月度 |
| 延遲 | 約 T+1 個月（月底發布上月數據） |
| 費用 | 免費 |

### 1.2 下載路徑

```
JSDA 官網
├── English
│   └── Statistics
│       └── Bonds
│           └── Trends in Bond Transactions (by investor type)
│               └── [XLS 下載連結]
```

**注意**：JSDA 網站改版可能導致路徑變更，需定期確認。

### 1.3 數據欄位

| 欄位 | 說明 | 單位 |
|------|------|------|
| Investor Type | 投資人類型 | - |
| Maturity Bucket | 天期區間 | - |
| Gross Purchases | 買入金額 | 十億日圓 |
| Gross Sales | 賣出金額 | 十億日圓 |
| Net Purchases | 淨買入 = 買入 - 賣出 | 十億日圓 |

### 1.4 投資人分類

| JSDA 分類 | 中文 | 說明 |
|-----------|------|------|
| City Banks | 都市銀行 | 大型商業銀行 |
| Regional Banks | 地方銀行 | 區域性銀行 |
| Trust Banks | 信託銀行 | 含年金管理 |
| Life Insurance | 壽險公司 | 人壽保險 |
| Non-life Insurance | 產險公司 | 財產保險 |
| Investment Trusts | 投資信託 | 共同基金 |
| Foreigners | 外國人 | 海外投資者 |
| Others | 其他 | 其他機構 |

### 1.5 天期桶定義

| JSDA 天期桶 | 英文 | 說明 |
|-------------|------|------|
| 短期 | Short-term | < 1 年 |
| 中期 | Medium-term | 1-5 年 |
| 長期 | Long-term | 5-10 年 |
| 超長期 | Super-long | > 10 年 |

**注意**：不同年份的 XLS 可能有不同的天期桶定義，需確認具體 sheet 結構。

---

## 2. 輔助數據來源

### 2.1 FRED（匯率換算用）

| 項目 | 內容 |
|------|------|
| 數據 | USDJPY 匯率 |
| 系列代碼 | DEXJPUS |
| 頻率 | 日度 |
| 用途 | 若需將 JPY 換算為 USD |

**抓取方式**：
```python
import pandas as pd

FRED_URL = "https://fred.stlouisfed.org/graph/fredgraph.csv"

def fetch_usdjpy(start_date, end_date):
    params = {"id": "DEXJPUS", "cosd": start_date, "coed": end_date}
    df = pd.read_csv(f"{FRED_URL}?{'&'.join(f'{k}={v}' for k, v in params.items())}")
    df.columns = ["DATE", "USDJPY"]
    df["DATE"] = pd.to_datetime(df["DATE"])
    df["USDJPY"] = pd.to_numeric(df["USDJPY"], errors="coerce")
    return df.dropna().set_index("DATE")
```

### 2.2 JGB 殖利率（關聯分析用）

| 來源 | 系列代碼 | 說明 |
|------|----------|------|
| FRED | IRLTLT01JPM156N | 日本 10 年期國債殖利率（月度） |
| BOJ | - | 日本銀行發布的各天期殖利率 |

---

## 3. 不可用的數據來源

### 3.1 Bloomberg

| 項目 | 說明 |
|------|------|
| 數據類型 | 加工後的投資人流量數據 |
| 可得性 | 付費終端 |
| 問題 | 口徑可能與 JSDA 原始數據不同，無法公開驗證 |

### 3.2 四大壽險未實現損失

| 項目 | 說明 |
|------|------|
| 數據類型 | 持倉未實現損益 |
| 來源 | 各公司財報 / IR 簡報 |
| 問題 | 需逐家抓取，口徑可能不一致 |

**公開替代方案**：
- 日本生命：https://www.nissay.co.jp/ir/
- 第一生命：https://www.dai-ichi-life-hd.com/investor/
- 住友生命：https://www.sumitomolife.co.jp/about/ir/
- 明治安田：https://www.meijiyasuda.co.jp/profile/ir/

---

## 4. 數據品質說明

### 4.1 已知限制

1. **延遲**：JSDA 數據約滯後 1 個月
2. **修正**：歷史數據可能有修正，需定期更新
3. **口徑變更**：天期桶定義可能隨時間調整
4. **網站改版**：下載路徑可能變更

### 4.2 Fallback 機制

若 JSDA 主站不可用：
1. 檢查緩存目錄是否有最近數據
2. 嘗試使用備份 URL（若有）
3. 輸出警告並使用最後已知數據

---

## 5. 快取策略

```
data/cache/
├── jsda_raw_YYYYMM.xlsx      # 原始 XLS 檔案
├── jsda_parsed_YYYYMM.json   # 解析後的 JSON
└── metadata.json              # 抓取時間與版本資訊
```

**快取有效期**：7 天（可配置）

**強制刷新**：
```bash
python scripts/fetch_jsda_data.py --refresh --force
```
