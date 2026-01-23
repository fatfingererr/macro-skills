# Workflow: 快速檢查信貸-存款脫鉤狀態

<required_reading>
無需額外閱讀，直接執行即可。
</required_reading>

<process>

## Step 1: 執行快速分析

```bash
cd scripts
python decoupling_analyzer.py --quick
```

## Step 2: 解讀輸出

快速分析會輸出以下摘要：

```json
{
  "as_of": "2026-01-23",
  "decoupling_gap_trillion_usd": 1.6,
  "deposit_stress_ratio": 0.76,
  "tightening_type": "hidden_balance_sheet_tightening",
  "confidence": "high",
  "summary": "銀行負債端壓力顯著，隱性緊縮狀態"
}
```

## Step 3: 訊號解讀

| 指標 | 當前值 | 意義 |
|------|--------|------|
| decoupling_gap | 正值且擴大 | 存款流失超過貸款創造 |
| deposit_stress_ratio | > 0.5 | 銀行需要積極搶存款 |
| tightening_type | hidden | 緊縮來自負債端而非資產端 |

</process>

<success_criteria>
快速檢查完成時：

- [ ] 取得最新的脫鉤狀態摘要
- [ ] 了解當前壓力水準
- [ ] 獲得可操作的訊號判定
</success_criteria>
