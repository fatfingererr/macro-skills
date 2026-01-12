import type { Category, RiskLevelInfo } from '../types/skill';

export const categories: Category[] = [
  { id: 'data-processing', name: '資料處理', nameEn: 'Data Processing' },
  { id: 'indicator-monitoring', name: '指標監控', nameEn: 'Indicator Monitoring' },
  { id: 'nowcasting', name: '即時預測', nameEn: 'Nowcasting' },
  { id: 'business-cycles', name: '景氣週期', nameEn: 'Business Cycles & Regimes' },
  { id: 'inflation-analytics', name: '通膨分析', nameEn: 'Inflation Analytics' },
  { id: 'labor-market', name: '勞動市場', nameEn: 'Labor Market Analytics' },
  { id: 'consumption-demand', name: '消費需求', nameEn: 'Consumption & Demand' },
  { id: 'production-investment', name: '產業景氣', nameEn: 'Production & Investment' },
  { id: 'housing-shelter', name: '房市居住', nameEn: 'Housing & Shelter' },
  { id: 'central-bank-policy', name: '央行操作', nameEn: 'Central Bank Policy Signals' },
  { id: 'policy-modeling', name: '政策模型', nameEn: 'Policy Modeling' },
  { id: 'interest-rates', name: '存貸利率', nameEn: 'Interest Rates' },
  { id: 'fx-factors', name: '外匯因子', nameEn: 'FX Factors' },
  { id: 'capital-flows', name: '跨境金流', nameEn: 'Capital Flows & BoP' },
  { id: 'credit-risk', name: '信用風險', nameEn: 'Credit Risk' },
  { id: 'liquidity-fci', name: '流動性條件', nameEn: 'Liquidity & FCI' },
  { id: 'commodity-sd', name: '商品供需', nameEn: 'Commodity S&D' },
  { id: 'event-scenario', name: '事件情境', nameEn: 'Event Risk & Scenario' },
];

export const riskLevels: RiskLevelInfo[] = [
  { id: 'safe', name: '安全', color: 'green' },
  { id: 'low', name: '低風險', color: 'blue' },
  { id: 'medium', name: '中風險', color: 'yellow' },
  { id: 'high', name: '高風險', color: 'orange' },
  { id: 'critical', name: '關鍵', color: 'red' },
];

export function getCategoryName(id: string): string {
  const category = categories.find(c => c.id === id);
  return category ? category.name : id;
}

export function getCategoryNameEn(id: string): string {
  const category = categories.find(c => c.id === id);
  return category ? category.nameEn : id;
}

export function getRiskLevelInfo(id: string): RiskLevelInfo | undefined {
  return riskLevels.find(r => r.id === id);
}
