<overview>
此參考文件深入解釋 CPI 與 PCE 的方法論差異，是理解兩指標分歧的核心知識。
</overview>

<why_two_measures>

**為什麼美國有兩個主要通膨指標？**

| 指標 | 發布單位 | 用途 |
|------|---------|------|
| **CPI** (Consumer Price Index) | BLS (勞工統計局) | 工資調整、社會福利、TIPS、公眾通膨預期 |
| **PCE** (Personal Consumption Expenditures) | BEA (經濟分析局) | **Fed 貨幣政策目標** (2% 目標) |

Fed 在 2000 年正式將 PCE 作為通膨目標指標，因為 PCE 的計算方式更能反映「消費者實際承受的通膨」。

</why_two_measures>

<key_differences>

<difference name="weighting_method" importance="highest">
**權重方法：最重要的差異**

| | CPI | PCE |
|---|-----|-----|
| **類型** | 固定權重 (Laspeyres-like) | 鏈結權重 (Fisher-Ideal) |
| **更新頻率** | 每年或每兩年 | 每月 |
| **反應速度** | 慢 | 快 |
| **替代效應** | 不捕捉 | 捕捉 |

**替代效應範例**：
- 當牛肉價格上漲時，消費者改買雞肉
- CPI：仍按原本的牛肉權重計算 → 高估通膨
- PCE：權重自動移向雞肉 → 更真實反映消費者支出

**結果**：長期而言，CPI 傾向高估通膨約 0.2-0.3 個百分點。

</difference>

<difference name="scope" importance="high">
**涵蓋範圍差異**

| 項目 | CPI | PCE |
|------|-----|-----|
| 消費者直接支付 | ✅ | ✅ |
| 雇主代付醫療 | ❌ | ✅ |
| 政府補貼醫療 | ❌ | ✅ |
| 非營利組織服務 | ❌ | ✅ |
| 金融服務隱含費用 | 部分 | ✅ |

**醫療是最大的 scope 差異**：
- CPI 醫療權重：約 7%（只計消費者自付）
- PCE 醫療權重：約 17%（含第三方支付）

這解釋了為什麼當醫療通膨走高時，PCE 受影響更大。

</difference>

<difference name="housing_weight" importance="high">
**住房權重差異**

| | CPI | PCE |
|---|-----|-----|
| 住房權重 | ~34% | ~15-18% |
| OER 權重 | ~26% | ~12% |

**OER (Owner's Equivalent Rent)**：用於估算自有住房的「隱含租金」。

**影響**：
- 當 OER/租金通膨走高時，CPI 受影響更大
- 當 OER 下降時，CPI 降溫速度比 PCE 快

這是 2022-2024 年間 CPI/PCE 分歧的主要來源之一。

</difference>

<difference name="formula" importance="medium">
**計算公式差異**

**CPI (Modified Laspeyres)**：
$$CPI_t = \frac{\sum_i p_i^t \cdot q_i^0}{\sum_i p_i^0 \cdot q_i^0} \times 100$$

其中 $q_i^0$ 是基準期的消費量（固定）。

**PCE (Fisher-Ideal Chain)**：
$$PCE_t = PCE_{t-1} \times \sqrt{\frac{\sum_i p_i^t \cdot q_i^{t-1}}{\sum_i p_i^{t-1} \cdot q_i^{t-1}} \times \frac{\sum_i p_i^t \cdot q_i^t}{\sum_i p_i^{t-1} \cdot q_i^t}}$$

Fisher-Ideal 指數是 Laspeyres 和 Paasche 的幾何平均，減少了偏誤。

</difference>

<difference name="population" importance="low">
**人口涵蓋**

| | CPI | PCE |
|---|-----|-----|
| 涵蓋 | 都市消費者 (Urban Consumers) | 所有消費者 + 非營利組織 |
| 比例 | 約 93% 人口 | 100% |

實務上，這個差異影響較小。

</difference>

</key_differences>

<divergence_patterns>

**常見的 CPI/PCE 分歧模式**

<pattern name="pce_higher_than_cpi">
**PCE > CPI 的情況**（較常見）

可能原因：
1. 醫療通膨走高（PCE 醫療權重更高）
2. 住房通膨降溫（CPI 住房權重更高）
3. 消費者支出移向通膨較高的桶位（PCE 動態權重）

**交易含義**：Fed 看到的通膨比市場預期更頑固，鷹派機率上升。
</pattern>

<pattern name="cpi_higher_than_pce">
**CPI > PCE 的情況**（較少見）

可能原因：
1. 住房/租金通膨大幅走高
2. 能源/食品價格衝擊
3. 替代效應發生（消費者換購便宜商品）

**交易含義**：市場可能高估通膨壓力，Fed 實際目標指標較低。
</pattern>

<pattern name="divergence_widening">
**分歧擴大中**

需要關注：
1. 哪些桶位在驅動分歧？
2. 是暫時性還是結構性？
3. Fed 會如何解讀？
</pattern>

</divergence_patterns>

<fed_perspective>

**Fed 如何看待 CPI/PCE 差異**

1. **政策目標是 PCE**（具體是 Core PCE）
   - Fed 的 2% 通膨目標是針對 PCE
   - SEP (經濟預測摘要) 中的通膨預測是 PCE

2. **但 Fed 也看 CPI**
   - CPI 先於 PCE 公布（約早 2 週）
   - 市場對 CPI 反應更大
   - TIPS 盈虧平衡率基於 CPI

3. **Fed 特別關注**
   - **Core PCE**：排除波動的食品和能源
   - **Supercore**：Core Services ex Housing（勞動密集服務）
   - **Trimmed Mean PCE**（達拉斯 Fed 編製）

**Powell 的常見說法**：
> "We look at a variety of measures... PCE is our target, but we also look at CPI, trimmed mean, and other measures."

</fed_perspective>

<trading_implications>

**對交易的影響**

<scenario name="cpi_release">
**CPI 公布日**

- 市場反應：即時且大
- 但需要注意：Fed 目標是 PCE
- 交易策略：CPI 意外後，評估對 PCE 的含義
</scenario>

<scenario name="pce_release">
**PCE 公布日**

- 市場反應：通常較小（因 CPI 已公布）
- 但這是 Fed 的目標指標
- 若 PCE 與 CPI 分歧擴大，可能影響 Fed 政策
</scenario>

<scenario name="divergence_trade">
**分歧交易機會**

當 CPI 數據引發市場大幅反應，但你預期 PCE 將有不同訊號：
1. 分析分歧來源（住房？醫療？權重？）
2. 預測 PCE 數據
3. 在 CPI 反應過度時逆向操作
</scenario>

</trading_implications>

<historical_context>

**歷史上的重大分歧**

| 時期 | 分歧方向 | 主因 |
|------|---------|------|
| 2008-2009 | CPI > PCE | 能源價格衝擊 |
| 2014-2015 | PCE > CPI | 醫療通膨走高 |
| 2021-2022 | 混合 | 供應鏈衝擊 + 住房滯後 |
| 2023-2024 | CPI > PCE | 住房通膨（OER）高位 |

**2023-2024 的案例**：
- CPI 中 OER 權重 ~26%，通膨 5-6%
- PCE 中 OER 權重 ~12%
- 結果：CPI 比 PCE 高約 0.3-0.5 個百分點
- 市場一度過度悲觀（盯著 CPI）
- Fed 持續強調「看 PCE」

</historical_context>
