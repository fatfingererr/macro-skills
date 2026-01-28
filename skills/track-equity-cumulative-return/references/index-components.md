# 支援的指數成分股列表

本文檔列出支援的指數及其成分股。

> **注意**：成分股列表可能會隨時間調整，此為 2026 年初的參考版本。

---

## 1. Nasdaq 100 (nasdaq100)

**描述**：納斯達克 100 指數，追蹤納斯達克交易所市值最大的 100 家非金融公司。

**預設基準**：^NDX

**成分股**（約 100 支）：

```
AAPL    MSFT    AMZN    NVDA    GOOGL   GOOG    META    TSLA    AVGO    COST
NFLX    AMD     PEP     ADBE    CSCO    TMUS    INTC    CMCSA   INTU    QCOM
TXN     AMGN    HON     AMAT    ISRG    BKNG    SBUX    LRCX    VRTX    ADP
MDLZ    GILD    ADI     REGN    PANW    KLAC    MU      SNPS    CDNS    PYPL
MELI    CSX     ASML    CRWD    MAR     ORLY    ABNB    MRVL    CTAS    NXPI
PCAR    WDAY    CPRT    ROP     MNST    FTNT    DXCM    PAYX    ROST    KDP
ODFL    MCHP    KHC     AEP     IDXX    GEHC    FAST    AZN     LULU    EXC
VRSK    EA      CTSH    CSGP    XEL     DLTR    BKR     FANG    TTWO
TEAM    ON      CDW     BIIB    ZS      DDOG    GFS     ILMN    MDB     WBD
CEG     LCID    RIVN    SIRI    JD      PDD     BIDU    NTES    ZM
```

---

## 2. S&P 100 (sp100)

**描述**：標普 100 指數，追蹤美國市值最大的 100 家公司。

**預設基準**：^GSPC

**成分股**（100 支）：

```
AAPL    ABBV    ABT     ACN     ADBE    AIG     AMD     AMGN    AMZN    AVGO
AXP     BA      BAC     BK      BKNG    BLK     BMY     BRK-B   C       CAT
CHTR    CL      CMCSA   COF     COP     COST    CRM     CSCO    CVS     CVX
DE      DHR     DIS     DOW     DUK     EMR     EXC     F       FDX     GD
GE      GILD    GM      GOOG    GOOGL   GS      HD      HON     IBM     INTC
JNJ     JPM     KHC     KO      LIN     LLY     LMT     LOW     MA      MCD
MDLZ    MDT     MET     META    MMM     MO      MRK     MS      MSFT    NEE
NFLX    NKE     NVDA    ORCL    PEP     PFE     PG      PM      PYPL    QCOM
RTX     SBUX    SCHW    SO      SPG     T       TGT     TMO     TMUS    TSLA
TXN     UNH     UNP     UPS     USB     V       VZ      WFC     WMT     XOM
```

---

## 3. Dow Jones 30 (dow30)

**描述**：道瓊工業平均指數，追蹤美國 30 家大型藍籌股。

**預設基準**：^DJI

**成分股**（30 支）：

```
AAPL    AMGN    AMZN    AXP     BA      CAT     CRM     CSCO    CVX     DIS
DOW     GS      HD      HON     IBM     INTC    JNJ     JPM     KO      MCD
MMM     MRK     MSFT    NKE     PG      TRV     UNH     V       VZ      WMT
```

---

## 4. Philadelphia Semiconductor (sox)

**描述**：費城半導體指數，追蹤美國上市的半導體公司。

**預設基準**：^SOX

**成分股**（30 支）：

```
NVDA    AVGO    AMD     QCOM    TXN     INTC    MU      AMAT    LRCX    KLAC
ADI     MRVL    NXPI    ON      MCHP    MPWR    SWKS    QRVO    TER     ENTG
TSM     ASML    ARM     WOLF    ACLS    ALGM    AMKR    COHR    CRUS    FORM
```

---

## 5. 成分股分類

### 按產業（Nasdaq 100）

| 產業         | 代表公司                        |
|--------------|---------------------------------|
| 科技         | AAPL, MSFT, GOOGL, META         |
| 半導體       | NVDA, AMD, AVGO, INTC           |
| 電商/零售    | AMZN, COST                      |
| 串流/娛樂    | NFLX, EA, TTWO                  |
| 電動車       | TSLA, RIVN, LCID                |
| 雲端/SaaS    | CRM, WDAY, DDOG, ZS             |
| 生技/醫療    | AMGN, GILD, REGN, VRTX          |
| 電信         | TMUS, CMCSA                     |

### 按產業（費城半導體）

| 類型         | 代表公司                        |
|--------------|---------------------------------|
| GPU/AI       | NVDA, AMD                       |
| 代工         | TSM                             |
| 設備         | ASML, AMAT, LRCX, KLAC          |
| 通訊晶片     | QCOM, AVGO                      |
| 記憶體       | MU                              |
| 類比/混合    | ADI, TXN                        |
| 車用/工業    | ON, NXPI, MCHP                  |

---

## 6. 更新說明

### 成分股調整

- 指數成分股會定期調整（通常季度或年度）
- 本列表需定期更新以反映最新組成

### 最後更新

- 日期：2026-01-28
- 來源：各指數官方網站、Yahoo Finance

### 更新方式

若需更新成分股列表，請編輯：
`scripts/index_component_analyzer.py` 中的以下變數：

- `SP100_COMPONENTS`
- `NASDAQ100_COMPONENTS`
- `DOW30_COMPONENTS`
- `SOX_COMPONENTS`
