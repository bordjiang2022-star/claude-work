#!/bin/bash
# LiveTranslate v2.0 - Docker Logs Script for Linux/Mac
# 日志查看脚本 / Logs Script / ログスクリプト

echo "===================================="
echo "LiveTranslate v2.0 Docker Logs"
echo "===================================="
echo
echo "Press Ctrl+C to stop viewing logs"
echo "按 Ctrl+C 停止查看日志"
echo "Ctrl+Cでログ表示を停止"
echo

docker compose logs -f --tail=100
