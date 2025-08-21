"""配置管理模块"""
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings


class DatabaseSettings(BaseSettings):
    """数据库配置"""
    host: str = Field(default="35.215.85.104", alias="MYSQL_HOST")
    port: int = Field(default=13306, alias="MYSQL_PORT")
    user: str = Field(default="chaindata_parser", alias="MYSQL_USER")
    password: str = Field(default="2esd134jnfdsdfr3r", alias="MYSQL_PASSWORD")
    database: str = Field(default="tp_chaindata_parser", alias="MYSQL_DATABASE")

    @property
    def url(self) -> str:
        return f"mysql+aiomysql://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"


class RedisSettings(BaseSettings):
    """Redis配置"""
    host: str = Field(default="localhost", alias="REDIS_HOST")
    port: int = Field(default=6379, alias="REDIS_PORT")
    password: Optional[str] = Field(default=None, alias="REDIS_PASSWORD")
    db: int = Field(default=0)


class BlockchainSettings(BaseSettings):
    """区块链配置"""
    eth_rpc_url: str = Field(default="https://mainnet.infura.io/v3/c3fbac6d01a74109b3c5088d657f528e",
                             alias="ETH_RPC_URL")
    bsc_rpc_url: str = Field(default="https://bsc-dataseed.binance.org/", alias="BSC_RPC_URL")
    polygon_rpc_url: str = Field(default="https://polygon-rpc.com/", alias="POLYGON_RPC_URL")
    solana_rpc_url: str = Field(default="https://api.mainnet-beta.solana.com", alias="SOLANA_RPC_URL")


class APISettings(BaseSettings):
    """API配置"""
    host: str = Field(default="0.0.0.0", alias="API_HOST")
    port: int = Field(default=8001, alias="API_PORT")
    debug: bool = Field(default=False, alias="API_DEBUG")
    reload: bool = Field(default=False, alias="API_RELOAD")


class SecuritySettings(BaseSettings):
    """安全配置"""
    secret_key: str = Field(default="your-secret-key-here", alias="SECRET_KEY")
    access_token_expire_minutes: int = Field(default=30, alias="ACCESS_TOKEN_EXPIRE_MINUTES")


class LogSettings(BaseSettings):
    """日志配置"""
    level: str = Field(default="INFO", alias="LOG_LEVEL")
    file: str = Field(default="logs/app.log", alias="LOG_FILE")


class Settings(BaseSettings):
    """应用配置"""
    database: DatabaseSettings = DatabaseSettings()
    redis: RedisSettings = RedisSettings()
    blockchain: BlockchainSettings = BlockchainSettings()
    api: APISettings = APISettings()
    security: SecuritySettings = SecuritySettings()
    log: LogSettings = LogSettings()

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore"  # 忽略额外字段
    }


# 全局配置实例
settings = Settings()
