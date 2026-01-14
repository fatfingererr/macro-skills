<required_reading>
**執行此 workflow 前，先閱讀：**
1. references/data-sources.md - 資料來源與 FRED 系列代碼
2. references/cpi-pce-methodology.md - CPI/PCE 方法論差異
</required_reading>

<objective>
執行完整的 CPI-PCE 比較分析，產出三層訊號：Headline 分歧、桶位歸因、風險框架。
</objective>

<process>

<step number="1" name="執行分析腳本">

**使用 Python 腳本執行分析**

```bash
# 進入 skill 目錄
cd skills/us-cpi-pce-comparator

# 安裝依賴（首次使用）
pip install pandas numpy requests

# 執行完整分析
python scripts/cpi_pce_analyzer.py \
  --start {START_DATE} \
  --end {END_DATE} \
  --measure {MEASURE} \
  --output analysis_result.json
```

**參數說明**：
- `--start`: 起始日期 (YYYY-MM-DD)
- `--end`: 結束日期 (YYYY-MM-DD)
- `--measure`: 計算方式 (`yoy` | `mom_saar` | `qoq_saar`)
- `--baseline`: 基準期 (可選，如 `2018-10-01:2018-12-31`)
- `--cache-dir`: 快取目錄 (可選，加速重複分析)

**範例**：
```bash
# YoY 分析，2020 年至今
python scripts/cpi_pce_analyzer.py --start 2020-01-01 --measure yoy

# 含 baseline 調整
python scripts/cpi_pce_analyzer.py --start 2016-01-01 --baseline 2018-10-01:2018-12-31

# 使用快取加速
python scripts/cpi_pce_analyzer.py --start 2020-01-01 --cache-dir ./cache
```

</step>

<step number="2" name="解讀分析結果">

**檢查輸出的 JSON 結構**

```python
import json
with open('analysis_result.json', 'r') as f:
    result = json.load(f)

# 1. Headline 分歧
print(f"CPI YoY: {result['headline']['cpi_headline']}%")
print(f"PCE YoY: {result['headline']['pce_headline']}%")
print(f"分歧: {result['headline']['headline_gap_bps']} bps")

# 2. 低波動高權重桶位
for bucket in result['low_vol_high_weight_buckets']:
    print(f"{bucket['bucket']}: signal={bucket['signal']}, momentum={bucket['momentum_3m']}")

# 3. 歸因
for contrib in result['attribution']['top_contributors']:
    print(f"{contrib['bucket']}: {contrib['contribution']}")
```

</step>

<step number="3" name="生成報告（可選）">

**使用模板生成 Markdown 報告**

參考 `templates/output-markdown.md` 的模板結構，將 JSON 結果轉換為可讀報告。

```python
# 簡易報告生成
result = json.load(open('analysis_result.json'))

report = f"""
# CPI-PCE 分析報告

## 摘要
- CPI: {result['headline']['cpi_headline']}%
- PCE: {result['headline']['pce_headline']}%
- 分歧: {result['headline']['headline_gap_bps']} bps

## 解讀
{chr(10).join('- ' + i for i in result['interpretation'])}

## 注意事項
{chr(10).join('- ' + c for c in result['caveats'])}
"""
print(report)
```

</step>

<step number="4" name="驗證與交叉檢查">

**驗證步驟**：

1. **數據一致性檢查**
   - 比對 FRED 網站的最新數據
   - 確認日期範圍正確

2. **計算邏輯檢查**
   - YoY: `(current / year_ago - 1) * 100`
   - 確認無異常跳躍

3. **權重合理性檢查**
   - PCE 權重總和應接近 1
   - 與 BEA 公布值比對

</step>

</process>

<alternative_approach>

**若腳本無法執行，可手動分析**

1. **手動下載資料**
   ```
   https://fred.stlouisfed.org/graph/fredgraph.csv?id=CPIAUCSL
   https://fred.stlouisfed.org/graph/fredgraph.csv?id=PCEPI
   ```

2. **在 Excel/Google Sheets 中計算**
   - YoY: `=(current/OFFSET(current,-12,0)-1)*100`
   - Gap: `=PCE_YoY - CPI_YoY`

3. **參考 references/implementation.md 中的公式**

</alternative_approach>

<troubleshooting>

**常見問題**

<issue name="module_not_found">
**錯誤**: `ModuleNotFoundError: No module named 'pandas'`

**解決**:
```bash
pip install pandas numpy requests
```
</issue>

<issue name="connection_error">
**錯誤**: `ConnectionError` 或 `Timeout`

**解決**:
- 檢查網路連線
- 重試幾次
- 使用 `--cache-dir` 啟用快取
</issue>

<issue name="empty_data">
**錯誤**: 部分序列無資料

**原因**: 某些 FRED 序列可能有延遲或不存在

**解決**:
- 檢查 `data-sources.md` 中的系列代碼
- 使用備用序列
</issue>

</troubleshooting>

<success_criteria>
此 workflow 完成時應確認：

- [ ] 成功執行分析腳本
- [ ] 輸出包含 headline 分歧數據
- [ ] 識別出低波動高權重桶位
- [ ] 計算出各桶位貢獻
- [ ] 若有 baseline_period，產出偏離度
- [ ] 輸出包含可操作的解讀
- [ ] 明確標註資料限制
</success_criteria>
