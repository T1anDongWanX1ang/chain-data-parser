#!/bin/bash

# =======================================================
# Flink MultiChainTokenJob 作业详情查询脚本
# 获取指定作业名称的详细信息
# =======================================================

set -e

# =================配置参数=================
FLINK_REST_URL="http://35.208.145.201:8081"
JOB_NAME_FILTER="${1:-DDC-RTC-DataProc}"
OUTPUT_FORMAT="${2:-pretty}"  # pretty, json, simple

echo "==========================================="
echo "🔍 Flink运行中作业详情查询"
echo "Flink地址: $FLINK_REST_URL"
echo "作业名称: $JOB_NAME_FILTER"
echo "过滤状态: RUNNING"
echo "输出格式: $OUTPUT_FORMAT"
echo "==========================================="

# =================函数定义=================

# 显示帮助信息
show_help() {
    echo "用法: $0 [作业名称] [输出格式]"
    echo
    echo "参数说明:"
    echo "  作业名称: 要查询的作业名称 (默认: MultiChainTokenJob)"
    echo "  输出格式: pretty|json|simple (默认: pretty)"
    echo
    echo "特别说明:"
    echo "  ⚠️  此脚本只显示状态为 RUNNING 的作业"
    echo "  📊 会自动过滤掉CANCELED、FINISHED等非运行状态的作业"
    echo
    echo "示例:"
    echo "  $0                           # 查询运行中的MultiChainTokenJob"
    echo "  $0 MultiChainTokenJob pretty # 查询指定运行中作业，友好格式输出"
    echo "  $0 MultiChainTokenJob json   # 查询指定运行中作业，JSON格式输出"
    echo "  $0 MyJob simple              # 查询运行中的MyJob，简单格式输出"
    echo
    echo "作业状态说明:"
    echo "  INITIALIZING - 初始化中"
    echo "  CREATED      - 已创建"
    echo "  RUNNING      - 运行中"
    echo "  FAILING      - 失败中"
    echo "  FAILED       - 已失败"
    echo "  CANCELLING   - 取消中"
    echo "  CANCELED     - 已取消"
    echo "  FINISHED     - 已完成"
    echo "  RESTARTING   - 重启中"
    echo "  SUSPENDED    - 已暂停"
}

# 检查Flink集群连接
check_flink_connection() {
    echo "🔗 检查Flink集群连接..."
    if ! curl -s --connect-timeout 10 "$FLINK_REST_URL/overview" > /dev/null; then
        echo "❌ 无法连接到Flink集群: $FLINK_REST_URL"
        echo "请检查："
        echo "  1. Flink集群是否启动"
        echo "  2. REST地址是否正确"
        echo "  3. 网络连接是否正常"
        exit 1
    fi
    echo "✅ Flink集群连接正常"
}

# 格式化时间戳
format_timestamp() {
    local timestamp=$1
    if [ "$timestamp" = "null" ] || [ "$timestamp" = "" ]; then
        echo "N/A"
    else
        # 将毫秒时间戳转换为可读格式
        local seconds=$((timestamp / 1000))
        if command -v date >/dev/null 2>&1; then
            if [[ "$OSTYPE" == "darwin"* ]]; then
                # macOS
                date -r "$seconds" '+%Y-%m-%d %H:%M:%S'
            else
                # Linux
                date -d "@$seconds" '+%Y-%m-%d %H:%M:%S'
            fi
        else
            echo "$timestamp"
        fi
    fi
}

# 格式化持续时间
format_duration() {
    local start_time=$1
    local end_time=${2:-$(date +%s000)}  # 如果没有结束时间，使用当前时间
    
    if [ "$start_time" = "null" ] || [ "$start_time" = "" ]; then
        echo "N/A"
        return
    fi
    
    local duration_ms=$((end_time - start_time))
    local duration_s=$((duration_ms / 1000))
    
    local days=$((duration_s / 86400))
    local hours=$(((duration_s % 86400) / 3600))
    local minutes=$(((duration_s % 3600) / 60))
    local seconds=$((duration_s % 60))
    
    if [ $days -gt 0 ]; then
        echo "${days}天 ${hours}时 ${minutes}分 ${seconds}秒"
    elif [ $hours -gt 0 ]; then
        echo "${hours}时 ${minutes}分 ${seconds}秒"
    elif [ $minutes -gt 0 ]; then
        echo "${minutes}分 ${seconds}秒"
    else
        echo "${seconds}秒"
    fi
}

# 获取所有作业
get_all_jobs() {
    echo "📋 获取所有作业列表..."
    
    local jobs_response=$(curl -s --connect-timeout 10 "$FLINK_REST_URL/jobs")
    if [ $? -ne 0 ] || [ "$jobs_response" = "" ]; then
        echo "❌ 获取作业列表失败"
        exit 1
    fi
    
    # 提取作业ID列表
    echo "$jobs_response" | grep -o '"id":"[^"]*"' | sed 's/"id":"\([^"]*\)"/\1/' 2>/dev/null || true
}

# 获取作业详情
get_job_details() {
    local job_id=$1
    
    if [ "$job_id" = "" ]; then
        echo "❌ 作业ID为空"
        return 1
    fi
    
    local job_detail=$(curl -s --connect-timeout 10 "$FLINK_REST_URL/jobs/$job_id")
    if [ $? -ne 0 ] || [ "$job_detail" = "" ]; then
        echo "❌ 获取作业详情失败: $job_id"
        return 1
    fi
    
    echo "$job_detail"
}



# =================主程序逻辑=================

# 检查参数
if [ "$1" = "help" ] || [ "$1" = "-h" ] || [ "$1" = "--help" ]; then
    show_help
    exit 0
fi

# 检查curl命令
if ! command -v curl >/dev/null 2>&1; then
    echo "❌ curl命令不存在，请先安装curl"
    exit 1
fi

# 检查Flink连接
check_flink_connection

# 获取所有作业
echo "🔍 查找匹配的运行中作业..."
job_ids=$(get_all_jobs)

if [ "$job_ids" = "" ]; then
    echo "❌ 没有找到任何作业"
    exit 1
fi

# 查找匹配的作业
found_jobs=0
temp_file=$(mktemp)

echo "找到 $(echo "$job_ids" | wc -l) 个作业，正在筛选运行中的作业..."

for job_id in $job_ids; do
    echo "  检查作业: $job_id"
    
    job_detail=$(get_job_details "$job_id")
    if [ $? -eq 0 ]; then
        job_name=$(echo "$job_detail" | grep -o '"name":"[^"]*"' | sed 's/"name":"\([^"]*\)"/\1/')
        
        if echo "$job_name" | grep -q "$JOB_NAME_FILTER"; then
            # 先提取作业状态进行筛选
            job_state=$(echo "$job_detail" | grep -o '"state":"[^"]*"' | sed 's/"state":"\([^"]*\)"/\1/')
            
            # 只处理状态为RUNNING的作业
            if [ "$job_state" = "RUNNING" ]; then
                found_jobs=$((found_jobs + 1))
                echo "  ✅ 匹配运行中: $job_name ($job_state)"
                
                # 直接解析并输出作业信息
                job_id=$(echo "$job_detail" | grep -o '"jid":"[^"]*"' | sed 's/"jid":"\([^"]*\)"/\1/')
                start_time=$(echo "$job_detail" | grep -o '"start-time":[0-9]*' | sed 's/"start-time":\([0-9]*\)/\1/')
                end_time=$(echo "$job_detail" | grep -o '"end-time":[0-9]*' | sed 's/"end-time":\([0-9]*\)/\1/')
                duration=$(echo "$job_detail" | grep -o '"duration":[0-9]*' | sed 's/"duration":\([0-9]*\)/\1/')
            
            # 直接输出格式化结果
            case "$OUTPUT_FORMAT" in
                "json")
                    echo "{"
                    echo "  \"job_id\": \"$job_id\","
                    echo "  \"job_name\": \"$job_name\","
                    echo "  \"job_state\": \"$job_state\","
                    echo "  \"start_time\": $start_time,"
                    echo "  \"end_time\": $end_time,"
                    echo "  \"duration\": $duration,"
                    echo "  \"flink_ui_url\": \"$FLINK_REST_URL/#/job/$job_id/overview\","
                    echo "  \"query_time\": \"$(date -Iseconds)\""
                    echo "}"
                    ;;
                "simple")
                    echo "$job_id|$job_name|$job_state|$(format_timestamp $start_time)"
                    ;;
                "pretty"|*)
                    echo
                    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
                    echo "📊 作业详细信息"
                    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
                    echo "🆔 作业ID     : $job_id"
                    echo "📝 作业名称   : $job_name"
                    echo "🔄 作业状态   : $job_state"
                    echo "⏰ 启动时间   : $(format_timestamp $start_time)"
                    
                    if [ "$end_time" != "null" ] && [ "$end_time" != "" ]; then
                        echo "🏁 结束时间   : $(format_timestamp $end_time)"
                    fi
                    
                    if [ "$job_state" = "RUNNING" ]; then
                        echo "⏱️  运行时长   : $(format_duration $start_time)"
                    elif [ "$duration" != "null" ] && [ "$duration" != "" ]; then
                        echo "⏱️  总时长     : $(format_duration 0 $duration)"
                    fi
                    
                    echo "🌐 Web UI     : $FLINK_REST_URL/#/job/$job_id/overview"
                    echo "🔗 REST API   : $FLINK_REST_URL/jobs/$job_id"
                    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
                    ;;
            esac
            else
                echo "  ⏭️  跳过非运行状态: $job_name ($job_state)"
            fi
        else
            echo "  ⏭️  跳过: $job_name"
        fi
    fi
done

# 清理临时文件
rm -f "$temp_file"

if [ $found_jobs -eq 0 ]; then
    echo
    echo "❌ 没有找到名称包含 '$JOB_NAME_FILTER' 且状态为RUNNING的作业"
    echo
    echo "💡 提示："
    echo "  1. 检查作业名称是否正确"
    echo "  2. 确认作业是否正在运行中（非CANCELED/FINISHED状态）"
    echo "  3. 作业可能已停止或尚未启动"
    echo "  4. 使用原版脚本查看所有状态的作业"
    exit 1
else
    echo
    echo "✅ 查询完成，共找到 $found_jobs 个运行中的匹配作业"
fi

echo
echo "==========================================="
echo "运行中作业查询完成！"
echo "Flink Web UI: $FLINK_REST_URL/#/overview"
echo "✨ 仅显示状态为 RUNNING 的作业"
echo "===========================================" 