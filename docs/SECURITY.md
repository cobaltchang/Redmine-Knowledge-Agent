# 安全性設計文件 (Security Design Document)

## 文件資訊

**專案**: Redmine Knowledge Agent  
**版本**: 1.0.0  
**最後更新**: 2026-01-26  
**分類**: 機密 (Internal)

---

## 1. 威脅模型 (Threat Model)

### 1.1 系統邊界

```
┌─────────────────────────────────────────────────────────────────┐
│                        Trust Boundary                            │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │              Redmine Knowledge Agent                     │    │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐              │    │
│  │  │ Config   │  │  Core    │  │  Output  │              │    │
│  │  │ (.env)   │  │  Engine  │  │  (Wiki)  │              │    │
│  │  └────┬─────┘  └────┬─────┘  └────┬─────┘              │    │
│  │       │             │             │                     │    │
│  └───────┼─────────────┼─────────────┼─────────────────────┘    │
│          │             │             │                          │
└──────────┼─────────────┼─────────────┼──────────────────────────┘
           │             │             │
    ┌──────▼──────┐ ┌────▼────┐  ┌─────▼─────┐
    │ Environment │ │ Redmine │  │   File    │
    │  Variables  │ │   API   │  │  System   │
    └─────────────┘ └─────────┘  └───────────┘
         外部            外部          外部
```

### 1.2 資產識別 (Assets)

| 資產 | 敏感度 | 說明 |
|------|--------|------|
| Redmine API Key | **高** | 可存取 Redmine 所有資料 |
| Issue 內容 | 中 | 可能包含內部技術資訊 |
| 附件檔案 | 中 | 可能包含機密文件 |
| 設定檔 | **高** | 包含連線資訊 |
| 產出的 Wiki | 中 | 彙整後的知識文件 |

### 1.3 威脅識別 (STRIDE)

| 威脅類型 | 威脅描述 | 風險等級 | 緩解措施 |
|----------|----------|----------|----------|
| **Spoofing** | 偽造 API 請求 | 中 | 使用 HTTPS, 驗證憑證 |
| **Tampering** | 中間人攻擊修改資料 | 中 | TLS 加密傳輸 |
| **Repudiation** | 否認執行的操作 | 低 | 結構化日誌記錄 |
| **Information Disclosure** | API Key 洩露 | **高** | 環境變數、不記錄敏感資訊 |
| **Denial of Service** | API 過度請求 | 中 | Rate limiting |
| **Elevation of Privilege** | 未授權存取 | 中 | 最小權限原則 |

---

## 2. 安全設計原則

### 2.1 敏感資料處理

#### 禁止事項

```python
# ❌ 絕對禁止：硬編碼 API Key
API_KEY = "abc123secret"

# ❌ 禁止：記錄敏感資訊
logger.info(f"Using API key: {api_key}")

# ❌ 禁止：URL 中包含敏感資訊
url = f"https://redmine.local/issues.json?key={api_key}"

# ❌ 禁止：例外訊息包含敏感資訊
raise Exception(f"Auth failed with key: {api_key}")
```

#### 正確做法

```python
# ✅ 正確：從環境變數讀取
import os
api_key = os.environ.get("REDMINE_API_KEY")

# ✅ 正確：使用 Header 傳遞
headers = {"X-Redmine-API-Key": api_key}

# ✅ 正確：遮蔽敏感資訊
def mask_sensitive(value: str) -> str:
    if len(value) <= 4:
        return "****"
    return f"{value[:2]}***{value[-2:]}"

logger.info(f"Using API key: {mask_sensitive(api_key)}")

# ✅ 正確：安全的錯誤訊息
raise AuthenticationError("API key authentication failed")
```

### 2.2 設定檔安全

#### .env 檔案規範

```bash
# .env 檔案 (絕對不能提交到版本控制)
REDMINE_URL=https://redmine.local
REDMINE_API_KEY=your_api_key_here

# 權限設定
# chmod 600 .env
```

#### .gitignore 必須包含

```gitignore
# 敏感設定
.env
.env.*
*.pem
*.key
secrets/
```

### 2.3 日誌安全

#### 日誌過濾器實作

```python
class SensitiveDataFilter:
    """過濾日誌中的敏感資料"""
    
    SENSITIVE_PATTERNS = [
        (r'api[_-]?key["\s:=]+["\']?[\w-]+', 'api_key=***'),
        (r'token["\s:=]+["\']?[\w-]+', 'token=***'),
        (r'password["\s:=]+["\']?[\w-]+', 'password=***'),
    ]
    
    def filter(self, record):
        # 實作敏感資料過濾
        pass
```

---

## 3. 網路安全

### 3.1 TLS/SSL 要求

| 設定項目 | 要求 |
|----------|------|
| TLS 版本 | >= TLS 1.2 |
| 憑證驗證 | **必須啟用** |
| 自簽憑證 | 需明確設定信任 |

### 3.2 HTTP Client 安全設定

```python
import httpx

# 安全的 HTTP client 設定
client = httpx.Client(
    # 啟用憑證驗證
    verify=True,
    # 設定逾時
    timeout=httpx.Timeout(30.0, connect=10.0),
    # 限制重導向
    follow_redirects=False,
    # 設定 User-Agent
    headers={"User-Agent": "RedmineKnowledgeAgent/1.0"},
)
```

### 3.3 Rate Limiting

為避免對 Redmine 造成過大負載：

| 參數 | 預設值 | 說明 |
|------|--------|------|
| 請求間隔 | 100ms | 連續請求最小間隔 |
| 批次大小 | 25 | 單次查詢數量上限 |
| 重試次數 | 3 | 失敗重試上限 |
| 重試延遲 | 1s, 2s, 4s | 指數退避 |

---

## 4. 輸入驗證

### 4.1 驗證規則

所有外部輸入必須驗證：

```python
from pydantic import BaseModel, field_validator, HttpUrl
from typing import Annotated

class RedmineConfig(BaseModel):
    """Redmine 連線設定"""
    
    url: HttpUrl
    api_key: Annotated[str, Field(min_length=20, max_length=100)]
    
    @field_validator('api_key')
    @classmethod
    def validate_api_key_format(cls, v: str) -> str:
        # API Key 只允許英數字和特定符號
        if not re.match(r'^[a-zA-Z0-9_-]+$', v):
            raise ValueError('Invalid API key format')
        return v
```

### 4.2 路徑遍歷防護

```python
import os
from pathlib import Path

def safe_path_join(base_dir: Path, filename: str) -> Path:
    """安全的路徑組合，防止路徑遍歷攻擊"""
    # 正規化路徑
    safe_path = (base_dir / filename).resolve()
    
    # 確保在基礎目錄內
    if not str(safe_path).startswith(str(base_dir.resolve())):
        raise SecurityError("Path traversal detected")
    
    return safe_path
```

---

## 5. 錯誤處理

### 5.1 安全的錯誤訊息

| 情境 | 不安全 | 安全 |
|------|--------|------|
| 認證失敗 | "Invalid key: abc123" | "Authentication failed" |
| 連線失敗 | "Cannot connect to 192.168.1.100:3000" | "Cannot connect to Redmine server" |
| 檔案錯誤 | "File not found: /etc/passwd" | "Requested file not found" |

### 5.2 例外處理原則

```python
class RedmineKnowledgeAgentError(Exception):
    """基礎例外類別，不包含敏感資訊"""
    pass

class AuthenticationError(RedmineKnowledgeAgentError):
    """認證失敗"""
    def __init__(self):
        super().__init__("Authentication failed. Please check your API key.")

class ConnectionError(RedmineKnowledgeAgentError):
    """連線失敗"""
    def __init__(self):
        super().__init__("Cannot connect to Redmine server.")
```

---

## 6. 稽核與監控

### 6.1 日誌記錄事項

| 事件類型 | 記錄內容 | 敏感處理 |
|----------|----------|----------|
| 認證嘗試 | 時間、結果 | 不記錄 key |
| API 請求 | URL、狀態碼、耗時 | 遮蔽 query params |
| 錯誤 | 錯誤類型、訊息 | 過濾敏感資訊 |
| 檔案操作 | 檔案名稱、操作類型 | 相對路徑 |

### 6.2 日誌格式

```json
{
  "timestamp": "2026-01-26T10:30:00Z",
  "level": "INFO",
  "event": "api_request",
  "module": "redmine_client",
  "url": "https://redmine.local/issues.json",
  "status_code": 200,
  "duration_ms": 150
}
```

---

## 7. 安全檢查清單

### 開發階段

- [ ] 無硬編碼的敏感資料
- [ ] .env 檔案已加入 .gitignore
- [ ] 所有輸入已驗證
- [ ] 日誌已過濾敏感資訊
- [ ] 使用 HTTPS 連線
- [ ] 啟用 TLS 憑證驗證

### 部署階段

- [ ] .env 檔案權限設為 600
- [ ] API Key 為專用 key (非管理員)
- [ ] 日誌輸出目錄權限正確
- [ ] 無測試用敏感資料殘留

---

## 8. 安全事件回應

### 8.1 API Key 洩露處理

1. **立即** 在 Redmine 撤銷該 API Key
2. 產生新的 API Key
3. 更新所有使用該 key 的系統
4. 檢查 Redmine 稽核日誌是否有異常存取
5. 記錄事件並檢討改善

---

## 附錄 A: 安全相關設定範本

### A.1 .env.example

```bash
# Redmine Knowledge Agent Configuration
# 複製此檔案為 .env 並填入實際值

# Redmine 連線設定
REDMINE_URL=https://your-redmine-server.local
REDMINE_API_KEY=your_api_key_here

# 輸出設定
OUTPUT_DIR=./output

# 日誌設定
LOG_LEVEL=INFO
LOG_FILE=./logs/app.log
```

---

## 文件變更歷史

| 版本 | 日期 | 變更者 | 變更說明 |
|------|------|--------|----------|
| 1.0.0 | 2026-01-26 | Initial | 初始版本 |
