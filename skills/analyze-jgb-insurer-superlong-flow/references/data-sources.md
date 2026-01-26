# 資料來源說明

## 1. 主要數據來源：JSDA 公社債店頭売買高

### 1.1 來源資訊

| 項目 | 內容 |
|------|------|
| 機構 | 日本證券業協會（Japan Securities Dealers Association, JSDA） |
| 數據類型 | Trading Volume of OTC Bonds（公社債店頭売買高） |
| 網址 | https://www.jsda.or.jp/shiryoshitsu/toukei/tentoubaibai/ |
| 格式 | Excel (XLSX) |
| 頻率 | 月度 |
| 延遲 | 約 T+1 個月（月底發布上月數據） |
| 費用 | 免費 |

### 1.2 下載路徑

**當前財年（持續更新）**：
```
https://www.jsda.or.jp/shiryoshitsu/toukei/tentoubaibai/koushasai.xlsx
```

**歷史財年（日本財年 4 月開始）**：
```
https://www.jsda.or.jp/shiryoshitsu/toukei/tentoubaibai/koushasai{YYYY}.xlsx
```

例如：
- `koushasai2024.xlsx` → FY2024（2024/04 ~ 2025/03）
- `koushasai2023.xlsx` → FY2023（2023/04 ~ 2024/03）
- `koushasai2022.xlsx` → FY2022（2022/04 ~ 2023/03）

### 1.3 Excel 結構

**關鍵 Sheet**：

| Sheet 名稱 | 內容 |
|------------|------|
| `(Ａ)合計売買高` | 總交易量 |
| `(Ｄ)合計売付額` | 總賣出額 |
| `(Ｇ)合計買付額` | 總買入額 |
| `(Ｊ)合計差引` | **淨買賣額（Sell - Purchase）** ← 本 Skill 使用 |

**欄位結構（Sheet: 合計差引）**：

| 欄位位置 | 內容 |
|----------|------|
| 第 0 列 | 年/月（如 2025/12） |
| 第 1 列 | 投資人類型 |
| 第 2 列 | 投資人類型（英文） |
| 第 3 列 | 國債總計 |
| **第 4 列** | **超長期（Interest-bearing Long-term over 10-year）** |
| 第 5 列 | 利付長期（Interest-bearing Long-term） |
| 第 6 列 | 利付中期（Interest-bearing Medium-term） |
| 第 7 列 | 割引（Zero-Coupon） |
| 第 8 列 | 国庫短期証券等（Treasury Discount Bills） |

### 1.4 投資人分類

| JSDA 分類 | 英文 | 說明 |
|-----------|------|------|
| 都市銀行 | City Banks & Long-Term Credit Banks | 大型商業銀行 |
| 地方銀行 | Regional Banks | 區域性銀行 |
| 信託銀行 | Trust Banks | 含年金管理 |
| 農林系金融機関 | Fin.Insts. for Agr. & Forestry | 農林金融 |
| 第二地銀協加盟行 | 2nd Regional | 第二地方銀行 |
| 信用金庫 | Shinkin Banks | 信用金庫 |
| その他金融機関 | Other Fin.Insts. | 其他金融機構 |
| **生保・損保** | **Life & Non-Life Insurance Companies** | **壽險 + 產險** |
| 投資信託 | Investment Trusts | 共同基金 |
| 官公庁共済組合 | Mutual Aid Association of Govt.Offices | 政府互助會 |
| 事業法人 | Business Corporations | 一般企業 |
| その他法人 | Other Corporations | 其他法人 |
| 外国人 | Foreigners | 海外投資者 |
| 個人 | Individuals | 個人投資者 |
| その他 | Others | 其他 |
| 債券ディーラー | Bond Dealers | 債券交易商 |
| 合計 | Total | 總計 |

### 1.5 符號慣例

**重要**：JSDA 的「差引」使用「賣出 - 買入」計算：

```
差引 = 売付額 - 買付額
```

- **正值 = 淨賣出**（賣出 > 買入）
- **負值 = 淨買入**（買入 > 賣出）

---

## 2. 歷史沿革

### 2.1 2018/05 改版

JSDA 在 2018 年 5 月進行統計格式改版：

- **舊版**：「Trends in Bond Transactions (by investor type)」單獨發布
- **新版**：整併進「Trading Volume of OTC Bonds」資料集

**影響**：
- 英文版 Bonds 頁面的舊表只到 2018/05
- 2018/05 後的數據需從新的 `koushasai.xlsx` 系列取得
- 數據口徑和欄位結構有所調整

### 2.2 數據可追溯性

目前 JSDA 網站提供的歷史檔案：
- `koushasai.xlsx` - 當前財年
- `koushasai2024.xlsx` - FY2024
- `koushasai2023.xlsx` - FY2023
- `koushasai2022.xlsx` - FY2022
- 更早年份可能需要向 JSDA 申請

---

## 3. 數據品質說明

### 3.1 已知限制

1. **延遲**：JSDA 數據約滯後 1 個月
2. **修正**：歷史數據可能有修正，需定期更新
3. **範圍**：僅包含店頭（OTC）交易，不含交易所交易
4. **合併口徑**：「生保・損保」為壽險 + 產險合計，無法分拆

### 3.2 快取策略

腳本會自動快取下載的 Excel 檔案：

```
data/cache/
├── koushasai.xlsx        # 當前財年
├── koushasai2024.xlsx    # FY2024
├── koushasai2023.xlsx    # FY2023
└── koushasai2022.xlsx    # FY2022
```

**快取邏輯**：
- 檔案存在且大於 50KB → 使用快取
- 使用 `--refresh` 參數 → 強制重新下載

---

## 4. 替代與補充數據來源

### 4.1 日本銀行（BOJ）Flow of Funds

| 項目 | 說明 |
|------|------|
| 數據類型 | 資金循環統計（Flow of Funds） |
| 網址 | https://www.boj.or.jp/statistics/sj/ |
| 優點 | 季度，含持倉存量 |
| 缺點 | 天期分類較粗，延遲較長 |

### 4.2 財務省（MOF）國債持有者統計

| 項目 | 說明 |
|------|------|
| 數據類型 | JGB Investor Presentation |
| 網址 | https://www.mof.go.jp/english/policy/jgbs/IR/ |
| 優點 | 官方投資人報告 |
| 缺點 | 季度，口徑可能與 JSDA 不同 |

### 4.3 Bloomberg / Reuters（付費）

| 項目 | 說明 |
|------|------|
| 數據類型 | 加工後的投資人流量數據 |
| 優點 | 即時，易於使用 |
| 缺點 | 付費，口徑可能經過調整 |

---

## 5. 數據驗證實例

### 5.1 2025/12 數據驗證

從 `koushasai.xlsx` 提取的「生保・損保」超長期國債數據：

| 年月 | 淨賣出（億日圓） | 解讀 |
|------|------------------|------|
| 2025/12 | +8,224 | 淨賣出 8,224 億 |
| 2025/11 | +451 | 淨賣出 451 億 |
| 2025/10 | +2,767 | 淨賣出 2,767 億 |
| 2025/09 | +2,258 | 淨賣出 2,258 億 |
| 2025/08 | +259 | 淨賣出 259 億 |

**結論**：2025/12 的 8,224 億日圓為樣本期間（2022/04~2025/12）最大單月淨賣出。
