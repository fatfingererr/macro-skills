# Workflow: 歷史事件對照分析

<required_reading>
**執行前請閱讀：**
1. references/methodology.md - 形狀比對方法論
2. references/wudsho-mechanism.md - WUDSHO 指標機制
</required_reading>

<process>

## Step 1: 理解歷史基準窗口

本技能預設的歷史基準窗口：

### COVID_2020 (2020-01-01 ~ 2020-06-30)
**背景**：
- 2020 年初 COVID-19 全球擴散
- 市場恐慌，流動性危機
- Fed 宣布無限 QE

**WUDSHO 走勢**：
- 初期：利率快速下降，未攤銷折價變動劇烈
- 後期：QE 大量購債，持有結構改變

**後續發展**：
- 市場 V 型反轉
- 股市創新高
- 通膨最終爆發

### GFC_2008 (2008-09-01 ~ 2009-03-31)
**背景**：
- 雷曼兄弟倒閉
- 全球金融危機
- 信用凍結

**WUDSHO 走勢**：
- 劇烈波動
- QE1 開始後逐漸穩定

**後續發展**：
- 長期低利率環境
- 量化寬鬆常態化
- 緩慢復甦

### TAPER_2013 (2013-05-01 ~ 2013-09-30)
**背景**：
- Bernanke 暗示縮減 QE
- 「縮減恐慌」(Taper Tantrum)
- 新興市場資金外流

**WUDSHO 走勢**：
- 利率上升驅動
- 非系統性壓力

**後續發展**：
- 利率上升但經濟持續復甦
- 股市續創新高
- 2015 年開始升息

### RATE_HIKE_2022 (2022-01-01 ~ 2022-12-31)
**背景**：
- Fed 激進升息
- 通膨對抗
- 債券大熊市

**WUDSHO 走勢**：
- 利率快速上升
- 持有債券市值大幅下降
- 未攤銷折價劇增

**後續發展**：
- SVB 銀行倒閉（2023-03）
- 區域銀行危機
- Fed 緊急流動性支持

## Step 2: 事件後統計分析

對每個歷史事件，計算後續的市場表現：

### 計算指標

```python
forward_windows = [60, 180, 365]  # 天

for event in historical_events:
    for window in forward_windows:
        # 股市報酬
        sp500_return = calculate_return(event.end_date, window)

        # 信用利差變化
        spread_change = calculate_spread_change(event.end_date, window)

        # VIX 變化
        vix_change = calculate_vix_change(event.end_date, window)

        # 最大回撤
        max_drawdown = calculate_max_drawdown(event.end_date, window)
```

### 歷史統計表

| 事件 | 60d 報酬 | 180d 報酬 | 365d 報酬 | 最大回撤 |
|------|----------|-----------|-----------|----------|
| COVID_2020 | +15% | +35% | +50% | -34% (已發生) |
| GFC_2008 | -15% | +20% | +30% | -57% (已發生) |
| TAPER_2013 | +5% | +10% | +15% | -6% |
| RATE_HIKE_2022 | -5% | +10% | +20% | -25% |

**注意**：這是「條件分布」，不是預測。

## Step 3: 當前 vs. 歷史比較

### 形狀相似度比較

```
當前 vs. COVID_2020: corr=0.85, dtw=0.42, sim=0.82
當前 vs. GFC_2008:   corr=0.45, dtw=1.20, sim=0.38
當前 vs. TAPER_2013: corr=0.72, dtw=0.65, sim=0.68
當前 vs. RATE_HIKE:  corr=0.78, dtw=0.55, sim=0.75
```

### 壓力指標比較

| 指標 | 當前 | COVID 峰值 | GFC 峰值 | 2022 峰值 |
|------|------|------------|----------|-----------|
| IG 利差 | 1.0% | 4.0% | 6.0% | 1.5% |
| VIX | 15 | 80 | 80 | 35 |
| HY 利差 | 3.5% | 11% | 20% | 6% |

## Step 4: 情境推演

### 情境 A: 形狀相似 + 壓力驗證支持
- 若未來 60 天內壓力指標開始惡化
- 參考歷史：COVID 初期、GFC 初期
- 可能發展：市場波動加劇，Fed 可能介入

### 情境 B: 形狀相似 + 壓力驗證不支持
- 當前狀態：壓力指標中性
- 參考歷史：Taper Tantrum
- 可能發展：利率效果為主，非系統性壓力

### 情境 C: 形狀開始偏離
- 若相關係數開始下降
- 圖形類比失效
- 回歸正常觀察

## Step 5: 輸出歷史對照報告

```bash
python scripts/pattern_detector.py \
  --historical_analysis \
  --output historical_report.json
```

輸出內容：
- 各基準窗口的形狀相似度
- 歷史事件後續統計
- 當前 vs. 歷史的壓力指標比較
- 情境推演說明

</process>

<success_criteria>
工作流完成時應產出：

- [ ] 各基準窗口的詳細說明
- [ ] 形狀相似度排名
- [ ] 歷史事件後續統計
- [ ] 壓力指標的歷史比較
- [ ] 情境推演（至少 2-3 個情境）
- [ ] 明確標註「條件分布 ≠ 預測」
</success_criteria>
