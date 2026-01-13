import type { Category, DataLevelInfo } from '../types/skill';

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

export const dataLevels: DataLevelInfo[] = [
  {
    id: 'free-nolimit',
    name: '免費不限量',
    nameEn: 'Free Unlimited',
    color: 'green',
    emoji: '🟢',
    cost: '$0',
    description: '無 key、寬鬆 rate limit、或可離線資料',
  },
  {
    id: 'free-limit',
    name: '免費有限制',
    nameEn: 'Free Limited',
    color: 'yellow',
    emoji: '🟡',
    cost: '$0',
    description: 'API call/分鐘、日配額、延遲、資料範圍縮水',
  },
  {
    id: 'low-cost',
    name: '小額付費',
    nameEn: 'Low Cost',
    color: 'blue',
    emoji: '🔵',
    cost: '$5–$50/mo',
    description: '較高配額、更少延遲、更多欄位',
  },
  {
    id: 'high-cost',
    name: '高額付費',
    nameEn: 'High Cost',
    color: 'purple',
    emoji: '🟣',
    cost: '$100–$1k+/mo',
    description: '更完整覆蓋、即時/深度、SLA',
  },
  {
    id: 'enterprise',
    name: '企業/終端',
    nameEn: 'Enterprise',
    color: 'red',
    emoji: '🔴',
    cost: '合約/終端',
    description: '合約授權、終端、企業級 SLA',
  },
];

export function getCategoryName(id: string): string {
  const category = categories.find(c => c.id === id);
  return category ? category.name : id;
}

export function getCategoryNameEn(id: string): string {
  const category = categories.find(c => c.id === id);
  return category ? category.nameEn : id;
}

export function getDataLevelInfo(id: string): DataLevelInfo | undefined {
  return dataLevels.find(d => d.id === id);
}
