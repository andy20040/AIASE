# Markdown to HTML 渲染環境 (Python-based)

## 1. 專案簡介
本專案提供一個輕量、乾淨的 Sandbox 環境，用於將包含**中文字元**、**程式碼區塊 (Syntax Highlighting)**、**待辦清單 (Task Lists)** 以及 **數學公式 (KaTeX)** 的 `content.md` 檔案，渲染成排版精美且能在瀏覽器中直接開啟的 HTML 網頁格式。

### 選用工具與理由：
改採純 Python 網頁渲染生態系，無需安裝龐大的 PDF 渲染引擎或底層依賴，轉換速度極快且絕不跑版：
* **`Markdown` + `pymdown-extensions`**：負責將文本精準解析為 HTML，並支援表格、待辦清單 (`- [ ]`) 等 HackMD 常用語法。
* **`Pygments`**：提供高質感的程式碼語法高亮。
* **`markdown-katex`**：負責正確渲染數學公式。

---

## 2. 專案檔案結構
```text
your-project/
├── content.md          # 你的 Markdown 筆記原始檔（輸入檔）
├── render.py           # 負責執行轉換的 Python 主程式
├── requirements.txt    # Python 套件清單
├── README.md           # 專案說明文件
└── output/             # 渲染後的 HTML 會自動儲存於此資料夾
    └── output.html

3. 環境需求與建置步驟
步驟一：建立並啟動 Python 虛擬環境 (venv)
為避免套件版本與系統中其他的 Python 專案衝突，強烈建議使用虛擬環境將專案隔離。

# 1. 建立名為 .venv 的虛擬環境
python3 -m venv .venv

# 2. 啟動虛擬環境 (終端機前方會出現 `(.venv)` 標籤)
source .venv/bin/activate

步驟二：安裝 Python 渲染套件
透過 pip 讀取清單，一次安裝所有需要的 Python 轉換套件。


pip install -r requirements.txt

(註：若安裝過程中 WeasyPrint 發生版本衝突，可手動執行 pip install --upgrade weasyprint pydyf 更新底層依賴。)

4. 執行渲染
確認你的 content.md 已準備好並放置於專案根目錄下。接著，只要執行 Python 腳本即可：


python render.py

5. 預期輸出
檔案位置： 渲染完成後，請至 output/output.html，並直接點擊以瀏覽器（如 Chrome, Edge）開啟。

