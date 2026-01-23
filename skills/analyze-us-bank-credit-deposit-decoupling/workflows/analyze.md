# Workflow: 完整信貸-存款脫鉤分析

<required_reading>
**執行前請先閱讀：**
1. references/methodology.md - 理解計算邏輯與解讀方式
2. references/data-sources.md - 了解數據來源與 API 使用
</required_reading>

<process>

## Step 1: 環境準備

**1.1 確認依賴已安裝**
```bash
pip install pandas numpy fredapi matplotlib
```

**1.2 設定 FRED API Key**
```bash
# 從 https://fred.stlouisfed.org/docs/api/api_key.html 取得 API Key
export FRED_API_KEY="your_api_key_here"
```

## Step 2: 資料擷取（Data Ingestion）

**2.1 執行數據抓取腳本**
```bash
cd scripts
python decoupling_analyzer.py \
  --fetch-only \
  --start 2022-06-01 \
  --end 2026-01-23
```

**2.2 驗證數據完整性**

檢查輸出的 cache 檔案：
```bash
ls cache/
# 應包含：
# - loans_TOTLL.json
# - deposits_DPSACBW027SBOG.json
# - rrp_RRPONTSYD.json
```

**2.3 數據來源說明**

| 指標 | FRED Series ID | 單位 | 頻率 |
|------|----------------|------|------|
| 銀行貸款總量 | TOTLL | Billions USD | Weekly |
| 銀行存款總量 | DPSACBW027SBOG | Billions USD | Weekly |
| 隔夜逆回購 | RRPONTSYD | Billions USD | Daily |

## Step 3: 資料處理（Data Processing）

**3.1 計算累積變化量**

以分析起始日為基準點，計算各指標的累積變化：

```python
# 虛擬碼
loan_change = loans - loans.iloc[0]      # 累積新增貸款
deposit_change = deposits - deposits.iloc[0]  # 累積新增存款
rrp_change = rrp - rrp.iloc[0]           # 累積 RRP 變化
```

**3.2 計算 Decoupling Gap**

```python
decoupling_gap = loan_change - deposit_change
```

**3.3 計算 Deposit Stress Ratio**

```python
deposit_stress_ratio = decoupling_gap / loan_change
```

**3.4 執行完整計算**
```bash
python decoupling_analyzer.py \
  --start 2022-06-01 \
  --end 2026-01-23 \
  --output result.json
```

## Step 4: 洞察生成（Insight Generation）

**4.1 結構判定**

根據以下條件判定緊縮類型：

| 條件 | 判定 |
|------|------|
| 貸款上升 + 存款落後 + Gap 與 RRP 相關 | hidden_balance_sheet_tightening |
| 貸款下降 + 存款下降 | traditional_credit_tightening |
| 貸款上升 + 存款同步上升 | neutral |

**4.2 壓力指標解讀**

| deposit_stress_ratio | 壓力等級 | 意義 |
|---------------------|----------|------|
| < 0.3 | 低 | 正常信貸創造 |
| 0.3 - 0.5 | 中 | 輕度脫鉤 |
| 0.5 - 0.7 | 高 | 顯著脫鉤，銀行需搶存款 |
| > 0.7 | 極高 | 嚴重負債端壓力 |

**4.3 RRP 相關性驗證**

計算 decoupling_gap 與 rrp_change 的相關係數：
- r > 0.8：高度相關，RRP 是主要驅動因素
- r = 0.5-0.8：中度相關，RRP 部分解釋
- r < 0.5：低相關，需考慮其他因素

## Step 5: 視覺化輸出

**5.1 生成分析圖表**
```bash
python visualize_decoupling.py \
  --start 2022-06-01 \
  --output ../../output/decoupling_chart_$(date +%Y-%m-%d).png
```

**5.2 圖表內容**

1. **上半部**：累積變化量對比
   - 藍線：累積新增貸款
   - 綠線：累積新增存款
   - 紅線：累積 RRP 變化
   - 灰色區域：Decoupling Gap

2. **下半部**：壓力指標
   - deposit_stress_ratio 時序圖
   - 警戒水準標示（0.5, 0.7）

## Step 6: 輸出結果

**6.1 JSON 輸出**

參考 `templates/output-json.md` 格式輸出完整分析結果。

**6.2 Markdown 報告**

參考 `templates/output-markdown.md` 格式生成人類可讀報告。

</process>

<success_criteria>
此工作流完成時應達成：

- [ ] 成功從 FRED 抓取三個核心指標數據
- [ ] 計算累積變化量（貸款、存款、RRP）
- [ ] 計算 Decoupling Gap 與 deposit_stress_ratio
- [ ] 驗證 RRP 與 Gap 的相關性
- [ ] 生成緊縮類型判定與信心水準
- [ ] 輸出視覺化圖表
- [ ] 輸出 JSON 與 Markdown 格式結果
- [ ] 提供可操作的宏觀解讀
</success_criteria>
