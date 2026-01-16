# Workflow: 數據來源與口徑驗證

<required_reading>
**讀取以下參考文件：**
1. references/data-sources.md
2. references/unit-conversion.md
3. references/failure-modes.md
</required_reading>

<process>
## Step 1: 識別待驗證說法

收集用戶提供的市場說法或數據點：

**常見待驗證說法範例：**
- 「印尼控制 60-70% 全球鎳供給」
- 「Top 5 mines 控制 20% 全球產量」
- 「2026 印尼 RKAB 配額從 379 Mt 降至 250 Mt」
- 「印尼市佔從 30% 升至 60%」

**結構化待驗證項目：**

```yaml
claims_to_validate:
  - claim: "Indonesia 控制 60-70% 全球鎳供給"
    source: "社群貼文/研報"
    claimed_value: 0.60-0.70
    claimed_unit: "不明確"
    claimed_year: 2024
```

## Step 2: 查找原始來源

針對每個待驗證說法，查找可追溯的原始數據來源：

**驗證 "Indonesia 60% share" 的來源鏈：**

| 來源層級 | 來源 | 數據點 | 口徑 |
|----------|------|--------|------|
| L1 (原始) | S&P Global MI | 60.2% (2024) | mined nickel content |
| L2 (引用) | BTG Research Report | ~60% | 轉引 S&P |
| L3 (傳播) | 社群貼文 | 60-70% | 口徑不明 |

**來源可靠度評分：**

| Tier | 來源類型 | Confidence | 說明 |
|------|----------|------------|------|
| 0 | USGS/INSG 官方 | 0.9-1.0 | 口徑一致、可追溯 |
| 1 | 公司財報 | 0.7-0.9 | 需注意報告口徑 |
| 2 | 付費研究 (S&P) | 0.8-0.95 | 專業但需訂閱驗證 |
| 3 | 研報/新聞 | 0.5-0.7 | 常有轉引誤差 |
| 4 | 社群貼文 | 0.2-0.5 | 需完整驗證 |

## Step 3: 口徑對齊檢查

執行口徑一致性檢查：

```python
def check_unit_consistency(claim, reference_data):
    """
    檢查 claim 的口徑是否與 reference 一致
    """
    issues = []

    # 檢查 1: supply_type 是否一致
    if claim.supply_type != reference_data.supply_type:
        issues.append({
            "type": "supply_type_mismatch",
            "claim_type": claim.supply_type,
            "reference_type": reference_data.supply_type,
            "impact": "mined vs refined 可差 10-30%"
        })

    # 檢查 2: unit 是否一致
    if claim.unit != reference_data.unit:
        issues.append({
            "type": "unit_mismatch",
            "claim_unit": claim.unit,
            "reference_unit": reference_data.unit,
            "impact": "ore_wet vs Ni_content 可差 50-100x"
        })

    # 檢查 3: year 是否一致
    if abs(claim.year - reference_data.year) > 1:
        issues.append({
            "type": "year_mismatch",
            "claim_year": claim.year,
            "reference_year": reference_data.year,
            "impact": "印尼市佔快速成長中，年份差異影響顯著"
        })

    return issues
```

## Step 4: 交叉驗證

使用多個獨立來源交叉驗證：

**範例：驗證 "Indonesia 60% share (2024)"**

| 來源 | 數據點 | 口徑 | 一致性 |
|------|--------|------|--------|
| S&P Global MI | 60.2% | mined Ni content | ✓ 基準 |
| USGS MCS 2025 | ~55% (估) | mine production | ≈ 合理範圍 |
| INSG | ~58% (估) | nickel production | ≈ 合理範圍 |
| Wood Mackenzie | 60% | mined | ✓ 一致 |

**驗證結論**：
- Confidence: 0.85
- 口徑: mined nickel content
- 有效範圍: 58-62%

## Step 5: 識別潛在陷阱

常見口徑陷阱檢查清單：

```yaml
pitfall_checks:
  - name: "ore_vs_content"
    description: "礦石濕噸 vs 鎳金屬含量"
    red_flag: "數字大於預期 10x 以上"
    example: "379 Mt RKAB quota 是 ore wet tonnes，非 nickel content"

  - name: "mined_vs_refined"
    description: "礦場產量 vs 精煉產量"
    red_flag: "不同國家排名差異大"
    example: "China refined > mined，Indonesia mined > refined"

  - name: "nickel_vs_NPI"
    description: "純鎳 vs NPI 產品"
    red_flag: "產品噸 vs 含鎳量"
    example: "NPI 產品噸約含 10-15% Ni"

  - name: "year_drift"
    description: "年份不一致"
    red_flag: "市佔快速變化時期"
    example: "Indonesia 2020 31.5% → 2024 60.2%"
```

## Step 6: 生成驗證報告

**JSON 輸出結構：**

```json
{
  "validation_date": "2026-01-16",
  "claims_validated": [
    {
      "claim": "Indonesia 控制 60-70% 全球鎳供給",
      "verdict": "部分正確",
      "confidence": 0.85,
      "validated_value": 0.602,
      "validated_unit": "mined nickel content",
      "validated_year": 2024,
      "source_chain": [
        {
          "source": "S&P Global Market Intelligence",
          "value": 0.602,
          "tier": 2,
          "confidence": 0.9
        }
      ],
      "caveats": [
        "數字適用於 mined nickel content，非 ore wet tonnes",
        "70% 上限可能是 ore 口徑或預測值",
        "refined 口徑下市佔會不同"
      ]
    }
  ],
  "unit_warnings": [
    {
      "type": "unit_ambiguity",
      "message": "原始說法未明確口徑，可能指 ore 或 content"
    }
  ],
  "cross_validation": {
    "sources_checked": 4,
    "consistent": 3,
    "divergent": 1,
    "conclusion": "高置信度，數據可用"
  }
}
```

**Markdown 報告結構：**

```markdown
## 數據來源驗證報告

**驗證日期**: 2026-01-16

### 待驗證說法

> "Indonesia 控制 60-70% 全球鎳供給"

### 驗證結果

| 項目 | 結果 |
|------|------|
| 判定 | ⚠️ 部分正確 |
| 驗證值 | 60.2% |
| 正確口徑 | mined nickel content |
| 年份 | 2024 |
| 置信度 | 85% |

### 來源追溯

1. **S&P Global MI** (Tier 2): 60.2% → 基準來源
2. **USGS MCS** (Tier 0): ~55% → 略低，可能口徑差異
3. **INSG** (Tier 0): ~58% → 合理範圍

### 口徑警告

⚠️ **注意事項**：
- 60% 適用於 **mined nickel content**
- 若用 **ore wet tonnes**，數字會完全不同
- **70%** 可能是預測值或不同口徑

### 結論

該說法在以下條件下成立：
- ✅ 口徑: mined nickel content
- ✅ 年份: 2024
- ✅ 數值: ~60%（非 70%）

建議表述：「印尼 2024 年 mined nickel 產量約佔全球 60%（S&P Global 數據）」
```
</process>

<success_criteria>
此 workflow 完成時：
- [ ] 待驗證說法已結構化
- [ ] 原始來源已追溯
- [ ] 口徑對齊已檢查
- [ ] 交叉驗證已執行
- [ ] 潛在陷阱已識別
- [ ] 輸出驗證報告（JSON + Markdown）
- [ ] 給出置信度評分
</success_criteria>
