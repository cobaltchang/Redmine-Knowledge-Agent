# Redmine Knowledge Agent

> 自動化知識提取工具 - 連接 Redmine 並整理成結構化技術 Wiki

## 功能特點

- 🔗 連接本地 Redmine 系統
- 📋 自動抓取 Issues 清單與詳情
- 🖼️ 圖片 OCR 文字辨識
- 📄 PDF 內容解析
- 📚 產生結構化技術 Wiki

## 快速開始

### 環境需求

- Python >= 3.11
- Tesseract OCR (用於圖片文字辨識)

### 安裝

```bash
# 複製專案
git clone <repository-url>
cd Redmine-Knowledge-Agent

# 建立虛擬環境
python -m venv .venv
source .venv/bin/activate  # macOS/Linux
# .venv\Scripts\activate  # Windows

# 安裝相依套件
pip install -e ".[dev]"

# 複製設定檔
cp .env.example .env
# 編輯 .env 填入你的 Redmine 設定
```

### 設定

編輯 `.env` 檔案：

```bash
REDMINE_URL=https://your-redmine-server.local
REDMINE_API_KEY=your_api_key_here
```

### 執行

```bash
# 執行測試
pytest

# 抓取 Issue 清單 (開發中)
python -m redmine_knowledge_agent
```

## 專案結構

```
Redmine-Knowledge-Agent/
├── docs/                    # 文件
│   ├── SPEC.md             # 規格文件
│   └── SECURITY.md         # 安全設計文件
├── src/
│   └── redmine_knowledge_agent/
│       ├── __init__.py
│       ├── client.py       # Redmine API Client
│       ├── config.py       # 設定管理
│       ├── models.py       # 資料模型
│       └── exceptions.py   # 例外定義
├── tests/                   # 測試
│   ├── __init__.py
│   ├── conftest.py
│   └── test_client.py
├── .env.example            # 設定範本
├── .gitignore
├── pyproject.toml          # 專案設定
└── README.md
```

## 開發原則

1. **規格優先** - 所有功能需先定義於 SPEC.md
2. **安全設計** - 遵循 SECURITY.md 安全規範
3. **TDD** - 測試驅動開發，覆蓋率 100%
4. **原子 Commit** - 每個變更獨立提交並說明
5. **語言規範** - 使用繁體中文或英文

## 開發

```bash
# 執行測試
pytest

# 執行測試並顯示覆蓋率
pytest --cov

# 程式碼檢查
ruff check src tests

# 型別檢查
mypy src
```

## 文件

- [規格文件](docs/SPEC.md)
- [安全設計](docs/SECURITY.md)

## 授權

MIT License
