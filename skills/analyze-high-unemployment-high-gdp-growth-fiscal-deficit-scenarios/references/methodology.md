<overview>
本文件詳細說明「高失業 + 高 GDP」情境下財政赤字推估的方法論，包含理論基礎、指標建構、分析模型，以及 UST 風險雙通道框架。
</overview>

<theoretical_foundation>

<concept name="labor_fiscal_linkage">
**勞動-財政連結機制**

當勞動市場轉弱時，財政赤字擴張主要透過兩個管道：

**1. 自動穩定器 (Automatic Stabilizers)**
- 失業上升 → 失業救濟支出自動增加
- 收入下降 → 所得稅收自動減少
- 消費減緩 → 銷售稅收減少

估計係數：失業率每上升 1%，赤字/GDP 約增加 0.3-0.5%（自動穩定器效應）

**2. 自主性財政政策 (Discretionary Fiscal Policy)**
- 經濟轉弱時政府可能推出刺激方案
- 規模不定，取決於政治意願與財政空間
- 2008: TARP + ARRA ≈ GDP 5%
- 2020: CARES + 後續 ≈ GDP 10%+

**關鍵洞察**：
自動穩定器效應相對穩定可預測，自主性政策變異大。本技能的「事件分組區間法」能捕捉兩者的歷史分布。
</concept>

<concept name="divergence_scenario">
**勞動-GDP 背離情境**

本技能聚焦的特殊情境：**勞動轉弱但 GDP 仍高**

這種背離通常出現在：
1. **景氣循環晚期**：領先指標（就業）先轉，GDP 尚未反映
2. **結構性調整期**：生產力提升導致「無就業成長」
3. **名目 GDP 被通膨撐高**：實質經濟放緩但名目數字仍高
4. **財政/信用擴張期**：政府支出或信貸撐住總需求

為什麼這個情境重要？
- 勞動轉弱啟動自動穩定器
- GDP 仍高意味稅基尚未崩潰
- 但赤字擴張已經開始
- 這是赤字從「溫和」跳升到「大幅」的關鍵轉折點
</concept>

</theoretical_foundation>

<indicator_construction>

<indicator name="ujo">
**UJO（失業/職缺比）**

```
UJO = UNEMPLOY / JTSJOL
    = 失業人數 / 職缺數
```

**解讀**：
| UJO 水準 | 市場狀態 | 歷史參照 |
|----------|----------|----------|
| < 0.5    | 極度緊張 | 2021-2022 復甦期 |
| 0.5-1.0  | 正常偏緊 | 2015-2019 擴張期 |
| 1.0-1.5  | 正常偏鬆 | 2010-2014 復甦中 |
| 1.5-2.0  | 鬆弛     | 2003-2004 |
| > 2.0    | 嚴重鬆弛 | 2009-2010 金融海嘯 |

**優點**：能捕捉「職缺掉很快、失業還沒上來」的早期轉弱階段
**缺點**：JOLTS 數據從 2001 年才開始
</indicator>

<indicator name="sahm_rule">
**Sahm Rule**

```
Sahm = 3M_MA(UNRATE) - min(UNRATE over last 12M)
```

**解讀**：
- Sahm ≥ 0.5 → 衰退警示（歷史上準確率極高）
- Sahm ≥ 0.3 → 勞動轉弱早期跡象
- Sahm < 0.2 → 勞動市場穩定

**優點**：由 Fed 經濟學家 Claudia Sahm 提出，有理論基礎
**缺點**：是「確認型」指標，轉弱後才會觸發
</indicator>

<indicator name="delta_ur">
**ΔUR（失業率變化）**

```
ΔUR = UNRATE(t) - UNRATE(t-6M)
```

**解讀**：
| ΔUR 6M | 市場狀態 |
|--------|----------|
| < 0    | 改善中   |
| 0-0.3  | 穩定     |
| 0.3-1.0| 溫和惡化 |
| > 1.0  | 快速惡化 |

**優點**：簡單直觀，數據覆蓋長
**缺點**：對起點敏感（從低點上升 vs 從中等水準上升意義不同）
</indicator>

<indicator name="high_gdp">
**高 GDP 條件**

```python
# 方法 1：分位數法
GDP_pctl = percentile_rank(GDP, lookback_years)
HIGH_GDP = GDP_pctl >= 0.70

# 方法 2：成長法
GDP_growth = (GDP / GDP.shift(4) - 1) * 100  # YoY
HIGH_GDP = GDP_growth > 0

# 方法 3：組合法（建議）
HIGH_GDP = (GDP_pctl >= 0.70) | (GDP_growth > 0)
```
</indicator>

</indicator_construction>

<analysis_models>

<model name="event_study_banding">
**事件分組區間法 (Event Study Banding)**

最貼近「歷史顯示…」敘事的方法。

**步驟**：
1. 找出歷史上所有「勞動轉弱事件」的起點
2. 篩選事件發生時滿足「高 GDP」條件的樣本
3. 觀察每個事件後 horizon_quarters 內的 Deficit/GDP
4. 計算這些樣本的分布統計

```python
def event_study_banding(data, episodes, horizon_q, gdp_condition):
    forward_deficits = []

    for ep in episodes:
        if not ep.meets_condition(gdp_condition):
            continue

        # 取事件後 horizon_q 季的最大赤字
        future_deficit = data['DEFICIT_GDP'][
            ep.start : ep.start + pd.DateOffset(months=horizon_q*3)
        ].max()

        forward_deficits.append({
            'start': ep.start,
            'deficit_peak': future_deficit,
            'slack_at_start': ep.slack_metric
        })

    # 計算統計
    deficits = [d['deficit_peak'] for d in forward_deficits]
    return {
        'p25': np.percentile(deficits, 25),
        'p50': np.percentile(deficits, 50),
        'p75': np.percentile(deficits, 75),
        'min': min(deficits),
        'max': max(deficits),
        'n_episodes': len(deficits),
        'episodes': forward_deficits
    }
```

**優點**：
- 直觀，產出「12–17%」這種範圍型敘事
- 可追溯到每一次歷史事件
- 不依賴參數估計

**缺點**：
- 樣本數有限（約 6 次）
- 每次事件的財政反應強度不同
</model>

<model name="quantile_mapping">
**分位數映射 (Quantile Mapping)**

適合回答「現在落在歷史哪個角落？」

**步驟**：
1. 計算當前 slack_metric 在歷史分布的分位數 p
2. 找出歷史上 slack_metric 落在 p±ε 的所有時點
3. 對這些時點的後續 Deficit/GDP 做統計

```python
def quantile_mapping(data, current_slack, epsilon=0.05, horizon_q=8):
    # 計算當前 slack 的分位數
    slack_series = data['SLACK_METRIC']
    current_pctl = (slack_series < current_slack).mean()

    # 找出相似時期
    all_pctl = slack_series.rank(pct=True)
    similar_mask = abs(all_pctl - current_pctl) < epsilon

    # 取這些時期的後續赤字
    forward_deficits = []
    for date in data.index[similar_mask]:
        future_date = date + pd.DateOffset(months=horizon_q*3)
        if future_date <= data.index.max():
            forward_deficits.append(data['DEFICIT_GDP'].loc[:future_date].iloc[-1])

    return {
        'current_percentile': current_pctl,
        'similar_periods_count': len(forward_deficits),
        'deficit_distribution': {
            'p25': np.percentile(forward_deficits, 25),
            'p50': np.percentile(forward_deficits, 50),
            'p75': np.percentile(forward_deficits, 75)
        }
    }
```

**優點**：
- 使用所有歷史數據，不只是「事件」
- 適合連續型分析

**缺點**：
- 可能混入非危機時期的樣本
- 對 ε 參數敏感
</model>

<model name="robust_regression">
**穩健迴歸 (Robust Regression)**

適合連續型情境推演。

**模型**：
```
Deficit/GDP(t+4Q) = α + β₁·Slack(t) + β₂·GDP_regime(t) + β₃·Inflation(t) + ε
```

使用分位數迴歸 (Quantile Regression) 可得到不同分位數的預測區間。

```python
from statsmodels.regression.quantile_regression import QuantReg

def robust_regression_projection(data, scenario, quantiles=[0.25, 0.5, 0.75]):
    # 準備特徵
    X = data[['SLACK_METRIC', 'GDP_GROWTH', 'INFLATION']].dropna()
    y = data['DEFICIT_GDP'].shift(-4).dropna()  # 4Q 後的赤字

    # 對齊
    idx = X.index.intersection(y.index)
    X, y = X.loc[idx], y.loc[idx]

    results = {}
    for q in quantiles:
        model = QuantReg(y, X).fit(q=q)
        # 用情境值預測
        X_scenario = [[scenario['slack'], scenario['gdp_growth'], scenario['inflation']]]
        results[f'p{int(q*100)}'] = model.predict(X_scenario)[0]

    return results
```

**優點**：
- 可納入多個控制變數
- 產出連續的預測路徑
- 可做敏感度分析

**缺點**：
- 樣本量有限時估計不穩定
- 線性假設可能不成立
- 可解釋性較低
</model>

</analysis_models>

<ust_risk_framework>

<dual_channel>
**UST 風險雙通道框架**

長天期美債價格（或殖利率）同時受到兩股相反力量影響：

```
┌─────────────────────────────────────────────────────────────┐
│                                                              │
│   供給壓力通道                      避險買盤通道             │
│   ────────────                      ────────────             │
│                                                              │
│   赤字↑                             經濟轉弱                 │
│      ↓                                 ↓                     │
│   發債需求↑                         風險趨避↑               │
│      ↓                                 ↓                     │
│   期限溢酬↑                         債券需求↑               │
│      ↓                                 ↓                     │
│   殖利率↑（債券價格↓）              殖利率↓（債券價格↑）    │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

**哪個力量主導？**

取決於：
1. 衝擊的性質（金融危機 vs 通膨驅動的緊縮）
2. Fed 的政策立場（是否 QE 吸收供給）
3. 全球避險需求（美元/美債的避風港地位）
4. 通膨預期（影響實質報酬要求）
</dual_channel>

<historical_precedents>
**歷史先例**

| 事件 | 赤字/GDP 峰值 | 10Y 殖利率變化 | 主導力量 |
|------|---------------|----------------|----------|
| 2001-2003 | 3.4% | -200 bps | 避險/Fed 降息 |
| 2008-2010 | 9.8% | -150 bps | 避險/QE 吸收 |
| 2020 Q1-Q2 | 14.9% | -100 bps | 避險/Fed 無限 QE |
| 2022-2023 | 6% | +200 bps | 供給/通膨 |

**觀察**：
- 當避險需求極強（危機時刻）+ Fed 介入，避險主導
- 當沒有危機氣氛 + Fed 不介入（或 QT），供給主導
- 通膨預期高時，供給壓力更明顯
</historical_precedents>

<switching_indicators>
**力量切換指標**

| 指標 | 供給主導訊號 | 避險主導訊號 |
|------|--------------|--------------|
| VIX | < 25 | > 30 |
| IG 信用利差 | 穩定 | 急升 > 50 bps |
| 股債相關性 | 正相關 | 負相關 |
| 通膨預期 (5Y5Y) | > 2.5% | < 2% |
| 國債拍賣尾差 | > 2 bps | < -2 bps |
| Fed 政策 | QT 進行中 | QE/暫停 QT |

**決策樹**：
```
IF VIX > 30 AND 信用利差急升 THEN
    避險主導 → 長債可能上漲
ELIF VIX < 25 AND 拍賣持續疲軟 THEN
    供給主導 → 長債可能承壓
ELSE
    混合/拉鋸 → 觀望
```
</switching_indicators>

</ust_risk_framework>

<limitations>
**方法論限制**

1. **樣本量有限**：過去 30 年符合條件的事件約 6 次
2. **每次不同**：財政反應強度取決於政治環境
3. **數據延遲**：JOLTS 延遲 2 個月，GDP 延遲 1 個月
4. **模型不確定性**：三種模型可能給出不同答案
5. **政策依賴**：Fed 政策可大幅改變結果

**建議使用方式**：
- 將輸出視為「歷史參照區間」而非精確預測
- 搭配其他分析工具交叉驗證
- 持續監控切換指標判斷主導力量
</limitations>
