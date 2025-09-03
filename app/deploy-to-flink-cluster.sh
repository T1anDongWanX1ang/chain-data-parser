#!/bin/bash

# =======================================================
# 数据自动化生产处理服务一键部署到Flink集群
# 整合构建、上传、部署所有步骤
# =======================================================

set -e

# =================配置参数=================
ENVIRONMENT="${1:-data-proc-dev}"
OPERATION="${2:-deploy}"

# Flink服务器配置
FLINK_SERVER="35.208.145.201"
FLINK_USER="ops"
UPLOAD_DIR="/home/ops/flink-1.20.0/flink-web-upload-data-proc"

echo "==========================================="
echo "🚀 数据自动化生产处理服务一键部署到Flink集群"
echo "环境: $ENVIRONMENT"
echo "操作: $OPERATION"
echo "目标服务器: $FLINK_USER@$FLINK_SERVER"
echo "==========================================="

# =================函数定义=================

# 显示帮助信息
show_help() {
    echo "用法: $0 [环境] [操作]"
    echo
    echo "参数说明:"
    echo "  环境: data-proc-dev, data-proc-prod (默认: data-proc-dev)"
    echo "  操作: deploy|upload|build|status|help (默认: deploy)"
    echo
    echo "操作说明:"
    echo "  deploy - 完整部署流程 (构建+上传+启动)"
    echo "  upload - 只上传文件到服务器"
    echo "  build  - 只构建JAR文件"
    echo "  status - 查看作业状态"
    echo "  help   - 显示帮助信息"
    echo
    echo "示例:"
    echo "  $0                           # 完整部署到data-proc-dev环境"
    echo "  $0 data-proc-prod deploy     # 部署到生产环境"
    echo "  $0 data-proc-dev upload      # 只上传文件"
    echo "  $0 data-proc-dev status      # 查看作业状态"
    echo
    echo "部署完成后可以访问: http://$FLINK_SERVER:8081"
}

# 构建项目
build_project() {
    echo "🔨 构建项目..."
    
    # 检查是否在正确的目录
    if [ ! -f "pom.xml" ]; then
        echo "❌ 未找到pom.xml文件，请在ddc-rtc-data-proc目录下执行"
        exit 1
    fi
    
    # 构建项目
    echo "执行Maven构建..."
    mvn clean package -DskipTests
    
    # 检查JAR文件
    if [ ! -f "target/ddc-rtc-data-proc-1.0-SNAPSHOT.jar" ]; then
        echo "❌ JAR文件构建失败"
        exit 1
    fi
    
    # 重命名JAR文件
    cp "target/ddc-rtc-data-proc-1.0-SNAPSHOT.jar" "target/ddc-rtc-data-proc-1.0.jar"
    
    echo "✅ 项目构建完成"
    echo "   JAR文件: target/ddc-rtc-data-proc-1.0.jar"
    echo "   大小: $(ls -lh target/ddc-rtc-data-proc-1.0.jar | awk '{print $5}')"
}

# 上传文件
upload_files() {
    echo "📤 上传文件到Flink服务器..."
    
    # 检查服务器连接
    if ! ssh -o ConnectTimeout=10 "$FLINK_USER@$FLINK_SERVER" "echo 'test'" > /dev/null 2>&1; then
        echo "❌ 无法连接到服务器: $FLINK_USER@$FLINK_SERVER"
        echo "请检查SSH连接配置"
        exit 1
    fi
    
    # 创建远程目录
    ssh "$FLINK_USER@$FLINK_SERVER" "mkdir -p $UPLOAD_DIR/config $UPLOAD_DIR/logs"
    
    # 上传JAR文件
    echo "上传JAR文件..."
    scp "target/ddc-rtc-data-proc-1.0.jar" "$FLINK_USER@$FLINK_SERVER:$UPLOAD_DIR/"
    
    # 上传配置文件
    echo "上传配置文件..."
    scp src/main/resources/*.properties "$FLINK_USER@$FLINK_SERVER:$UPLOAD_DIR/config/"
    
    # 上传部署脚本
    echo "上传部署脚本..."
    scp flink-data-proc.sh "$FLINK_USER@$FLINK_SERVER:$UPLOAD_DIR/"
    
    # 设置权限
    ssh "$FLINK_USER@$FLINK_SERVER" "chmod +x $UPLOAD_DIR/flink-data-proc.sh"
    
    echo "✅ 文件上传完成"
}

# 远程部署
remote_deploy() {
    echo "🚀 在Flink集群上部署作业..."
    
    # 执行远程部署
    ssh "$FLINK_USER@$FLINK_SERVER" "
        cd $UPLOAD_DIR
        echo '开始部署数据自动化生产处理作业...'
        ./flink-data-proc.sh $ENVIRONMENT
    "
    if [ $? -eq 0 ]; then
        echo "✅ 作业部署成功"
        echo
        echo "后续操作:"
        echo "🌐 查看Web UI: http://$FLINK_SERVER:8081"
        echo "📊 查看状态: $0 $ENVIRONMENT status"
        echo "📝 查看日志: ssh $FLINK_USER@$FLINK_SERVER 'cd $UPLOAD_DIR && ./flink-data-proc.sh $ENVIRONMENT list'"
    else
        echo "❌ 作业部署失败"
        echo "请检查Flink集群状态和日志"
        exit 1
    fi
}

# 查看作业状态
check_status() {
    echo "📊 查看Flink集群作业状态..."
    
    ssh "$FLINK_USER@$FLINK_SERVER" "
        cd $UPLOAD_DIR
        echo '=== 运行中的作业 ==='
        ./flink-data-proc.sh $ENVIRONMENT list
        echo
        echo '=== Flink集群状态 ==='
        curl -s http://localhost:8081/overview | grep -o '\"slots-available\":[0-9]*' || echo '无法获取集群状态'
    "
}

# 完整部署流程
full_deploy() {
    echo "🎯 开始完整部署流程..."
    echo
    
    # 步骤1: 构建项目
    # build_project
    # echo
    
    # # 步骤2: 上传文件
    # upload_files
    # echo
    
    # 步骤3: 远程部署
     remote_deploy
    echo
    
    echo "🎉 完整部署流程完成！"
}

# 预检查
pre_check() {
    echo "🔍 执行预检查..."
    
    # 检查必要的命令
    local commands=("mvn" "ssh" "scp")
    for cmd in "${commands[@]}"; do
        if ! command -v "$cmd" > /dev/null; then
            echo "❌ 命令不存在: $cmd"
            exit 1
        fi
    done
    
    # 检查项目文件
    if [ ! -f "pom.xml" ]; then
        echo "❌ 请在ddc-rtc-data-proc项目目录下执行此脚本"
        exit 1
    fi
    
    if [ ! -f "flink-data-proc.sh" ]; then
        echo "⚠️ flink-data-proc.sh脚本不存在，将创建默认脚本"
        create_default_flink_script
    fi
    
    local config_file="src/main/resources/application.properties"
    if [ ! -f "$config_file" ]; then
        echo "⚠️ 配置文件不存在: $config_file，将使用默认配置"
    fi
    
    echo "✅ 预检查完成"
}

# 创建默认的Flink脚本
create_default_flink_script() {
    cat > flink-data-proc.sh << 'EOF'
#!/bin/bash

ENVIRONMENT="${1:-data-proc-dev}"
OPERATION="${2:-run}"

FLINK_HOME="/home/ops/flink-1.20.0"
JAR_FILE="ddc-rtc-data-proc-1.0.jar"

case "$OPERATION" in
    run)
        echo "启动数据自动化生产处理作业..."
        $FLINK_HOME/bin/flink run -c com.moontrade.job.dataproc.Application $JAR_FILE
        ;;
    list)
        echo "查看运行中的作业..."
        $FLINK_HOME/bin/flink list
        ;;
    *)
        echo "支持的操作: run, list"
        ;;
esac
EOF
    chmod +x flink-data-proc.sh
    echo "✅ 创建默认Flink脚本: flink-data-proc.sh"
}

# =================主程序逻辑=================

# 检查参数
if [ "$OPERATION" = "help" ] || [ "$1" = "-h" ] || [ "$1" = "--help" ]; then
    show_help
    exit 0
fi

# 执行预检查
# pre_check
echo

# 根据操作类型执行相应功能
case "$OPERATION" in
    deploy)
        full_deploy
        ;;
    build)
        build_project
        ;;
    upload)
        upload_files
        ;;
    status)
        check_status
        ;;
    *)
        echo "❌ 不支持的操作: $OPERATION"
        echo "支持的操作: deploy, build, upload, status, help"
        echo "使用 '$0 help' 查看详细帮助"
        exit 1
        ;;
esac

echo
echo "==========================================="
echo "操作完成！"
echo "Flink Web UI: http://$FLINK_SERVER:8081"
echo "服务器目录: $UPLOAD_DIR"
echo "===========================================" 