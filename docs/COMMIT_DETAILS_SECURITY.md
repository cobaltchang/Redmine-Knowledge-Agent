Commit: fix: 修復 mypy 型別檢查與安全工具設定

此檔為此次 commit 的逐項變更說明（繁體中文），方便追溯與審查：

- src/redmine_knowledge_agent/converter.py
  - 為正則回呼函式加入 `typing.Match[str]` 型別註記，修正 mypy 對 regex match 的型別錯誤，避免 Missing type parameters 與相關警告。

- src/redmine_knowledge_agent/processors.py
  - 對未帶型別檔的第三方套件（Pillow、pytesseract、PyMuPDF/fitz、python-docx、openpyxl）採用先宣告為 `Any` 占位，之後再以暫時變數匯入再指派，避免 mypy 對缺少 stub 的靜態分析錯誤與重定義警告。
  - OCR 處理：避免直接改寫 PIL `Image` 物件導致型別不相容，改用中介變數 `img_to_process = img.convert("RGB")`。
  - PDF 處理：改為在 `PdfProcessor.process` 內動態使用 `importlib.import_module("fitz")`，以避免在靜態檢查期間直接匯入缺少 stub 的 C-extension 模組導致錯誤。
  - 將傳給外部庫的 `Path` 參數改為 `str(path)`（python-docx、openpyxl、PyMuPDF），確保相容性。

- src/redmine_knowledge_agent/__main__.py
  - 為 structlog processors 列表加上 `list[Callable[..., Any]]` 型別註記，修正 mypy 對 processors 列表型別推斷的錯誤。

- src/redmine_knowledge_agent/generator.py
  - 對 `yaml.dump` 的回傳結果使用 `str(...)` 包裹，以避免 mypy 對未型別化模組（PyYAML）回傳 `Any` 的警告。

- src/redmine_knowledge_agent/client.py
  - `list_projects()` 指定回傳型別 `list[dict[str, Any]]`，使型別更明確。
  - 對缺少型別 stub 的匯入（`requests`, `redminelib`）加入 `# type: ignore`，在不更改外部套件下避免 mypy 失敗。

- src/redmine_knowledge_agent/config.py
  - 對 `yaml` 匯入標註 `# type: ignore`，抑制本地 mypy 對 PyYAML stub 的缺失警告（推薦在 CI 的 dev extras 中安裝 `types-PyYAML`）。

- pyproject.toml
  - 新增 dev extras 的 type-stub 推薦（例如 `types-PyYAML`, `types-requests`, `types-openpyxl`），讓 CI / 開發機可安裝並提供更完整的型別檢查體驗。
  - 新增 mypy 的模組層級配置範例，允許對特定原生模組/第三方模組忽略 missing imports（在有必要時使用），並附註說明。

目的：
1. 讓本地與 CI 的 `mypy --strict` 一致通過，避免因第三方模組缺少型別檔或 native extension 導致 CI 失敗。
2. 保持程式在執行時行為不變，僅以型別與匯入策略改善靜態分析結果。

建議後續工作：
- 在 CI 或開發環境中安裝建議的 type-stub 套件（見 pyproject.toml dev extras），以減少 `# type: ignore` 的使用範圍。
- 若可行，逐步為常用第三方撰寫或貢獻型別 stub（或使用 `mypy --install-types` 自動安裝缺失 stubs）。
- 在 PR 模板或開發指南中加入「當新增原生依賴時需評估型別 stub 與 CI 影響」的流程。
