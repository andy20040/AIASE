import os
import markdown
from pygments.formatters import HtmlFormatter

def render_md_to_html(input_file, output_file):
    # 自動檢查並建立 output 資料夾
    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    # 1. 讀取 Markdown 檔案
    with open(input_file, 'r', encoding='utf-8') as f:
        md_text = f.read()

    # 2. 轉換 Markdown 為 HTML，掛載擴充套件
    html_body = markdown.markdown(
        md_text,
        extensions=[
            'tables',                   # 支援表格
            'pymdownx.superfences',     # 更強大的程式碼區塊支援
            'pymdownx.highlight',       # 配合 Pygments 處理語法高亮
            'markdown_katex',           # 支援數學公式渲染
            'pymdownx.tasklist',        # 支援 - [ ] / - [x] 待辦清單
        ],
    )

    # 3. 抓取 Pygments 的程式碼配色 CSS
    pygments_css = HtmlFormatter(style='default').get_style_defs('.highlight')

    # 4. 組合完整的 HTML
    full_html = f"""
    <!DOCTYPE html>
    <html lang="zh-TW">
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Markdown 渲染結果</title>
        <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.16.4/dist/katex.min.css">
        <style>
            /* 基礎排版設定 */
            body {{
                font-family: 'Noto Sans CJK TC', 'Microsoft JhengHei', sans-serif;
                line-height: 1.6;
                color: #333;
                max-width: 800px; /* 限制網頁最大寬度，讓閱讀體驗更好 */
                margin: 0 auto;   /* 讓內容置中 */
                padding: 2em;
            }}
            /* 處理 HackMD 風格的引言 (Blockquotes) */
            blockquote {{
                border-left: 4px solid #dfe2e5;
                margin: 0 0 16px 0;
                padding: 0 16px;
                color: #6a737d;
                background-color: #f9f9f9;
            }}
            /* 程式碼區塊美化 */
            pre {{
                background-color: #f6f8fa;
                padding: 16px;
                border-radius: 6px;
                font-family: 'Courier New', Courier, monospace;
                overflow-x: auto;
            }}
            code {{
                font-family: 'Courier New', Courier, monospace;
            }}
            /* 待辦清單樣式（對應 - [ ] / - [x]） */
            ul.task-list {{
                list-style: none;
                padding-left: 0;
            }}
            .task-list-item {{
                list-style: none;
            }}
            .task-list-item input[type="checkbox"] {{
                margin-right: 0.5em;
            }}
            /* 注入 Pygments 的顏色設定 */
            {pygments_css}
        </style>
    </head>
    <body>
        {html_body}
    </body>
    </html>
    """

    # 5. 將字串寫入 HTML 檔案 (取代原本的 WeasyPrint)
    print(" 正在產生 HTML 檔案...")
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(full_html)
    print(f" 渲染成功！請用瀏覽器打開檔案：{output_file}")

if __name__ == "__main__":
    # 指定輸入為 content.md，輸出至 output/output.html
    render_md_to_html("content.md", "output/output.html")