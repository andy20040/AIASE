# 📝 LogAlert CLI：從過濾工具到規則引擎的演化

## 1. 專案簡介

- **v1.0 功能與動機**：最初設計是為了協助開發者在繁雜的 Linux 日誌中快速定位關鍵字（如 Exception）。核心目標是建立一個「即插即用」的輕量級工具，支援基本規則管理與單次掃描。
- **v1.0 到 v2.0 的演化摘要**：從單純的「字串比對」演進為支援「正規表達式」的規則引擎，並加入了警報持久化與等級過濾功能，解決了大規模日誌追查時資訊過載與紀錄遺失的痛點。

## 2. v1.0 設計決策 (Design Decisions)

在撰寫 v1.0 時，我針對未來可能的延伸需求做了以下預先考量：

**為什麼選擇類別化設計 (Class-based Design)？**

我將 `RuleStorage`（資料層）與 `LogScanner`（邏輯層）完全拆分。

> **預判邏輯**：即使 v1.0 只用 JSON，我也預見了未來可能升級為 SQLite 的需求。透過類別化，v2.0 升級時只需修改 `RuleStorage` 內部實作，不影響主程式運作。

**為什麼將 `_is_match` 邏輯獨立？**

雖然 v1.0 只有 `keyword in line`，但我預留了比對邏輯的擴充介面。

> **預判邏輯**：考慮到未來客戶可能要求「正則表達式」或「多條件組合比對」，將比對邏輯抽離能確保 `scan` 與 `monitor` 功能同步升級。

**指令介面的前瞻性設計**：

使用 `argparse` 的子指令 (Subparsers) 結構，確保未來新增 `rule_stats` 等功能時，不會破壞現有的指令層級。

## 3. v2.0 實作說明

**需求映射**：針對 Agent 提出的「正則模式」需求，我透過擴充 Rule 資料模型的 `mode` 欄位，並在 `LogScanner` 中引入 `re` 模組來實現。

**非顯而易見的實作選擇**：

- **Regex 安全性**：在 `rule_add` 階段即使用 `re.compile()` 進行語法驗證，避免在掃描數 GB 的日誌到一半時才因為語法錯誤崩潰。
- **Monitor 摘要統計**：在監控迴圈中使用計數器，並利用 `KeyboardInterrupt` (Ctrl+C) 攔截機制，在結束前優雅地印出統計結果。

## 4. 向下相容性實作細節

為了確保 v1.0 的測試案例能在 v2.0 完美通過：

- **資料相容策略**：在讀取舊有的 `rules.json` 時，使用 `dict.get('mode', 'plain')`。這確保了 v1.0 建立的規則（沒有 `mode` 欄位）在 v2.0 中能被自動識別為一般比對模式，無需手動遷移。
- **參數預設值**：所有 v2.0 新增的參數（如 `--mode`, `--level`, `--log-output`）皆設有預設值或設為選填。若使用者沿用 v1.0 的指令習慣，程式行為將與舊版完全一致。

## 5. 架構演化比較

| 面向 | v1.0 | v2.0 |
|------|------|------|
| 比對引擎 | 字串包含 (Literal) | 字串包含 + 正則表達式 (Regex) |
| 資料模型 | ID, Keyword, Level, Time | 新增 Mode 欄位 |
| 監控模式 | 僅螢幕輸出 | 螢幕輸出 + 檔案同步持久化 |
| 過濾能力 | 全量輸出 | 支援按警報等級 (Level) 篩選 |

## 6. 環境需求與執行方式

**環境需求**

- Python 3.10+
- 無需額外套件（僅使用內建庫 `argparse`, `json`, `re`, `time`）

**執行方式**

```bash
# v1.0 核心指令（v2.0 亦完全支援）
python v1/main.py rule_add --keyword "Exception" --level "ERROR"
python v1/main.py scan --file "./sample.log"

# v2.0 新增功能
# 1. 使用正則表達式
python v2/main.py rule_add --keyword "Conn\w+" --mode regex
# 2. 等級過濾掃描
python v2/main.py scan --file "./sample.log" --level ERROR
# 3. 監控並匯出
python v2/main.py monitor --file "./sample.log" --log-output alerts.txt
# 4. 快速命中統計
python v2/main.py rule_stats --file "./sample.log"
```

## 7. 已知限制與未來改進方向 (v3.0 展望)

- **效能限制**：目前的 `monitor` 採用輪詢 (Polling) 機制，對於極高頻率更新的日誌可能會造成 CPU 負荷。未來 v3.0 可考慮引入 `inotify` 或 `watchdog` library。
- **多檔案監控**：目前的指令一次只能監控一個檔案，未來可擴充為支援目錄掃描。
- **安全性**：目前 `rules.json` 為明碼，未來若涉及敏感關鍵字，應引入加密儲存機制。
