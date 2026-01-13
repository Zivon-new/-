# scripts/utils.py
"""
统一工具函数库
整合和优化常用的工具函数
"""

import re
from typing import Optional, List, Pattern
from functools import lru_cache


class TextUtils:
    """文本处理工具类"""
    
    # 预编译正则表达式（性能优化）
    NUMBER_PATTERN: Pattern = re.compile(r"\d+\.?\d*")
    PRICE_PATTERN: Pattern = re.compile(r"(\d+\.?\d*)\s*/\s*(KG|CBM|件|吨|人|天)", re.IGNORECASE)
    CURRENCY_PATTERN: Pattern = re.compile(r"(RMB|USD|CNY|EUR|GBP|JPY)", re.IGNORECASE)
    PERCENTAGE_PATTERN: Pattern = re.compile(r"(\d+\.?\d*)\s*%")
    WEIGHT_PATTERN: Pattern = re.compile(r"(\d+\.?\d*)\s*k?g", re.IGNORECASE)
    VOLUME_PATTERN: Pattern = re.compile(r"(\d+\.?\d*)\s*(cbm|方|立方)", re.IGNORECASE)
    
    @staticmethod
    def normalize_text(text: str) -> str:
        """
        标准化文本
        - 去除首尾空格
        - 统一分隔符
        - 全角转半角
        """
        if text is None:
            return ""
        
        text = str(text).strip()
        
        # 统一分隔符
        text = text.replace("—", "-").replace("–", "-").replace("~", "-")
        
        # 全角转半角
        result = []
        for char in text:
            code = ord(char)
            if 0xFF01 <= code <= 0xFF5E:
                code -= 0xFEE0
            result.append(chr(code))
        
        return "".join(result)
    
    @staticmethod
    def extract_number(text: str) -> Optional[float]:
        """提取第一个数字"""
        if not text:
            return None
        
        match = TextUtils.NUMBER_PATTERN.search(text)
        if match:
            try:
                return float(match.group(0))
            except (ValueError, AttributeError):
                return None
        return None
    
    @staticmethod
    def extract_all_numbers(text: str) -> List[float]:
        """提取所有数字"""
        if not text:
            return []
        
        matches = TextUtils.NUMBER_PATTERN.findall(text)
        numbers = []
        for match in matches:
            try:
                numbers.append(float(match))
            except ValueError:
                continue
        return numbers
    
    @staticmethod
    def extract_percentage(text: str) -> Optional[float]:
        """提取百分比数值"""
        if not text:
            return None
        
        match = TextUtils.PERCENTAGE_PATTERN.search(text)
        if match:
            try:
                return float(match.group(1))
            except (ValueError, AttributeError):
                return None
        return None
    
    @staticmethod
    def extract_weight(text: str) -> Optional[float]:
        """提取重量（统一转换为kg）"""
        if not text:
            return None
        
        match = TextUtils.WEIGHT_PATTERN.search(text)
        if match:
            try:
                weight = float(match.group(1))
                # 如果包含"吨"，转换为kg
                if "吨" in text:
                    weight *= 1000
                return weight
            except (ValueError, AttributeError):
                return None
        return None
    
    @staticmethod
    def extract_volume(text: str) -> Optional[str]:
        """提取体积"""
        if not text:
            return None
        
        match = TextUtils.VOLUME_PATTERN.search(text)
        if match:
            return match.group(0)
        return None
    
    @staticmethod
    def contains_keywords(text: str, keywords: List[str], case_sensitive: bool = False) -> bool:
        """检查文本是否包含任一关键词"""
        if not text or not keywords:
            return False
        
        if not case_sensitive:
            text = text.lower()
            keywords = [kw.lower() for kw in keywords]
        
        return any(kw in text for kw in keywords)
    
    @staticmethod
    def clean_text(text: str, remove_patterns: List[str] = None) -> str:
        """
        清理文本
        
        Args:
            text: 原始文本
            remove_patterns: 需要移除的正则表达式模式列表
        """
        if not text:
            return ""
        
        cleaned = TextUtils.normalize_text(text)
        
        if remove_patterns:
            for pattern in remove_patterns:
                cleaned = re.sub(pattern, "", cleaned)
        
        return cleaned.strip()


class CurrencyUtils:
    """币种处理工具类"""
    
    # 币种映射表（从Config导入，这里作为默认值）
    CURRENCY_ALIAS = {
        "¥": "CNY",
        "RMB": "CNY",
        "CNY": "CNY",
        "USD": "USD",
        "美金": "USD",
        "$": "USD",
        "EUR": "EUR",
        "€": "EUR",
        "欧元": "EUR",
        "GBP": "GBP",
        "£": "GBP",
        "英镑": "GBP",
        "JPY": "JPY",
        "日元": "JPY",
    }
    
    @staticmethod
    @lru_cache(maxsize=256)
    def detect_currency(text: str) -> Optional[str]:
        """
        检测币种
        使用LRU缓存提升性能
        """
        if not text:
            return None
        
        text_upper = text.upper()
        
        for key, value in CurrencyUtils.CURRENCY_ALIAS.items():
            if key.upper() in text_upper:
                return value
        
        return None
    
    @staticmethod
    def extract_currency_and_amount(text: str) -> tuple[Optional[str], Optional[float]]:
        """
        提取币种和金额
        
        Returns:
            (币种, 金额)
        """
        currency = CurrencyUtils.detect_currency(text)
        amount = TextUtils.extract_number(text)
        
        return currency, amount


class ValidationUtils:
    """验证工具类"""
    
    @staticmethod
    def is_valid_price(value: float) -> bool:
        """验证价格是否有效"""
        return value is not None and value >= 0
    
    @staticmethod
    def is_valid_percentage(value: float) -> bool:
        """验证百分比是否有效"""
        return value is not None and 0 <= value <= 100
    
    @staticmethod
    def is_valid_weight(value: float) -> bool:
        """验证重量是否有效"""
        return value is not None and value > 0
    
    @staticmethod
    def is_empty_or_none(value) -> bool:
        """检查值是否为空或None"""
        if value is None:
            return True
        if isinstance(value, str):
            return not value.strip()
        return False


class ParseUtils:
    """解析工具类"""
    
    @staticmethod
    def safe_parse_float(value, default: float = None) -> Optional[float]:
        """安全地解析浮点数"""
        if value is None:
            return default
        
        try:
            return float(value)
        except (ValueError, TypeError):
            return default
    
    @staticmethod
    def safe_parse_int(value, default: int = None) -> Optional[int]:
        """安全地解析整数"""
        if value is None:
            return default
        
        try:
            return int(float(value))
        except (ValueError, TypeError):
            return default
    
    @staticmethod
    def safe_parse_bool(value, default: bool = False) -> bool:
        """安全地解析布尔值"""
        if value is None:
            return default
        
        if isinstance(value, bool):
            return value
        
        if isinstance(value, str):
            return value.lower() in ['true', '1', 'yes', 'y', '是', '真']
        
        try:
            return bool(int(value))
        except (ValueError, TypeError):
            return default


# 导出所有工具类
__all__ = [
    'TextUtils',
    'CurrencyUtils',
    'ValidationUtils',
    'ParseUtils'
]