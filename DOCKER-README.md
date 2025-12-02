# LiveTranslate v2.0 - Docker 快速参考
# Docker Quick Reference / Dockerクイックリファレンス

## 📦 Docker 文件说明 / Docker Files / Dockerファイル

本项目包含以下 Docker 相关文件 / This project includes the following Docker files / このプロジェクトには以下のDockerファイルが含まれています：

### 核心配置文件 / Core Configuration / コア設定ファイル

| 文件 / File / ファイル | 说明 / Description / 説明 |
|---|---|
| `docker-compose.yml` | Docker Compose 编排配置 / Orchestration config / オーケストレーション設定 |
| `backend/Dockerfile` | 后端容器镜像定义 / Backend image / バックエンドイメージ |
| `frontend/Dockerfile` | 前端容器镜像定义 / Frontend image / フロントエンドイメージ |
| `frontend/nginx.conf` | Nginx 反向代理配置 / Nginx config / Nginx設定 |
| `.dockerignore` | Docker 构建忽略文件 / Build ignore / ビルド無視ファイル |
| `.env.docker.example` | 环境变量模板 / Environment template / 環境変数テンプレート |

### 辅助脚本 / Helper Scripts / ヘルパースクリプト

#### Windows (.bat)
- `docker-start.bat` - 启动容器 / Start containers / コンテナ起動
- `docker-stop.bat` - 停止容器 / Stop containers / コンテナ停止
- `docker-logs.bat` - 查看日志 / View logs / ログ表示
- `docker-clean.bat` - 清理所有 / Clean all / すべてクリーン

#### Linux/Mac (.sh)
- `docker-start.sh` - 启动容器 / Start containers / コンテナ起動
- `docker-stop.sh` - 停止容器 / Stop containers / コンテナ停止
- `docker-logs.sh` - 查看日志 / View logs / ログ表示
- `docker-clean.sh` - 清理所有 / Clean all / すべてクリーン

## 🚀 快速开始 / Quick Start / クイックスタート

### 1. 配置环境 / Configure Environment / 環境設定

```bash
# 复制环境变量模板 / Copy template / テンプレートをコピー
cp .env.docker.example .env

# 编辑 .env 并填入你的 API Key
# Edit .env and add your API Key
# .envを編集してAPIキーを追加
```

### 2. 启动服务 / Start Services / サービス起動

**Windows:**
```cmd
docker-start.bat
```

**Linux/Mac:**
```bash
./docker-start.sh
```

**或使用 Docker Compose / Or use Docker Compose / またはDocker Composeを使用:**
```bash
docker compose up -d
```

### 3. 访问应用 / Access Application / アプリケーションアクセス

- 前端 / Frontend / フロントエンド: http://localhost:3000
- 后端 API / Backend API / バックエンドAPI: http://localhost:8000
- API 文档 / API Docs / APIドキュメント: http://localhost:8000/docs

## 📖 详细文档 / Detailed Documentation / 詳細ドキュメント

完整的部署指南请参阅 / For complete deployment guide, see / 完全なデプロイガイドについては以下を参照:

**→ [DOCKER.md](./DOCKER.md)**

该文档包含 / This document includes / このドキュメントには以下が含まれます:
- ✅ 详细的安装步骤 / Detailed installation / 詳細なインストール手順
- ✅ Windows 中文/日文环境配置 / Chinese/Japanese Windows setup / 中国語/日本語Windows設定
- ✅ 故障排除指南 / Troubleshooting guide / トラブルシューティングガイド
- ✅ 生产部署建议 / Production deployment / 本番デプロイメント推奨事項
- ✅ Sakura.net 服务器配置 / Sakura.net setup / Sakura.net設定

## 🛠️ 常用命令 / Common Commands / 一般的なコマンド

```bash
# 查看运行状态 / Check status / ステータス確認
docker compose ps

# 查看日志 / View logs / ログ表示
docker compose logs -f

# 重启服务 / Restart services / サービス再起動
docker compose restart

# 停止服务 / Stop services / サービス停止
docker compose stop

# 删除容器 / Remove containers / コンテナ削除
docker compose down

# 完全清理 / Complete cleanup / 完全クリーンアップ
docker compose down -v --rmi all
```

## 🐛 问题排查 / Troubleshooting / トラブルシューティング

### 常见问题 / Common Issues / よくある問題

1. **端口被占用 / Port in use / ポート使用中**
   ```bash
   # 修改 docker-compose.yml 中的端口
   # Change ports in docker-compose.yml
   # docker-compose.ymlのポートを変更
   ```

2. **API Key 错误 / API Key error / APIキーエラー**
   ```bash
   # 检查 .env 文件 / Check .env file / .envファイルを確認
   cat .env
   ```

3. **构建失败 / Build failed / ビルド失敗**
   ```bash
   # 清理缓存重新构建 / Clean and rebuild / クリーンして再ビルド
   docker compose build --no-cache
   ```

## 🌐 多语言支持 / Multi-Language Support / 多言語サポート

Docker 镜像已包含中文和日文字体支持 / Docker images include Chinese and Japanese font support / Dockerイメージには中国語と日本語のフォントサポートが含まれています:

- ✅ Noto CJK 字体 / Noto CJK fonts / Noto CJKフォント
- ✅ UTF-8 编码支持 / UTF-8 encoding / UTF-8エンコーディング
- ✅ 时区配置 / Timezone configuration / タイムゾーン設定

## 📞 支持 / Support / サポート

遇到问题？/ Issues? / 問題？

1. 查看 [DOCKER.md](./DOCKER.md) 故障排除部分 / Check troubleshooting section / トラブルシューティングセクションを確認
2. 查看容器日志 / Check container logs / コンテナログを確認
3. 提交 GitHub Issue / Submit GitHub Issue / GitHub Issueを提出

---

**版本 / Version / バージョン**: 2.0
**最后更新 / Last Updated / 最終更新**: 2025-12-02
