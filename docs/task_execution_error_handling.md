# 任务执行错误处理改进

## 问题描述

在管道任务执行过程中出现错误：`'NoneType' object has no attribute 'log_path'`

## 根本原因

在 `PipelineConfigService._execute_pipeline_async` 方法中，代码尝试访问 `task.log_path`，但没有检查 `task` 是否为 `None`。当数据库中找不到对应的任务记录时，`await session.get(PipelineTask, task_id)` 返回 `None`，导致后续访问 `log_path` 属性时出错。

## 修复内容

### 1. 添加任务存在性检查

```python
# 修复前
task = await session.get(PipelineTask, task_id)
if task:
    task.status = 0  # 正在运行
    await session.commit()

# 创建管道执行器并运行
pipeline = OptimizedBlockchainDataPipeline(config_dict=config, log_path=task.log_path)

# 修复后
task = await session.get(PipelineTask, task_id)
if not task:
    logger.error(f"任务不存在: task_id={task_id}")
    return

task.status = 0  # 正在运行
await session.commit()

# 创建管道执行器并运行
pipeline = OptimizedBlockchainDataPipeline(config_dict=config, log_path=task.log_path)
```

### 2. 改进任务状态更新

```python
# 修复前
task = await session.get(PipelineTask, task_id)
if task:
    task.status = 1  # 成功
    await session.commit()

logger.info(f"管道任务执行完成: task_id={task_id}")

# 修复后
task = await session.get(PipelineTask, task_id)
if task:
    task.status = 1  # 成功
    await session.commit()
    logger.info(f"管道任务执行完成: task_id={task_id}")
else:
    logger.warning(f"任务执行完成但无法更新状态，任务不存在: task_id={task_id}")
```

## 修复效果

### 修复前
- 当任务不存在时，程序崩溃并抛出 `AttributeError`
- 错误信息不清晰，难以定位问题
- 影响整个任务执行流程

### 修复后
- 任务不存在时，记录清晰的错误日志并优雅退出
- 不会影响其他任务的执行
- 提供明确的错误信息便于调试

## 测试验证

```python
# 测试用例1: 不存在的任务ID
invalid_task_id = 99999
await service._execute_pipeline_async(invalid_task_id, test_config)
# 预期: 记录 "任务不存在: task_id=99999" 日志，不抛出异常

# 测试用例2: 正常任务流程
result = await service.start_pipeline_task(pipeline_id=3, log_path="logs/test.log")
# 预期: 任务创建成功，返回任务信息
```

## 相关文件

- `app/services/pipeline_config_service.py` - 主要修复文件
- `app/models/pipeline_task.py` - 任务模型定义
- `app/api/pipeline.py` - API接口层

## 预防措施

1. **数据库查询后的空值检查**: 所有数据库查询操作后都应检查返回值是否为 `None`
2. **错误日志记录**: 在关键操作失败时记录详细的错误信息
3. **优雅降级**: 当某个组件失败时，不应影响整个系统的运行
4. **单元测试**: 为边界条件和异常情况编写测试用例

## 最佳实践

```python
# ✅ 推荐的数据库查询模式
async def safe_get_task(session: AsyncSession, task_id: int) -> Optional[PipelineTask]:
    """安全获取任务，包含错误处理"""
    try:
        task = await session.get(PipelineTask, task_id)
        if not task:
            logger.warning(f"任务不存在: task_id={task_id}")
        return task
    except Exception as e:
        logger.error(f"查询任务失败: task_id={task_id}, 错误: {e}")
        return None

# ✅ 推荐的属性访问模式
def get_task_log_path(task: Optional[PipelineTask]) -> Optional[str]:
    """安全获取任务日志路径"""
    if task and hasattr(task, 'log_path'):
        return task.log_path
    return None
```

## 总结

通过添加适当的空值检查和错误处理，成功解决了 `'NoneType' object has no attribute 'log_path'` 错误。这个修复不仅解决了当前问题，还提高了系统的健壮性和可维护性。
