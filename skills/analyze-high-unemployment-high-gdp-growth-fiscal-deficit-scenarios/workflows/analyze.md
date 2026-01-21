<required_reading>
**執行前請先閱讀：**
1. references/data-sources.md - 了解 FRED 系列代碼
2. references/input-schema.md - 了解完整參數定義
</required_reading>

<objective>
執行完整的「高失業 + 高 GDP」情境下財政赤字推估分析，包含：
- 抓取所有必要的 FRED 數據
- 計算勞動鬆緊指標（UJO、Sahm Rule、ΔUR）
- 識別歷史上符合條件的事件樣本
- 使用選定模型推估赤字/GDP 區間
- 生成完整的分析報告與 UST 風險解讀
</objective>

<process>

<step name="1_setup">
**Step 1: 環境準備與參數確認**

確認 Python 環境與依賴：
```bash
cd skills/analyze-high-unemployment-high-gdp-growth-fiscal-deficit-scenarios
pip install pandas numpy requests scipy
```

確認分析參數（使用者可自訂或使用預設）：
```python
params = {
    "country": "US",
    "lookback_years": 30,
    "frequency": "quarterly",
    "slack_metric": "unemployed_to_job_openings_ratio",
    "horizon_quarters": 8,
    "gdp_path": "high_gdp_sticky",
    "model": "event_study_banding",
    "output_format": "json"
}
```
</step>

<step name="2_fetch_data">
**Step 2: 抓取 FRED 數據**

執行數據抓取腳本：
```bash
python scripts/fetch_data.py --series UNRATE,UNEMPLOY,JTSJOL,GDP,GDPC1,FYFSGDA188S --years 30
```

或在 Python 中直接調用：
```python
from scripts.fetch_data import fetch_fred_series

labor_data = fetch_fred_series(['UNRATE', 'UNEMPLOY', 'JTSJOL'], years=30)
macro_data = fetch_fred_series(['GDP', 'GDPC1'], years=30)
fiscal_data = fetch_fred_series(['FYFSGDA188S'], years=30)
```

**數據驗證**：
- 確認各序列無過多缺失值
- 確認時間範圍覆蓋完整
- 確認最新數據日期
</step>

<step name="3_compute_indicators">
**Step 3: 計算勞動鬆緊指標**

3.1 **UJO（失業/職缺比）**：
```python
ujo = unemploy / jtsjol  # 越高表示越鬆
```

3.2 **Sahm Rule**：
```python
ur_3m_ma = unrate.rolling(3).mean()
ur_12m_min = unrate.rolling(12).min()
sahm = ur_3m_ma - ur_12m_min  # ≥0.5 為衰退警示
```

3.3 **ΔUR（半年變化）**：
```python
delta_ur = unrate - unrate.shift(6)
```

3.4 **計算分位數**：
```python
ujo_pctl = ujo.rank(pct=True)
```
</step>

<step name="4_define_conditions">
**Step 4: 定義背離事件條件**

4.1 **勞動轉弱條件**（滿足任一）：
- UJO 進入歷史 80% 分位以上
- Sahm Rule ≥ 0.5
- ΔUR（6M）≥ +1.0 百分點

4.2 **高 GDP 條件**（同時滿足）：
- GDP 水平在 70% 分位以上
- 或 GDP YoY 成長仍為正

4.3 **識別事件樣本**：
```python
event_mask = labor_soft & high_gdp
episodes = extract_episodes(data, event_mask, min_duration=2)
```
</step>

<step name="5_run_model">
**Step 5: 執行分析模型**

根據 `model` 參數選擇：

**A) event_study_banding（事件分組區間法）**：
```python
# 對每個事件，觀察後續 horizon_quarters 的 Deficit/GDP
forward_deficits = []
for ep in episodes:
    future_deficit = deficit_gdp[ep.start : ep.start + horizon_quarters].max()
    forward_deficits.append(future_deficit)

# 計算區間統計
result = {
    'p25': np.percentile(forward_deficits, 25),
    'p50': np.percentile(forward_deficits, 50),
    'p75': np.percentile(forward_deficits, 75),
    'min': min(forward_deficits),
    'max': max(forward_deficits)
}
```

**B) quantile_mapping（分位數映射）**：
```python
# 找出歷史上 slack_metric 落在當前分位數附近的時點
current_pctl = ujo_pctl.iloc[-1]
similar_periods = data[abs(ujo_pctl - current_pctl) < 0.05]
# 對這些時點的後續 Deficit/GDP 做統計
```

**C) robust_regression（穩健迴歸）**：
```python
from statsmodels.regression.quantile_regression import QuantReg
model = QuantReg(deficit_gdp_future, X)
result = model.fit(q=0.5)
```
</step>

<step name="6_generate_output">
**Step 6: 生成輸出報告**

執行完整分析並輸出：
```bash
python scripts/analyzer.py \
    --lookback 30 \
    --horizon 8 \
    --model event_study_banding \
    --output result.json
```

輸出內容應包含：
1. **診斷資訊**：當前 UJO、Sahm、ΔUR 數值與分位數
2. **條件判定**：是否觸發勞動轉弱、是否滿足高 GDP
3. **赤字區間**：條件分布（p25/p50/p75/min/max）
4. **歷史樣本**：事件年份與對應赤字峰值
5. **UST 解讀**：供給壓力與避險買盤的雙通道分析
6. **監控指標**：建議追蹤的切換指標
</step>

<step name="7_validate">
**Step 7: 驗證輸出**

確認輸出完整性：
- [ ] 所有診斷指標都有數值
- [ ] 赤字區間在合理範圍（0% - 25%）
- [ ] 歷史樣本數量 ≥ 3
- [ ] UST 解讀包含兩股力量
- [ ] 監控指標清單不為空
</step>

</process>

<success_criteria>
工作流程完成時：
- [ ] 成功抓取所有 FRED 數據
- [ ] 計算出 UJO、Sahm Rule、ΔUR 指標
- [ ] 識別出歷史事件樣本
- [ ] 產出赤字/GDP 的條件分布區間
- [ ] 生成 UST 風險解讀
- [ ] 輸出符合模板格式（JSON 或 Markdown）
</success_criteria>
