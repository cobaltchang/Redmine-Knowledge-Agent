# Redmine Knowledge Agent — 規格書 (v2.0)

## 目標

從 Redmine 自動提取 Issues 與 Wiki 頁面，處理各類附件（圖片、PDF、DOCX 等），將 Textile 格式轉為 Markdown，產生結構化的 `.md` 檔案，供後續 AI 摘要與 RAG (Retrieval-Augmented Generation) 使用。

---

## 功能需求

### 1. 多目錄 / 多專案支援

| 項目 | 說明 |
|------|------|
| **Config 多 output 目錄** | 可在 YAML 設定多個 output 目錄，每個目錄對應一組專案 |
| **指定 Projects** | 每個 output 目錄可列出要抓取的 `project_identifier` 清單 |
| **include_subprojects 選項** | 預設 `false`；設為 `true` 時會遞迴抓取子專案底下的 issues |
| **權限過濾** | 僅處理 API key 有權限讀取的 issues/wiki，無權限的項目會記錄 warning 並跳過 |

### 2. 資料抓取

- 使用 **python-redmine** 套件連接 Redmine REST API
- 支援分頁與 rate-limit 控制
- 抓取內容：
  - Issues（含狀態、tracker、priority、target version、assigned_to、attachments、journals）
  - Wiki 頁面（含 attachments）

### 3. 附件處理 — Factory Pattern

採用 **抽象工廠** + **策略模式**，以利擴充與測試：

```
AttachmentProcessor (Protocol / ABC)
├── ImageProcessor      → OCR (pytesseract / EasyOCR / 多模態 LLM)
├── PdfProcessor        → 文字提取 + 圖片 OCR (PyMuPDF)
├── DocxProcessor       → 文字提取 (python-docx)
├── SpreadsheetProcessor→ 表格轉 Markdown (openpyxl / pandas)
└── FallbackProcessor   → 記錄 metadata，不提取內文
```

- `ProcessorFactory.get_processor(mime_type, filename)` 回傳對應處理器
- 每個處理器實作 `process(file_path) -> ExtractedContent`
- 可選配置：是否啟用多模態 LLM（如 GPT-4o / Claude）進行高階分析

### 4. 格式轉換

| 來源 | 目標 |
|------|------|
| Textile | Markdown（使用 `textile` + `markdownify` 或 `pypandoc`） |

- 內嵌附件引用 (`!image.png!`) 轉為 `![image](./attachments/image.png)`
- 保留連結與格式

### 5. Markdown 輸出結構

每個 Issue 產生一個 `.md`，結構如下：

```markdown
---
id: 12345
project: my_project
tracker: Bug
status: In Progress
priority: High
target_version: v2.1.0
assigned_to: alice
created_on: 2024-01-15
updated_on: 2024-06-20
tags: [bug, backend]
---

# Issue #12345: 標題

## 描述

（Textile 轉 Markdown 後的內容）

## 附件分析

### image1.png

![image1](./attachments/image1.png)

> OCR 提取內容：...

### document.pdf

> 提取文字：...

## 討論記錄

- 2024-01-16 bob: 這是回覆內容...
- 2024-01-17 alice: ...
```

Wiki 頁面採用類似結構，front-matter 包含 `wiki_page`, `project`, `version` 等。

### 6. 輸出目錄結構

```
output/
├── project_a/
│   ├── issues/
│   │   ├── 00001.md
│   │   ├── 00002.md
│   │   └── attachments/
│   │       ├── 00001/
│   │       │   ├── image1.png
│   │       │   └── doc.pdf
│   │       └── 00002/
│   └── wiki/
│       ├── HomePage.md
│       └── attachments/
├── project_b/
│   └── ...
```

### 7. 執行模式

| 模式 | 說明 |
|------|------|
| **full** | 完整重新抓取所有 issues/wiki |
| **incremental** | 僅抓取 `updated_on` > 上次執行時間的項目 |

- 記錄最後執行狀態於 `.state.json` 或 SQLite

### 8. CLI 介面

```bash
# 完整抓取
redmine-ka fetch --config config.yaml --mode full

# 增量更新
redmine-ka fetch --config config.yaml --mode incremental

# 僅處理特定專案
redmine-ka fetch --config config.yaml --projects proj_a,proj_b

# 列出可用專案
redmine-ka list-projects --config config.yaml
```

### 9. Agent Tools / MCP 擴充（未來）

為便於與 AI Agent 整合，可設計 MCP Server 或 Tool 介面：

| Tool | 說明 |
|------|------|
| `list_projects` | 列出所有可存取專案 |
| `fetch_issues` | 抓取指定專案的 issues |
| `fetch_wiki` | 抓取指定專案的 wiki |
| `process_attachment` | 處理單一附件並回傳提取內容 |
| `convert_textile` | Textile → Markdown 轉換 |

---

## 非功能需求

| 項目 | 要求 |
|------|------|
| Python 版本 | >= 3.11 |
| 測試覆蓋率 | 100%（pytest-cov, fail-under=100） |
| 敏感資料保護 | API key 不可出現在 log/輸出 |
| 日誌 | structlog, JSON 格式, 可調整 level |
| 可測試性 | 所有外部依賴可 mock，支援 DI |
| 文件 | 繁體中文為主，README/docstring 英文 |

---

## 技術選型

| 功能 | 套件 |
|------|------|
| Redmine API | `python-redmine` |
| Config | `pydantic-settings` + YAML (`PyYAML`) |
| Textile → MD | `textile` + `markdownify` 或 `pypandoc` |
| PDF 處理 | `PyMuPDF` (fitz) |
| DOCX 處理 | `python-docx` |
| OCR | `pytesseract` 或 `easyocr` |
| Logging | `structlog` |
| Testing | `pytest`, `pytest-cov`, `pytest-asyncio`, `responses` |
| CLI | `typer` |

---

## 設計原則

1. **Spec-First**：先寫規格，再實作
2. **TDD**：先寫測試，再寫 production code
3. **Factory Pattern**：附件處理器使用工廠方法，易於擴充
4. **Dependency Injection**：方便測試與替換實作
5. **Incremental Commits**：小步提交，每個 commit 可獨立編譯/測試

---

## 里程碑

| 階段 | 內容 | 狀態 |
|------|------|------|
| M1 | Config + Redmine Client (python-redmine) | 待實作 |
| M2 | Attachment Processor Factory | 待實作 |
| M3 | Textile → Markdown 轉換 | 待實作 |
| M4 | Issue/Wiki MD 產生器 | 待實作 |
| M5 | CLI + 增量模式 | 待實作 |
| M6 | MCP / Agent Tools（可選） | 待實作 |

---

## 設定檔範例 (config.yaml)

```yaml
redmine:
  url: "https://redmine.example.com"
  api_key: "${REDMINE_API_KEY}"  # 從環境變數讀取

outputs:
  - path: "./output/team_a"
    projects:
      - project_alpha
      - project_beta
    include_subprojects: false

  - path: "./output/team_b"
    projects:
      - project_gamma
    include_subprojects: true

processing:
  textile_to_markdown: true
  ocr_enabled: true
  ocr_engine: "pytesseract"  # or "easyocr", "multimodal_llm"
  multimodal_llm:
    enabled: false
    provider: "openai"
    model: "gpt-4o"

logging:
  level: "INFO"
  format: "json"

state:
  backend: "sqlite"  # or "json"
  path: "./.state.db"
```

---

## 安全考量

> 📋 詳細安全設計請參閱 [SECURITY.md](SECURITY.md)  
> 📋 威脅建模請參閱 [THREAT_MODEL.md](THREAT_MODEL.md)

### 基本安全要求

- API key 僅從環境變數或加密儲存讀取
- Log 中自動遮蔽敏感欄位（api_key, password, token）
- 附件下載前驗證 MIME type，防止惡意檔案
- 輸出目錄不可位於系統敏感路徑

### 安全開發合規 (CRA / IEC 62443-4-1)

本專案遵循 **EU Cyber Resilience Act (CRA)** 以及 **IEC 62443-4-1** 安全開發生命週期要求：

#### 靜態程式碼分析 (SAST)

| 工具 | 用途 | 整合方式 |
|------|------|----------|
| `ruff` | 程式碼品質與安全規則 (S rules) | CI + pre-commit |
| `bandit` | Python 安全漏洞掃描 | CI + pre-commit |
| `mypy` | 型別檢查 (防止運行時錯誤) | CI |

#### 軟體組成分析 (SCA)

| 工具 | 用途 | 整合方式 |
|------|------|----------|
| `pip-audit` | 已知 CVE 漏洞掃描 | CI (每次 PR + 每週定期) |
| `safety` | 依賴項漏洞檢查 | CI |
| `CycloneDX` | SBOM 生成 | CI (每次建置) |

#### 機密掃描

| 工具 | 用途 | 整合方式 |
|------|------|----------|
| `detect-secrets` | 檢測意外提交的密鑰/憑證 | pre-commit |
| `gitleaks` | Git 歷史記錄掃描 | CI |

#### 測試要求

| 類型 | 要求 | 工具 |
|------|------|------|
| 單元測試 | 100% 覆蓋率 | pytest-cov |
| 整合測試 | 含 API 模擬 | responses / respx |
| 安全測試 | 靜態分析 + 依賴掃描 | bandit + pip-audit |

#### SBOM (軟體物料清單)

每次建置自動產生 CycloneDX 格式的 SBOM，包含：
- 所有直接依賴項及版本
- 所有間接（傳遞）依賴項
- 授權資訊
- 漏洞關聯 (via VEX)

#### 安全更新流程

1. 依賴項漏洞由 CI 自動檢測
2. 高風險漏洞（CVSS >= 7.0）需於 72 小時內修復
3. 中風險漏洞（CVSS 4.0-6.9）需於 30 天內修復
4. 定期（每週）執行全面依賴審計

---

## 附錄：資料模型

```python
@dataclass
class IssueMetadata:
    id: int
    project: str
    tracker: str
    status: str
    priority: str
    target_version: str | None
    assigned_to: str | None
    created_on: datetime
    updated_on: datetime
    subject: str
    description_textile: str
    attachments: list[AttachmentInfo]
    journals: list[JournalEntry]

@dataclass
class AttachmentInfo:
    id: int
    filename: str
    content_type: str
    filesize: int
    content_url: str

@dataclass
class ExtractedContent:
    text: str
    metadata: dict[str, Any]
    processing_method: str  # "ocr", "text_extract", "llm", "fallback"

@dataclass
class WikiPageMetadata:
    title: str
    project: str
    version: int
    created_on: datetime
    updated_on: datetime
    text_textile: str
    attachments: list[AttachmentInfo]
```
