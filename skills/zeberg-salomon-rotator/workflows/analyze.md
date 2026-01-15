# Workflow: 深度分析

<required_reading>
**執行前請先閱讀：**
1. references/methodology.md - Zeberg-Salomon 模型邏輯
2. references/data-sources.md - 各指標的經濟意義
3. references/input-schema.md - 參數配置
</required_reading>

<process>

## Step 1: 抓取完整數據

```bash
python scripts/fetch_data.py \
  --leading T10Y3M,T10Y2Y,PERMIT,ACDGNO,UMCSENT \
  --coincident PAYEMS,INDPRO,W875RX1,CMRMTSPL \
  --risk BAA10Y,VIXCLS \
  --prices SPY,TLT \
  --start 2015-01-01 \
  --output analysis_data.json
```

## Step 2: 建構並分解指標

計算各成分對合成指標的貢獻：

```python
from scripts.rotator import build_index_with_attribution

L, L_contrib = build_index_with_attribution(
    leading_config,
    data["macro"],
    z_win=120,
    smooth_win=3
)

C, C_contrib = build_index_with_attribution(
    coincident_config,
    data["macro"],
    z_win=120,
    smooth_win=3
)

# L_contrib 結構：
# {
#   "T10Y3M": {"value": -0.12, "weight": 0.25, "contribution": -0.03},
#   "T10Y2Y": {"value": -0.08, "weight": 0.15, "contribution": -0.012},
#   ...
# }
```

## Step 3: 趨勢分析

分析指標的趨勢方向與動量：

```python
from scripts.rotator import analyze_trend

trend_analysis = {
    "LeadingIndex": analyze_trend(L, windows=[3, 6, 12]),
    "CoincidentIndex": analyze_trend(C, windows=[3, 6, 12])
}

# analyze_trend 輸出：
# {
#   "current_value": 0.41,
#   "3m_change": 0.15,
#   "6m_change": 0.28,
#   "12m_change": 0.45,
#   "slope_3m": 0.05,
#   "slope_6m": 0.047,
#   "direction": "rising",
#   "momentum": "accelerating"
# }
```

## Step 4: 歷史分位數定位

將當前值放在歷史分布中定位：

```python
from scripts.rotator import percentile_rank

percentile = {
    "LeadingIndex": percentile_rank(L.iloc[-1], L),
    "CoincidentIndex": percentile_rank(C.iloc[-1], C)
}

# 例如：LeadingIndex 在歷史 65% 分位 → 高於 65% 的歷史觀測值
```

## Step 5: 濾鏡分析（可選）

若配置了 euphoria_filters 或 recovery_doubt_filters：

```python
from scripts.rotator import evaluate_filters

# 亢奮濾鏡（Risk-On 過熱信號）
euphoria = evaluate_filters(
    filters=[
        {"type": "credit_spread_reversal", "series_id": "BAA10Y", "z_below": -1.0, "turn_up": True},
        {"type": "vix_turn_up", "ticker": "VIXCLS", "level_below": 15, "turn_up": True}
    ],
    data=data
)

# 復甦懷疑濾鏡
doubt = evaluate_filters(
    filters=[
        {"type": "leading_momentum", "above": 0}
    ],
    data=data
)
```

## Step 6: 情境分析

基於當前狀態，分析各種情境：

```python
scenarios = {
    "current_path": {
        "description": "若指標維持當前趨勢",
        "expected_state_in_3m": predict_state(L, C, months=3),
        "probability": "baseline"
    },
    "acceleration": {
        "description": "若指標加速惡化（如衰退）",
        "trigger": "ΔL < -0.1 連續 2 期",
        "expected_action": "EXIT_EQUITY_ENTER_LONG_BOND"
    },
    "reversal": {
        "description": "若指標反轉（如政策刺激）",
        "trigger": "L 回升超過 hysteresis",
        "expected_action": "EXIT_LONG_BOND_ENTER_EQUITY"
    }
}
```

## Step 7: 生成分析報告

```json
{
  "analysis_date": "2026-01-15",
  "current_state": "RISK_ON",
  "indices": {
    "LeadingIndex": {
      "value": 0.41,
      "percentile": 65,
      "trend": "rising",
      "momentum": "stable"
    },
    "CoincidentIndex": {
      "value": 0.22,
      "percentile": 55,
      "trend": "flat",
      "momentum": "decelerating"
    }
  },
  "attribution": {
    "leading_top_contributors": [
      {"series": "T10Y3M", "contribution": 0.12, "direction": "positive"},
      {"series": "PERMIT", "contribution": 0.08, "direction": "positive"}
    ],
    "leading_top_detractors": [
      {"series": "UMCSENT", "contribution": -0.05, "direction": "negative"}
    ],
    "coincident_top_contributors": [...],
    "coincident_top_detractors": [...]
  },
  "events": {
    "iceberg": false,
    "sinking": false,
    "distance_to_iceberg": 0.71,
    "distance_to_sinking": 0.72
  },
  "filters": {
    "euphoria": {"active": false, "details": {...}},
    "doubt": {"active": true, "details": {...}}
  },
  "scenarios": [...],
  "interpretation": [
    "領先指標目前在歷史 65% 分位，處於擴張區間",
    "殖利率曲線（T10Y3M）貢獻最大正向動能",
    "消費者信心（UMCSENT）近期走弱，需關注",
    "距離「冰山事件」門檻還有 0.71 個標準差"
  ],
  "caveats": [
    "FRED 數據有 1-2 個月延遲",
    "本模型為 Zeberg 方法論的公開數據近似版"
  ]
}
```

</process>

<success_criteria>
深度分析完成時應產出：

- [ ] 當前指標值與歷史分位數定位
- [ ] 趨勢分析（方向、動量、斜率）
- [ ] 各成分指標的貢獻歸因
- [ ] 距離事件門檻的距離
- [ ] 濾鏡狀態（若有配置）
- [ ] 情境分析
- [ ] 可操作的解讀與注意事項
</success_criteria>
