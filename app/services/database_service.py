"""优化后的数据库服务"""
from typing import AsyncGenerator, Optional
from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker, AsyncEngine
from sqlalchemy.pool import StaticPool
from loguru import logger

from app.config import settings
from app.models.base import Base


class DatabaseService:
    """优化后的数据库服务类"""
    
    def __init__(self):
        """初始化数据库服务"""
        self._engine: Optional[AsyncEngine] = None
        self._session_factory: Optional[async_sessionmaker] = None
        self._initialized = True
    
    @property
    def engine(self) -> AsyncEngine:
        """获取数据库引擎"""
        if self._engine is None:
            self._create_engine()
        return self._engine
    
    @property
    def session_factory(self) -> async_sessionmaker:
        """获取会话工厂"""
        if self._session_factory is None:
            self._create_session_factory()
        return self._session_factory
    
    def _create_engine(self) -> None:
        """创建数据库引擎"""
        engine_kwargs = {
            "echo": settings.api.debug,
            "pool_pre_ping": True,
            "pool_recycle": 3600,
            "future": True
        }
        
        # 如果是SQLite，添加特殊配置
        if settings.database.url.startswith("sqlite"):
            engine_kwargs.update({
                "poolclass": StaticPool,
                "connect_args": {
                    "check_same_thread": False,
                    "timeout": 20
                }
            })
        
        self._engine = create_async_engine(
            settings.database.url,
            **engine_kwargs
        )
        logger.info(f"数据库引擎已创建: {settings.database.url.split('@')[-1] if '@' in settings.database.url else settings.database.url}")
    
    def _create_session_factory(self) -> None:
        """创建会话工厂"""
        self._session_factory = async_sessionmaker(
            bind=self.engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=True,
            autocommit=False
        )
        logger.debug("数据库会话工厂已创建")
    
    async def init_db(self) -> None:
        """初始化数据库表"""
        if self._initialized:
            logger.info("数据库已初始化，跳过")
            return
        
        try:
            async with self.engine.begin() as conn:
                # 创建所有表
                await conn.run_sync(Base.metadata.create_all)
            
            self._initialized = True
            logger.info("数据库表初始化完成")
            
        except Exception as e:
            logger.error(f"数据库初始化失败: {e}")
            raise
    
    async def drop_all_tables(self) -> None:
        """删除所有表（仅用于测试）"""
        try:
            async with self.engine.begin() as conn:
                await conn.run_sync(Base.metadata.drop_all)
            logger.warning("所有数据库表已删除")
        except Exception as e:
            logger.error(f"删除数据库表失败: {e}")
            raise
    
    async def close(self) -> None:
        """关闭数据库连接"""
        if self._engine:
            await self._engine.dispose()
            self._engine = None
            self._session_factory = None
            self._initialized = False
            logger.info("数据库连接已关闭")
    
    @asynccontextmanager
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """
        获取数据库会话（上下文管理器）
        
        使用方式:
        async with database_service.get_session() as session:
            # 使用 session 进行数据库操作
            pass
        """
        async with self.session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()
    
    async def get_session_dependency(self) -> AsyncGenerator[AsyncSession, None]:
        """
        FastAPI依赖注入用的会话获取器
        
        使用方式:
        @router.post("/endpoint")
        async def endpoint(session: AsyncSession = Depends(database_service.get_session_dependency)):
            pass
        """
        async with self.session_factory() as session:
            try:
                yield session
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()
    
    async def execute_raw_sql(self, sql: str, params: Optional[dict] = None) -> any:
        """
        执行原生SQL
        
        Args:
            sql: SQL语句
            params: 参数字典
            
        Returns:
            执行结果
        """
        async with self.get_session() as session:
            result = await session.execute(sql, params or {})
            return result
    
    async def health_check(self) -> dict:
        """
        数据库健康检查
        
        Returns:
            dict: 健康检查结果
        """
        try:
            async with self.get_session() as session:
                await session.execute("SELECT 1")
            
            return {
                "status": "healthy",
                "database": "connected",
                "initialized": self._initialized
            }
        except Exception as e:
            logger.error(f"数据库健康检查失败: {e}")
            return {
                "status": "unhealthy",
                "database": "disconnected",
                "error": str(e),
                "initialized": self._initialized
            }
    
    def get_connection_info(self) -> dict:
        """
        获取连接信息
        
        Returns:
            dict: 连接信息
        """
        if not self._engine:
            return {"status": "not_initialized"}
        
        # 隐藏敏感信息
        url_parts = str(self.engine.url).split('@')
        safe_url = url_parts[-1] if '@' in str(self.engine.url) else str(self.engine.url)
        
        return {
            "driver": self.engine.dialect.name,
            "url": safe_url,
            "pool_size": getattr(self.engine.pool, 'size', None),
            "checked_out": getattr(self.engine.pool, 'checkedout', None),
            "overflow": getattr(self.engine.pool, 'overflow', None),
            "initialized": self._initialized
        }


# 全局数据库服务实例
database_service = DatabaseService()


# 便捷的依赖注入函数
async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI依赖注入用的便捷函数
    
    使用方式:
    from app.services.database_service import get_db_session
    
    @router.post("/endpoint")
    async def endpoint(session: AsyncSession = Depends(get_db_session)):
        pass
    """
    async for session in database_service.get_session_dependency():
        yield session
