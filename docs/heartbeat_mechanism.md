# 任务心跳机制说明

## 概述

为了解决长期运行任务被误判为超时失败的问题，我们实现了任务心跳机制。该机制允许长期运行的任务定期更新心跳时间，任务监控系统根据心跳时间而不是创建时间来判断任务是否超时。

## 主要改进

### 1. 数据库模型更新

在 `PipelineTask` 模型中添加了 `last_heartbeat` 字段：

```python
last_heartbeat: Mapped[Optional[datetime]] = mapped_column(
    DateTime,
    nullable=True,
    comment="最后心跳时间"
)
```

### 2. 任务监控逻辑优化

修改了 `TaskMonitorService.check_timeout_tasks` 方法，使用心跳时间判断超时：

- 优先使用 `last_heartbeat` 时间判断超时
- 如果没有心跳时间，则回退到使用 `create_time` 判断
- 提供更详细的超时日志信息

### 3. 心跳更新机制

添加了 `TaskMonitorService.update_task_heartbeat` 方法：

- 只更新状态为"正在运行"的任务
- 提供错误处理和日志记录
- 支持批量心跳更新

### 4. 事件监控组件集成

在 `ContractEventMonitor` 中集成了心跳更新：

- 实时监控模式：每30秒更新一次心跳
- 历史监控模式：每30秒更新一次心跳
- 自动传递任务ID给监控器

## 使用方法

### 1. 数据库迁移

首先执行数据库迁移脚本：

```sql
-- 执行 sql/add_heartbeat_field.sql
ALTER TABLE pipeline_task 
ADD COLUMN last_heartbeat DATETIME NULL COMMENT '最后心跳时间';

-- 为现有任务设置初始心跳时间
UPDATE pipeline_task 
SET last_heartbeat = create_time 
WHERE last_heartbeat IS NULL AND create_time IS NOT NULL;

-- 添加索引
CREATE INDEX idx_pipeline_task_heartbeat ON pipeline_task(last_heartbeat);
```

### 2. 运行测试

执行心跳机制测试脚本：

```bash
cd chain-data-parser
python test_heartbeat_mechanism.py
```

### 3. 监控任务状态

通过API查看任务状态，现在会包含心跳时间信息：

```bash
curl http://localhost:8000/api/v1/pipeline/tasks
```

响应示例：
```json
{
  "tasks": [
    {
      "task_id": 123,
      "pipeline_id": 45,
      "status": 0,
      "status_text": "正在运行",
      "create_time": "2024-01-15T10:00:00",
      "last_heartbeat": "2024-01-15T10:05:30",
      "log_path": "/logs/pipeline_123.log"
    }
  ]
}
```

## 配置参数

### 心跳更新间隔

在事件监控组件中，心跳更新间隔默认为30秒，可以根据需要调整：

```python
# 在 app/component/event_monitor.py 中
heartbeat_interval = 30  # 心跳间隔（秒）
```

### 任务超时时间

任务监控守护进程的超时时间默认为60分钟：

```python
# 在 app/services/task_monitor_service.py 中
task_monitor_daemon = TaskMonitorDaemon(timeout_minutes=60)
```

## 工作原理

### 1. 任务启动

1. 创建任务时，`last_heartbeat` 字段初始为 `None`
2. 管道执行器启动时，将任务ID传递给组件
3. 事件监控组件开始监控并定期更新心跳

### 2. 心跳更新

1. 事件监控组件每30秒调用 `_update_heartbeat()` 方法
2. 该方法通过 `TaskMonitorService.update_task_heartbeat()` 更新数据库
3. 只更新状态为"正在运行"的任务

### 3. 超时检测

1. 任务监控守护进程每5分钟检查一次超时任务
2. 优先使用 `last_heartbeat` 时间判断超时
3. 如果没有心跳时间，则使用 `create_time` 判断
4. 超时的任务被标记为失败状态

## 优势

### 1. 解决误判问题

- 长期运行的任务不会被误判为超时失败
- 只有真正无响应的任务才会被标记为失败

### 2. 提供实时状态

- 可以通过心跳时间了解任务的活跃状态
- 便于监控和调试长期运行的任务

### 3. 向后兼容

- 对于没有心跳时间的旧任务，仍然使用创建时间判断超时
- 不影响现有功能的正常运行

### 4. 性能优化

- 心跳更新频率适中，不会对数据库造成压力
- 添加了数据库索引提高查询性能

## 故障排除

### 1. 心跳更新失败

检查日志中的错误信息：
```
ERROR: 更新任务心跳异常: task_id=123, 错误: ...
```

可能原因：
- 数据库连接问题
- 任务状态不是"正在运行"
- 任务不存在

### 2. 任务仍然被误判为超时

检查：
1. 心跳更新是否正常工作
2. 任务监控守护进程是否正常运行
3. 超时时间设置是否合理

### 3. 数据库迁移问题

如果迁移失败，可以手动执行SQL：

```sql
-- 检查字段是否存在
DESCRIBE pipeline_task;

-- 手动添加字段
ALTER TABLE pipeline_task ADD COLUMN last_heartbeat DATETIME NULL;
```

## 监控建议

### 1. 日志监控

关注以下日志信息：
- 心跳更新成功/失败
- 任务超时检测结果
- 任务状态变化

### 2. 指标监控

建议监控：
- 心跳更新成功率
- 任务超时率
- 长期运行任务数量

### 3. 告警设置

建议设置告警：
- 心跳更新连续失败
- 任务超时率异常
- 数据库连接问题

## 总结

心跳机制有效解决了长期运行任务被误判为超时失败的问题，提高了任务监控系统的准确性和可靠性。通过定期更新心跳时间，系统可以准确判断任务的真实状态，避免因监控机制缺陷导致的误判。
