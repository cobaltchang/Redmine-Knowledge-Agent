# Redmine Knowledge Agent

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Coverage](https://img.shields.io/badge/coverage-100%25-brightgreen.svg)](https://github.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> 從 Redmine 自動提取知識，轉換為結構化 Markdown，供 AI 摘要與 RAG 使用

## ✨ 功能特點

- 🔗 **多專案支援**：一次配置抓取多個專案，支援子專案遞迴
- 📋 **Issues & Wiki**：完整抓取 Issues（含 journals）與 Wiki 頁面
- 🖼️ **附件處理**：圖片 OCR、PDF 解析、DOCX/Excel 文字提取
- 🔄 **格式轉換**：Textile → Markdown 完整轉換
- 📁 **結構化輸出**：YAML front-matter + Markdown 內容
- 🧪 **100% 測試覆蓋**：完整的單元測試套件

## 🚀 快速開始

### 環境需求

- Python >= 3.11
- Tesseract OCR（用於圖片文字辨識，可選）

### 安裝

```bash
# Clone 專案
git clone https://github.com/your-org/Redmine-Knowledge-Agent.git
cd Redmine-Knowledge-Agent

# 建立虛擬環境
python -m venv .venv
source .venv/bin/activate

# 安裝
pip install -e ".[dev]"
```

### 配置

1. 複製配置範例：
```bash
cp config.example.yaml config.yaml
```

2. 編輯 `config.yaml`：
```yaml
redmine:
  url: https://your-redmine-server.com
  api_key: ${REDMINE_API_KEY}  # 可使用環境變數

outputs:
  - path: ./output/team-a
    projects:
      - project-alpha
      - project-beta
    include_subprojects: true
  
  - path: ./output/team-b
    projects:
      - project-gamma
```

3. 設定環境變數：
```bash
export REDMINE_API_KEY="your_api_key_here"
```

### 使用

```bash
# 列出可存取的專案
redmine-ka list-projects --config config.yaml

# 抓取所有配置的專案
redmine-ka fetch --config config.yaml

# 只抓取特定專案
redmine-ka fetch --config config.yaml --projects project-alpha

# 跳過附件處理（快速抓取）
redmine-ka fetch --config config.yaml --skip-attachments

# 轉換 Textile 檔案
redmine-ka convert-textile input.textile -o output.md
```

## 📁 輸出結構

```
output/team-a/
├── project-alpha/
│   ├── issues/
│   │   ├── 00001.md
│   │   ├── 00002.md
│   │   └── attachments/
│   │       ├── 00001/
│   │       │   └── screenshot.png
│   │       └── 00002/
│   │           └── document.pdf
│   └── wiki/
│       ├── HomePage.md
│       └── attachments/
│           └── diagram.png
└── project-beta/
    └── ...
```

## 🏗️ 架構

```
src/redmine_knowledge_agent/
├── __init__.py      # 套件入口，版本資訊
├── __main__.py      # Typer CLI 入口
├── config.py        # Pydantic 配置管理
├── models.py        # 資料模型 (Issue, Wiki, Attachment)
├── client.py        # Redmine API 客戶端 (python-redmine)
├── converter.py     # Textile → Markdown 轉換器
├── processors.py    # 附件處理器 (Factory Pattern)
└── generator.py     # Markdown 輸出產生器
```

### 附件處理器

| 處理器 | 支援格式 | 依賴 |
|--------|----------|------|
| `ImageProcessor` | PNG, JPEG, GIF, BMP | pytesseract, Pillow |
| `PdfProcessor` | PDF | PyMuPDF |
| `DocxProcessor` | DOCX, DOC | python-docx |
| `SpreadsheetProcessor` | XLSX, CSV | openpyxl |
| `FallbackProcessor` | 其他 | - |

## 🧪 開發

```bash
# 執行測試
pytest

# 執行測試 + 覆蓋率
pytest --cov

# 程式碼檢查
ruff check src/ tests/
ruff format src/ tests/

# Type 檢查
mypy src/
```

## 📖 文件

- [規格書](docs/SPEC.md) - 完整功能規格
- [安全設計](docs/SECURITY.md) - 安全考量與威脅模型
- [變更記錄](CHANGELOG.md) - 版本歷史

## 📝 License

MIT License - 詳見 [LICENSE](LICENSE) 文件
