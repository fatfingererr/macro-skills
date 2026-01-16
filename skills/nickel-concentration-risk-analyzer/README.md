# Nickel Concentration Risk Analyzer

全球鎳供給集中度分析工具，量化各國主導程度（特別是印尼）、集中度指標演進、以及政策變動對全球供給的潛在衝擊。

## 核心功能

### 1. 供給集中度分析 (Analyze)
- 計算國家市佔率（Country Share）
- 計算集中度指標（CR1, CR3, CR5）
- 計算HHI（Herfindahl-Hirschman Index）
- 生成時序趨勢分析（2015-2024）
- **視覺化圖表生成**

### 2. 政策情境模擬 (Scenario)
- 模擬RKAB配額變動影響
- 計算政策槓桿效應
- 輸出三層結果（Hard/Half/Soft）

### 3. 數據來源驗證 (Validate)
- 驗證市場說法的數據口徑
- 追溯原始數據來源
- 交叉驗證數據一致性

### 4. 數據擷取 (Ingest)
- Tier 0: USGS, INSG（免費穩定）
- Tier 1: 公司報告（免費但分散）
- Tier 2: S&P Global（付費精確）

## 快速開始

### 基礎分析

```bash
# 1. 進入腳本目錄
cd .claude/skills/nickel-concentration-risk-analyzer/scripts

# 2. 執行集中度分析
python nickel_pipeline.py analyze --asof=2026-01-16 --scope=mined

# 3. 生成視覺化圖表
python visualize_concentration.py
```

### 視覺化輸出

執行 `visualize_concentration.py` 會生成以下圖表（保存在項目根目錄 `output/` 資料夾）：

| 圖表檔名 | 內容 |
|---------|------|
| `nickel_indonesia_share_trend_YYYYMMDD.png` | 印尼市佔率與HHI時序趨勢 (2015-2024) |
| `nickel_country_share_pie_YYYYMMDD.png` | 2024年國家份額分布餅圖 |
| `nickel_concentration_metrics_YYYYMMDD.png` | 集中度指標演進（CR1, CR3, CR5） |
| `nickel_production_volume_YYYYMMDD.png` | 印尼vs全球產量對比堆疊圖 |
| `nickel_risk_matrix_YYYYMMDD.png` | 集中度風險矩陣定位圖 |

**範例輸出**：
- 印尼市佔率：57.9% (2024)
- HHI：3,779（高集中）
- 市場結構：極高風險

### Python Library 使用

```python
from nickel_pipeline import NickelConcentrationAnalyzer

# 初始化分析器
analyzer = NickelConcentrationAnalyzer(
    asof_date="2026-01-16",
    scope={"supply_type": "mined", "unit": "t_Ni_content"},
    data_level="free_nolimit"
)

# 計算集中度指標
result = analyzer.compute_concentration()
print(f"Indonesia share: {result['indonesia_share']:.1%}")
print(f"HHI: {result['hhi']:.0f}")
print(f"Market structure: {result['market_structure']}")

# 計算時序趨勢
time_series = analyzer.compute_time_series(start_year=2015)

# 輸出結果
analyzer.generate_output(output_format='json', output_dir='./output')
```

## 核心概念

### 口徑先行 (Unit Enforcement)

所有分析必須先確定數據口徑：

| 口徑 | 說明 | 典型數值差異 |
|------|------|-------------|
| `t_Ni_content` | 鎳金屬含量（預設） | 基準值 |
| `t_ore_wet` | 礦石濕噸 | 50-100x |
| `t_NPI_product` | NPI產品噸 | 10-15% Ni |
| `t_matte` | 鎳鋶噸 | 75% Ni |

### 集中度指標

| 指標 | 公式 | 解讀 |
|------|------|------|
| Country Share | `country_prod / global_prod` | 單國佔比 |
| CR_n | `Σ top_n_share` | 前N國集中度 |
| HHI | `Σ share²` | 市場集中度（0-10000） |

**HHI判讀標準**：
- < 1500：低集中（Unconcentrated）
- 1500-2500：中等集中（Moderately Concentrated）
- \> 2500：高集中（Highly Concentrated）

### 數據來源分層

| Tier | 來源 | 特性 | 用途 |
|------|------|------|------|
| 0 | USGS MCS, INSG | 免費、穩定、口徑一致 | Baseline主幹 |
| 1 | 公司年報 | 免費但分散 | Mine-level錨點 |
| 2 | S&P Global | 付費、即時完整 | 精度驗證 |
| 3 | 政策新聞 | 即時但需驗證 | 情境輸入 |

## 目錄結構

```
nickel-concentration-risk-analyzer/
├── SKILL.md                      # Skill 定義檔
├── README.md                     # 本文件
├── scripts/                      # Python 腳本
│   ├── nickel_pipeline.py       # 核心分析管線
│   ├── ingest_sources.py        # 數據擷取
│   ├── compute_concentration.py # 集中度計算
│   ├── scenario_impact.py       # 情境模擬
│   └── visualize_concentration.py # 視覺化圖表生成 ⭐
├── workflows/                    # 工作流程定義
│   ├── analyze.md               # 分析流程
│   ├── scenario-engine.md       # 情境模擬流程
│   ├── validate-sources.md      # 驗證流程
│   └── ingest.md               # 數據擷取流程
├── references/                   # 參考文件
│   ├── data-sources.md          # 數據來源說明
│   ├── concentration-metrics.md # 集中度指標詳解
│   ├── indonesia-supply-structure.md # 印尼供給結構
│   └── unit-conversion.md       # 單位轉換規則
└── templates/                    # 輸出模板
    ├── output-json.md           # JSON輸出格式
    ├── output-markdown.md       # Markdown報告格式
    └── config.yaml              # 配置模板
```

## 2024年分析結果摘要

**印尼主導地位**：
- 市佔率：**57.9%** (2.2 Mt Ni / 3.8 Mt global)
- 10年增長：**11倍**（2015: 5.1% → 2024: 57.9%）
- 成長驅動：2020年礦石出口禁令、NPI產能擴張

**市場集中度**：
- CR1（最大國）：57.9%
- CR3（前三國）：84.2%
- CR5（前五國）：93.7%
- HHI：**3,779**（高集中）

**風險評級**：🔴 **極高風險**

## 政策風險示例

**假設：印尼RKAB配額減少20%**
- 受影響供給：440 kt Ni
- 全球衝擊：11.6%
- 相當於：42天全球消費量
- 風險等級：極高風險

## 數據口徑注意事項

⚠️ **重要提醒**：

本工具使用 **mined nickel content**（礦場產量的鎳金屬含量）：
- ✅ 鎳金屬含量（metric tons Ni）
- ❌ 非 ore wet tonnes（礦石濕噸）
- ❌ 非 refined production（精煉產量）
- ❌ 非 NPI product tonnes（NPI產品噸）

## 依賴套件

```bash
pip install pandas numpy matplotlib requests beautifulsoup4
```

可選：
```bash
pip install camelot-py tabula-py  # PDF解析（進階功能）
```

## License

MIT License

## Author

Ricky Wang

---

**最後更新**: 2026-01-16
**版本**: 0.1.0
