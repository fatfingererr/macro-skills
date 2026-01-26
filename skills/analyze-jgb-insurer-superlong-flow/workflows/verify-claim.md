# Workflow: 驗證新聞/媒體報導

<required_reading>
**執行前請先閱讀**：
1. references/data-sources.md - 確認 JSDA 數據可用性
2. references/methodology.md - 了解計算邏輯與符號慣例
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
cd .claude/skills/analyze-jgb-insurer-superlong-flow
python scripts/jsda_flow_analyzer.py --full --format json
```

## Step 3: 符號慣例確認（重要）

**JSDA 符號慣例**：
```
net_sale = 売付額 - 買付額
```

| JSDA 數值 | 意義 | 新聞常見表達 |
|-----------|------|--------------|
| **正值** | 淨賣出（賣出 > 買入）| 「賣超」、「減持」|
| **負值** | 淨買入（買入 > 賣出）| 「買超」、「增持」|

**注意**：部分新聞使用相反的符號慣例（負值 = 淨賣出），需確認。

## Step 4: 口徑對照分析

### 4.1 天期桶對照

| 新聞口徑   | JSDA 對應                | 說明 |
|------------|--------------------------|------|
| 10+ years  | 超長期（over 10-year）   | 直接對應 |
| super-long | 超長期（over 10-year）   | 直接對應 |
| long-term  | 利付長期（5-10 年）      | 不同天期桶 |
| 10年以上   | 超長期                   | 直接對應 |

### 4.2 投資人分類對照

| 新聞口徑 | JSDA 對應 | 說明 |
|----------|-----------|------|
| 保險公司 | 生保・損保 | 壽險 + 產險合計 |
| 壽險公司 | （無法分拆）| JSDA 僅提供合計 |
| 產險公司 | （無法分拆）| JSDA 僅提供合計 |

## Step 5: 生成驗證報告

```markdown
### 新聞數字驗證報告

**新聞聲稱**：
- 數字：¥8,000 億（淨賣出）
- 時間：2025-12
- 口徑：10 年以上 / 保險公司

**JSDA 原始數據對照**：

| 指標 | JSDA 數值 | 說明 |
|------|-----------|------|
| 超長期淨賣出 | +8,224 億日圓 | 正值 = 淨賣出 |
| 與新聞差異 | +2.8% | 新聞數字略低 |

**驗證結論**：

✓ 數量級一致（約 ¥8,000 億）
✓ 方向一致（確實為淨賣出）
✓ 口徑一致（超長期 = 10 年以上）
✓ 創紀錄屬實（樣本期間最大淨賣出）

**結論**：新聞報導數字基本準確。
```

## Step 6: 常見差異原因

若數字有顯著差異，檢查以下原因：

1. **符號慣例**：JSDA 正值 = 淨賣出，部分來源相反
2. **天期桶口徑**：超長期 vs 長期 vs 合併 10Y+
3. **投資人細分**：全保險 vs 僅壽險（JSDA 無法分拆）
4. **時間點**：月份是否對齊
5. **單位**：億 vs 十億 vs 兆
6. **數據版本**：JSDA 可能有修正值
7. **數據來源**：店頭 vs 交易所

## Step 7: 輸出驗證摘要

```json
{
  "verification_result": {
    "claim": {
      "value_100m_jpy": 8000,
      "direction": "淨賣出",
      "date": "2025-12",
      "source": "新聞/Bloomberg"
    },
    "jsda_data": {
      "super_long_100m_jpy": 8224,
      "sign_convention": "正值=淨賣出"
    },
    "match_assessment": {
      "magnitude_match": true,
      "direction_match": true,
      "exact_match": false,
      "difference_pct": 2.8
    },
    "recommendation": "數字準確，創紀錄屬實"
  }
}
```

</process>

<success_criteria>
驗證工作流完成時：

- [x] 收集新聞/報導的具體聲稱
- [x] 確認符號慣例（JSDA 正值 = 淨賣出）
- [x] 抓取對應時間點的 JSDA 原始數據
- [x] 進行口徑對照分析
- [x] 計算數值差異百分比
- [x] 識別可能的差異原因
- [x] 生成驗證結論與建議
- [x] 輸出結構化驗證報告
</success_criteria>
