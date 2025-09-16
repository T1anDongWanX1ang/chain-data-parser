-- 添加任务心跳字段
-- 用于监控长期运行任务的状态

ALTER TABLE pipeline_task 
ADD COLUMN last_heartbeat DATETIME NULL COMMENT '最后心跳时间';

-- 为现有任务设置初始心跳时间为创建时间
UPDATE pipeline_task 
SET last_heartbeat = create_time 
WHERE last_heartbeat IS NULL AND create_time IS NOT NULL;

-- 添加索引以提高查询性能
CREATE INDEX idx_pipeline_task_heartbeat ON pipeline_task(last_heartbeat);
