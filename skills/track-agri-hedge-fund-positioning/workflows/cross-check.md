# Workflow: 宏觀與基本面交叉驗證

<required_reading>
**執行前請先閱讀：**
1. references/methodology.md
2. references/macro-indicators.md
</required_reading>

<process>

## Step 1: 確認驗證目標

交叉驗證的核心問題：
- COT 週資料只到週二，週三～週五的「買回」是否有代理證據？
- 資金流向是否與宏觀風向一致？
- 基本面事件是否支持當週的流量變化？

```python
validation_targets = {
    "wed_fri_buyback": "週三～週五是否出現回補跡象",
    "macro_alignment": "資金流向與宏觀指標是否同向",
    "fundamental_trigger": "是否有對應的基本面事件"
}
```

## Step 2: 週中回補驗證（Wed-Fri）

```python
def validate_wed_fri_buyback(cot_week_end, price_df, macro_df):
    """驗證週三～週五的回補跡象"""

    # 取得 Wed-Fri 的資料
    wed = cot_week_end + timedelta(days=1)  # COT 截止週二
    fri = cot_week_end + timedelta(days=3)

    wed_fri_data = price_df.loc[wed:fri]

    evidence = {
        "price_momentum": None,
        "volume_change": None,
        "macro_resonance": None
    }

    # 1. 價格動能
    if len(wed_fri_data) > 0:
        wed_fri_return = (wed_fri_data['close'].iloc[-1] /
                          wed_fri_data['close'].iloc[0] - 1)
        evidence["price_momentum"] = {
            "value": wed_fri_return,
            "signal": "bullish" if wed_fri_return > 0.005 else
                      "bearish" if wed_fri_return < -0.005 else "neutral"
        }

    # 2. 成交量變化
    if 'volume' in wed_fri_data.columns:
        avg_volume = price_df['volume'].rolling(20).mean().iloc[-1]
        wed_fri_volume = wed_fri_data['volume'].mean()
        vol_ratio = wed_fri_volume / avg_volume
        evidence["volume_change"] = {
            "value": vol_ratio,
            "signal": "elevated" if vol_ratio > 1.2 else "normal"
        }

    # 3. 宏觀共振
    macro_wed_fri = macro_df.loc[wed:fri]
    if len(macro_wed_fri) > 0:
        usd_down = macro_wed_fri['dxy_ret'].sum() < 0
        oil_up = macro_wed_fri['wti_ret'].sum() > 0
        metals_up = macro_wed_fri['metals_ret'].sum() > 0

        resonance_score = sum([usd_down, oil_up, metals_up]) / 3
        evidence["macro_resonance"] = {
            "value": resonance_score,
            "details": {
                "usd_down": usd_down,
                "oil_up": oil_up,
                "metals_up": metals_up
            },
            "signal": "supportive" if resonance_score >= 0.67 else
                      "mixed" if resonance_score >= 0.33 else "unsupportive"
        }

    return evidence
```

## Step 3: 宏觀一致性驗證

```python
def validate_macro_alignment(flow_direction, macro_score):
    """驗證資金流向與宏觀指標的一致性"""

    alignment = {
        "flow_direction": "inflow" if flow_direction > 0 else "outflow",
        "macro_bias": "bullish" if macro_score >= 0.67 else
                      "bearish" if macro_score <= 0.33 else "neutral",
        "aligned": None,
        "interpretation": None
    }

    # 判斷一致性
    if flow_direction > 0 and macro_score >= 0.5:
        alignment["aligned"] = True
        alignment["interpretation"] = "資金流入且宏觀順風，敘事一致"
    elif flow_direction < 0 and macro_score <= 0.5:
        alignment["aligned"] = True
        alignment["interpretation"] = "資金流出且宏觀逆風，敘事一致"
    elif flow_direction > 0 and macro_score < 0.5:
        alignment["aligned"] = False
        alignment["interpretation"] = "資金流入但宏觀逆風，需警惕反轉"
    else:
        alignment["aligned"] = False
        alignment["interpretation"] = "資金流出但宏觀順風，可能是超賣反彈機會"

    return alignment
```

## Step 4: 基本面事件匹配

```python
FUNDAMENTAL_EVENTS = {
    "export_sales": {
        "source": "USDA FAS Weekly Export Sales",
        "frequency": "weekly",
        "impact_groups": ["grains", "oilseeds"]
    },
    "wasde_release": {
        "source": "USDA WASDE",
        "frequency": "monthly",
        "impact_groups": ["grains", "oilseeds", "meats", "softs"]
    },
    "crop_progress": {
        "source": "USDA Crop Progress",
        "frequency": "weekly",
        "impact_groups": ["grains", "oilseeds"]
    },
    "cattle_on_feed": {
        "source": "USDA Cattle on Feed",
        "frequency": "monthly",
        "impact_groups": ["meats"]
    }
}

def match_fundamental_events(cot_week_end, flow_by_group):
    """匹配當週的基本面事件"""
    week_start = cot_week_end - timedelta(days=6)

    matched_events = []

    for event_name, event_info in FUNDAMENTAL_EVENTS.items():
        # 檢查該週是否有事件發布
        event_dates = get_event_dates(event_name, week_start, cot_week_end)

        if event_dates:
            # 取得事件內容
            event_data = fetch_event_data(event_name, event_dates[-1])

            # 判斷事件偏向
            bias = interpret_event_bias(event_data)

            # 檢查與流量方向的一致性
            for group in event_info["impact_groups"]:
                if group in flow_by_group:
                    flow = flow_by_group[group]
                    consistent = (bias == "bullish" and flow > 0) or \
                                (bias == "bearish" and flow < 0)

                    matched_events.append({
                        "event": event_name,
                        "date": str(event_dates[-1]),
                        "bias": bias,
                        "group": group,
                        "flow": flow,
                        "consistent": consistent
                    })

    return matched_events
```

## Step 5: 生成驗證報告

```python
def generate_validation_report(cot_result, validation_results):
    """生成交叉驗證報告"""

    report = {
        "validation_timestamp": datetime.now().isoformat(),
        "cot_week_end": cot_result["cot_week_end"],

        "wed_fri_validation": validation_results["wed_fri"],
        "macro_alignment": validation_results["macro"],
        "fundamental_events": validation_results["fundamentals"],

        "overall_consistency": None,
        "confidence_adjustment": None,
        "narrative_assessment": None
    }

    # 計算整體一致性分數
    consistency_scores = []

    # Wed-Fri 驗證
    wed_fri = validation_results["wed_fri"]
    if wed_fri["price_momentum"]["signal"] == "bullish":
        consistency_scores.append(1)
    elif wed_fri["price_momentum"]["signal"] == "bearish":
        consistency_scores.append(0)
    else:
        consistency_scores.append(0.5)

    # 宏觀一致性
    if validation_results["macro"]["aligned"]:
        consistency_scores.append(1)
    else:
        consistency_scores.append(0)

    # 基本面一致性
    fundamentals = validation_results["fundamentals"]
    if fundamentals:
        fund_score = sum(1 for f in fundamentals if f["consistent"]) / len(fundamentals)
        consistency_scores.append(fund_score)

    report["overall_consistency"] = sum(consistency_scores) / len(consistency_scores)

    # 信心調整
    if report["overall_consistency"] >= 0.7:
        report["confidence_adjustment"] = 0.1  # 增加 10% 信心
        report["narrative_assessment"] = "敘事高度一致，可信度高"
    elif report["overall_consistency"] >= 0.5:
        report["confidence_adjustment"] = 0
        report["narrative_assessment"] = "敘事部分一致，需持續觀察"
    else:
        report["confidence_adjustment"] = -0.15  # 降低 15% 信心
        report["narrative_assessment"] = "敘事存在矛盾，謹慎對待"

    return report
```

## Step 6: 輸出驗證結果

```bash
python scripts/cross_check.py \
  --cot-result output/result.json \
  --output output/validation_report.json
```

</process>

<success_criteria>
此工作流程完成時應確認：

- [ ] Wed-Fri 價格動能已計算
- [ ] 宏觀一致性已評估
- [ ] 基本面事件已匹配
- [ ] 整體一致性分數落在 0-1 範圍
- [ ] 信心調整建議已給出
- [ ] 敘事評估結論明確
</success_criteria>
