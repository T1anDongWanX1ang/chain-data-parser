/**
 * Flink作业信息处理工具函数
 */

/**
 * 获取Flink作业信息并生成跳转链接
 * @param {string} jobName - 作业名称，默认为MultiChainTokenJob
 * @param {string} outputFormat - 输出格式，默认为json
 * @returns {Promise<Object>} 包含作业信息和跳转链接的对象
 */
async function getFlinkJobInfoAndGenerateLink(jobName = 'MultiChainTokenJob', outputFormat = 'json') {
    try {
        // 构建API请求URL
        const apiUrl = `/api/v1/get-job-info?job_name=${encodeURIComponent(jobName)}&output_format=${outputFormat}`;
        
        // 发送请求
        const response = await fetch(apiUrl, {
            method: 'GET',
            headers: {
                'accept': 'application/json'
            }
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        
        if (!data.success) {
            throw new Error(data.message || '获取作业信息失败');
        }
        
        // 解析返回的数据
        const jobs = data.data.jobs || [];
        const totalJobs = data.data.total_jobs || 0;
        const metadata = data.data.metadata || {};
        
        // 生成跳转链接
        let jobDetailLink = null;
        if (jobs.length > 0) {
            // 取第一个作业的ID
            const firstJob = jobs[0];
            const jobId = firstJob.job_id;
            
            // 清理job_id（去除可能的重复部分）
            const cleanJobId = jobId.split(' ')[0]; // 取第一个空格前的部分
            
            // 生成Flink Web UI链接
            jobDetailLink = `http://35.208.145.201:8081/#/job/running/${cleanJobId}/overview`;
        }
        
        return {
            success: true,
            data: {
                jobs: jobs,
                totalJobs: totalJobs,
                metadata: metadata,
                jobDetailLink: jobDetailLink,
                flinkServerUrl: 'http://35.208.145.201:8081'
            }
        };
        
    } catch (error) {
        console.error('获取Flink作业信息失败:', error);
        return {
            success: false,
            error: error.message
        };
    }
}

/**
 * 在step6卡片中添加任务详情跳转按钮
 * @param {string} containerId - 容器元素ID
 * @param {string} jobName - 作业名称
 */
async function addJobDetailButtonToStep6(containerId, jobName = 'MultiChainTokenJob') {
    try {
        // 获取作业信息
        const result = await getFlinkJobInfoAndGenerateLink(jobName);
        
        if (!result.success) {
            console.error('无法获取作业信息:', result.error);
            return;
        }
        
        const { jobs, totalJobs, jobDetailLink } = result.data;
        
        // 查找容器元素
        const container = document.getElementById(containerId);
        if (!container) {
            console.error(`找不到容器元素: ${containerId}`);
            return;
        }
        
        // 创建任务详情按钮
        const buttonHtml = `
            <div class="job-detail-section" style="margin-top: 15px; padding: 10px; background-color: #f8f9fa; border-radius: 5px;">
                <h4 style="margin: 0 0 10px 0; color: #495057;">📊 Flink任务详情</h4>
                <p style="margin: 5px 0; color: #6c757d; font-size: 14px;">
                    找到 ${totalJobs} 个运行中的作业
                </p>
                ${jobDetailLink ? `
                    <a href="${jobDetailLink}" target="_blank" class="btn btn-primary" 
                       style="display: inline-block; padding: 8px 16px; background-color: #007bff; color: white; 
                              text-decoration: none; border-radius: 4px; font-size: 14px;">
                        🔗 查看任务详情
                    </a>
                ` : `
                    <p style="color: #dc3545; font-size: 14px;">⚠️ 未找到运行中的作业</p>
                `}
            </div>
        `;
        
        // 将按钮添加到容器中
        container.insertAdjacentHTML('beforeend', buttonHtml);
        
        console.log('任务详情按钮已添加到step6卡片');
        
    } catch (error) {
        console.error('添加任务详情按钮失败:', error);
    }
}

/**
 * 格式化作业信息用于显示
 * @param {Array} jobs - 作业列表
 * @returns {string} 格式化后的HTML
 */
function formatJobInfoForDisplay(jobs) {
    if (!jobs || jobs.length === 0) {
        return '<p>暂无运行中的作业</p>';
    }
    
    let html = '<div class="job-list">';
    jobs.forEach((job, index) => {
        const jobId = job.job_id.split(' ')[0]; // 清理job_id
        const jobName = job.job_name || 'Unknown';
        const jobState = job.job_state || 'Unknown';
        
        html += `
            <div class="job-item" style="margin-bottom: 10px; padding: 8px; border: 1px solid #dee2e6; border-radius: 4px;">
                <div style="font-weight: bold; color: #495057;">作业 ${index + 1}</div>
                <div style="font-size: 12px; color: #6c757d;">ID: ${jobId}</div>
                <div style="font-size: 12px; color: #6c757d;">状态: ${jobState}</div>
                <div style="font-size: 12px; color: #6c757d; word-break: break-all;">名称: ${jobName}</div>
            </div>
        `;
    });
    html += '</div>';
    
    return html;
}

// 导出函数供全局使用
window.getFlinkJobInfoAndGenerateLink = getFlinkJobInfoAndGenerateLink;
window.addJobDetailButtonToStep6 = addJobDetailButtonToStep6;
window.formatJobInfoForDisplay = formatJobInfoForDisplay;
