# 資料來源說明

本 Skill 使用的資料來源與 API 端點。

## 優先使用：官方/公開資料

### 1. JGB 殖利率

#### 日本財務省 (MOF)
- **網站**: https://www.mof.go.jp/jgbs/reference/interest_rate/
- **資料**: 日本國債殖利率時間序列
- **格式**: CSV/Excel 可下載
- **期限**: 1Y, 2Y, 3Y, 5Y, 10Y, 20Y, 30Y, 40Y

#### 日本銀行 (BOJ) 統計
- **網站**: https://www.stat-search.boj.or.jp/
- **資料**: 金融市場統計
- **格式**: CSV

#### FRED（替代方案）
- **端點**: `https://fred.stlouisfed.org/graph/fredgraph.csv?id=IRLTLT01JPM156N`
- **系列**:
  - `IRLTLT01JPM156N` - 日本長期利率（10Y 近似）
  - `INTGSTJPM193N` - 日本短期利率

```python
# 無需 API key 的 FRED CSV 抓取
import pandas as pd
url = "https://fred.stlouisfed.org/graph/fredgraph.csv?id=IRLTLT01JPM156N"
df = pd.read_csv(url, parse_dates=["DATE"])
```

### 2. 財政數據（稅收、利息支出、債務）

#### 日本財務省 預算/決算
- **網站**: https://www.mof.go.jp/policy/budget/
- **資料**:
  - 一般會計歲入歲出（稅收）
  - 國債費（利息+本金償還）
  - 國債殘高（債務存量）
- **頻率**: 年度

#### 日本財務省 國債統計
- **網站**: https://www.mof.go.jp/jgbs/reference/gbb/
- **資料**: 國債發行殘高、到期結構
- **用途**: 計算 pass_through 再定價比例

#### IMF / OECD（跨國比較用）
- **IMF IFS**: General government interest payments / revenue
- **OECD**: Government debt interest payments
- **注意**: 口徑可能與日本國內統計不同

### 3. 外溢通道（日本對美資產）

#### US Treasury TIC
- **網站**: https://ticdata.treasury.gov/
- **資料**: 外國持有美國證券
- **系列**: Major Foreign Holders of Treasury Securities
- **日本數據**: 月度更新

```python
# TIC 日本持有美債
url = "https://ticdata.treasury.gov/resource-center/data-chart-center/tic/Documents/mfh.txt"
```

#### 日本 IIP（國際投資頭寸）
- **來源**: 日本銀行
- **資料**: 對外資產負債表
- **用途**: 估算對美資產總規模

## 資料口徑說明

### 稅收口徑

| 口徑 | 說明 | 數值量級 |
|------|------|----------|
| `national_tax` | 國稅（所得稅+法人稅+消費稅等） | ~60-65 兆 |
| `general_account_tax` | 一般會計稅收 | ~70-75 兆 |
| `total_revenue` | 總收入（含非稅收入） | ~100+ 兆 |

### 利息口徑

| 口徑 | 說明 | 數值量級 |
|------|------|----------|
| `interest_only` | 純利息支出 | ~8-10 兆 |
| `debt_service` | 國債費（利息+本金償還） | ~25-28 兆 |

**重要**：媒體敘事「1/3」通常使用 `debt_service / general_account_tax`。

## 資料更新頻率

| 資料類型 | 更新頻率 | 滯後 |
|----------|----------|------|
| JGB 殖利率 | 每日 | T+0 |
| 稅收/利息 | 年度 | 1-2 年 |
| 債務存量 | 季度/年度 | 1 季度 |
| TIC 持有 | 月度 | 2 個月 |

## 資料品質警示

1. **殖利率 vs 財政資料時間不同步**：殖利率為即時，財政為歷史
2. **會計年度差異**：日本財政年度為 4 月～3 月
3. **口徑混用風險**：不同來源可能使用不同定義
4. **預算 vs 決算**：預算數與實際執行數可能有差異
