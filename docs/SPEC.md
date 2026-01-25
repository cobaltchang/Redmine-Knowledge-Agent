# Redmine Knowledge Agent - 規格文件

## 專案概述

**專案名稱**: Redmine Knowledge Agent  
**Vibe**: 自動化知識提取  
**版本**: 1.0.0  
**最後更新**: 2026-01-26

### 目標

開發一個自動化工具，連接本地 Redmine 系統，提取 Issues 中的知識內容（包含文字、圖片 OCR、PDF 解析），並整理成結構化的技術 Wiki。

---

## 功能架構

### 核心模組

```
┌─────────────────────────────────────────────────────────────────┐
│                    Redmine Knowledge Agent                       │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐              │
│  │   Redmine   │  │   Content   │  │    Wiki     │              │
│  │   Client    │  │   Parser    │  │  Generator  │              │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘              │
│         │                │                │                      │
│  ┌──────▼──────┐  ┌──────▼──────┐  ┌──────▼──────┐              │
│  │Issue Fetcher│  │  OCR Engine │  │  Markdown   │              │
│  │Attachment DL│  │  PDF Parser │  │  Formatter  │              │
│  └─────────────┘  └─────────────┘  └─────────────┘              │
├─────────────────────────────────────────────────────────────────┤
│                      Configuration Layer                         │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐              │
│  │   Secrets   │  │   Logging   │  │   Config    │              │
│  │   Manager   │  │   System    │  │   Loader    │              │
│  └─────────────┘  └─────────────┘  └─────────────┘              │
└─────────────────────────────────────────────────────────────────┘
```

### 模組說明

| 模組 | 責任 | 輸入 | 輸出 |
|------|------|------|------|
| `RedmineClient` | 與 Redmine API 通訊 | API URL, API Key | Issue 資料 |
| `IssueFetcher` | 抓取 Issue 清單與詳情 | 過濾條件 | Issue 物件列表 |
| `AttachmentDownloader` | 下載附件檔案 | Attachment URL | 本地檔案路徑 |
| `OCREngine` | 圖片文字辨識 | 圖片檔案 | 辨識文字 |
| `PDFParser` | 解析 PDF 內容 | PDF 檔案 | 結構化文字 |
| `WikiGenerator` | 產生 Wiki 文件 | 結構化資料 | Markdown 檔案 |
| `SecretsManager` | 安全管理敏感資料 | 加密金鑰 | 解密後的 secrets |

---

## 技術棧

### 核心技術

| 類別 | 技術選擇 | 版本 | 用途 |
|------|----------|------|------|
| 語言 | Python | >= 3.11 | 主要開發語言 |
| HTTP Client | httpx | >= 0.27 | 非同步 HTTP 請求 |
| OCR | pytesseract + Tesseract | >= 0.3.10 | 圖片文字辨識 |
| PDF | PyMuPDF (fitz) | >= 1.24 | PDF 解析 |
| 資料驗證 | Pydantic | >= 2.0 | 資料模型與驗證 |
| 設定管理 | python-dotenv | >= 1.0 | 環境變數管理 |
| 日誌 | structlog | >= 24.0 | 結構化日誌 |

### 測試工具

| 工具 | 用途 |
|------|------|
| pytest | 單元測試框架 |
| pytest-cov | 測試覆蓋率 |
| pytest-asyncio | 非同步測試支援 |
| pytest-mock | Mock 工具 |
| responses / respx | HTTP Mock |

### 可選整合

| 技術 | 用途 |
|------|------|
| MCP SDK | Model Context Protocol 整合 (未來擴充) |
| SQLite | 本地快取 (未來擴充) |

---

## API 規格

### Redmine API 整合

#### 認證方式

使用 Redmine API Key 進行認證，支援兩種方式：
1. HTTP Header: `X-Redmine-API-Key`
2. Query Parameter: `key` (不建議，會暴露於 log)

**本專案採用 Header 方式**

#### 端點使用

| 端點 | 方法 | 用途 |
|------|------|------|
| `/issues.json` | GET | 取得 Issue 清單 |
| `/issues/{id}.json` | GET | 取得單一 Issue 詳情 |
| `/attachments/download/{id}/{filename}` | GET | 下載附件 |

---

## 資料模型

### Issue 模型

```python
class Issue:
    id: int
    subject: str
    description: str | None
    project: Project
    tracker: Tracker
    status: Status
    priority: Priority
    author: User
    assigned_to: User | None
    created_on: datetime
    updated_on: datetime
    attachments: list[Attachment]
    journals: list[Journal]
```

### Attachment 模型

```python
class Attachment:
    id: int
    filename: str
    filesize: int
    content_type: str
    content_url: str
    created_on: datetime
    author: User
```

---

## 開發原則

### 1. 規格優先 (Spec-First)

- 所有功能開發前必須先定義於本規格文件
- 規格變更需經過審查並更新版本號
- 實作必須符合規格定義

### 2. 安全性設計

- 參考 [SECURITY.md](./SECURITY.md) 安全設計文件
- 敏感資料 (API Key, Token) 禁止硬編碼
- 使用環境變數或加密設定檔
- 日誌輸出需過濾敏感資訊

### 3. 版本控制

- 開發過程拆分為原子性 commit
- Commit message 需包含：
  - 變更類型 (feat/fix/docs/test/refactor)
  - 變更說明
  - 關聯的規格章節

### 4. 測試驅動開發 (TDD)

- 開發前先撰寫測試案例
- 測試覆蓋率要求: **100%**
- 測試類型：
  - 單元測試
  - 整合測試
  - 邊界測試
  - 錯誤處理測試

### 5. 語言規範

- 文件語言: 繁體中文 或 英文
- 禁止使用簡體中文
- 程式碼註解: 英文優先

---

## 錯誤處理

### 錯誤碼定義

| 錯誤碼 | 名稱 | 說明 |
|--------|------|------|
| RKA-001 | ConnectionError | 無法連接 Redmine |
| RKA-002 | AuthenticationError | 認證失敗 |
| RKA-003 | NotFoundError | 資源不存在 |
| RKA-004 | RateLimitError | 請求過於頻繁 |
| RKA-005 | ParseError | 內容解析失敗 |
| RKA-006 | OCRError | OCR 處理失敗 |
| RKA-007 | ConfigError | 設定錯誤 |

---

## 版本歷程

| 版本 | 日期 | 變更說明 |
|------|------|----------|
| 1.0.0 | 2026-01-26 | 初始版本，定義核心架構 |
