<required_reading>
**執行此 workflow 前，可選擇閱讀：**
1. references/data-sources.md - 了解資料來源
</required_reading>

<objective>
快速檢查最新的 CPI/PCE 分歧，適合日常監控或快速回答「現在 CPI/PCE 差多少？」
</objective>

<process>

<step number="1" name="執行快速檢查">

**最簡單的方式**

```bash
cd skills/us-cpi-pce-comparator
python scripts/cpi_pce_analyzer.py --quick
```

這會輸出：
```json
{
  "as_of": "2026-01-14",
  "headline": {
    "cpi_yoy": 2.65,
    "pce_yoy": 2.79,
    "gap_bps": 14
  },
  "core": {
    "cpi_core_yoy": 2.65,
    "pce_core_yoy": 2.83,
    "gap_bps": 18
  },
  "momentum": {
    "cpi_3m_saar": 2.07,
    "pce_3m_saar": 2.82,
    "momentum_divergence": 0.75
  }
}
```

</step>

<step number="2" name="解讀結果">

**關鍵指標解讀**

| 指標 | 含義 |
|------|------|
| `headline.gap_bps > 0` | PCE 高於 CPI，Fed 目標指標更具黏性 |
| `headline.gap_bps < 0` | PCE 低於 CPI，罕見 |
| `core.gap_bps` | Core 分歧，排除食品能源波動 |
| `momentum_divergence > 0` | PCE 短期動能更強 |

**快速結論模板**：

```
當前 CPI/PCE 分歧：{gap_bps} bps

解讀：
- PCE {'高於' if gap > 0 else '低於'} CPI
- {'Fed 目標指標更頑固，鷹派風險' if gap > 0 else '市場可能高估通膨壓力'}
- 3M 動能：{'PCE 加速更快' if momentum > 0 else 'CPI 加速更快'}
```

</step>

<step number="3" name="（可選）手動檢查">

**若不想執行腳本，可直接查看 FRED**

1. 打開瀏覽器訪問：
   - CPI: https://fred.stlouisfed.org/series/CPIAUCSL
   - PCE: https://fred.stlouisfed.org/series/PCEPI
   - Core CPI: https://fred.stlouisfed.org/series/CPILFESL
   - Core PCE: https://fred.stlouisfed.org/series/PCEPILFE

2. 查看「Percent Change from Year Ago」選項

3. 手動計算 gap = PCE - CPI

</step>

</process>

<quick_interpretation_guide>

**快速解讀指南**

| 情境 | 分歧 | 含義 |
|------|------|------|
| 常態 | PCE > CPI 10-30 bps | 正常範圍 |
| 分歧擴大 | PCE > CPI > 30 bps | 醫療或權重效應推升 PCE |
| 分歧縮小 | PCE ≈ CPI | 兩指標訊號趨於一致 |
| 反轉 | CPI > PCE | 住房或能源價格衝擊 |

**動能解讀**

| momentum_divergence | 含義 |
|---------------------|------|
| > 0.5 | PCE 短期加速明顯，關注上行風險 |
| -0.5 ~ 0.5 | 兩指標動能相近 |
| < -0.5 | CPI 短期加速更快，可能是住房驅動 |

</quick_interpretation_guide>

<success_criteria>
快速檢查完成時應輸出：

- [ ] 最新 CPI 和 PCE 的 YoY 數值
- [ ] Core CPI 和 Core PCE 的 YoY 數值
- [ ] Headline 和 Core 的 gap（bps）
- [ ] 3M SAAR 動能比較
- [ ] 一句話 quick take
</success_criteria>
