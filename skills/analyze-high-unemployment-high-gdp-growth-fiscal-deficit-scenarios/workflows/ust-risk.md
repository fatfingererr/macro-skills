<required_reading>
**執行前請先閱讀：**
1. references/methodology.md - 了解雙通道風險框架
2. templates/output-markdown.md - 了解報告格式
</required_reading>

<objective>
生成專注於長天期美債（UST）供給/利率風險的深度報告，包含：
- 供給壓力通道分析（赤字 → 發債 → 期限溢酬）
- 避險買盤通道分析（風險趨避 → 債券買盤）
- 兩股力量的主導性判斷指標
- 監控建議與切換訊號
</objective>

<process>

<step name="1_run_base_analysis">
**Step 1: 執行基礎情境分析**

首先取得赤字/GDP 投影結果：
```bash
python scripts/analyzer.py --quick --output base_result.json
```

或使用自訂情境：
```bash
python scripts/analyzer.py --scenario '{"horizon_quarters": 8, "gdp_path": "high_gdp_sticky", "unemployment_shock": {"type": "rate_jump", "size": 1.5, "speed": "fast"}}' --output base_result.json
```
</step>

<step name="2_supply_pressure_analysis">
**Step 2: 供給壓力通道分析**

分析赤字擴張對長端利率的影響：

**2.1 淨發行估算**：
```python
# 赤字/GDP → 年度淨發行額
gdp_level = 28_000  # 假設 GDP 28 兆美元
deficit_gdp_mid = 0.135  # 中位數 13.5%
net_issuance = gdp_level * deficit_gdp_mid  # 約 3.78 兆

# 與當前比較
current_issuance = 2_000  # 假設當前約 2 兆
issuance_increase = (net_issuance - current_issuance) / current_issuance
```

**2.2 期限溢酬敏感度**：
```python
# 歷史上發債增加與期限溢酬的關係
# ACM Term Premium 與 Net Issuance 的迴歸係數
term_premium_sensitivity = 0.05  # 每增加 1 兆發債，期限溢酬上升約 5 bps
projected_term_premium_change = term_premium_sensitivity * (net_issuance - current_issuance) / 1000
```

**2.3 供給壓力評級**：
| 赤字/GDP 區間 | 供給壓力等級 | 期限溢酬影響估計 |
|---------------|--------------|------------------|
| < 8%          | 低           | 有限             |
| 8% - 12%      | 中           | +20-40 bps       |
| 12% - 16%     | 高           | +40-80 bps       |
| > 16%         | 極高         | +80-120+ bps     |
</step>

<step name="3_risk_aversion_analysis">
**Step 3: 避險買盤通道分析**

分析勞動轉弱對避險需求的影響：

**3.1 歷史參照**：
```python
# 過去勞動轉弱期間的債券買盤流入
historical_episodes = [
    {"period": "2008-2009", "tlt_return": "+33%", "10y_yield_change": "-200 bps"},
    {"period": "2020 Q1", "tlt_return": "+21%", "10y_yield_change": "-150 bps"},
]
```

**3.2 避險力道指標**：
- **VIX**：> 25 表示避險需求上升
- **信用利差**：IG 利差擴大 > 50 bps
- **股債相關性**：轉為負相關表示避險模式

**3.3 避險壓力評級**：
| 指標組合                     | 避險力道等級 | 對長端的影響     |
|------------------------------|--------------|------------------|
| VIX < 20, 利差穩定           | 低           | 避險買盤有限     |
| VIX 20-30, 利差小幅擴大      | 中           | 部分對沖供給壓力 |
| VIX > 30, 利差大幅擴大       | 高           | 可能主導長端走勢 |
</step>

<step name="4_dominant_force_assessment">
**Step 4: 主導力量判斷**

建立判斷框架：

```
供給壓力 vs 避險買盤：誰主導？

┌────────────────────────────────────────────────────────────┐
│                                                             │
│   供給主導區                        避險主導區              │
│   ┌─────────┐                      ┌─────────┐             │
│   │ 赤字↑   │                      │ 恐慌↑   │             │
│   │ VIX正常 │     ←────────────→   │ VIX飆升 │             │
│   │ 利差穩定│                      │ 利差暴增│             │
│   └─────────┘                      └─────────┘             │
│        ↓                                ↓                   │
│   長端殖利率↑                      長端殖利率↓              │
│                                                             │
└────────────────────────────────────────────────────────────┘

判斷指標：
1. VIX 是否 > 30？
2. IG 信用利差是否 > +100 bps（從低點）？
3. 金融壓力指數是否轉正？
4. 股債相關性是否轉負？

滿足 ≥3 項 → 避險主導
滿足 ≤1 項 → 供給主導
滿足 2 項 → 混合/拉鋸
```
</step>

<step name="5_monitoring_framework">
**Step 5: 建立監控框架**

**關鍵監控指標**：

| 指標             | 數據源    | 供給主導訊號      | 避險主導訊號      |
|------------------|-----------|-------------------|-------------------|
| VIX              | Yahoo     | < 25              | > 30              |
| IG 信用利差      | FRED      | 穩定              | 擴大 > 50 bps     |
| 通膨預期 (5Y5Y)  | FRED      | > 2.5%            | < 2%              |
| 國債拍賣尾差     | Treasury  | > 2 bps           | < -2 bps          |
| 外國持有變化     | TIC       | 下降              | 上升              |

**切換訊號**：
- 供給 → 避險：VIX 突破 30 + 信用利差暴增
- 避險 → 供給：VIX 回落 < 20 + 拍賣持續疲軟
</step>

<step name="6_generate_report">
**Step 6: 生成 UST 風險報告**

使用模板生成報告：

```bash
python scripts/analyzer.py \
    --ust-risk-report \
    --input base_result.json \
    --output ust_risk_report.md
```

報告結構：
1. 執行摘要（當前狀態 + 主要結論）
2. 供給壓力通道分析
3. 避險買盤通道分析
4. 主導力量判斷
5. 監控指標清單
6. 情境風險矩陣
7. 行動建議
</step>

</process>

<success_criteria>
UST 風險報告完成時：
- [ ] 供給壓力通道分析完整（赤字 → 發債 → 期限溢酬）
- [ ] 避險買盤通道分析完整（指標 + 歷史參照）
- [ ] 主導力量判斷框架清晰
- [ ] 監控指標清單可操作
- [ ] 報告格式符合模板
</success_criteria>
