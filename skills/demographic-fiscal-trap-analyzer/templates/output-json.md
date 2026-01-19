# JSON 輸出模板 (JSON Output Template)

## 單一實體完整分析輸出

```json
{
  "metadata": {
    "skill": "demographic-fiscal-trap-analyzer",
    "version": "0.1.0",
    "generated_at": "2024-01-15T10:30:00Z",
    "workflow": "full-analysis"
  },
  "parameters": {
    "entities": ["JPN"],
    "start_year": 2010,
    "end_year": 2023,
    "forecast_end_year": 2050,
    "weights": {
      "aging": 0.35,
      "debt": 0.35,
      "bloat": 0.15,
      "growth_drag": 0.15
    }
  },
  "results": {
    "entity": "JPN",
    "entity_name": "Japan",
    "scores": {
      "fiscal_trap_score": 2.35,
      "inflation_incentive_score": 1.95,
      "aging_pressure": 2.80,
      "debt_dynamics": 2.50,
      "bloat_index": 0.85,
      "growth_drag": 1.20
    },
    "risk_level": "CRITICAL",
    "quadrant": {
      "code": "Q1",
      "name": "HighAging_HighDebt",
      "description": "雙高危機：老化壓力與債務動態均處於高風險區"
    },
    "key_metrics": {
      "demographics": {
        "old_age_dependency_ratio": {
          "value": 0.485,
          "year": 2023,
          "unit": "ratio",
          "zscore": 2.8,
          "interpretation": "65歲以上人口為工作年齡人口的48.5%"
        },
        "old_age_dependency_slope_10y": {
          "value": 0.018,
          "unit": "per_year",
          "zscore": 1.5,
          "interpretation": "每年增加1.8個百分點"
        },
        "old_age_dependency_forecast_2050": {
          "value": 0.78,
          "source": "UN WPP Medium Variant"
        }
      },
      "debt": {
        "debt_to_gdp": {
          "value": 262.5,
          "year": 2023,
          "unit": "percent",
          "zscore": 2.9,
          "interpretation": "政府債務為GDP的262.5%"
        },
        "debt_to_gdp_slope_5y": {
          "value": 2.3,
          "unit": "pct_per_year",
          "zscore": 1.2,
          "interpretation": "每年增加約2.3個百分點"
        },
        "r_minus_g": {
          "nominal_yield_10y": 0.8,
          "nominal_gdp_growth": 2.1,
          "r_minus_g": -1.3,
          "zscore": -0.5,
          "interpretation": "名義利率低於名義成長，債務有自動穩定效果"
        }
      },
      "expenditure": {
        "gov_consumption_to_gdp": {
          "value": 20.5,
          "year": 2023,
          "unit": "percent",
          "zscore": 0.9
        },
        "gov_expenditure_to_gdp": {
          "value": 44.5,
          "year": 2023,
          "unit": "percent",
          "zscore": 1.2
        }
      },
      "growth": {
        "nominal_gdp_growth": {
          "value": 2.1,
          "year": 2023,
          "unit": "percent",
          "zscore": -0.8
        },
        "real_gdp_growth": {
          "value": 1.2,
          "year": 2023,
          "unit": "percent"
        }
      },
      "inflation_path": {
        "real_rate_current": {
          "value": -1.2,
          "year": 2023,
          "unit": "percent"
        },
        "negative_real_rate_share_5y": {
          "value": 0.80,
          "interpretation": "過去5年有80%時間處於負實質利率"
        },
        "financial_repression_index": {
          "value": 1.45,
          "interpretation": "顯示金融抑制特徵明顯"
        }
      }
    },
    "time_series": {
      "old_age_dependency": {
        "2010": 0.355,
        "2015": 0.425,
        "2020": 0.480,
        "2023": 0.485
      },
      "debt_to_gdp": {
        "2010": 215.8,
        "2015": 231.3,
        "2020": 259.4,
        "2023": 262.5
      }
    },
    "projection": {
      "old_age_dependency": {
        "2030": 0.55,
        "2040": 0.68,
        "2050": 0.78
      },
      "fiscal_pressure_increase_pct_gdp": 12.5
    }
  },
  "interpretation": {
    "summary": "日本呈現典型的人口-財政陷阱特徵：超高老化撫養比、超高政府債務、長期負實質利率。儘管r-g為負暫時穩定債務比率，但老化壓力持續攀升將推高養老金與健康支出，財政空間極度緊縮。",
    "key_findings": [
      "老年撫養比全球最高，且仍在加速上升",
      "政府債務佔GDP超過260%，為已開發國家中最高",
      "負實質利率持續8年以上，顯示金融抑制政策已制度化",
      "預計2050年老年撫養比將達78%，老年相關支出將再增GDP的12%以上"
    ],
    "policy_implications": [
      "財政改革空間極窄，削減福利政治代價高",
      "持續依賴央行購債維持低利率環境",
      "通膨稀釋是緩解實質債務負擔的主要出口",
      "需關注日圓長期購買力風險"
    ],
    "asset_allocation_implications": {
      "japanese_government_bonds": "UNDERWEIGHT - 實質報酬長期為負",
      "inflation_linked_bonds": "OVERWEIGHT - 若可用，提供通膨保護",
      "japanese_equities": "NEUTRAL - 名義資產受益於通膨，但經濟成長有限",
      "japanese_yen": "CAUTION - 長期購買力可能持續流失",
      "real_assets_japan": "OVERWEIGHT - 不動產、基礎設施等實質資產"
    }
  },
  "data_notes": {
    "sources": {
      "dependency_ratio": "World Bank WDI (SP.POP.DPND.OL)",
      "debt_to_gdp": "IMF WEO (GGXWDG_NGDP)",
      "gov_consumption": "World Bank WDI (NE.CON.GOVT.ZS)",
      "yield_10y": "OECD (IRLT)",
      "gdp_growth": "World Bank WDI (NY.GDP.MKTP.KD.ZG)",
      "cpi": "World Bank WDI (FP.CPI.TOTL.ZG)",
      "projection": "UN World Population Prospects 2024"
    },
    "missing_data": [],
    "fallbacks_used": [],
    "cross_section_stats": {
      "entities_in_sample": 38,
      "reference_group": "OECD"
    }
  }
}
```

---

## 多國比較輸出

```json
{
  "metadata": {
    "skill": "demographic-fiscal-trap-analyzer",
    "version": "0.1.0",
    "generated_at": "2024-01-15T10:30:00Z",
    "workflow": "cross-country"
  },
  "parameters": {
    "entities": ["G7"],
    "start_year": 2015,
    "end_year": 2023
  },
  "results": {
    "comparison_group": "G7",
    "entities_analyzed": ["USA", "JPN", "DEU", "GBR", "FRA", "ITA", "CAN"],
    "ranking": [
      {
        "rank": 1,
        "entity": "JPN",
        "entity_name": "Japan",
        "fiscal_trap_score": 2.35,
        "inflation_incentive_score": 1.95,
        "quadrant": "Q1",
        "risk_level": "CRITICAL"
      },
      {
        "rank": 2,
        "entity": "ITA",
        "entity_name": "Italy",
        "fiscal_trap_score": 1.82,
        "inflation_incentive_score": 1.45,
        "quadrant": "Q1",
        "risk_level": "HIGH"
      },
      {
        "rank": 3,
        "entity": "FRA",
        "entity_name": "France",
        "fiscal_trap_score": 1.15,
        "inflation_incentive_score": 0.95,
        "quadrant": "Q2",
        "risk_level": "ELEVATED"
      },
      {
        "rank": 4,
        "entity": "GBR",
        "entity_name": "United Kingdom",
        "fiscal_trap_score": 0.85,
        "inflation_incentive_score": 0.72,
        "quadrant": "Q3",
        "risk_level": "MODERATE"
      },
      {
        "rank": 5,
        "entity": "USA",
        "entity_name": "United States",
        "fiscal_trap_score": 0.72,
        "inflation_incentive_score": 0.88,
        "quadrant": "Q3",
        "risk_level": "MODERATE"
      },
      {
        "rank": 6,
        "entity": "DEU",
        "entity_name": "Germany",
        "fiscal_trap_score": 0.45,
        "inflation_incentive_score": 0.35,
        "quadrant": "Q2",
        "risk_level": "LOW"
      },
      {
        "rank": 7,
        "entity": "CAN",
        "entity_name": "Canada",
        "fiscal_trap_score": 0.12,
        "inflation_incentive_score": 0.25,
        "quadrant": "Q4",
        "risk_level": "LOW"
      }
    ],
    "risk_groups": {
      "critical": ["JPN"],
      "high": ["ITA"],
      "elevated": ["FRA"],
      "moderate": ["GBR", "USA"],
      "low": ["DEU", "CAN"]
    },
    "quadrant_distribution": {
      "Q1_HighAging_HighDebt": ["JPN", "ITA"],
      "Q2_HighAging_LowDebt": ["DEU", "FRA"],
      "Q3_LowAging_HighDebt": ["USA", "GBR"],
      "Q4_LowAging_LowDebt": ["CAN"]
    },
    "pillar_comparison": {
      "aging_pressure": {
        "JPN": 2.80,
        "ITA": 1.95,
        "DEU": 1.45,
        "FRA": 1.20,
        "GBR": 0.65,
        "USA": 0.45,
        "CAN": 0.30
      },
      "debt_dynamics": {
        "JPN": 2.50,
        "ITA": 1.75,
        "USA": 1.15,
        "GBR": 1.05,
        "FRA": 0.95,
        "CAN": 0.25,
        "DEU": 0.15
      },
      "bloat_index": {
        "FRA": 1.35,
        "ITA": 1.10,
        "JPN": 0.85,
        "DEU": 0.75,
        "GBR": 0.55,
        "USA": 0.40,
        "CAN": 0.30
      },
      "growth_drag": {
        "JPN": 1.20,
        "ITA": 1.55,
        "DEU": 0.85,
        "FRA": 0.65,
        "GBR": 0.50,
        "USA": -0.25,
        "CAN": -0.45
      }
    },
    "cross_section_stats": {
      "fiscal_trap_score": {
        "mean": 1.07,
        "std": 0.78,
        "min": 0.12,
        "max": 2.35
      }
    }
  },
  "interpretation": {
    "summary": "G7國家中，日本與義大利位於最高風險區（Q1象限），兩國均面臨高老化與高債務的雙重壓力。加拿大是唯一位於Q4健康象限的國家，政策空間最為寬廣。",
    "key_findings": [
      "日本與義大利需關注財政陷阱風險與通膨稀釋動機",
      "德國雖老化嚴重但財政紀律良好，債務水準可控",
      "美國與英國債務較高但人口結構相對年輕",
      "法國官僚膨脹指標為G7最高"
    ]
  }
}
```

---

## 錯誤/警告輸出

```json
{
  "metadata": {
    "skill": "demographic-fiscal-trap-analyzer",
    "version": "0.1.0",
    "generated_at": "2024-01-15T10:30:00Z",
    "workflow": "full-analysis"
  },
  "parameters": {
    "entities": ["XYZ"],
    "start_year": 2010,
    "end_year": 2023
  },
  "status": "partial_failure",
  "errors": [
    {
      "code": "ENTITY_NOT_FOUND",
      "message": "Entity 'XYZ' is not a valid ISO 3166-1 alpha-3 code",
      "severity": "error"
    }
  ],
  "warnings": [
    {
      "code": "DATA_MISSING",
      "entity": "ABC",
      "indicator": "IRLT",
      "message": "10-year yield not available, using policy rate as fallback",
      "severity": "warning"
    }
  ],
  "results": null
}
```
