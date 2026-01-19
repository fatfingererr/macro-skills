# Demographic-Fiscal Trap Analyzer - Visualization Scripts

人口財政陷阱分析器 - 可視化腳本

---

## 📊 可用腳本

### visualize_combined.py
綜合可視化圖表生成器，整合所有關鍵分析指標於單一高清圖表中。

**功能：**
- 生成 20×14 英吋高清圖表（300 DPI）
- 支持中英文雙語
- 包含 10 個關鍵信息視圖
- 自動生成 PNG 和 PDF 兩種格式
- 跨平台中文字體支持

---

## 🚀 使用方法

### 基本用法

```bash
# 生成中文版本
python visualize_combined.py --language zh

# 生成英文版本
python visualize_combined.py --language en

# 指定數據文件和輸出目錄
python visualize_combined.py \
    --data path/to/data.json \
    --output path/to/output \
    --language zh
```

### 參數說明

| 參數 | 類型 | 預設值 | 說明 |
|------|------|--------|------|
| `--data` | string | `output/japan_demographic_fiscal_trap_2010-2023_structured.json` | 結構化數據文件路徑 |
| `--output` | string | `output` | 輸出目錄 |
| `--language` | string | `zh` | 語言選擇：`zh`（中文）或 `en`（英文）|

---

## 📈 生成內容

### 10 個關鍵視圖

1. **綜合風險評分** - Fiscal Trap Score & Inflation Incentive Score
2. **四支柱評分** - Aging, Debt, Bloat, Growth
3. **老年撫養比時序** - 2010-2023 歷史數據
4. **政府債務/GDP** - 2010-2023 歷史數據
5. **實質利率分析** - 2019-2023 金融抑制
6. **名義GDP成長** - 2010-2023 經濟表現
7. **撫養比投影** - 2024-2050 長期預測
8. **債務投影** - 2024-2050 債務軌跡
9. **利息支出投影** - 財政壓力預測
10. **資產配置建議** - 投資組合優化

---

## 🎨 中文字體支持

腳本使用以下字體備用鏈（按優先順序）：

1. **Microsoft JhengHei** - 微軟正黑體（Windows 繁體中文）
2. **SimHei** - 黑體（Windows 簡體中文）
3. **STHeiti** - 華文黑體（macOS）
4. **WenQuanYi Zen Hei** - 文泉驛正黑（Linux）
5. **DejaVu Sans** - 備用英文字體

### 字體安裝建議

**Windows:**
- 預裝了 Microsoft JhengHei 和 SimHei，無需額外安裝

**macOS:**
- 預裝了 STHeiti，無需額外安裝
- 可選安裝 Microsoft JhengHei 以獲得更好的繁體中文支持

**Linux:**
```bash
# Ubuntu/Debian
sudo apt-get install fonts-wqy-zenhei

# Fedora/RHEL
sudo dnf install wqy-zenhei-fonts

# Arch Linux
sudo pacman -S wqy-zenhei
```

---

## 📦 依賴套件

```bash
pip install matplotlib numpy
```

或使用 requirements.txt：
```bash
pip install -r requirements.txt
```

---

## 🖼️ 輸出範例

### 檔案命名格式

```
Japan_Demographic_Fiscal_Trap_Combined_{LANGUAGE}_{DATE}.{EXT}
```

例如：
- `Japan_Demographic_Fiscal_Trap_Combined_ZH_20260119.png` (中文版 PNG)
- `Japan_Demographic_Fiscal_Trap_Combined_ZH_20260119.pdf` (中文版 PDF)
- `Japan_Demographic_Fiscal_Trap_Combined_EN_20260119.png` (英文版 PNG)
- `Japan_Demographic_Fiscal_Trap_Combined_EN_20260119.pdf` (英文版 PDF)

### 規格

- **尺寸**: 20 × 14 英吋
- **解析度**: 300 DPI
- **格式**: PNG (高清) + PDF (列印優化)
- **檔案大小**: 約 700-800 KB (PNG), 60-100 KB (PDF)

---

## ⚡ 快速開始

### 從專案根目錄執行

```bash
# 切換到專案根目錄
cd /path/to/macro-skills

# 生成中英文雙語圖表
python .claude/skills/demographic-fiscal-trap-analyzer/scripts/visualize_combined.py --language zh
python .claude/skills/demographic-fiscal-trap-analyzer/scripts/visualize_combined.py --language en
```

### 從 scripts 目錄執行

```bash
cd .claude/skills/demographic-fiscal-trap-analyzer/scripts

# 需要指定相對於專案根目錄的路徑
python visualize_combined.py \
    --data ../../../output/japan_demographic_fiscal_trap_2010-2023_structured.json \
    --output ../../../output \
    --language zh
```

---

## 🔧 故障排除

### 問題：中文顯示為方塊

**解決方案：**
1. 確認已安裝中文字體（見上方「字體安裝建議」）
2. 嘗試使用英文版本（`--language en`）
3. 清除 matplotlib 字體緩存：
```bash
rm -rf ~/.cache/matplotlib
```

### 問題：找不到數據文件

**解決方案：**
確保數據文件存在且路徑正確：
```bash
ls -l output/japan_demographic_fiscal_trap_2010-2023_structured.json
```

### 問題：權限錯誤

**解決方案：**
```bash
chmod +x .claude/skills/demographic-fiscal-trap-analyzer/scripts/visualize_combined.py
```

---

## 📊 與其他腳本的集成

### 完整分析流程

```bash
# 步驟 1: 執行分析（生成數據）
# （由主 skill 執行）

# 步驟 2: 生成可視化圖表
python .claude/skills/demographic-fiscal-trap-analyzer/scripts/visualize_combined.py --language zh
python .claude/skills/demographic-fiscal-trap-analyzer/scripts/visualize_combined.py --language en

# 步驟 3: 查看結果
ls -lh output/Japan_Demographic_Fiscal_Trap_Combined_*
```

---

## 📖 技術細節

### 圖表布局

使用 matplotlib GridSpec 創建 4×4 網格：
```
┌─────────────────────────────────────────┐
│  Row 1: 風險評分卡 | 四支柱評分          │
├─────────────────────────────────────────┤
│  Row 2: 撫養比時序 | 債務時序            │
├─────────────────────────────────────────┤
│  Row 3: 實質利率   | 名義成長            │
├─────────────────────────────────────────┤
│  Row 4: 撫養比投影 | 債務投影 | 利息 | 配置 │
└─────────────────────────────────────────┘
```

### 顏色編碼

- **紅色** (#d62728): 高風險/危險
- **橙色** (#ff7f0e): 中度風險/警告
- **綠色** (#2ca02c): 低風險/正常
- **藍色** (#1f77b4): 資訊性數據

---

## 📝 許可證

本腳本為 demographic-fiscal-trap-analyzer skill 的一部分。

---

## 🤝 貢獻

如需改進或新增功能，請參考專案主 README。

---

**最後更新**: 2026-01-19
**版本**: 1.0.0
**維護者**: macro-skills-team
