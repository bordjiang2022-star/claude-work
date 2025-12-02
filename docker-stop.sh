#!/bin/bash
# LiveTranslate v2.0 - Docker Stop Script for Linux/Mac
# 停止脚本 / Stop Script / 停止スクリプト

set -e

echo "===================================="
echo "LiveTranslate v2.0 Docker Stop"
echo "===================================="
echo

echo "Stopping Docker containers..."
echo "停止 Docker 容器..."
echo "Dockerコンテナを停止中..."
echo

docker compose stop

echo
echo "[SUCCESS] Containers stopped successfully."
echo "[成功] 容器已成功停止。"
echo "[成功] コンテナが正常に停止しました。"
echo
