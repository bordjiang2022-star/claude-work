#!/bin/bash
# LiveTranslate v2.0 - Docker Clean Script for Linux/Mac
# 清理脚本 / Clean Script / クリーンスクリプト

echo "===================================="
echo "LiveTranslate v2.0 Docker Clean"
echo "===================================="
echo
echo "WARNING: This will remove all containers, volumes, and images!"
echo "警告：这将删除所有容器、卷和镜像！"
echo "警告：これによりすべてのコンテナ、ボリューム、イメージが削除されます！"
echo
echo "Your database and user data will be deleted!"
echo "您的数据库和用户数据将被删除！"
echo "データベースとユーザーデータが削除されます！"
echo

read -p "Are you sure? Type YES to confirm / 确认请输入 YES / 確認するにはYESと入力: " confirm

if [ "$confirm" != "YES" ]; then
    echo
    echo "Cancelled / 已取消 / キャンセルされました"
    exit 0
fi

echo
echo "Removing containers, volumes, and images..."
echo "删除容器、卷和镜像..."
echo "コンテナ、ボリューム、イメージを削除中..."
echo

docker compose down -v --rmi all

echo
echo "[SUCCESS] Cleanup completed."
echo "[成功] 清理完成。"
echo "[成功] クリーンアップ完了。"
echo
