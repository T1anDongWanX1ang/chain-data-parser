"""Flink作业管理API接口"""
import os
import re
import json
import asyncio
import subprocess
from typing import Dict, Any, Optional
from datetime import datetime
from enum import Enum
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field
from loguru import logger

from app.services.database_service import get_db_session

router = APIRouter(prefix="", tags=["Flink作业管理"])


def parse_flink_job_info(script_output: str) -> Dict[str, Any]:
    """
    解析脚本输出中的Flink作业信息，从JobID输出中提取作业ID
    
    Args:
        script_output: 脚本输出内容
        
    Returns:
        Dict: 解析后的作业信息
    """
    try:
        # 首先尝试提取 JobID - 格式：Job has been submitted with JobID xxxxxx
        job_id_pattern = r'Job has been submitted with JobID ([a-fA-F0-9]+)'
        job_id_match = re.search(job_id_pattern, script_output)
        
        if job_id_match:
            job_id = job_id_match.group(1)
            logger.info(f"从脚本输出中提取到JobID: {job_id}")
            
            # 返回基础作业信息，稍后会通过API查询详细信息
            return {
                "success": True,
                "job_id": job_id,
                "source": "script_output",
                "timestamp": datetime.now().isoformat()
            }
        
        # 如果没找到JobID，尝试原来的JSON格式（向后兼容）
        json_pattern = r'=== FLINK_JOB_INFO_START ===(.*?)=== FLINK_JOB_INFO_END ==='
        json_match = re.search(json_pattern, script_output, re.DOTALL)
        
        if json_match:
            json_str = json_match.group(1).strip()
            # 尝试解析JSON
            try:
                job_info = json.loads(json_str)
                logger.info(f"成功解析JSON格式作业信息: job_id={job_info.get('job_id', 'unknown')}")
                return job_info
            except json.JSONDecodeError as e:
                logger.error(f"JSON解析失败: {e}, 原始内容: {json_str}")
                return {
                    "success": False,
                    "error": "作业信息JSON格式错误",
                    "raw_content": json_str
                }
        
        # 都没找到，返回失败信息
        logger.warning("未在脚本输出中找到JobID或作业信息标记")
        return {
            "success": False,
            "error": "未找到JobID或作业信息",
            "raw_output": script_output[-500:]  # 保留最后500字符用于调试
        }
        
    except Exception as e:
        logger.error(f"解析作业信息异常: {e}")
        return {
            "success": False,
            "error": f"解析异常: {str(e)}"
        }


def fetch_job_details_by_id_sync(job_id: str, environment: str = "multichain-dev") -> Dict[str, Any]:
    """
    根据JobID通过SSH连接到Flink服务器查询作业详细信息（同步版本）
    
    Args:
        job_id: Flink作业ID
        environment: 环境标识
        
    Returns:
        Dict: 作业详细信息
    """
    try:
        # Flink服务器配置
        flink_server = "35.208.145.201"
        flink_user = "ops"
        
        logger.info(f"同步查询作业详情: JobID={job_id}, 环境={environment}")
        
        # 通过SSH连接查询作业信息
        cmd = [
            "ssh", "-o", "ConnectTimeout=10", f"{flink_user}@{flink_server}",
            f"timeout 15 curl -s http://localhost:8081/jobs/{job_id}"
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            job_detail_text = result.stdout.strip()
            
            if job_detail_text:
                try:
                    job_detail = json.loads(job_detail_text)
                    
                    # 提取关键信息
                    job_name = job_detail.get('name', 'Unknown')
                    job_state = job_detail.get('state', 'Unknown')
                    start_time = job_detail.get('start-time', 0)
                    
                    response = {
                        "success": True,
                        "job_id": job_id,
                        "job_name": job_name,
                        "job_state": job_state,
                        "start_time": start_time,
                        "environment": environment,
                        "flink_ui_url": f"http://{flink_server}:8081",
                        "job_detail_url": f"http://{flink_server}:8081/#/job/{job_id}/overview",
                        "timestamp": datetime.now().isoformat(),
                        "raw_detail": job_detail
                    }
                    
                    logger.info(f"同步成功获取作业详情: JobID={job_id}, 状态={job_state}")
                    return response
                    
                except json.JSONDecodeError as e:
                    logger.error(f"同步解析作业详情JSON失败: {e}")
                    return {
                        "success": False,
                        "job_id": job_id,
                        "error": "作业详情JSON解析失败",
                        "raw_response": job_detail_text[:500]
                    }
            else:
                logger.warning(f"同步获取作业详情为空: JobID={job_id}")
                return {
                    "success": False,
                    "job_id": job_id,
                    "error": "作业详情为空"
                }
        else:
            error_text = result.stderr if result.stderr else "Unknown error"
            logger.error(f"同步查询作业详情失败: JobID={job_id}, 错误={error_text}")
            return {
                "success": False,
                "job_id": job_id,
                "error": f"查询作业详情失败: {error_text}"
            }
            
    except subprocess.TimeoutExpired:
        logger.error(f"同步查询作业详情超时: JobID={job_id}")
        return {
            "success": False,
            "job_id": job_id,
            "error": "查询作业详情超时"
        }
    except Exception as e:
        logger.error(f"同步查询作业详情异常: JobID={job_id}, 异常={str(e)}")
        return {
            "success": False,
            "job_id": job_id,
            "error": f"查询异常: {str(e)}"
        }


async def fetch_job_details_by_id(job_id: str, environment: str = "multichain-dev") -> Dict[str, Any]:
    """
    根据JobID通过SSH连接到Flink服务器查询作业详细信息
    
    Args:
        job_id: Flink作业ID
        environment: 环境标识
        
    Returns:
        Dict: 作业详细信息
    """
    try:
        # Flink服务器配置
        flink_server = "35.208.145.201"
        flink_user = "ops"
        
        logger.info(f"查询作业详情: JobID={job_id}, 环境={environment}")
        
        # 通过SSH连接查询作业信息
        cmd = [
            "ssh", "-o", "ConnectTimeout=10", f"{flink_user}@{flink_server}",
            f"timeout 15 curl -s http://localhost:8081/jobs/{job_id}"
        ]
        
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=30)
        
        if process.returncode == 0:
            job_detail_text = stdout.decode('utf-8').strip()
            
            if job_detail_text:
                try:
                    job_detail = json.loads(job_detail_text)
                    
                    # 提取关键信息
                    job_name = job_detail.get('name', 'Unknown')
                    job_state = job_detail.get('state', 'Unknown')
                    start_time = job_detail.get('start-time', 0)
                    
                    result = {
                        "success": True,
                        "job_id": job_id,
                        "job_name": job_name,
                        "job_state": job_state,
                        "start_time": start_time,
                        "environment": environment,
                        "flink_ui_url": f"http://{flink_server}:8081",
                        "job_detail_url": f"http://{flink_server}:8081/#/job/{job_id}/overview",
                        "timestamp": datetime.now().isoformat(),
                        "raw_detail": job_detail
                    }
                    
                    logger.info(f"成功获取作业详情: JobID={job_id}, 状态={job_state}")
                    return result
                    
                except json.JSONDecodeError as e:
                    logger.error(f"解析作业详情JSON失败: {e}")
                    return {
                        "success": False,
                        "job_id": job_id,
                        "error": "作业详情JSON解析失败",
                        "raw_response": job_detail_text[:500]
                    }
            else:
                logger.warning(f"获取作业详情为空: JobID={job_id}")
                return {
                    "success": False,
                    "job_id": job_id,
                    "error": "作业详情为空"
                }
        else:
            error_text = stderr.decode('utf-8') if stderr else "Unknown error"
            logger.error(f"查询作业详情失败: JobID={job_id}, 错误={error_text}")
            return {
                "success": False,
                "job_id": job_id,
                "error": f"查询作业详情失败: {error_text}"
            }
            
    except asyncio.TimeoutError:
        logger.error(f"查询作业详情超时: JobID={job_id}")
        return {
            "success": False,
            "job_id": job_id,
            "error": "查询作业详情超时"
        }
    except Exception as e:
        logger.error(f"查询作业详情异常: JobID={job_id}, 异常={str(e)}")
        return {
            "success": False,
            "job_id": job_id,
            "error": f"查询异常: {str(e)}"
        }


class EnvironmentType(str, Enum):
    """环境类型枚举"""
    MULTICHAIN_DEV = "multichain-dev"
    MULTICHAIN_PROD = "multichain-prod"


class OperationType(str, Enum):
    """操作类型枚举"""
    DEPLOY = "deploy"
    BUILD = "build"
    UPLOAD = "upload"
    STATUS = "status"


class StartFlinkJobResponse(BaseModel):
    """启动Flink作业响应模型"""
    success: bool = Field(..., description="操作是否成功启动")
    message: str = Field(..., description="操作消息")
    data: Dict[str, Any] = Field(default_factory=dict, description="返回数据")


class FlinkJobStatusResponse(BaseModel):
    """Flink作业状态响应模型"""
    success: bool = Field(..., description="查询是否成功")
    message: str = Field(..., description="状态消息")
    data: Dict[str, Any] = Field(default_factory=dict, description="状态数据")


async def execute_shell_script(script_path: str, environment: str, operation: str) -> Dict[str, Any]:
    """
    异步执行shell脚本
    
    Args:
        script_path: 脚本路径
        environment: 环境参数
        operation: 操作参数
    
    Returns:
        执行结果字典
    """
    try:
        logger.info(f"开始执行Flink部署脚本: {script_path} {environment} {operation}")
        
        # 构建命令
        cmd = [script_path, environment, operation]
        
        # 设置工作目录为脚本所在目录
        script_dir = Path(script_path).parent
        
        # 异步执行命令
        process = await asyncio.create_subprocess_exec(
            *cmd,
            cwd=script_dir,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await process.communicate()
        
        # 解码输出
        stdout_text = stdout.decode('utf-8') if stdout else ""
        stderr_text = stderr.decode('utf-8') if stderr else ""
        
        # 解析脚本输出中的作业信息
        job_info = None
        if process.returncode == 0:
            basic_job_info = parse_flink_job_info(stdout_text)
            if basic_job_info and basic_job_info.get('success') and basic_job_info.get('job_id'):
                # 如果成功提取到JobID，查询详细信息
                job_id = basic_job_info.get('job_id')
                logger.info(f"提取到JobID: {job_id}, 开始查询作业详情...")
                job_info = await fetch_job_details_by_id(job_id, environment)
            else:
                job_info = basic_job_info
        
        result = {
            "return_code": process.returncode,
            "stdout": stdout_text,
            "stderr": stderr_text,
            "success": process.returncode == 0,
            "command": " ".join(cmd),
            "execution_time": datetime.now().isoformat(),
            "job_info": job_info
        }
        
        if process.returncode == 0:
            logger.info(f"Flink部署脚本执行成功: {environment} {operation}")
            if job_info and job_info.get('success'):
                logger.info(f"获取作业信息成功: {job_info.get('job_id', 'unknown')}")
        else:
            logger.error(f"Flink部署脚本执行失败: {environment} {operation}, 错误码: {process.returncode}")
        
        return result
        
    except Exception as e:
        logger.error(f"执行Flink部署脚本异常: {str(e)}")
        return {
            "return_code": -1,
            "stdout": "",
            "stderr": str(e),
            "success": False,
            "command": " ".join(cmd) if 'cmd' in locals() else "unknown",
            "execution_time": datetime.now().isoformat(),
            "error": str(e)
        }


def execute_shell_script_sync(script_path: str, environment: str, operation: str) -> Dict[str, Any]:
    """
    同步执行shell脚本
    
    Args:
        script_path: 脚本路径
        environment: 环境参数
        operation: 操作参数
    
    Returns:
        执行结果字典
    """
    try:
        logger.info(f"同步执行Flink部署脚本: {script_path} {environment} {operation}")
        
        # 构建命令
        cmd = [script_path, environment, operation]
        
        # 设置工作目录为脚本所在目录
        script_dir = Path(script_path).parent
        
        # 同步执行命令
        result = subprocess.run(
            cmd,
            cwd=script_dir,
            capture_output=True,
            text=True,
            timeout=300  # 5分钟超时
        )
        
        # 解析脚本输出中的作业信息
        job_info = None
        if result.returncode == 0:
            basic_job_info = parse_flink_job_info(result.stdout)
            if basic_job_info and basic_job_info.get('success') and basic_job_info.get('job_id'):
                # 如果成功提取到JobID，查询详细信息
                job_id = basic_job_info.get('job_id')
                logger.info(f"提取到JobID: {job_id}, 开始查询作业详情...")
                job_info = fetch_job_details_by_id_sync(job_id, environment)
            else:
                job_info = basic_job_info
        
        execution_result = {
            "return_code": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "success": result.returncode == 0,
            "command": " ".join(cmd),
            "execution_time": datetime.now().isoformat(),
            "job_info": job_info
        }
        
        if result.returncode == 0:
            logger.info(f"Flink部署脚本执行成功: {environment} {operation}")
            if job_info and job_info.get('success'):
                logger.info(f"获取作业信息成功: {job_info.get('job_id', 'unknown')}")
        else:
            logger.error(f"Flink部署脚本执行失败: {environment} {operation}, 错误码: {result.returncode}")
        
        return execution_result
        
    except subprocess.TimeoutExpired:
        logger.error(f"Flink部署脚本执行超时: {environment} {operation}")
        return {
            "return_code": -2,
            "stdout": "",
            "stderr": "执行超时",
            "success": False,
            "command": " ".join(cmd),
            "execution_time": datetime.now().isoformat(),
            "error": "执行超时"
        }
    except Exception as e:
        logger.error(f"执行Flink部署脚本异常: {str(e)}")
        return {
            "return_code": -1,
            "stdout": "",
            "stderr": str(e),
            "success": False,
            "command": " ".join(cmd) if 'cmd' in locals() else "unknown",
            "execution_time": datetime.now().isoformat(),
            "error": str(e)
        }


async def background_flink_job(script_path: str, environment: str, operation: str):
    """后台执行Flink作业"""
    try:
        result = await execute_shell_script(script_path, environment, operation)
        success = result['success']
        job_info = result.get('job_info')
        
        if success:
            logger.info(f"后台Flink作业完成: {environment} {operation}, 成功: {success}")
            if job_info and job_info.get('success'):
                logger.info(f"作业信息: JobID={job_info.get('job_id')}, 状态={job_info.get('job_state')}, 名称={job_info.get('job_name')}")
            else:
                logger.warning(f"未获取到有效的作业信息: {job_info}")
        else:
            logger.error(f"后台Flink作业执行失败: {environment} {operation}")
            
    except Exception as e:
        logger.error(f"后台Flink作业异常: {str(e)}")


@router.post("/start-flink-job", response_model=StartFlinkJobResponse, summary="启动Flink作业")
async def start_flink_job(
    sync_execution: bool = False,
    background_tasks: BackgroundTasks = None,
    session: AsyncSession = Depends(get_db_session)
):
    """
    启动Flink作业部署
    
    使用脚本默认配置：
    - 环境: multichain-dev (开发环境)
    - 操作: deploy (部署操作) 
    
    Args:
        sync_execution: 是否同步执行（默认false，异步执行）
        background_tasks: 后台任务管理器
        session: 数据库会话
    
    Returns:
        StartFlinkJobResponse: 执行结果，同步执行时包含完整的作业信息
    """
    try:
        # 使用脚本默认值
        environment_str = "multichain-dev"  # 脚本默认环境
        operation_str = "deploy"            # 脚本默认操作
        
        logger.info(f"启动Flink作业请求: 环境={environment_str}, 操作={operation_str}, 同步={sync_execution}")
        
        # 查找部署脚本
        script_path = None
        possible_paths = [
            "app/deploy-to-flink-cluster.sh",         # 正式脚本优先
            "./deploy-to-flink-cluster.sh",           # 当前目录
            "../deploy-to-flink-cluster.sh",          # 上级目录
            "app/test-flink-script.sh"                # 测试脚本作为备选
        ]
        
        for path in possible_paths:
            if Path(path).exists():
                script_path = str(Path(path).resolve())
                break
        
        if not script_path:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="未找到部署脚本文件: deploy-to-flink-cluster.sh"
            )
        
        # 检查脚本是否可执行
        if not os.access(script_path, os.X_OK):
            # 尝试添加执行权限
            try:
                os.chmod(script_path, 0o755)
                logger.info(f"已添加脚本执行权限: {script_path}")
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"脚本无执行权限且无法修改: {str(e)}"
                )
        
        if sync_execution:
            # 同步执行，立即返回包含作业信息的结果
            logger.info(f"同步执行Flink作业: {environment_str} {operation_str}")
            result = execute_shell_script_sync(script_path, environment_str, operation_str)
            
            # 准备响应数据
            response_data = {
                "environment": environment_str,
                "operation": operation_str,
                "execution_mode": "sync",
                "script_path": script_path,
                "return_code": result["return_code"],
                "execution_time": result["execution_time"],
                "command": result["command"],
                "flink_ui_url": "http://35.208.145.201:8081"
            }
            
            # 如果有作业信息，添加到响应中
            job_info = result.get("job_info")
            if job_info and job_info.get('success'):
                response_data.update({
                    "job_id": job_info.get('job_id'),
                    "job_name": job_info.get('job_name'),
                    "job_state": job_info.get('job_state'),
                    "start_time": job_info.get('start_time'),
                    "job_detail_url": job_info.get('job_detail_url'),
                    "job_info": job_info
                })
                
            return StartFlinkJobResponse(
                success=result["success"],
                message="Flink作业执行完成" if result["success"] else "Flink作业执行失败",
                data=response_data
            )
        else:
            # 异步执行（为了避免前端请求超时）
            if background_tasks:
                background_tasks.add_task(
                    background_flink_job, 
                    script_path, 
                    environment_str, 
                    operation_str
                )
            
            logger.info(f"Flink作业已加入后台执行队列: {environment_str} {operation_str}")
            
            return StartFlinkJobResponse(
                success=True,
                message=f"Flink作业已启动（后台执行）",
                data={
                    "environment": environment_str,
                    "operation": operation_str,
                    "execution_mode": "async",
                    "script_path": script_path,
                    "start_time": datetime.now().isoformat(),
                    "status": "running",
                    "message": "作业正在后台执行，请稍后查看执行结果",
                    "flink_ui_url": "http://35.208.145.201:8081"
                }
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"启动Flink作业失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"启动Flink作业失败: {str(e)}"
        )


@router.get("/flink-job/status", response_model=FlinkJobStatusResponse, summary="查看Flink作业状态")
async def get_flink_job_status(
    session: AsyncSession = Depends(get_db_session)
):
    """
    查看Flink作业状态
    
    使用脚本默认环境 multichain-dev
    
    Args:
        session: 数据库会话
    
    Returns:
        FlinkJobStatusResponse: 状态信息
    """
    try:
        environment_str = "multichain-dev"  # 使用脚本默认环境
        
        logger.info(f"查询Flink作业状态: 环境={environment_str}")
        
        # 查找部署脚本
        script_path = None
        possible_paths = [
            "app/deploy-to-flink-cluster.sh",         # 正式脚本优先
            "./deploy-to-flink-cluster.sh",           # 当前目录
            "../deploy-to-flink-cluster.sh",          # 上级目录
            "app/test-flink-script.sh"                # 测试脚本作为备选
        ]
        
        for path in possible_paths:
            if Path(path).exists():
                script_path = str(Path(path).resolve())
                break
        
        if not script_path:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="未找到部署脚本文件"
            )
        
        # 执行状态查询
        result = execute_shell_script_sync(script_path, environment_str, "status")
        
        return FlinkJobStatusResponse(
            success=result["success"],
            message="状态查询完成" if result["success"] else "状态查询失败",
            data={
                "environment": environment_str,
                "operation": "status",
                "return_code": result["return_code"],
                "stdout": result["stdout"],
                "stderr": result["stderr"],
                "execution_time": result["execution_time"],
                "flink_ui_url": "http://35.208.145.201:8081"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"查询Flink作业状态失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"查询状态失败: {str(e)}"
        ) 