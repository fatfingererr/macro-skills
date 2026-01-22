# Markdown 報告模板

本文件定義 `detect-shanghai-silver-stock-drain` skill 的 Markdown 報告輸出格式。

---

## 完整報告模板

```markdown
# 上海白銀庫存耗盡分析報告

**截至日期**：{as_of}
**數據來源**：{sources}
**分析單位**：{unit}

---

## 核心結論

| 指標 | 數值 | 判定 |
|------|------|------|
| **訊號等級** | {signal} | {signal_emoji} {signal_description} |
| **合併庫存** | {latest_combined_stock} {unit} | {level_description} |
| **庫存分位數** | {level_percentile_pct}% | {level_assessment} |

---

## 三維度量化結果

### 方向、速度、加速度

| 維度 | 數值 | Z 分數 | 解讀 |
|------|------|--------|------|
| **方向 (Δ1)** | {delta1_weekly} | - | {direction_description} |
| **速度** | {drain_rate_4w_avg} | {z_drain_rate} | {speed_description} |
| **加速度** | {acceleration_4w_avg} | {z_acceleration} | {accel_description} |

### 訊號判定邏輯

{condition_A_check} A. 庫存水位偏低（{level_percentile_pct}% {condition_A_operator} 20% 門檻）
{condition_B_check} B. 耗盡速度異常（z_drain = {z_drain_rate} {condition_B_operator} -1.5）
{condition_C_check} C. 耗盡加速（z_accel = {z_acceleration} {condition_C_operator} +1.0）

→ {signal_logic} → **{signal}**

---

## 歷史脈絡

| 指標 | 數值 |
|------|------|
| 歷史最高庫存 | {decade_high_stock} {unit} |
| 歷史最低庫存 | {decade_low_stock} {unit} |
| 當前分位數 | {level_percentile_pct}% |
| 距離歷史低點 | {distance_to_decade_low_pct}% |

---

## 交叉驗證（如啟用）

**綜合信心度**：{confidence_pct}%

| 指標 | 狀態 | 詳情 |
|------|------|------|
{cross_validation_rows}

**驗證後訊號**：{validated_signal}

---

## 敘事解讀

{narrative_list}

---

## 數據口徑說明

{caveats_list}

---

## 下一步建議

{next_steps_list}

---

*報告生成時間：{generated_at}*
*技能版本：{skill_version}*
```

---

## 變數說明

### 訊號相關

| 變數 | 說明 | 範例值 |
|------|------|--------|
| {signal} | 訊號等級 | HIGH_LATE_STAGE_SUPPLY_SIGNAL |
| {signal_emoji} | 訊號表情符號 | 🔴 / 🟡 / 🟢 |
| {signal_description} | 訊號描述 | 晚期供給訊號 |

### 數據相關

| 變數 | 說明 | 範例值 |
|------|------|--------|
| {latest_combined_stock} | 最新合併庫存 | 1133.3 |
| {level_percentile_pct} | 分位數百分比 | 12 |
| {z_drain_rate} | 耗盡速度 Z 分數 | -2.1 |
| {z_acceleration} | 加速度 Z 分數 | +1.4 |

### 條件判定

| 變數 | 說明 | 範例值 |
|------|------|--------|
| {condition_A_check} | 條件 A 狀態 | ✅ / ❌ |
| {condition_B_check} | 條件 B 狀態 | ✅ / ❌ |
| {condition_C_check} | 條件 C 狀態 | ✅ / ❌ |

---

## 範例輸出

### HIGH 訊號報告

```markdown
# 上海白銀庫存耗盡分析報告

**截至日期**：2026-01-16
**數據來源**：SGE, SHFE
**分析單位**：tonnes

---

## 核心結論

| 指標 | 數值 | 判定 |
|------|------|------|
| **訊號等級** | HIGH_LATE_STAGE_SUPPLY_SIGNAL | 🔴 晚期供給訊號 |
| **合併庫存** | 1,133.3 噸 | 歷史低檔 |
| **庫存分位數** | 12% | 低於 20% 門檻 |

---

## 三維度量化結果

### 方向、速度、加速度

| 維度 | 數值 | Z 分數 | 解讀 |
|------|------|--------|------|
| **方向 (Δ1)** | -58.4 | - | 庫存下降中 |
| **速度** | 58.4 噸/週 | -2.1 | ⚠️ 流出顯著高於常態 |
| **加速度** | +9.7 | +1.4 | ⚠️ 流出正在加速 |

### 訊號判定邏輯

✅ A. 庫存水位偏低（12% < 20% 門檻）
✅ B. 耗盡速度異常（z_drain = -2.1 ≤ -1.5）
✅ C. 耗盡加速（z_accel = +1.4 ≥ +1.0）

→ A+B+C 同時成立 → **HIGH_LATE_STAGE_SUPPLY_SIGNAL**

---

## 敘事解讀

1. 上海合併庫存處於歷史低分位（約 12% 分位）。
2. 近 4 週平均庫存流出顯著高於常態（耗盡速度 Z=-2.1）。
3. 流出在加速（加速度 Z=+1.4），符合「方向 + 速度」核心判準。
4. 若同時觀察到其他市場庫存/溢價惡化，可進一步提高信心。

---

## 數據口徑說明

⚠️ 這是「交易所可交割/倉單/指定倉庫」口徑，不等於全中國社會庫存。
⚠️ 單週跳動可能反映倉儲/交割規則變動或搬倉，需用平滑與多來源交叉確認。

---

*報告生成時間：2026-01-16T10:30:00Z*
*技能版本：0.1.0*
```

---

## 程式碼範例

### Python 生成報告

```python
from string import Template

def generate_markdown_report(result):
    """從分析結果生成 Markdown 報告"""
    template = Template(open("templates/output-markdown.md").read())

    # 計算派生變數
    signal_emoji = {
        "HIGH_LATE_STAGE_SUPPLY_SIGNAL": "🔴",
        "MEDIUM_SUPPLY_TIGHTENING": "🟡",
        "WATCH": "🟠",
        "NO_SIGNAL": "🟢"
    }.get(result["result"]["signal"], "⚪")

    # 填入變數
    report = template.substitute(
        as_of=result["as_of"],
        sources=", ".join(result["sources"]),
        unit=result["unit"],
        signal=result["result"]["signal"],
        signal_emoji=signal_emoji,
        latest_combined_stock=f"{result['result']['latest_combined_stock']:,.1f}",
        level_percentile_pct=f"{result['result']['level_percentile']*100:.0f}",
        z_drain_rate=f"{result['result']['z_scores']['z_drain_rate']:.1f}",
        z_acceleration=f"+{result['result']['z_scores']['z_acceleration']:.1f}",
        # ... 更多變數
    )

    return report
```
