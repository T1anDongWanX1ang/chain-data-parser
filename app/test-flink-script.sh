#!/bin/bash

# 测试用Flink部署脚本模拟器
# 用于验证API接口功能

ENVIRONMENT="${1:-multichain-dev}"
OPERATION="${2:-deploy}"

echo "========================================="
echo "🧪 模拟Flink部署脚本测试"
echo "环境: $ENVIRONMENT"
echo "操作: $OPERATION"
echo "========================================="

# 模拟不同操作
case "$OPERATION" in
    deploy)
        echo "🚀 模拟部署流程..."
        sleep 2
        echo "✅ 部署完成"
        
        # 模拟真实的JobID输出格式
        MOCK_JOB_ID="$(printf "%032x" $((RANDOM * RANDOM)))"  # 生成32位16进制JobID
        
        # 输出模拟的Flink提交成功信息（模拟真实脚本输出）
        echo "Job has been submitted with JobID $MOCK_JOB_ID"
        
        echo "Web UI: http://35.208.145.201:8081"
        exit 0
        ;;
    build)
        echo "🔨 模拟构建流程..."
        sleep 1
        echo "✅ 构建完成"
        exit 0
        ;;
    upload)
        echo "📤 模拟上传流程..."
        sleep 1
        echo "✅ 上传完成"
        exit 0
        ;;
    status)
        echo "📊 查看作业状态..."
        echo "=== 运行中的作业 ==="
        echo "JobID: abc123 | Status: RUNNING | Name: MultiChainTokenJob"
        echo "=== Flink集群状态 ==="
        echo "TaskManagers: 2 | Available Slots: 8"
        exit 0
        ;;
    help)
        echo "模拟Flink脚本帮助信息"
        echo "支持的操作: deploy, build, upload, status, help"
        exit 0
        ;;
    *)
        echo "❌ 不支持的操作: $OPERATION"
        exit 1
        ;;
esac 