# JSON 輸出結構模板

<overview>
定義 nickel-concentration-risk-analyzer 的標準 JSON 輸出結構。
所有 workflow 的 JSON 輸出應遵循此模板。
</overview>

<base_structure>
**基礎結構**

所有輸出共享的基礎欄位：

```json
{
  "metadata": {
    "skill": "nickel-concentration-risk-analyzer",
    "version": "0.1.0",
    "generated_at": "2026-01-16T12:00:00Z",
    "asof_date": "2026-01-16",
    "workflow": "analyze|scenario|validate|ingest"
  },
  "scope": {
    "commodity": "nickel",
    "supply_type": "mined",
    "unit": "t_Ni_content"
  },
  "data_sources_used": [],
  "warnings": [],
  "errors": []
}
```
</base_structure>

<analyze_output>
**Analyze Workflow 輸出**

```json
{
  "metadata": {
    "skill": "nickel-concentration-risk-analyzer",
    "version": "0.1.0",
    "generated_at": "2026-01-16T12:00:00Z",
    "asof_date": "2026-01-16",
    "workflow": "analyze"
  },
  "scope": {
    "commodity": "nickel",
    "supply_type": "mined",
    "unit": "t_Ni_content",
    "horizon": {
      "history_start_year": 2015,
      "history_end_year": 2024,
      "analysis_year": 2024
    }
  },
  "concentration": {
    "analysis_year": 2024,
    "indonesia_share": 0.602,
    "cr1": 0.602,
    "cr3": 0.75,
    "cr5": 0.85,
    "hhi": 4002,
    "market_structure": "高集中 (Highly Concentrated)",
    "top_countries": {
      "Indonesia": 0.602,
      "Philippines": 0.106,
      "Russia": 0.056,
      "Canada": 0.040,
      "Australia": 0.035
    }
  },
  "time_series": [
    {
      "year": 2020,
      "indonesia_share": 0.315,
      "hhi": 2100,
      "market_structure": "中等集中"
    },
    {
      "year": 2021,
      "indonesia_share": 0.38,
      "hhi": 2500,
      "market_structure": "高集中"
    },
    {
      "year": 2022,
      "indonesia_share": 0.48,
      "hhi": 3000,
      "market_structure": "高集中"
    },
    {
      "year": 2023,
      "indonesia_share": 0.54,
      "hhi": 3500,
      "market_structure": "高集中"
    },
    {
      "year": 2024,
      "indonesia_share": 0.602,
      "hhi": 4002,
      "market_structure": "高集中"
    }
  ],
  "key_facts": {
    "indonesia_share_2024": 0.602,
    "share_source": "S&P Global Market Intelligence",
    "share_growth_5yr": 0.287,
    "dominant_product": "NPI (~70% of Indonesia production)"
  },
  "data_sources_used": [
    {
      "name": "USGS MCS 2025 (Nickel)",
      "tier": 0,
      "confidence": 0.95
    },
    {
      "name": "INSG World Nickel Statistics",
      "tier": 0,
      "confidence": 0.90
    },
    {
      "name": "S&P Global Market Intelligence",
      "tier": 2,
      "confidence": 0.90,
      "note": "Used for Indonesia share validation"
    }
  ],
  "warnings": [],
  "errors": []
}
```
</analyze_output>

<scenario_output>
**Scenario Workflow 輸出**

```json
{
  "metadata": {
    "skill": "nickel-concentration-risk-analyzer",
    "version": "0.1.0",
    "generated_at": "2026-01-16T12:00:00Z",
    "asof_date": "2026-01-16",
    "workflow": "scenario"
  },
  "scope": {
    "commodity": "nickel",
    "supply_type": "mined",
    "unit": "t_Ni_content"
  },
  "baseline": {
    "year": 2024,
    "indonesia_production_kt": 2280,
    "global_production_kt": 3780,
    "indonesia_share": 0.602
  },
  "scenarios": [
    {
      "name": "ID_RKAB_cut_2026",
      "description": "Indonesia RKAB ore quota reduction",
      "parameters": {
        "target_country": "Indonesia",
        "policy_variable": "ore_quota_RKAB",
        "cut_type": "pct_country",
        "cut_value": 0.20,
        "start_year": 2026,
        "end_year": 2026,
        "execution_prob": 0.5
      },
      "results": {
        "hard_cut": {
          "name": "完全執行",
          "execution_rate": 1.0,
          "cut_amount_kt": 456,
          "global_hit_pct": 0.121,
          "equivalent_days_consumption": 44,
          "risk_level": "極高風險",
          "description": "政策 100% 落地"
        },
        "half_success": {
          "name": "半成功",
          "execution_rate": 0.5,
          "cut_amount_kt": 228,
          "global_hit_pct": 0.060,
          "equivalent_days_consumption": 22,
          "risk_level": "高風險",
          "description": "執行 50%"
        },
        "soft_landing": {
          "name": "軟著陸",
          "execution_rate": 0.25,
          "cut_amount_kt": 114,
          "global_hit_pct": 0.030,
          "equivalent_days_consumption": 11,
          "risk_level": "中等風險",
          "description": "只延遲新增產能/部分執行"
        }
      },
      "sensitivity": [
        {"execution_rate": 1.00, "cut_kt": 456, "global_hit_pct": 0.121},
        {"execution_rate": 0.75, "cut_kt": 342, "global_hit_pct": 0.090},
        {"execution_rate": 0.50, "cut_kt": 228, "global_hit_pct": 0.060},
        {"execution_rate": 0.25, "cut_kt": 114, "global_hit_pct": 0.030},
        {"execution_rate": 0.00, "cut_kt": 0, "global_hit_pct": 0.000}
      ]
    }
  ],
  "assumptions": [
    "Baseline uses S&P Global 2024 data",
    "execution_prob = 0.5 (default)",
    "cut_type = pct_country (20% of Indonesia production)",
    "No supply response from other countries"
  ],
  "data_sources_used": [
    {
      "name": "S&P Global Market Intelligence",
      "tier": 2,
      "confidence": 0.90
    }
  ],
  "warnings": [
    {
      "type": "unit_mismatch",
      "code": "RKAB_ORE_QUOTA",
      "message": "RKAB ore quota is in ore wet tonnes, not nickel content",
      "impact": "Direct percentage application may underestimate actual impact",
      "recommendation": "Consider ore-to-content conversion with grade assumptions"
    }
  ],
  "errors": []
}
```
</scenario_output>

<validate_output>
**Validate Workflow 輸出**

```json
{
  "metadata": {
    "skill": "nickel-concentration-risk-analyzer",
    "version": "0.1.0",
    "generated_at": "2026-01-16T12:00:00Z",
    "asof_date": "2026-01-16",
    "workflow": "validate"
  },
  "scope": {
    "commodity": "nickel",
    "supply_type": "mined",
    "unit": "t_Ni_content"
  },
  "claims_validated": [
    {
      "claim_id": 1,
      "original_claim": "Indonesia controls 60-70% of global nickel supply",
      "source": "Social media / research report",
      "verdict": "partially_correct",
      "confidence": 0.85,
      "validated_value": 0.602,
      "validated_unit": "mined nickel content",
      "validated_year": 2024,
      "source_chain": [
        {
          "source": "S&P Global Market Intelligence",
          "value": 0.602,
          "tier": 2,
          "confidence": 0.90,
          "is_primary": true
        },
        {
          "source": "USGS MCS 2025",
          "value": 0.55,
          "tier": 0,
          "confidence": 0.95,
          "note": "Slightly lower, possible timing difference"
        }
      ],
      "caveats": [
        "Value applies to mined nickel content, not ore wet tonnes",
        "70% upper bound may refer to ore production or forecast",
        "Refined production share would differ"
      ],
      "recommended_statement": "Indonesia's 2024 mined nickel production was approximately 60% of global total (S&P Global data)"
    }
  ],
  "cross_validation": {
    "sources_checked": 4,
    "consistent": 3,
    "divergent": 1,
    "overall_confidence": 0.85,
    "conclusion": "High confidence - data is usable with noted caveats"
  },
  "pitfall_checks": [
    {
      "check": "ore_vs_content",
      "status": "warning",
      "finding": "Original claim did not specify unit - could be ore or content"
    },
    {
      "check": "mined_vs_refined",
      "status": "ok",
      "finding": "Context suggests mined production"
    },
    {
      "check": "year_consistency",
      "status": "ok",
      "finding": "All sources refer to 2024 data"
    }
  ],
  "data_sources_used": [
    {
      "name": "S&P Global Market Intelligence",
      "tier": 2,
      "confidence": 0.90
    },
    {
      "name": "USGS MCS 2025",
      "tier": 0,
      "confidence": 0.95
    },
    {
      "name": "INSG World Nickel Statistics",
      "tier": 0,
      "confidence": 0.90
    }
  ],
  "warnings": [
    {
      "type": "unit_ambiguity",
      "code": "CLAIM_UNIT_UNCLEAR",
      "message": "Original claim did not specify unit (ore vs content)"
    }
  ],
  "errors": []
}
```
</validate_output>

<ingest_output>
**Ingest Workflow 輸出**

```json
{
  "metadata": {
    "skill": "nickel-concentration-risk-analyzer",
    "version": "0.1.0",
    "generated_at": "2026-01-16T12:00:00Z",
    "asof_date": "2026-01-16",
    "workflow": "ingest"
  },
  "scope": {
    "commodity": "nickel",
    "supply_type": "mined",
    "unit": "t_Ni_content"
  },
  "ingest_summary": {
    "status": "success",
    "total_records": 225,
    "years_covered": [2015, 2024],
    "countries_covered": 20,
    "sources_processed": 3
  },
  "sources_ingested": [
    {
      "name": "USGS MCS 2025 (Nickel)",
      "tier": 0,
      "status": "success",
      "records": 150,
      "confidence": 0.95,
      "url": "https://www.usgs.gov/...",
      "download_time": "2026-01-16T11:30:00Z"
    },
    {
      "name": "INSG World Nickel Statistics",
      "tier": 0,
      "status": "success",
      "records": 50,
      "confidence": 0.90,
      "url": "https://insg.org/...",
      "download_time": "2026-01-16T11:32:00Z"
    },
    {
      "name": "Company Reports (Tier 1)",
      "tier": 1,
      "status": "partial",
      "records": 25,
      "confidence": 0.75,
      "note": "Some companies have delayed reports"
    }
  ],
  "output_files": {
    "parquet": "data/nickel/curated/nickel_supply.parquet",
    "json": "data/nickel/curated/nickel_supply.json",
    "metadata": "data/nickel/curated/metadata.json"
  },
  "data_quality": {
    "avg_confidence": 0.88,
    "records_with_estimates": 15,
    "records_with_warnings": 5,
    "schema_validation": "passed"
  },
  "warnings": [],
  "errors": []
}
```
</ingest_output>

<field_definitions>
**欄位定義**

| 欄位 | 類型 | 必填 | 說明 |
|------|------|------|------|
| `metadata.skill` | string | Y | Skill 名稱 |
| `metadata.version` | string | Y | Skill 版本 |
| `metadata.generated_at` | ISO datetime | Y | 生成時間 |
| `metadata.asof_date` | ISO date | Y | 分析基準日 |
| `metadata.workflow` | string | Y | 執行的 workflow |
| `scope.commodity` | string | Y | 商品（nickel） |
| `scope.supply_type` | string | Y | mined/refined |
| `scope.unit` | string | Y | 數據單位 |
| `data_sources_used` | array | Y | 使用的數據來源 |
| `warnings` | array | Y | 警告訊息 |
| `errors` | array | Y | 錯誤訊息 |
</field_definitions>
