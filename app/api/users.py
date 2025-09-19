"""用户管理API路由"""
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func
from sqlalchemy.orm import selectinload
from loguru import logger

from app.models import User, UserSession
from app.services.database_service import get_db_session
from app.auth.dependencies import (
    get_current_active_user,
    get_admin_user,
    get_admin_user_or_options,
    RoleChecker
)
from app.auth.decorators import admin_required, roles_required
from app.auth.schemas import UserInfo
from pydantic import BaseModel
from datetime import datetime


router = APIRouter(prefix="/users", tags=["用户管理"])



class UserCreateRequest(BaseModel):
    """创建用户请求"""
    wallet_address: str
    role: str = "user"
    status: str = "active"
    display_name: Optional[str] = None


class UserUpdateRequest(BaseModel):
    """更新用户请求"""
    role: Optional[str] = None
    status: Optional[str] = None
    display_name: Optional[str] = None


class UserListResponse(BaseModel):
    """用户列表响应"""
    total: int
    users: List[UserInfo]
    page: int
    size: int


@router.options("/")
async def options_users():
    """处理用户管理API的CORS预检请求"""
    return {"message": "OK"}


@router.get("/", response_model=UserListResponse)
async def get_users(
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=100, description="每页大小"),
    role: Optional[str] = Query(None, description="按角色筛选"),
    status: Optional[str] = Query(None, description="按状态筛选"),
    search: Optional[str] = Query(None, description="搜索钱包地址或显示名称"),
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_admin_user)
):
    """
    获取用户列表（仅管理员）

    Args:
        page: 页码
        size: 每页大小
        role: 角色筛选
        status: 状态筛选
        search: 搜索关键词
        db: 数据库会话
        current_user: 当前用户

    Returns:
        用户列表响应
    """
    try:
        # 构建查询
        query = select(User)
        count_query = select(func.count(User.id))

        # 添加筛选条件
        if role:
            query = query.where(User.role == role)
            count_query = count_query.where(User.role == role)

        if status:
            query = query.where(User.status == status)
            count_query = count_query.where(User.status == status)

        if search:
            search_pattern = f"%{search}%"
            query = query.where(
                (User.wallet_address.ilike(search_pattern)) |
                (User.display_name.ilike(search_pattern))
            )
            count_query = count_query.where(
                (User.wallet_address.ilike(search_pattern)) |
                (User.display_name.ilike(search_pattern))
            )

        # 获取总数
        total_result = await db.execute(count_query)
        total = total_result.scalar()

        # 分页查询
        offset = (page - 1) * size
        query = query.offset(offset).limit(size).order_by(User.created_at.desc())

        result = await db.execute(query)
        users = result.scalars().all()

        # 转换为响应格式
        user_list = [
            UserInfo(
                id=user.id,
                wallet_address=user.wallet_address,
                role=user.role,
                status=user.status,
                display_name=user.display_name,
                last_login_at=user.last_login_at,
                created_at=user.created_at
            )
            for user in users
        ]

        if current_user:
            logger.info(f"管理员 {current_user.wallet_address} 查询用户列表，页码: {page}")

        return UserListResponse(
            total=total,
            users=user_list,
            page=page,
            size=size
        )

    except Exception as e:
        logger.error(f"获取用户列表失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取用户列表失败"
        )


@router.get("/{user_id}", response_model=UserInfo)
async def get_user(
    user_id: int,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_admin_user)
):
    """
    获取用户详情（仅管理员）

    Args:
        user_id: 用户ID
        db: 数据库会话
        current_user: 当前用户

    Returns:
        用户信息
    """
    try:
        # 查询用户
        query = await db.execute(
            select(User).where(User.id == user_id)
        )
        user = query.scalar_one_or_none()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在"
            )

        logger.info(f"管理员 {current_user.wallet_address} 查询用户详情: {user.wallet_address}")

        return UserInfo(
            id=user.id,
            wallet_address=user.wallet_address,
            role=user.role,
            status=user.status,
            display_name=user.display_name,
            last_login_at=user.last_login_at,
            created_at=user.created_at
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取用户详情失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取用户详情失败"
        )


@router.post("/", response_model=UserInfo)
async def create_user(
    request: UserCreateRequest,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_admin_user)
):
    """
    创建用户（仅管理员）

    Args:
        request: 创建用户请求
        db: 数据库会话
        current_user: 当前用户

    Returns:
        创建的用户信息
    """
    try:
        # 检查钱包地址是否已存在
        existing_query = await db.execute(
            select(User).where(User.wallet_address == request.wallet_address.lower())
        )
        existing_user = existing_query.scalar_one_or_none()

        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="钱包地址已存在"
            )

        # 创建新用户
        new_user = User(
            wallet_address=request.wallet_address.lower(),
            role=request.role,
            status=request.status,
            display_name=request.display_name
        )

        db.add(new_user)
        await db.commit()
        await db.refresh(new_user)

        logger.info(f"管理员 {current_user.wallet_address} 创建用户: {new_user.wallet_address}")

        return UserInfo(
            id=new_user.id,
            wallet_address=new_user.wallet_address,
            role=new_user.role,
            status=new_user.status,
            display_name=new_user.display_name,
            last_login_at=new_user.last_login_at,
            created_at=new_user.created_at
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"创建用户失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="创建用户失败"
        )


@router.put("/{user_id}", response_model=UserInfo)
async def update_user(
    user_id: int,
    request: UserUpdateRequest,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_admin_user)
):
    """
    更新用户信息（仅管理员）

    Args:
        user_id: 用户ID
        request: 更新用户请求
        db: 数据库会话
        current_user: 当前用户

    Returns:
        更新后的用户信息
    """
    try:
        # 查询用户
        query = await db.execute(
            select(User).where(User.id == user_id)
        )
        user = query.scalar_one_or_none()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在"
            )

        # 防止管理员修改自己的角色
        if user.id == current_user.id and request.role and request.role != user.role:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="无法修改自己的角色"
            )

        # 更新用户信息
        update_data = {}
        if request.role is not None:
            update_data["role"] = request.role
        if request.status is not None:
            update_data["status"] = request.status
        if request.display_name is not None:
            update_data["display_name"] = request.display_name

        if update_data:
            await db.execute(
                update(User)
                .where(User.id == user_id)
                .values(**update_data)
            )
            await db.commit()
            await db.refresh(user)

        logger.info(f"管理员 {current_user.wallet_address} 更新用户: {user.wallet_address}")

        return UserInfo(
            id=user.id,
            wallet_address=user.wallet_address,
            role=user.role,
            status=user.status,
            display_name=user.display_name,
            last_login_at=user.last_login_at,
            created_at=user.created_at
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新用户失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="更新用户失败"
        )


@router.delete("/{user_id}")
async def delete_user(
    user_id: int,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_admin_user)
):
    """
    删除用户（仅管理员）

    Args:
        user_id: 用户ID
        db: 数据库会话
        current_user: 当前用户

    Returns:
        删除结果
    """
    try:
        # 查询用户
        query = await db.execute(
            select(User).where(User.id == user_id)
        )
        user = query.scalar_one_or_none()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在"
            )

        # 防止管理员删除自己
        if user.id == current_user.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="无法删除自己的账户"
            )

        # 删除用户的所有会话
        await db.execute(
            delete(UserSession).where(UserSession.user_id == user_id)
        )

        # 删除用户
        await db.execute(
            delete(User).where(User.id == user_id)
        )
        await db.commit()

        logger.info(f"管理员 {current_user.wallet_address} 删除用户: {user.wallet_address}")

        return {"message": "用户删除成功"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除用户失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="删除用户失败"
        )


@router.get("/me/profile", response_model=UserInfo)
async def get_my_profile(
    current_user: User = Depends(get_current_active_user)
):
    """
    获取当前用户个人资料

    Args:
        current_user: 当前用户

    Returns:
        用户信息
    """
    return UserInfo(
        id=current_user.id,
        wallet_address=current_user.wallet_address,
        role=current_user.role,
        status=current_user.status,
        display_name=current_user.display_name,
        last_login_at=current_user.last_login_at,
        created_at=current_user.created_at
    )