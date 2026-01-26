# GitHub Copilot Instructions

本文件定義此專案的 AI 輔助開發規範，供 GitHub Copilot 遵循。

## 開發原則

### 1. 規格優先 (Spec-First)
- 任何功能實作前，先確認 `docs/SPEC.md` 中的規格定義
- 若規格不明確，先更新規格文件再實作

### 2. 測試驅動開發 (TDD)
- 先寫測試，再寫實作
- 測試覆蓋率要求：**100%**
- 每個模組都需要對應的測試檔案

### 3. 頻繁提交 (Frequent Commits)
- **每次有意義的改動都要 commit**
- 不要累積大量變更後才一次提交
- Commit 訊息使用 [Conventional Commits](https://www.conventionalcommits.org/) 格式：
  - `feat:` 新功能
  - `fix:` 修復 bug
  - `docs:` 文件更新
  - `test:` 測試相關
  - `refactor:` 重構
  - `chore:` 雜項維護
  - `build:` 建置相關

### 4. 安全設計
- 遵循 `docs/SECURITY.md` 中的安全規範
- 敏感資料（API keys）不得硬編碼
- 使用環境變數或配置檔案管理敏感資訊

## 程式碼規範

### Python 風格
- 遵循 PEP 8
- 使用 type hints
- 使用 `ruff` 進行 linting
- 行寬上限：100 字元

### 文件結構
```
src/redmine_knowledge_agent/
├── __init__.py      # 套件入口
├── __main__.py      # CLI 入口
├── config.py        # 配置管理
├── models.py        # 資料模型
├── client.py        # Redmine API 客戶端
├── converter.py     # Textile 轉 Markdown
├── processors.py    # 附件處理器
└── generator.py     # Markdown 產生器

tests/
├── conftest.py      # 共用 fixtures
├── test_*.py        # 對應模組的測試
```

### 測試規範
- 使用 `pytest` 作為測試框架
- 測試檔案命名：`test_<模組名>.py`
- 使用 fixtures 共用測試資源
- Mock 外部依賴（Redmine API、檔案系統）

## Commit 工作流程

1. 完成一個小功能或修復
2. 執行測試確認通過：`pytest tests/ -q`
3. 確認覆蓋率達標：`pytest --cov --cov-fail-under=100`
4. 立即 commit：
   ```bash
   git add <相關檔案>
   git commit -m "<type>: <描述>"
   ```
5. 繼續下一個任務

## 語言偏好

- Commit 訊息：中文或英文皆可
- 程式碼註解：英文
- 文件：繁體中文優先
- 變數/函數命名：英文

## 禁止事項

- ❌ 不要累積大量變更後才 commit
- ❌ 不要跳過測試直接 commit
- ❌ 不要硬編碼敏感資訊
- ❌ 不要忽略 type hints
- ❌ 不要使用 `# type: ignore` 除非有充分理由
