# LiveTranslate v2.0 - Docker 部署指南
# LiveTranslate v2.0 - Docker Deployment Guide
# LiveTranslate v2.0 - Docker デプロイメントガイド

## 📋 目录 / Table of Contents / 目次

- [前置要求 / Prerequisites / 前提条件](#前置要求--prerequisites--前提条件)
- [快速开始 / Quick Start / クイックスタート](#快速开始--quick-start--クイックスタート)
- [Windows 环境配置 / Windows Configuration / Windows環境設定](#windows-环境配置--windows-configuration--windows環境設定)
- [构建与运行 / Build & Run / ビルドと実行](#构建与运行--build--run--ビルドと実行)
- [配置说明 / Configuration / 設定](#配置说明--configuration--設定)
- [故障排除 / Troubleshooting / トラブルシューティング](#故障排除--troubleshooting--トラブルシューティング)
- [生产部署 / Production Deployment / 本番デプロイメント](#生产部署--production-deployment--本番デプロイメント)

---

## 前置要求 / Prerequisites / 前提条件

### 必需软件 / Required Software / 必要なソフトウェア

1. **Docker Desktop** (Windows 10/11, macOS, Linux)
   - Windows: [Docker Desktop for Windows](https://www.docker.com/products/docker-desktop/)
   - 最低版本 / Minimum version / 最小バージョン: 20.10+
   - 需要启用 WSL 2 / Requires WSL 2 / WSL 2を有効化

2. **Docker Compose**
   - 版本 / Version / バージョン: 2.0+
   - 通常随 Docker Desktop 安装 / Usually included with Docker Desktop / Docker Desktopに含まれる

3. **Git** (可选，用于克隆仓库 / Optional, for cloning repository / オプション)

### 系统要求 / System Requirements / システム要件

- **内存 / RAM / メモリ**: 最低 4GB，推荐 8GB+ / Minimum 4GB, Recommended 8GB+ / 最小4GB、推奨8GB以上
- **磁盘空间 / Disk Space / ディスク容量**: 至少 2GB / At least 2GB / 最低2GB
- **网络 / Network / ネットワーク**: 需要访问阿里云 DashScope API / Requires access to Alibaba Cloud DashScope API / Alibaba Cloud DashScope APIへのアクセスが必要

---

## 快速开始 / Quick Start / クイックスタート

### 1. 克隆或下载项目 / Clone or Download Project / プロジェクトをクローンまたはダウンロード

```bash
git clone <repository-url>
cd claude-work
```

### 2. 配置环境变量 / Configure Environment Variables / 環境変数を設定

```bash
# 复制环境变量模板 / Copy environment template / 環境変数テンプレートをコピー
cp .env.docker.example .env

# 编辑 .env 文件，填入你的 API Key / Edit .env and add your API key / .envファイルを編集してAPIキーを追加
# Windows: notepad .env
# macOS/Linux: nano .env 或 vim .env
```

**必须配置 / Must Configure / 必須設定:**
```env
DASHSCOPE_API_KEY=sk-your-actual-api-key-here
SECRET_KEY=your-secure-secret-key-here
```

### 3. 启动服务 / Start Services / サービスを起動

```bash
# 构建并启动所有服务 / Build and start all services / すべてのサービスをビルドして起動
docker-compose up -d

# 查看日志 / View logs / ログを表示
docker-compose logs -f
```

### 4. 访问应用 / Access Application / アプリケーションにアクセス

- **前端 / Frontend / フロントエンド**: http://localhost:3000
- **后端 API / Backend API / バックエンドAPI**: http://localhost:8000
- **API 文档 / API Documentation / APIドキュメント**: http://localhost:8000/docs

---

## Windows 环境配置 / Windows Configuration / Windows環境設定

### Windows 10/11 + Docker Desktop 设置 / Setup / 設定

#### 1. 启用 WSL 2 / Enable WSL 2 / WSL 2を有効化

```powershell
# 以管理员身份运行 PowerShell / Run PowerShell as Administrator / 管理者としてPowerShellを実行
wsl --install
wsl --set-default-version 2
```

#### 2. Docker Desktop 配置 / Configuration / 設定

1. 打开 Docker Desktop Settings / Open Settings / 設定を開く
2. 进入 **Resources → WSL Integration** / Go to Resources → WSL Integration / リソース → WSL統合に移動
3. 启用你的 WSL 发行版 / Enable your WSL distributions / WSLディストリビューションを有効化
4. 内存分配 / Memory Allocation / メモリ割り当て: 至少 4GB / At least 4GB / 最低4GB

#### 3. 中文/日文 Windows 系统测试 / Testing on Chinese/Japanese Windows / 中国語/日本語Windows環境でのテスト

##### 中文 Windows / Chinese Windows / 中国語Windows

```powershell
# 1. 确认系统区域设置 / Check system locale / システムロケールを確認
[System.Threading.Thread]::CurrentThread.CurrentCulture.Name
# 应该显示: zh-CN / Should show: zh-CN / 表示されるべき: zh-CN

# 2. 设置时区（可选）/ Set timezone (optional) / タイムゾーンを設定（オプション）
# 编辑 .env 文件 / Edit .env file / .envファイルを編集
TZ=Asia/Shanghai
```

##### 日文 Windows / Japanese Windows / 日本語Windows

```powershell
# 1. 确认系统区域设置 / Check system locale / システムロケールを確認
[System.Threading.Thread]::CurrentThread.CurrentCulture.Name
# 应该显示: ja-JP / Should show: ja-JP / 表示されるべき: ja-JP

# 2. 设置时区（可选）/ Set timezone (optional) / タイムゾーンを設定（オプション）
# 编辑 .env 文件 / Edit .env file / .envファイルを編集
TZ=Asia/Tokyo
```

#### 4. 测试 CJK 字符显示 / Test CJK Character Display / CJK文字表示のテスト

访问应用后测试以下内容 / Test the following after accessing the app / アプリにアクセス後、以下をテスト:

- ✅ 中文界面显示 / Chinese UI display / 中国語UI表示
- ✅ 日文界面显示 / Japanese UI display / 日本語UI表示
- ✅ 语音识别（中文/日文）/ Speech recognition (Chinese/Japanese) / 音声認識（中国語/日本語）
- ✅ 翻译结果显示 / Translation display / 翻訳結果の表示

---

## 构建与运行 / Build & Run / ビルドと実行

### 基本命令 / Basic Commands / 基本コマンド

```bash
# 构建镜像 / Build images / イメージをビルド
docker-compose build

# 仅构建后端 / Build backend only / バックエンドのみビルド
docker-compose build backend

# 仅构建前端 / Build frontend only / フロントエンドのみビルド
docker-compose build frontend

# 启动服务（后台运行）/ Start services (detached) / サービスを起動（バックグラウンド）
docker-compose up -d

# 启动服务（前台运行，查看日志）/ Start services (foreground) / サービスを起動（フォアグラウンド）
docker-compose up

# 停止服务 / Stop services / サービスを停止
docker-compose stop

# 停止并删除容器 / Stop and remove containers / コンテナを停止して削除
docker-compose down

# 停止并删除容器、卷、镜像 / Stop and remove everything / すべてを停止して削除
docker-compose down -v --rmi all
```

### 查看日志 / View Logs / ログを表示

```bash
# 所有服务日志 / All services logs / すべてのサービスのログ
docker-compose logs -f

# 仅后端日志 / Backend logs only / バックエンドのログのみ
docker-compose logs -f backend

# 仅前端日志 / Frontend logs only / フロントエンドのログのみ
docker-compose logs -f frontend

# 最近 100 行日志 / Last 100 lines / 最新100行
docker-compose logs --tail=100
```

### 进入容器 / Enter Container / コンテナに入る

```bash
# 进入后端容器 / Enter backend container / バックエンドコンテナに入る
docker-compose exec backend /bin/bash

# 进入前端容器 / Enter frontend container / フロントエンドコンテナに入る
docker-compose exec frontend /bin/sh
```

---

## 配置说明 / Configuration / 設定

### 环境变量 / Environment Variables / 環境変数

详见 `.env.docker.example` 文件 / See `.env.docker.example` for details / 詳細は`.env.docker.example`を参照

#### 必需变量 / Required Variables / 必須変数

| 变量名 / Variable / 変数名 | 说明 / Description / 説明 | 示例 / Example / 例 |
|---|---|---|
| `DASHSCOPE_API_KEY` | 阿里云 API Key / Alibaba Cloud API Key / Alibaba Cloud APIキー | `sk-abc123...` |
| `SECRET_KEY` | JWT 签名密钥 / JWT Secret / JWT署名キー | `random-32-char-string` |

#### 可选变量 / Optional Variables / オプション変数

| 变量名 / Variable / 変数名 | 默认值 / Default / デフォルト | 说明 / Description / 説明 |
|---|---|---|
| `DATABASE_URL` | `sqlite+aiosqlite:////app/data/livetranslate.db` | 数据库连接 / DB connection / データベース接続 |
| `TZ` | `UTC` | 时区 / Timezone / タイムゾーン |
| `LOG_LEVEL` | `INFO` | 日志级别 / Log level / ログレベル |

### 端口配置 / Port Configuration / ポート設定

默认端口 / Default ports / デフォルトポート:
- 前端 / Frontend / フロントエンド: `3000`
- 后端 / Backend / バックエンド: `8000`

修改端口 / Change ports / ポートを変更:
```yaml
# 编辑 docker-compose.yml / Edit docker-compose.yml / docker-compose.ymlを編集
services:
  backend:
    ports:
      - "8080:8000"  # 主机端口:容器端口 / Host:Container / ホスト:コンテナ
  frontend:
    ports:
      - "3001:3000"
```

### 数据持久化 / Data Persistence / データ永続化

SQLite 数据库存储在 Docker 卷中 / SQLite database stored in Docker volume / SQLiteデータベースはDockerボリュームに保存:

```bash
# 查看卷 / List volumes / ボリュームを表示
docker volume ls

# 备份数据库 / Backup database / データベースをバックアップ
docker run --rm -v livetranslate-db-data:/data -v $(pwd):/backup alpine tar czf /backup/db-backup.tar.gz /data

# 恢复数据库 / Restore database / データベースを復元
docker run --rm -v livetranslate-db-data:/data -v $(pwd):/backup alpine tar xzf /backup/db-backup.tar.gz -C /
```

---

## 故障排除 / Troubleshooting / トラブルシューティング

### 常见问题 / Common Issues / よくある問題

#### 1. 容器无法启动 / Container Won't Start / コンテナが起動しない

```bash
# 检查日志 / Check logs / ログを確認
docker-compose logs backend
docker-compose logs frontend

# 检查容器状态 / Check container status / コンテナの状態を確認
docker-compose ps

# 重新构建 / Rebuild / 再ビルド
docker-compose build --no-cache
docker-compose up -d
```

#### 2. API Key 错误 / API Key Error / APIキーエラー

```bash
# 确认 .env 文件存在 / Verify .env file exists / .envファイルが存在することを確認
ls -la .env

# 检查环境变量 / Check environment variables / 環境変数を確認
docker-compose config

# 重启服务 / Restart services / サービスを再起動
docker-compose restart
```

#### 3. 端口被占用 / Port Already in Use / ポートが使用中

```bash
# Windows: 查找占用端口的进程 / Find process using port / ポートを使用しているプロセスを検索
netstat -ano | findstr :3000
netstat -ano | findstr :8000

# 终止进程（替换 PID）/ Kill process (replace PID) / プロセスを終了（PIDを置換）
taskkill /PID <PID> /F

# 或修改 docker-compose.yml 中的端口 / Or change ports in docker-compose.yml / またはdocker-compose.ymlのポートを変更
```

#### 4. 中文/日文显示乱码 / CJK Characters Display Issues / 中国語/日本語の文字化け

```bash
# 确认容器内的字体 / Check fonts in container / コンテナ内のフォントを確認
docker-compose exec backend fc-list | grep -i noto
docker-compose exec frontend fc-list | grep -i noto

# 如果缺少字体，重新构建镜像 / If fonts missing, rebuild / フォントが不足している場合は再ビルド
docker-compose build --no-cache
```

#### 5. WebSocket 连接失败 / WebSocket Connection Failed / WebSocket接続失敗

```bash
# 检查 Nginx 配置 / Check Nginx config / Nginx設定を確認
docker-compose exec frontend cat /etc/nginx/conf.d/default.conf

# 检查后端是否运行 / Check if backend is running / バックエンドが実行中か確認
docker-compose ps backend

# 查看后端日志 / View backend logs / バックエンドログを表示
docker-compose logs -f backend
```

### 性能优化 / Performance Optimization / パフォーマンス最適化

#### Windows Docker Desktop 性能调优 / Tuning / チューニング

1. **增加内存分配 / Increase Memory / メモリを増やす**
   - Settings → Resources → Memory: 6-8GB 推荐 / recommended / 推奨

2. **启用 WSL 2 集成 / Enable WSL 2 Integration / WSL 2統合を有効化**
   - 比 Hyper-V 更快 / Faster than Hyper-V / Hyper-Vより高速

3. **禁用不必要的 WSL 发行版 / Disable Unused WSL Distros / 不要なWSLディストリビューションを無効化**
   - Settings → Resources → WSL Integration

---

## 生产部署 / Production Deployment / 本番デプロイメント

### 云服务器部署建议 / Cloud Server Recommendations / クラウドサーバー推奨事項

#### 1. 使用反向代理 / Use Reverse Proxy / リバースプロキシを使用

推荐使用 Nginx 或 Traefik / Recommended: Nginx or Traefik / 推奨: Nginx または Traefik

```nginx
# /etc/nginx/sites-available/livetranslate
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /api {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
    }

    location /ws {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

#### 2. 启用 HTTPS / Enable HTTPS / HTTPSを有効化

```bash
# 使用 Let's Encrypt / Use Let's Encrypt / Let's Encryptを使用
sudo apt-get install certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com
```

#### 3. 配置防火墙 / Configure Firewall / ファイアウォールを設定

```bash
# UFW (Ubuntu)
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

#### 4. 数据库迁移到 PostgreSQL / Migrate to PostgreSQL / PostgreSQLに移行

编辑 `.env` / Edit `.env` / `.env`を編集:
```env
DATABASE_URL=postgresql+asyncpg://user:password@postgres:5432/livetranslate
```

添加到 `docker-compose.yml` / Add to `docker-compose.yml` / `docker-compose.yml`に追加:
```yaml
services:
  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: livetranslate
      POSTGRES_USER: user
      POSTGRES_PASSWORD: password
    volumes:
      - postgres-data:/var/lib/postgresql/data
volumes:
  postgres-data:
```

#### 5. 监控和日志 / Monitoring & Logging / 監視とログ

- 使用 Docker logs driver / Use Docker logs driver / Dockerログドライバーを使用
- 配置日志聚合（如 ELK, Loki）/ Set up log aggregation (ELK, Loki) / ログ集約を設定（ELK、Loki）
- 健康检查已在 docker-compose.yml 中配置 / Health checks configured in docker-compose.yml / ヘルスチェックはdocker-compose.ymlに設定済み

### Sakura.net 服务器部署 / Sakura.net Deployment / Sakura.netデプロイメント

参考单独的 Sakura 部署文档 / See separate Sakura deployment docs / 別途Sakuraデプロイメントドキュメントを参照

---

## 支持 / Support / サポート

遇到问题？/ Issues? / 問題が発生しましたか？

1. 检查本文档的故障排除部分 / Check Troubleshooting section / トラブルシューティングセクションを確認
2. 查看 GitHub Issues / Check GitHub Issues / GitHub Issuesを確認
3. 提交新 Issue 并附上日志 / Submit new Issue with logs / ログ付きで新しいIssueを提出

---

## 版本 / Version / バージョン

- **LiveTranslate**: v2.0
- **Docker**: 20.10+
- **Docker Compose**: 2.0+
- **Last Updated / 最后更新 / 最終更新**: 2025-12-02
