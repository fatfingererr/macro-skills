<overview>
此參考文件列出 CPI-PCE 比較分析所需的資料來源、FRED 系列代碼，以及桶位對應關係。

**重要更新**：經測試，FRED CSV endpoint 無需 API key 即可使用，BLS 公開 API 也可用。
</overview>

<data_access_methods>

<method name="fred_csv" recommended="true">
**FRED CSV Endpoint（推薦，無需 API key）**

```
https://fred.stlouisfed.org/graph/fredgraph.csv?id={SERIES_ID}
```

**參數**：
- `id`: 系列代碼（如 CPIAUCSL）
- `cosd`: 起始日期（可選，格式 YYYY-MM-DD）
- `coed`: 結束日期（可選）

**範例**：
```
https://fred.stlouisfed.org/graph/fredgraph.csv?id=CPIAUCSL&cosd=2020-01-01&coed=2024-12-01
```

**優點**：
- 無需 API key
- 直接返回 CSV
- 無請求限制（合理使用）

**腳本位置**: `scripts/fetch_fred_data.py`
</method>

<method name="bls_api">
**BLS Public Data API**

```
POST https://api.bls.gov/publicAPI/v2/timeseries/data/
```

**限制**（無 API key）：
- 每次最多 50 個系列
- 每日 500 次請求
- 歷史資料限 20 年

**腳本位置**: `scripts/fetch_bls_data.py`
</method>

<method name="bea_api" needs_key="true">
**BEA API（需要 API key）**

若需要 BEA 細項資料，需申請免費 API key：
https://apps.bea.gov/api/signup/

**替代方案**：多數 BEA 資料已收錄於 FRED，可直接使用 FRED CSV。
</method>

</data_access_methods>

<fred_series>

<category name="Headline Indexes">
**主要通膨指數**

| 別名 | Series ID | 描述 | 頻率 |
|------|-----------|------|------|
| `cpi_headline` | CPIAUCSL | CPI All Urban Consumers | 月 |
| `pce_headline` | PCEPI | PCE Chain-type Price Index | 月 |
</category>

<category name="Core Indexes">
**核心通膨指數（排除食品和能源）**

| 別名 | Series ID | 描述 | 頻率 |
|------|-----------|------|------|
| `cpi_core` | CPILFESL | CPI Less Food and Energy | 月 |
| `pce_core` | PCEPILFE | PCE Excluding Food and Energy | 月 |
</category>

<category name="PCE Components">
**PCE 分項價格指數**

| 別名 | Series ID | 描述 | Bucket Mapping |
|------|-----------|------|----------------|
| `pce_goods` | DGDSRG3M086SBEA | PCE: Goods | goods |
| `pce_services` | DSERRG3M086SBEA | PCE: Services | services |
| `pce_durable_goods` | DDURRG3M086SBEA | PCE: Durable Goods | durable_goods |
| `pce_nondurable_goods` | DNDGRG3M086SBEA | PCE: Nondurable Goods | nondurable_goods |
| `pce_housing` | DHUTRG3M086SBEA | PCE: Housing and Utilities | housing |
| `pce_medical` | DHLCRG3M086SBEA | PCE: Health Care | medical |
</category>

<category name="CPI Components">
**CPI 分項**

| 別名 | Series ID | 描述 | Bucket Mapping |
|------|-----------|------|----------------|
| `cpi_shelter` | CUSR0000SAH1 | CPI: Shelter | housing |
| `cpi_medical` | CUSR0000SAM | CPI: Medical Care | medical |
| `cpi_services` | CUSR0000SAS | CPI: Services | services |
| `cpi_food` | CUSR0000SAF1 | CPI: Food | food |
| `cpi_energy` | CUSR0000SA0E | CPI: Energy | energy |
</category>

<category name="PCE Nominal">
**PCE 名目值（用於計算動態權重）**

| 別名 | Series ID | 描述 |
|------|-----------|------|
| `pce_nominal_total` | PCE | Personal Consumption Expenditures |
| `pce_nominal_goods` | PCEDG | PCE: Goods |
| `pce_nominal_services` | PCES | PCE: Services |
</category>

</fred_series>

<bucket_definitions>

<bucket name="core_goods">
**定義**：扣除食品和能源的商品

**近似計算**：
```python
# 方案 A：使用 Goods - Food goods - Energy goods
core_goods ≈ pce_goods - food_goods - energy_goods

# 方案 B：使用 Durable + Nondurable（粗粒度）
core_goods ≈ pce_durable_goods + pce_nondurable_goods
```

**注意**：FRED 無直接 Core Goods 單一序列
</bucket>

<bucket name="core_services_ex_housing">
**定義**：核心服務扣除住房（Fed 的 "Supercore"）

**近似計算**：
```python
core_services_ex_housing = pce_services - pce_housing
```

**重要性**：Fed 越來越關注此指標，因為它反映勞動成本傳導。
</bucket>

<bucket name="housing">
**定義**：住房相關消費

**權重對比**：
| | PCE | CPI |
|---|-----|-----|
| 住房權重 | ~15-18% | ~34% |
| OER 權重 | ~12% | ~26% |

**這是 CPI/PCE 分歧的重要來源。**
</bucket>

<bucket name="medical">
**定義**：醫療相關消費

**Scope 差異**：
- PCE 包含第三方支付（雇主、政府）
- CPI 只計消費者直接支付
- 結果：PCE 醫療權重 (~17%) > CPI 醫療權重 (~7%)
</bucket>

</bucket_definitions>

<weight_sources>

<source name="pce_dynamic_weights">
**PCE 動態權重計算**

使用 FRED 名目支出資料計算：
```python
# 各桶占比
weight[bucket] = nominal_pce[bucket] / nominal_pce['total']
```

**近似權重（2024 年）**：
```python
DEFAULT_PCE_WEIGHTS = {
    'pce_goods': 0.31,
    'pce_services': 0.69,
    'pce_housing': 0.18,
    'pce_medical': 0.17,
}
```
</source>

<source name="cpi_fixed_weights">
**CPI 固定權重**

BLS 每年 12 月發布 "Relative Importance" 表。

**近似權重（2024 年）**：
```python
DEFAULT_CPI_WEIGHTS = {
    'cpi_shelter': 0.36,
    'cpi_services': 0.62,
    'cpi_medical': 0.07,
    'cpi_food': 0.14,
    'cpi_energy': 0.07,
}
```

**注意**：CPI 權重更新較慢，這是與 PCE 的核心差異。
</source>

</weight_sources>

<scripts_reference>

**資料抓取腳本**

| 腳本 | 功能 | 資料來源 |
|------|------|---------|
| `scripts/fetch_fred_data.py` | 抓取 FRED 資料 | FRED CSV (無需 API key) |
| `scripts/fetch_bls_data.py` | 抓取 BLS 資料 | BLS Public API |
| `scripts/cpi_pce_analyzer.py` | 完整分析 | 整合 FRED + BLS |

**使用範例**：

```bash
# 快速檢查
python scripts/cpi_pce_analyzer.py --quick

# 完整分析
python scripts/cpi_pce_analyzer.py --start 2020-01-01 --end 2024-12-01 --measure yoy

# 含 baseline 調整
python scripts/cpi_pce_analyzer.py --start 2016-01-01 --baseline 2018-10-01:2018-12-31
```

</scripts_reference>

<update_schedule>

**資料更新時程**

| 資料 | 發布時間 | 延遲 |
|------|---------|------|
| CPI | 每月中旬 | 約 2 週 |
| PCE | 每月底 | 約 4 週 |
| PCE 權重 | 隨 PCE 發布 | 即時 |
| CPI 權重 | 每年 12 月 | 年度 |

**注意**：CPI 比 PCE 早約 2 週公布，市場通常對 CPI 反應更大。

</update_schedule>
