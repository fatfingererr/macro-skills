# Markdown 報告模板

<overview>
本文件定義 analyze-gas-fertilizer-contract-shock 技能的 Markdown 輸出模板。
</overview>

---

## 報告模板

```markdown
# 天然氣→化肥因果假說分析報告

**分析日期**: {{analysis_date}}
**數據區間**: {{start_date}} 至 {{end_date}}
**數據來源**: TradingEconomics ({{gas_symbol}}, {{fert_symbol}})

---

## TL;DR

{{signal_emoji}} **{{signal_text}}**（信心水準：{{confidence}}）

{{summary_sentence}}

---

## 一、三段式因果檢驗結果

| 階段 | 檢驗內容 | 結果 | 說明 |
|------|----------|------|------|
| A: Gas Shock | 天然氣出現異常暴漲？ | {{A_result}} | {{A_explanation}} |
| B: Fert Follows | 化肥在 A 段後上漲？ | {{B_result}} | {{B_explanation}} |
| C: Lead-Lag | 統計上 Gas 領先 Fert？ | {{C_result}} | {{C_explanation}} |

---

## 二、天然氣 Shock Regime

{{#if gas_shock_regimes}}
| 起始 | 結束 | 峰值日 | 峰值 | 漲幅 | 持續 |
|------|------|--------|------|------|------|
{{#each gas_shock_regimes}}
| {{start}} | {{end}} | {{peak_date}} | {{peak_value}} {{unit}} | +{{regime_return_pct}}% | {{duration_days}} 天 |
{{/each}}

**最大 z-score**: {{max_z_score}}
**最大斜率**: {{max_slope}}%/天
{{else}}
*樣本期間內未偵測到天然氣 shock。*
{{/if}}

---

## 三、化肥 Spike Regime

{{#if fert_spike_regimes}}
| 起始 | 結束 | 峰值日 | 峰值 | 漲幅 | 持續 |
|------|------|--------|------|------|------|
{{#each fert_spike_regimes}}
| {{start}} | {{end}} | {{peak_date}} | {{peak_value}} {{unit}} | +{{regime_return_pct}}% | {{duration_days}} 天 |
{{/each}}

**與天然氣 shock 的時序關係**: 化肥 spike 起點晚於天然氣 shock 起點約 {{lag_days}} 天
{{else}}
*樣本期間內未偵測到化肥 spike。*
{{/if}}

---

## 四、領先落後分析

| 指標 | 值 | 解讀 |
|------|-----|------|
| 最佳 Lag | {{best_lag}} 天 | {{lag_interpretation}} |
| 相關係數 | {{best_corr}} | {{corr_interpretation}} |
| 合理範圍 | 7-56 天 | {{in_range_text}} |

**方法**: {{method}}（{{method_description}}）

---

## 五、敘事評估

### 結論

{{narrative_summary}}

### 支持證據

{{#each supporting_evidence}}
- {{this}}
{{/each}}

### 替代解釋

{{#each alternative_explanations}}
- {{this}}
{{/each}}

---

## 六、注意事項

{{#each caveats}}
- {{this}}
{{/each}}

---

## 七、下一步建議

{{#each recommendations}}
- {{this}}
{{/each}}

---

## 附錄：圖表

{{#if charts}}
{{#each charts}}
![{{description}}]({{path}})
{{/each}}
{{else}}
*未生成圖表。*
{{/if}}

---

*報告由 analyze-gas-fertilizer-contract-shock v{{skill_version}} 自動生成*
*數據來源: TradingEconomics | 分析時間: {{analysis_timestamp}}*
```

---

## 變數說明

### 信號相關

| 變數 | 來源 | 說明 |
|------|------|------|
| signal_emoji | 根據 signal 值 | ✅ / ⚠️ / ❓ |
| signal_text | 根據 signal 值 | 敘事有支撐 / 敘事較弱 / 無法判斷 |
| confidence | JSON output | high / medium / low |
| summary_sentence | 動態生成 | 一句話總結 |

### 三段式檢驗

| 變數 | 來源 | 說明 |
|------|------|------|
| A_result | three_part_test.A_gas_shock.pass | ✓ / ✗ |
| B_result | three_part_test.B_fert_follows.pass | ✓ / ✗ |
| C_result | three_part_test.C_lead_lag_supports.pass | ✓ / ✗ |
| A_explanation | 動態生成 | A 段解釋 |
| B_explanation | 動態生成 | B 段解釋 |
| C_explanation | 動態生成 | C 段解釋 |

### Regime 資訊

| 變數 | 來源 | 說明 |
|------|------|------|
| gas_shock_regimes | detections | 天然氣 shock 清單 |
| fert_spike_regimes | detections | 化肥 spike 清單 |

### Lead-Lag

| 變數 | 來源 | 說明 |
|------|------|------|
| best_lag | lead_lag_test | 最佳 lag 天數 |
| best_corr | lead_lag_test | 最大相關係數 |
| lag_interpretation | 動態生成 | lag 解讀 |
| corr_interpretation | 動態生成 | 相關係數解讀 |

---

## 範例輸出

```markdown
# 天然氣→化肥因果假說分析報告

**分析日期**: 2026-01-28
**數據區間**: 2025-08-01 至 2026-02-01
**數據來源**: TradingEconomics (natural-gas, urea)

---

## TL;DR

✅ **敘事有量化支撐**（信心水準：medium）

天然氣在 2026 年 1 月出現明顯 shock，化肥在其後約 8 天開始上漲，領先落後分析顯示 gas 領先 fert 約 12 天，時序關係支持「天然氣暴漲→化肥飆價」的敘事。

---

## 一、三段式因果檢驗結果

| 階段 | 檢驗內容 | 結果 | 說明 |
|------|----------|------|------|
| A: Gas Shock | 天然氣出現異常暴漲？ | ✓ | 2026-01-12 至 01-29，漲幅 85.4% |
| B: Fert Follows | 化肥在 A 段後上漲？ | ✓ | 2026-01-20 起漲，晚於 gas shock 8 天 |
| C: Lead-Lag | 統計上 Gas 領先 Fert？ | ✓ | 最佳 lag 12 天，在合理範圍內 |

---

## 二、天然氣 Shock Regime

| 起始 | 結束 | 峰值日 | 峰值 | 漲幅 | 持續 |
|------|------|--------|------|------|------|
| 2026-01-12 | 2026-01-29 | 2026-01-29 | 6.95 USD/MMBtu | +85.4% | 18 天 |

**最大 z-score**: 4.2
**最大斜率**: 2.1%/天

---

## 三、化肥 Spike Regime

| 起始 | 結束 | 峰值日 | 峰值 | 漲幅 | 持續 |
|------|------|--------|------|------|------|
| 2026-01-20 | 2026-02-01 | 2026-01-31 | 420.0 USD/ton | +22.1% | 13 天 |

**與天然氣 shock 的時序關係**: 化肥 spike 起點晚於天然氣 shock 起點約 8 天

---

## 四、領先落後分析

| 指標 | 值 | 解讀 |
|------|-----|------|
| 最佳 Lag | 12 天 | 天然氣領先化肥 |
| 相關係數 | 0.41 | 中度相關 |
| 合理範圍 | 7-56 天 | ✓ 在範圍內 |

**方法**: corr_returns（報酬率交叉相關）

---

## 五、敘事評估

### 結論

三段式因果檢驗通過，「天然氣暴漲→化肥飆價」的敘事在時間序列上有量化支撐。

### 支持證據

- 天然氣在樣本末端出現明顯 shock regime（z-score 達 4.2）
- 化肥在天然氣 shock 後約 8 天開始上漲
- 交叉相關顯示 gas 領先 fert 約 12 天，在合理傳導期內

### 替代解釋

- 化肥 spike 可能還受其他因素影響（運費、需求、政策）
- 相關係數 0.41 為中度，部分變異來自其他驅動因素
- 僅憑價格無法證明 force majeure/毀約

---

## 六、注意事項

- 數據來源為 TradingEconomics，可能與交易所官方數據有差異
- 日頻數據可能有缺失，已使用 forward-fill 處理
- 相關不代表因果，需配合機制分析
- 本分析不構成任何投資建議

---

## 七、下一步建議

- 若需驗證具體公司行為，應查閱該公司公告與新聞
- 可擴展分析其他化肥種類（DAP、磷肥）
- 可使用不同地區天然氣（歐洲 TTF）重複驗證

---

*報告由 analyze-gas-fertilizer-contract-shock v0.1.0 自動生成*
*數據來源: TradingEconomics | 分析時間: 2026-01-28T10:30:00Z*
```
