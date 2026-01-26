# Changelog

本專案所有重要變更都會記錄在此文件中。

格式基於 [Keep a Changelog](https://keepachangelog.com/zh-TW/1.0.0/)，
版本號遵循 [Semantic Versioning](https://semver.org/lang/zh-TW/)。

## [2.0.0] - 2026-01-26

### 新增
- **多專案支援**：可在 YAML 配置多個 output 目錄，每個對應不同專案群組
- **Subprojects 選項**：支援 `include_subprojects` 遞迴抓取子專案
- **python-redmine 整合**：使用官方套件連接 Redmine API
- **Factory Pattern 附件處理**：
  - `ImageProcessor`：圖片 OCR (pytesseract)
  - `PdfProcessor`：PDF 文字提取 (PyMuPDF)
  - `DocxProcessor`：Word 文件處理 (python-docx)
  - `SpreadsheetProcessor`：Excel/CSV 轉 Markdown 表格
  - `FallbackProcessor`：未知格式的 metadata 記錄
- **Textile → Markdown 轉換器**：完整支援 Redmine Textile 語法
- **Typer CLI**：提供 `fetch`、`list-projects`、`convert-textile` 命令
- **完整測試套件**：173 個測試，100% 覆蓋率

### 技術細節
- Python 3.11+
- 使用 pydantic-settings 管理配置
- structlog 結構化日誌
- pytest + coverage 確保品質

## [1.0.0] - 2026-01-26 (已廢棄)

初始版本，使用 httpx 直接連接 API。已由 v2.0 完全重寫取代。
