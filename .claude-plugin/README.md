# Macro Skills - Claude Plugin Marketplace

宏觀經濟技能市集，專為宏觀經濟分析設計的 Claude 技能集合。

## 安裝方式

在 Claude 中執行以下指令即可安裝整個技能市集：

```
/plugin marketplace add fatfingererr/macro-skills
```

## 包含技能

市集目前包含以下技能：

- **經濟指標分析師** - 分析 GDP、CPI、失業率、PMI 等經濟指標
- **央行政策解碼器** - 解讀央行聲明、會議紀要、政策訊號
- **景氣循環判官** - 判斷當前景氣位置、預測週期轉折點

## 技能分類

市集將技能分為 18 個類別：

1. 資料處理
2. 指標監控
3. 即時預測
4. 景氣週期
5. 通膨分析
6. 勞動市場
7. 消費需求
8. 產業景氣
9. 房市居住
10. 央行操作
11. 政策模型
12. 存貸利率
13. 外匯因子
14. 跨境金流
15. 信用風險
16. 流動性條件
17. 商品供需
18. 事件情境

## 資料等級

每個技能都標示其資料來源成本等級：

- **免費不限量** (green) - 無 API key 需求、寬鬆存取限制
- **免費有限制** (yellow) - 有 API 呼叫次數限制
- **小額付費** (blue) - $5-$50/月
- **高額付費** (purple) - $100-$1000+/月
- **企業授權** (red) - 合約制

## 進階操作

```bash
# 列出所有可用技能
/plugin marketplace list macroskills

# 啟用特定技能
/plugin marketplace enable macroskills/economic-indicator-analyst

# 停用特定技能
/plugin marketplace disable macroskills/economic-indicator-analyst

# 更新 marketplace
/plugin marketplace update macroskills

# 移除 marketplace
/plugin marketplace remove macroskills
```

## 使用方式

安裝後，您可以直接與 Claude 對話，Claude 會自動選擇適合的技能來處理您的請求：

```
請幫我分析最新的 CPI 數據
```

或明確指定技能：

```
使用經濟指標分析師，分析最新的非農就業報告
```

## 授權

MIT License

## 連結

- 網站：https://fatfingererr.github.io/macro-skills/
- GitHub：https://github.com/fatfingererr/macro-skills
