# Markdown to PDF 渲染環境 (Python-based)

## 1. 專案簡介
本專案提供一個輕量、乾淨的 Sandbox 環境，用於將包含**中文字元**、**程式碼區塊 (Syntax Highlighting)** 以及 **數學公式 (KaTeX)** 的 `content.md` 檔案，渲染成排版精美的 PDF 格式。

### 選用工具與理由：
捨棄了龐大且設定繁瑣的 LaTeX (XeLaTeX) 環境，改採 Python 網頁渲染生態系，徹底解決缺字與跑版問題：
* **`Markdown` + `pymdown-extensions`**：負責將文本精準解析為 HTML。
* **`Pygments`**：提供高質感的程式碼語法高亮。
* **`markdown-katex`**：負責正確渲染數學公式。
* **`WeasyPrint`**：負責將 HTML 與 CSS 轉換為 PDF，原生支援 UTF-8 與現代網頁字體。

---

## 2. 專案檔案結構
```text
your-project/
├── content.md          # 你的 Markdown 筆記原始檔（輸入檔）
├── render.py           # 負責執行轉換的 Python 主程式
├── requirements.txt    # Python 套件清單
├── README.md           # 專案說明文件
└── output/             # 渲染後的 PDF 會自動儲存於此資料夾
    └──output.pdf

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
檔案位置： 渲染完成後，請至 output/output.pdf 查看結果。