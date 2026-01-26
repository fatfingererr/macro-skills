# Workflow: 驗證新聞/媒體報導

<required_reading>
**執行前請先閱讀**：
1. references/data-sources.md - 確認 JSDA 數據可用性
2. references/methodology.md - 了解計算邏輯
3. references/jsda-structure.md - 了解天期桶對照
</required_reading>

<process>

## Step 1: 收集新聞/報導的聲稱

請用戶提供以下資訊：

1. **聲稱的數字**：如「創紀錄賣超 ¥8,000 億」
2. **時間點**：如「2025 年 12 月」
3. **天期桶口徑**：如「10 年以上」或「超長端」
4. **投資人類型**：如「保險公司」或「壽險公司」
5. **來源**：如「Bloomberg」或「JSDA」

## Step 2: 對照 JSDA 原始數據

```bash
python scripts/jsda_flow_analyzer.py --verify \
  --claim-value -8000 \
  --claim-date 2025-12 \
  --claim-maturity 10y_plus
```

## Step 3: 口徑對照分析

### 3.1 天期桶對照

| 新聞口徑   | JSDA 可能對應     | 是否完全一致 |
|------------|-------------------|--------------|
| 10+ years  | super_long        | 可能不一致   |
| 10+ years  | long + super_long | 需合併計算   |
| super-long | super_long        | 一致         |
| long-term  | long              | 一致         |

### 3.2 投資人分類對照

| 新聞口徑 | JSDA 可能對應       | 是否完全一致 |
|----------|---------------------|--------------|
| 保險公司 | insurance_companies | 一致         |
| 壽險公司 | life_insurance      | 需細分       |
| 產險公司 | non_life_insurance  | 需細分       |

## Step 4: 生成驗證報告

```markdown
### 新聞數字驗證報告

**新聞聲稱**：
- 數字：-¥8,000 億
- 時間：2025-12
- 口徑：10 年以上 / 保險公司

**JSDA 原始數據對照**：

| 口徑              | JSDA 數值  | 差異  | 說明         |
|-------------------|------------|-------|--------------|
| super_long        | -¥8,224 億 | +2.8% | 新聞數字略低 |
| long              | -¥XXX 億   | -     | 僅長端       |
| long + super_long | -¥XXX 億   | -     | 合併 10Y+    |

**驗證結論**：

✓ 數量級一致（約 ¥8,000 億）
⚠️ 口徑可能不完全一致（新聞用 10+，JSDA 用 super_long）
✓ 趨勢一致（確實為淨賣出）

**建議**：新聞數字基本可信，但口徑需標註。
```

## Step 5: 常見差異原因

若數字有顯著差異，檢查以下原因：

1. **天期桶口徑**：10+ vs super-long vs long+super-long
2. **投資人細分**：全保險 vs 僅壽險
3. **時間點**：月份是否對齊
4. **單位**：十億 vs 兆 vs 億
5. **數據版本**：JSDA 可能有修正值

## Step 6: 輸出驗證摘要

```json
{
  "verification_result": {
    "claim": {
      "value_billion_jpy": -800,
      "date": "2025-12",
      "source": "新聞/Bloomberg"
    },
    "jsda_data": {
      "super_long": -822.4,
      "long": -XXX,
      "long_plus_super_long": -XXX
    },
    "match_assessment": {
      "magnitude_match": true,
      "exact_match": false,
      "difference_pct": 2.8,
      "likely_reason": "天期桶口徑差異"
    },
    "recommendation": "數字基本可信，建議標註口徑差異"
  }
}
```

</process>

<success_criteria>
驗證工作流完成時：

- [ ] 收集新聞/報導的具體聲稱
- [ ] 抓取對應時間點的 JSDA 原始數據
- [ ] 進行多口徑對照分析
- [ ] 計算數值差異百分比
- [ ] 識別可能的差異原因
- [ ] 生成驗證結論與建議
- [ ] 輸出結構化驗證報告
</success_criteria>
