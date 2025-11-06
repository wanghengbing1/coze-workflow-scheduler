#!/bin/bash
# GitHub仓库设置脚本

echo "🚀 开始设置GitHub仓库..."

# 设置变量
GITHUB_USERNAME="wanghengbing1"
REPO_NAME="coze-workflow-scheduler"
REPO_DESCRIPTION="🤖 Automated Coze workflow scheduler with dynamic timing configuration and retry mechanism"

echo "📋 仓库信息："
echo "  用户名: $GITHUB_USERNAME"
echo "  仓库名: $REPO_NAME"
echo "  描述: $REPO_DESCRIPTION"

# 添加远程仓库
echo "🔗 添加远程仓库..."
git remote add origin https://github.com/${GITHUB_USERNAME}/${REPO_NAME}.git

# 检查是否已安装GitHub CLI
if command -v gh &> /dev/null; then
    echo "✅ 检测到GitHub CLI，使用CLI创建仓库..."
    gh repo create ${REPO_NAME} \
        --public \
        --description "${REPO_DESCRIPTION}" \
        --source . \
        --remote origin \
        --push
else
    echo "⚠️  未检测到GitHub CLI，请手动创建仓库后运行推送命令"
    echo "📋 手动创建步骤："
    echo "  1. 访问 https://github.com/new"
    echo "  2. 创建名为 '${REPO_NAME}' 的空仓库"
    echo "  3. 不要添加任何文件"
    echo "  4. 创建完成后运行: git push -u origin main"
fi

echo "✅ GitHub仓库设置完成！"
echo "📍 仓库地址: https://github.com/${GITHUB_USERNAME}/${REPO_NAME}"