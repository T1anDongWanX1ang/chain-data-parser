"""辅助工具函数"""
import re
from typing import Optional


def format_address(address: str) -> str:
    """格式化区块链地址"""
    if not address:
        return ""
    
    # 移除空格并转换为小写
    formatted = address.strip().lower()
    
    # 确保以太坊地址以0x开头
    if len(formatted) == 40 and not formatted.startswith("0x"):
        formatted = "0x" + formatted
    
    return formatted


def validate_chain_type(chain_type: str) -> bool:
    """验证链类型是否有效"""
    valid_chain_types = ["evm", "sol"]
    return chain_type.lower() in valid_chain_types


def validate_evm_address(address: str) -> bool:
    """验证EVM地址格式"""
    if not address:
        return False
    
    # EVM地址应该是42个字符（包含0x前缀）且只包含十六进制字符
    pattern = r"^0x[a-fA-F0-9]{40}$"
    return bool(re.match(pattern, address))


def validate_solana_address(address: str) -> bool:
    """验证Solana地址格式"""
    if not address:
        return False
    
    # Solana地址通常是32-44个字符的Base58编码
    if len(address) < 32 or len(address) > 44:
        return False
    
    # 简单的Base58字符检查
    base58_chars = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
    return all(c in base58_chars for c in address)


def validate_tx_hash(tx_hash: str, chain_type: str) -> bool:
    """验证交易哈希格式"""
    if not tx_hash or not chain_type:
        return False
    
    if chain_type.lower() == "evm":
        # EVM交易哈希是64个字符的十六进制字符串（可能带0x前缀）
        pattern = r"^(0x)?[a-fA-F0-9]{64}$"
        return bool(re.match(pattern, tx_hash))
    elif chain_type.lower() == "sol":
        # Solana交易签名通常是87-88个字符的Base58编码
        if len(tx_hash) < 87 or len(tx_hash) > 88:
            return False
        base58_chars = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
        return all(c in base58_chars for c in tx_hash)
    
    return False


def format_amount(amount: int, decimals: int = 18) -> float:
    """格式化代币数量（从最小单位转换为标准单位）"""
    return amount / (10 ** decimals)


def to_wei(amount: float, decimals: int = 18) -> int:
    """将标准单位转换为最小单位"""
    return int(amount * (10 ** decimals))


def truncate_string(text: str, max_length: int = 100) -> str:
    """截断字符串"""
    if not text or len(text) <= max_length:
        return text
    return text[:max_length] + "..."


def safe_int(value, default: int = 0) -> int:
    """安全转换为整数"""
    try:
        return int(value)
    except (ValueError, TypeError):
        return default


def safe_float(value, default: float = 0.0) -> float:
    """安全转换为浮点数"""
    try:
        return float(value)
    except (ValueError, TypeError):
        return default