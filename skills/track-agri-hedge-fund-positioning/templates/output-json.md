# JSON 輸出結構定義

## 完整輸出結構

```json
{
  "skill": "track-agri-hedge-fund-positioning",
  "version": "0.1.0",
  "generated_at": "2026-01-27T10:30:00Z",
  "as_of": "2026-01-21",

  "summary": {
    "call": "Funds back & buying",
    "confidence": 0.72,
    "why": [
      "COT 週部位變化顯示農產品總流量由負轉正",
      "分組（穀物/油籽）同步改善，非單一品種噪音",
      "宏觀順風：美元走弱、原油與金屬偏強"
    ],
    "risks": [
      "COT 只到週二：Wed–Fri 的『買回』屬推估",
      "USDA 報告或天氣變動可能讓訊號反轉"
    ],
    "next_steps": [
      "監控週五 USDA Export Sales 報告",
      "觀察火力是否持續回升"
    ]
  },

  "latest_metrics": {
    "cot_week_end": "2026-01-21",
    "flow_total_contracts": 58,
    "flow_by_group_contracts": {
      "grains": 35,
      "oilseeds": 25,
      "meats": 5,
      "softs": 0
    },
    "net_position_by_group": {
      "grains": 125000,
      "oilseeds": 85000,
      "meats": 12000,
      "softs": -5000,
      "total": 217000
    },
    "buying_firepower": {
      "total": 0.63,
      "grains": 0.58,
      "oilseeds": 0.67,
      "meats": 0.41,
      "softs": 0.75
    },
    "macro_tailwind_score": 0.67,
    "macro_components": {
      "usd_down": true,
      "crude_up": true,
      "metals_up": false
    }
  },

  "weekly_flows": [
    {
      "date": "2026-01-21",
      "grains": 35,
      "oilseeds": 25,
      "meats": 5,
      "softs": 0,
      "total": 65
    },
    {
      "date": "2026-01-14",
      "grains": -10,
      "oilseeds": 15,
      "meats": -5,
      "softs": 2,
      "total": 2
    }
  ],

  "firepower_history": [
    {
      "date": "2026-01-21",
      "total": 0.63,
      "grains": 0.58,
      "oilseeds": 0.67,
      "meats": 0.41,
      "softs": 0.75
    }
  ],

  "annotations": [
    {
      "label": "macro_mood_bullish",
      "rule_hit": true,
      "evidence": ["USD down", "crude up"],
      "date": "2026-01-21"
    },
    {
      "label": "grains_momentum_up",
      "rule_hit": true,
      "evidence": ["Grains flow turned positive", "Corn export sales up"],
      "date": "2026-01-21"
    }
  ],

  "validation": {
    "wed_fri_buyback": {
      "price_momentum": "bullish",
      "volume_elevated": true,
      "macro_resonance": 0.67
    },
    "macro_alignment": {
      "aligned": true,
      "interpretation": "資金流入且宏觀順風，敘事一致"
    },
    "overall_consistency": 0.78,
    "confidence_adjustment": 0.1
  },

  "metadata": {
    "cot_report_type": "legacy",
    "trader_group": "noncommercial",
    "position_metric": "net",
    "lookback_weeks": 156,
    "data_sources": {
      "cot": "CFTC",
      "macro": "Yahoo Finance",
      "fundamentals": "USDA"
    }
  }
}
```

---

## 欄位說明

### 頂層欄位

| 欄位         | 類型   | 說明                         |
|--------------|--------|------------------------------|
| skill        | string | 技能名稱                     |
| version      | string | 技能版本                     |
| generated_at | string | 報告生成時間（ISO 8601）     |
| as_of        | string | 資料截止日期                 |

### summary 區塊

| 欄位       | 類型     | 說明                           |
|------------|----------|--------------------------------|
| call       | string   | 可交易呼叫（主要結論）         |
| confidence | number   | 信心水準（0-1）                |
| why        | string[] | 結論依據清單                   |
| risks      | string[] | 風險提示清單                   |
| next_steps | string[] | 下一步建議                     |

### latest_metrics 區塊

| 欄位                    | 類型   | 說明                         |
|-------------------------|--------|------------------------------|
| cot_week_end            | string | COT 週截止日期               |
| flow_total_contracts    | number | 總流量（合約數）             |
| flow_by_group_contracts | object | 各群組流量                   |
| net_position_by_group   | object | 各群組淨部位                 |
| buying_firepower        | object | 各群組火力分數               |
| macro_tailwind_score    | number | 宏觀順風評分（0-1）          |
| macro_components        | object | 宏觀成分詳情                 |

### annotations 區塊

| 欄位     | 類型     | 說明                         |
|----------|----------|------------------------------|
| label    | string   | 標註名稱                     |
| rule_hit | boolean  | 規則是否觸發                 |
| evidence | string[] | 觸發證據                     |
| date     | string   | 觸發日期                     |

### validation 區塊

| 欄位                  | 類型   | 說明                         |
|-----------------------|--------|------------------------------|
| wed_fri_buyback       | object | 週中回補驗證                 |
| macro_alignment       | object | 宏觀一致性                   |
| overall_consistency   | number | 整體一致性評分               |
| confidence_adjustment | number | 信心調整值                   |

---

## 可能的 call 值

| call                        | 意義                           |
|-----------------------------|--------------------------------|
| Funds back & buying         | 基金回來買進                   |
| Funds selling               | 基金賣出                       |
| Macro mood bullish          | 宏觀情緒偏多                   |
| Macro headwind              | 宏觀逆風                       |
| Crowded long - caution      | 多單擁擠，謹慎                 |
| Extreme short - watch       | 極端空頭，留意反彈             |
| Mixed signals               | 訊號混合                       |
| Holiday thin flows          | 假日薄流量                     |

---

## 快速輸出模式

使用 `--quick` 時的簡化輸出：

```json
{
  "cot_week_end": "2026-01-21",
  "flow_total_contracts": 58,
  "flow_by_group": {"grains": 35, "oilseeds": 25, "meats": 5, "softs": 0},
  "buying_firepower": {"total": 0.63},
  "macro_tailwind_score": 0.67,
  "call": "Funds back & buying"
}
```
