"""字典映射服务"""
import re
import json
from datetime import datetime
from typing import Dict, List, Any, Optional, Callable, Union
from copy import deepcopy
from loguru import logger


class DictMapper:
    """字典映射器"""
    
    def __init__(self, config: 'MappingConfig'):
        """
        初始化字典映射器
        
        Args:
            config: 映射配置
        """
        self.config = config
        self.mapping_rules = config.mapping_rules
        self.transformers = config.transformers or {}
        self.validators = config.validators or {}
        
        # 统计信息
        self.mapped_count = 0
        self.failed_count = 0
        
        logger.info(f"字典映射器初始化完成 - 规则数量: {len(self.mapping_rules)}")
    
    def map_dict(self, source_dict: Dict[str, Any]) -> Dict[str, Any]:
        """
        映射字典
        
        Args:
            source_dict: 源字典
            
        Returns:
            Dict[str, Any]: 映射后的字典
        """
        if not isinstance(source_dict, dict):
            raise ValueError("输入必须是字典类型")
        
        try:
            result = {}
            
            # 应用映射规则
            for rule in self.mapping_rules:
                mapped_value = self._apply_mapping_rule(source_dict, rule)
                if mapped_value is not None:
                    result[rule.target_key] = mapped_value
            
            # 应用默认值
            if self.config.default_values:
                for key, value in self.config.default_values.items():
                    if key not in result:
                        result[key] = value
            
            # 应用后处理函数
            if self.config.post_processor:
                result = self.config.post_processor(result, source_dict)
            
            self.mapped_count += 1
            return result
            
        except Exception as e:
            self.failed_count += 1
            logger.error(f"字典映射失败: {e}")
            
            if self.config.error_handler:
                return self.config.error_handler(source_dict, e)
            
            raise
    
    def map_list(self, source_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        映射字典列表
        
        Args:
            source_list: 源字典列表
            
        Returns:
            List[Dict[str, Any]]: 映射后的字典列表
        """
        if not isinstance(source_list, list):
            raise ValueError("输入必须是列表类型")
        
        result = []
        
        for i, source_dict in enumerate(source_list):
            try:
                mapped_dict = self.map_dict(source_dict)
                result.append(mapped_dict)
            except Exception as e:
                logger.error(f"映射列表第{i}项失败: {e}")
                
                if self.config.error_handler:
                    error_result = self.config.error_handler(source_dict, e)
                    if error_result is not None:
                        result.append(error_result)
        
        return result
    
    def _apply_mapping_rule(self, source_dict: Dict[str, Any], rule: 'MappingRule') -> Any:
        """应用单个映射规则"""
        try:
            # 获取源值
            source_value = self._get_source_value(source_dict, rule.source_key)
            
            if source_value is None:
                # 处理空值
                if rule.default_value is not None:
                    return rule.default_value
                elif rule.required:
                    raise ValueError(f"必需字段 {rule.source_key} 为空")
                else:
                    return None
            
            # 应用转换器
            if rule.transformer:
                if rule.transformer in self.transformers:
                    source_value = self.transformers[rule.transformer](source_value)
                else:
                    logger.warning(f"转换器 {rule.transformer} 未找到")
            
            # 应用验证器
            if rule.validator:
                if rule.validator in self.validators:
                    if not self.validators[rule.validator](source_value):
                        raise ValueError(f"字段 {rule.source_key} 验证失败")
                else:
                    logger.warning(f"验证器 {rule.validator} 未找到")
            
            # 应用条件
            if rule.condition:
                if not self._evaluate_condition(source_dict, rule.condition):
                    return rule.default_value if rule.default_value is not None else None
            
            return source_value
            
        except Exception as e:
            logger.error(f"应用映射规则失败 - 规则: {rule.target_key}, 错误: {e}")
            raise
    
    def _get_source_value(self, source_dict: Dict[str, Any], source_key: str) -> Any:
        """获取源值，支持嵌套路径"""
        if '.' not in source_key:
            return source_dict.get(source_key)
        
        # 处理嵌套路径，如 "user.profile.name"
        keys = source_key.split('.')
        current = source_dict
        
        for key in keys:
            if isinstance(current, dict):
                current = current.get(key)
            else:
                return None
            
            if current is None:
                break
        
        return current
    
    def _evaluate_condition(self, source_dict: Dict[str, Any], condition: Dict[str, Any]) -> bool:
        """评估条件"""
        try:
            condition_type = condition.get('type', 'equals')
            field = condition.get('field')
            value = condition.get('value')
            
            if field is None:
                return True
            
            field_value = self._get_source_value(source_dict, field)
            
            if condition_type == 'equals':
                return field_value == value
            elif condition_type == 'not_equals':
                return field_value != value
            elif condition_type == 'contains':
                return value in field_value if field_value else False
            elif condition_type == 'not_contains':
                return value not in field_value if field_value else True
            elif condition_type == 'greater_than':
                return field_value > value if field_value is not None else False
            elif condition_type == 'less_than':
                return field_value < value if field_value is not None else False
            elif condition_type == 'exists':
                return field_value is not None
            elif condition_type == 'not_exists':
                return field_value is None
            elif condition_type == 'regex':
                if isinstance(field_value, str) and isinstance(value, str):
                    return bool(re.match(value, field_value))
                return False
            elif condition_type == 'custom':
                custom_func = condition.get('function')
                if custom_func and callable(custom_func):
                    return custom_func(field_value, source_dict)
                return True
            else:
                return True
                
        except Exception as e:
            logger.error(f"条件评估失败: {e}")
            return False
    
    def add_mapping_rule(self, rule: 'MappingRule'):
        """添加映射规则"""
        self.mapping_rules.append(rule)
        logger.info(f"添加映射规则: {rule.target_key}")
    
    def remove_mapping_rule(self, target_key: str):
        """移除映射规则"""
        self.mapping_rules = [rule for rule in self.mapping_rules if rule.target_key != target_key]
        logger.info(f"移除映射规则: {target_key}")
    
    def get_mapping_rules(self) -> List['MappingRule']:
        """获取所有映射规则"""
        return self.mapping_rules.copy()
    
    def validate_mapping(self, source_dict: Dict[str, Any]) -> Dict[str, Any]:
        """验证映射结果"""
        validation_result = {
            "valid": True,
            "errors": [],
            "warnings": []
        }
        
        try:
            mapped_dict = self.map_dict(source_dict)
            
            # 验证必需字段
            for rule in self.mapping_rules:
                if rule.required and rule.target_key not in mapped_dict:
                    validation_result["errors"].append(f"必需字段 {rule.target_key} 缺失")
                    validation_result["valid"] = False
                
                if rule.validator and rule.target_key in mapped_dict:
                    value = mapped_dict[rule.target_key]
                    if rule.validator in self.validators:
                        if not self.validators[rule.validator](value):
                            validation_result["errors"].append(f"字段 {rule.target_key} 验证失败")
                            validation_result["valid"] = False
            
            return validation_result
            
        except Exception as e:
            validation_result["errors"].append(str(e))
            validation_result["valid"] = False
            return validation_result
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            "mapped_count": self.mapped_count,
            "failed_count": self.failed_count,
            "success_rate": self.mapped_count / (self.mapped_count + self.failed_count) if (self.mapped_count + self.failed_count) > 0 else 0,
            "rules_count": len(self.mapping_rules)
        }


class MappingRule:
    """映射规则"""
    
    def __init__(
        self,
        source_key: str,
        target_key: str,
        transformer: Optional[str] = None,
        validator: Optional[str] = None,
        default_value: Any = None,
        required: bool = False,
        condition: Optional[Dict[str, Any]] = None,
        description: str = ""
    ):
        """
        初始化映射规则
        
        Args:
            source_key: 源字段键
            target_key: 目标字段键
            transformer: 转换器名称
            validator: 验证器名称
            default_value: 默认值
            required: 是否必需
            condition: 条件配置
            description: 规则描述
        """
        self.source_key = source_key
        self.target_key = target_key
        self.transformer = transformer
        self.validator = validator
        self.default_value = default_value
        self.required = required
        self.condition = condition
        self.description = description
    
    def __repr__(self):
        return f"MappingRule({self.source_key} -> {self.target_key})"


class MappingConfig:
    """映射配置"""
    
    def __init__(
        self,
        mapping_rules: List[MappingRule] = None,
        transformers: Dict[str, Callable] = None,
        validators: Dict[str, Callable] = None,
        default_values: Dict[str, Any] = None,
        post_processor: Optional[Callable] = None,
        error_handler: Optional[Callable] = None
    ):
        """
        初始化映射配置
        
        Args:
            mapping_rules: 映射规则列表
            transformers: 转换器字典
            validators: 验证器字典
            default_values: 默认值字典
            post_processor: 后处理函数
            error_handler: 错误处理函数
        """
        self.mapping_rules = mapping_rules or []
        self.transformers = transformers or {}
        self.validators = validators or {}
        self.default_values = default_values or {}
        self.post_processor = post_processor
        self.error_handler = error_handler


# 内置转换器
class BuiltinTransformers:
    """内置转换器"""
    
    @staticmethod
    def to_string(value: Any) -> str:
        """转换为字符串"""
        return str(value) if value is not None else ""
    
    @staticmethod
    def to_int(value: Any) -> int:
        """转换为整数"""
        if value is None:
            return 0
        try:
            return int(float(value))
        except (ValueError, TypeError):
            return 0
    
    @staticmethod
    def to_float(value: Any) -> float:
        """转换为浮点数"""
        if value is None:
            return 0.0
        try:
            return float(value)
        except (ValueError, TypeError):
            return 0.0
    
    @staticmethod
    def to_bool(value: Any) -> bool:
        """转换为布尔值"""
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.lower() in ('true', '1', 'yes', 'on')
        if isinstance(value, (int, float)):
            return value != 0
        return False
    
    @staticmethod
    def to_uppercase(value: Any) -> str:
        """转换为大写"""
        return str(value).upper() if value is not None else ""
    
    @staticmethod
    def to_lowercase(value: Any) -> str:
        """转换为小写"""
        return str(value).lower() if value is not None else ""
    
    @staticmethod
    def trim(value: Any) -> str:
        """去除首尾空格"""
        return str(value).strip() if value is not None else ""
    
    @staticmethod
    def format_timestamp(value: Any, format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
        """格式化时间戳"""
        if value is None:
            return ""
        try:
            if isinstance(value, (int, float)):
                dt = datetime.fromtimestamp(value)
            elif isinstance(value, str):
                dt = datetime.fromisoformat(value.replace('Z', '+00:00'))
            else:
                dt = value
            
            return dt.strftime(format_str)
        except Exception:
            return str(value)
    
    @staticmethod
    def format_address(value: Any) -> str:
        """格式化地址"""
        if not value:
            return ""
        addr = str(value).strip()
        if addr.startswith('0x'):
            return addr.lower()
        return addr
    
    @staticmethod
    def format_amount(value: Any, decimals: int = 18) -> str:
        """格式化金额"""
        if value is None:
            return "0"
        try:
            amount = float(value) / (10 ** decimals)
            return f"{amount:.6f}"
        except Exception:
            return str(value)


# 内置验证器
class BuiltinValidators:
    """内置验证器"""
    
    @staticmethod
    def is_not_empty(value: Any) -> bool:
        """检查是否非空"""
        if value is None:
            return False
        if isinstance(value, str):
            return len(value.strip()) > 0
        if isinstance(value, (list, dict)):
            return len(value) > 0
        return True
    
    @staticmethod
    def is_valid_email(value: Any) -> bool:
        """检查是否为有效邮箱"""
        if not isinstance(value, str):
            return False
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, value))
    
    @staticmethod
    def is_valid_address(value: Any) -> bool:
        """检查是否为有效地址"""
        if not isinstance(value, str):
            return False
        # 检查以太坊地址格式
        pattern = r'^0x[a-fA-F0-9]{40}$'
        return bool(re.match(pattern, value))
    
    @staticmethod
    def is_valid_hash(value: Any) -> bool:
        """检查是否为有效哈希"""
        if not isinstance(value, str):
            return False
        # 检查哈希格式（64位十六进制）
        pattern = r'^0x[a-fA-F0-9]{64}$'
        return bool(re.match(pattern, value))
    
    @staticmethod
    def is_positive_number(value: Any) -> bool:
        """检查是否为正数"""
        try:
            num = float(value)
            return num > 0
        except (ValueError, TypeError):
            return False
    
    @staticmethod
    def is_in_range(value: Any, min_val: float = None, max_val: float = None) -> bool:
        """检查是否在范围内"""
        try:
            num = float(value)
            if min_val is not None and num < min_val:
                return False
            if max_val is not None and num > max_val:
                return False
            return True
        except (ValueError, TypeError):
            return False


# 预定义配置
class CommonMappingConfigs:
    """常用映射配置"""
    
    @staticmethod
    def basic_config() -> MappingConfig:
        """基础配置"""
        transformers = {
            "to_string": BuiltinTransformers.to_string,
            "to_int": BuiltinTransformers.to_int,
            "to_float": BuiltinTransformers.to_float,
            "to_bool": BuiltinTransformers.to_bool,
            "trim": BuiltinTransformers.trim
        }
        
        validators = {
            "is_not_empty": BuiltinValidators.is_not_empty,
            "is_positive_number": BuiltinValidators.is_positive_number
        }
        
        return MappingConfig(
            transformers=transformers,
            validators=validators
        )
    
    @staticmethod
    def blockchain_config() -> MappingConfig:
        """区块链数据配置"""
        transformers = {
            "to_string": BuiltinTransformers.to_string,
            "to_int": BuiltinTransformers.to_int,
            "to_float": BuiltinTransformers.to_float,
            "format_address": BuiltinTransformers.format_address,
            "format_amount": BuiltinTransformers.format_amount,
            "format_timestamp": BuiltinTransformers.format_timestamp,
            "to_lowercase": BuiltinTransformers.to_lowercase
        }
        
        validators = {
            "is_not_empty": BuiltinValidators.is_not_empty,
            "is_valid_address": BuiltinValidators.is_valid_address,
            "is_valid_hash": BuiltinValidators.is_valid_hash,
            "is_positive_number": BuiltinValidators.is_positive_number
        }
        
        return MappingConfig(
            transformers=transformers,
            validators=validators
        )
    
    @staticmethod
    def user_data_config() -> MappingConfig:
        """用户数据配置"""
        transformers = {
            "to_string": BuiltinTransformers.to_string,
            "to_int": BuiltinTransformers.to_int,
            "to_float": BuiltinTransformers.to_float,
            "to_bool": BuiltinTransformers.to_bool,
            "trim": BuiltinTransformers.trim,
            "to_lowercase": BuiltinTransformers.to_lowercase,
            "to_uppercase": BuiltinTransformers.to_uppercase
        }
        
        validators = {
            "is_not_empty": BuiltinValidators.is_not_empty,
            "is_valid_email": BuiltinValidators.is_valid_email,
            "is_positive_number": BuiltinValidators.is_positive_number
        }
        
        return MappingConfig(
            transformers=transformers,
            validators=validators
        ) 