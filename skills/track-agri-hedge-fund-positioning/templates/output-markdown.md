# Markdown 報告模板

## 模板結構

```markdown
# 農產品對沖基金部位追蹤報告

> **報告日期**: {generated_at}
> **資料截止**: {as_of}（COT 週截止日）

---

## TL;DR

**{call}** (信心: {confidence:.0%})

{why[0]}

---

## 最新指標

### 週流量（合約數）

| 群組     | 流量     | 淨部位       | 火力   |
|----------|----------|--------------|--------|
| 穀物     | {grains_flow:+,} | {grains_pos:,} | {grains_fp:.0%} |
| 油籽     | {oilseeds_flow:+,} | {oilseeds_pos:,} | {oilseeds_fp:.0%} |
| 肉類     | {meats_flow:+,} | {meats_pos:,} | {meats_fp:.0%} |
| 軟性商品 | {softs_flow:+,} | {softs_pos:,} | {softs_fp:.0%} |
| **總計** | **{total_flow:+,}** | **{total_pos:,}** | **{total_fp:.0%}** |

### 宏觀順風

**評分: {macro_score:.0%}**

| 指標 | 方向 | 訊號 |
|------|------|------|
| 美元 | {usd_direction} | {usd_signal} |
| 原油 | {crude_direction} | {crude_signal} |
| 金屬 | {metals_direction} | {metals_signal} |

---

## 結論依據

{for why in why_list}
- {why}
{endfor}

---

## 風險提示

{for risk in risks}
- ⚠️ {risk}
{endfor}

---

## 下一步建議

{for step in next_steps}
1. {step}
{endfor}

---

## 圖表標註

{for ann in annotations}
### {ann.label}
- **觸發**: {ann.rule_hit}
- **證據**: {ann.evidence}
{endfor}

---

## 驗證結果

### 週中回補驗證（Wed-Fri）

| 項目       | 結果              |
|------------|-------------------|
| 價格動能   | {wed_fri_momentum} |
| 成交量     | {wed_fri_volume}   |
| 宏觀共振   | {wed_fri_resonance:.0%} |

### 敘事一致性

**整體一致性: {overall_consistency:.0%}**

{narrative_assessment}

---

## 技術細節

- COT 報表類型: {cot_report_type}
- 交易者分類: {trader_group}
- 部位衡量: {position_metric}
- 火力視窗: {lookback_weeks} 週
- 資料來源: CFTC / Yahoo Finance / USDA

---

*本報告由 track-agri-hedge-fund-positioning v{version} 生成*
```

---

## 填充範例

```markdown
# 農產品對沖基金部位追蹤報告

> **報告日期**: 2026-01-27 10:30 UTC
> **資料截止**: 2026-01-21（COT 週截止日）

---

## TL;DR

**Funds back & buying** (信心: 72%)

COT 週部位變化顯示農產品總流量由負轉正，分組同步改善，宏觀順風。

---

## 最新指標

### 週流量（合約數）

| 群組     | 流量     | 淨部位       | 火力   |
|----------|----------|--------------|--------|
| 穀物     | +35,000  | 125,000      | 58%    |
| 油籽     | +25,000  | 85,000       | 67%    |
| 肉類     | +5,000   | 12,000       | 41%    |
| 軟性商品 | +0       | -5,000       | 75%    |
| **總計** | **+65,000** | **217,000** | **63%** |

### 宏觀順風

**評分: 67%**

| 指標 | 方向 | 訊號     |
|------|------|----------|
| 美元 | ↓    | 利多商品 |
| 原油 | ↑    | 風險偏好 |
| 金屬 | →    | 中性     |

---

## 結論依據

- COT 週部位變化顯示農產品總流量由負轉正
- 分組（穀物/油籽）同步改善，非單一品種噪音
- 宏觀順風：美元走弱、原油與金屬偏強

---

## 風險提示

- ⚠️ COT 只到週二：Wed–Fri 的『買回』屬推估，需要價格/未平倉等代理證據佐證
- ⚠️ USDA 報告或天氣/南美供給變動可能讓訊號反轉

---

## 下一步建議

1. 監控週五 USDA Export Sales 報告
2. 觀察火力是否持續回升
3. 若火力突破 70%，考慮減碼

---

## 圖表標註

### macro_mood_bullish
- **觸發**: ✓
- **證據**: USD down, crude up

### grains_momentum_up
- **觸發**: ✓
- **證據**: Grains flow turned positive, Corn export sales up

---

## 驗證結果

### 週中回補驗證（Wed-Fri）

| 項目       | 結果              |
|------------|-------------------|
| 價格動能   | 偏多              |
| 成交量     | 正常              |
| 宏觀共振   | 67%               |

### 敘事一致性

**整體一致性: 78%**

敘事高度一致，可信度高

---

## 技術細節

- COT 報表類型: legacy
- 交易者分類: noncommercial
- 部位衡量: net
- 火力視窗: 156 週
- 資料來源: CFTC / Yahoo Finance / USDA

---

*本報告由 track-agri-hedge-fund-positioning v0.1.0 生成*
```

---

## Python 生成函數

```python
def generate_markdown_report(result: dict) -> str:
    """生成 Markdown 報告"""
    template = """
# 農產品對沖基金部位追蹤報告

> **報告日期**: {generated_at}
> **資料截止**: {as_of}（COT 週截止日）

---

## TL;DR

**{call}** (信心: {confidence:.0%})

{primary_reason}

---

## 最新指標

### 週流量（合約數）

| 群組     | 流量     | 淨部位       | 火力   |
|----------|----------|--------------|--------|
| 穀物     | {grains_flow:+,} | {grains_pos:,} | {grains_fp:.0%} |
| 油籽     | {oilseeds_flow:+,} | {oilseeds_pos:,} | {oilseeds_fp:.0%} |
| 肉類     | {meats_flow:+,} | {meats_pos:,} | {meats_fp:.0%} |
| 軟性商品 | {softs_flow:+,} | {softs_pos:,} | {softs_fp:.0%} |
| **總計** | **{total_flow:+,}** | **{total_pos:,}** | **{total_fp:.0%}** |

### 宏觀順風評分: {macro_score:.0%}

---

## 結論依據

{reasons}

---

## 風險提示

{risks}

---

*本報告由 track-agri-hedge-fund-positioning v{version} 生成*
"""

    # 填充模板
    metrics = result['latest_metrics']
    summary = result['summary']

    return template.format(
        generated_at=result['generated_at'],
        as_of=result['as_of'],
        call=summary['call'],
        confidence=summary['confidence'],
        primary_reason=summary['why'][0],
        grains_flow=metrics['flow_by_group_contracts']['grains'],
        grains_pos=metrics['net_position_by_group']['grains'],
        grains_fp=metrics['buying_firepower']['grains'],
        oilseeds_flow=metrics['flow_by_group_contracts']['oilseeds'],
        oilseeds_pos=metrics['net_position_by_group']['oilseeds'],
        oilseeds_fp=metrics['buying_firepower']['oilseeds'],
        meats_flow=metrics['flow_by_group_contracts']['meats'],
        meats_pos=metrics['net_position_by_group']['meats'],
        meats_fp=metrics['buying_firepower']['meats'],
        softs_flow=metrics['flow_by_group_contracts']['softs'],
        softs_pos=metrics['net_position_by_group']['softs'],
        softs_fp=metrics['buying_firepower']['softs'],
        total_flow=metrics['flow_total_contracts'],
        total_pos=metrics['net_position_by_group']['total'],
        total_fp=metrics['buying_firepower']['total'],
        macro_score=metrics['macro_tailwind_score'],
        reasons='\n'.join(f'- {r}' for r in summary['why']),
        risks='\n'.join(f'- ⚠️ {r}' for r in summary['risks']),
        version=result['version']
    )
```
