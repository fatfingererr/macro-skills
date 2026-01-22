# Workflow: 交叉驗證

<required_reading>
**執行前請先閱讀：**
1. references/methodology.md - 交叉驗證邏輯
2. references/data-sources.md - 交叉驗證數據源
</required_reading>

<process>

## Step 1: 確認交叉驗證指標

交叉驗證使用以下指標確認上海庫存訊號的真實性：

| 指標 | 來源 | 支持緊縮假設 | 反駁緊縮假設 |
|------|------|--------------|--------------|
| COMEX Registered | CME Group | 同步下降 | 穩定或上升 |
| COMEX Eligible | CME Group | 同步下降 | 穩定或上升 |
| ETF 持倉（SLV） | MacroMicro | 同步下降 | 穩定或上升 |
| 期貨結構 | Yahoo Finance | Backwardation | Contango |
| 白銀價格波動 | Yahoo Finance | 上升 | 穩定 |

## Step 2: 抓取 COMEX 庫存數據

```bash
cd skills/detect-shanghai-silver-stock-drain

python scripts/fetch_comex_inventory.py \
  --commodity silver \
  --output data/comex_silver.csv
```

**注意**：COMEX 數據可能需要從 CME Group 網站抓取，有存取限制。如無法取得，此指標可跳過。

## Step 3: 抓取 ETF 持倉數據

使用 MacroMicro 爬蟲（參考 `monitor-etf-holdings-drawdown-risk` skill）：

```bash
# 如果已有 ETF 持倉 skill，可直接引用
python ../monitor-etf-holdings-drawdown-risk/scripts/fetch_etf_holdings.py \
  --etf SLV \
  --output data/slv_holdings.csv
```

## Step 4: 抓取價格與期貨數據

```python
import yfinance as yf

# 白銀期貨近月
si_near = yf.download("SI=F", start="2020-01-01", end="2026-01-16")

# 白銀期貨遠月（如有）
si_far = yf.download("SIK26.CMX", start="2020-01-01", end="2026-01-16")

# 計算期貨結構
# Contango: 遠月 > 近月 (正常)
# Backwardation: 近月 > 遠月 (緊縮訊號)
```

## Step 5: 綜合評估

執行交叉驗證評估：

```bash
python scripts/drain_detector.py \
  --result result.json \
  --cross-validate \
  --output result_validated.json
```

**評估邏輯：**

```python
def cross_validate(shanghai_signal, comex, etf, futures_structure):
    """交叉驗證上海庫存訊號"""
    support_count = 0
    total_checks = 0

    # COMEX 庫存
    if comex is not None:
        total_checks += 1
        if comex["registered_change"] < -0.05:  # 下降 > 5%
            support_count += 1

    # ETF 持倉
    if etf is not None:
        total_checks += 1
        if etf["slv_change"] < -0.05:  # 下降 > 5%
            support_count += 1

    # 期貨結構
    if futures_structure is not None:
        total_checks += 1
        if futures_structure == "backwardation":
            support_count += 1

    # 信心分數
    if total_checks > 0:
        confidence = support_count / total_checks
    else:
        confidence = 0.5  # 無法驗證，中性

    return {
        "confidence": confidence,
        "support_count": support_count,
        "total_checks": total_checks,
        "validated_signal": shanghai_signal if confidence >= 0.5 else "UNCONFIRMED"
    }
```

## Step 6: 輸出驗證報告

驗證報告包含：

```json
{
  "original_signal": "HIGH_LATE_STAGE_SUPPLY_SIGNAL",
  "cross_validation": {
    "confidence": 0.67,
    "checks": [
      {
        "indicator": "COMEX Registered",
        "result": "SUPPORT",
        "detail": "同期下降 8.2%"
      },
      {
        "indicator": "SLV Holdings",
        "result": "NEUTRAL",
        "detail": "持平 (+0.3%)"
      },
      {
        "indicator": "Futures Structure",
        "result": "SUPPORT",
        "detail": "Mild Backwardation"
      }
    ]
  },
  "validated_signal": "HIGH_LATE_STAGE_SUPPLY_SIGNAL",
  "interpretation": "上海庫存耗盡訊號獲得 2/3 跨市場指標支持，信心度中高。"
}
```

## Step 7: 解讀與建議

根據驗證結果提供解讀：

| 信心度 | 解讀 | 建議 |
|--------|------|------|
| ≥ 0.7 | 高度確認 | 訊號可信，可作為決策依據 |
| 0.5-0.7 | 部分確認 | 訊號可參考，需持續觀察 |
| < 0.5 | 未確認 | 訊號可能為假訊號，謹慎解讀 |

</process>

<success_criteria>
此工作流程完成時應產出：

- [ ] COMEX 庫存變化評估（如可取得）
- [ ] ETF 持倉變化評估（如可取得）
- [ ] 期貨結構評估
- [ ] 綜合信心分數
- [ ] 驗證後訊號等級
- [ ] 交叉驗證報告（JSON 格式）
- [ ] 中文解讀與建議
</success_criteria>
