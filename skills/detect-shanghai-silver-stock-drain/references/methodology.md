# 方法論：上海白銀庫存耗盡訊號偵測

本文件說明「三維度量化」方法論，將社群推文中的敘事（「上海白銀庫存暴跌」）轉化為可執行、可驗證的量化訊號。

---

## 核心概念

### 為什麼需要量化？

社群經常出現類似推文：
> 「上海白銀庫存又創新低了！供給緊縮訊號！」

這類敘事存在問題：
1. **模糊**：「新低」相對於什麼時間範圍？
2. **單一維度**：只看水位，沒看變化速度
3. **無法驗證**：缺乏可重現的判斷標準

本方法論將敘事轉為三維度量化框架：**方向 × 速度 × 加速度**

---

## 三維度量化框架

### 維度定義

| 維度 | 符號 | 計算方式 | 意義 |
|------|------|----------|------|
| 方向 | Δ1(t) | `combined(t) - combined(t-1)` | 庫存是上升還是下降 |
| 速度 | drain_rate(t) | `-Δ1(t)` | 每週流出量（正值=流出） |
| 加速度 | Δ2(t) | `drain_rate(t) - drain_rate(t-1)` | 流出速度的變化 |

### 直觀理解

想像庫存是一個水庫：
- **方向**：水位在上升還是下降？
- **速度**：水流出的速度有多快？
- **加速度**：水流出的速度是在加快還是減慢？

**關鍵洞察**：
- 水位下降（Δ1 < 0）很常見
- 水位下降且速度很快（drain_rate 高）值得注意
- 水位下降、速度快、且還在加速（Δ2 > 0）→ 這才是真正的「晚期供給訊號」

---

## Z 分數標準化

### 為什麼需要標準化？

原始數值難以跨時期比較：
- 2020 年流出 100 噸/週 vs 2025 年流出 100 噸/週
- 基數不同，意義不同

Z 分數解決這個問題：
```
z = (x - mean) / std
```

- Z = 0：與歷史平均相同
- Z = -2：比歷史平均低 2 個標準差（異常流出）
- Z = +2：比歷史平均高 2 個標準差（異常流入）

### 計算視窗

建議使用 156 週（約 3 年）滾動視窗：

```python
z_window = 156  # 3 年

df["z_drain_rate"] = (
    (df["drain_rate_sm"] - df["drain_rate_sm"].rolling(z_window).mean()) /
    df["drain_rate_sm"].rolling(z_window).std()
)

df["z_accel"] = (
    (df["accel_sm"] - df["accel_sm"].rolling(z_window).mean()) /
    df["accel_sm"].rolling(z_window).std()
)
```

### 平滑處理

單週數據可能有噪音（搬倉、規則變動），建議使用 4 週平滑：

```python
smooth_window = 4

df["drain_rate_sm"] = df["drain_rate"].rolling(smooth_window, min_periods=1).mean()
df["accel_sm"] = df["accel"].rolling(smooth_window, min_periods=1).mean()
```

---

## 三段式訊號判定

### 條件定義

| 條件 | 代號 | 判斷標準 | 說明 |
|------|------|----------|------|
| 庫存水位偏低 | A | level_percentile ≤ 0.20 | 低於歷史 20% 分位 |
| 耗盡速度異常 | B | z_drain_rate ≤ -1.5 | 流出顯著高於常態 |
| 耗盡加速 | C | z_accel ≥ +1.0 | 流出正在加速 |

### 訊號分級

```python
def classify_signal(A, B, C):
    if A and B and C:
        return "HIGH_LATE_STAGE_SUPPLY_SIGNAL"
    if (B and C) or (A and B):
        return "MEDIUM_SUPPLY_TIGHTENING"
    if A or B or C:
        return "WATCH"
    return "NO_SIGNAL"
```

### 訊號含義

| 訊號 | 條件組合 | 解讀 | 建議動作 |
|------|----------|------|----------|
| HIGH | A+B+C | 晚期供給訊號，所有條件成立 | 高度警戒，立即交叉驗證 |
| MEDIUM | B+C 或 A+B | 供給趨緊，多數條件成立 | 持續關注，準備行動 |
| WATCH | 任一成立 | 單一異常，可能是噪音 | 保持觀察 |
| NO_SIGNAL | 無 | 正常狀態 | 無需動作 |

---

## 數據口徑說明

### SGE vs SHFE

| 交易所 | 全稱 | 庫存口徑 | 數據頻率 |
|--------|------|----------|----------|
| SGE | 上海黃金交易所 | 指定倉庫庫存 | 週報 |
| SHFE | 上海期貨交易所 | 倉單（可交割） | 日報/週報 |

### 重要限制

**這不是全中國社會庫存！**

交易所庫存只反映：
- 可交割的白銀
- 存放在交易所指定/認可倉庫
- 登記為倉單的部分

不包括：
- 工業用戶庫存
- 貿易商庫存
- 零售/投資者實物持有

**解讀時需謹慎**：交易所庫存下降可能是：
1. 實物被提走（緊縮訊號）
2. 搬倉到其他倉庫（中性）
3. 倉儲規則調整（技術性）
4. 數據統計口徑變化（誤導）

---

## 交叉驗證邏輯

### 驗證指標

| 指標 | 支持緊縮假設 | 反駁緊縮假設 |
|------|--------------|--------------|
| COMEX Registered | 同步下降 | 穩定或上升 |
| SLV ETF 持倉 | 同步下降 | 穩定或上升 |
| 期貨結構 | Backwardation | Contango |
| 現貨溢價 | 擴大 | 穩定或收窄 |
| 價格波動 | 上升 | 穩定 |

### 信心度計算

```python
confidence = support_count / total_checks

# 信心度解讀
if confidence >= 0.7:
    interpretation = "高度確認"
elif confidence >= 0.5:
    interpretation = "部分確認"
else:
    interpretation = "未確認"
```

---

## 實例解讀

### 情境 1：HIGH 訊號

```
level_percentile = 0.12  # A ✓ (< 0.20)
z_drain_rate = -2.1      # B ✓ (≤ -1.5)
z_accel = +1.4           # C ✓ (≥ +1.0)
→ HIGH_LATE_STAGE_SUPPLY_SIGNAL
```

**解讀**：
> 上海合併庫存處於歷史低檔（12% 分位），近期流出速度異常（Z=-2.1），且流出仍在加速（Z=+1.4）。三項條件同時成立，為晚期供給緊縮訊號。

### 情境 2：WATCH 訊號

```
level_percentile = 0.35  # A ✗
z_drain_rate = -1.8      # B ✓
z_accel = +0.3           # C ✗
→ WATCH
```

**解讀**：
> 流出速度偏高（Z=-1.8），但庫存水位仍在中間區間（35% 分位），且流出並未加速。僅單一條件成立，建議持續觀察。

---

## 參考文獻

- 原始推文敘事分析
- CME Group COMEX 庫存報表
- 上海黃金交易所官網
- 上海期貨交易所官網
