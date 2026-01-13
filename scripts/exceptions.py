# scripts/exceptions.py
"""
统一异常处理系统
定义项目中所有自定义异常类
"""


class ParserException(Exception):
    """解析器基础异常"""
    def __init__(self, message: str, original_exception: Exception = None):
        super().__init__(message)
        self.original_exception = original_exception


class FileReadException(ParserException):
    """文件读取异常"""
    pass


class ExcelParseException(ParserException):
    """Excel解析异常"""
    pass


class RouteParseException(ParserException):
    """路线解析异常"""
    pass


class AgentParseException(ParserException):
    """代理商解析异常"""
    pass


class GoodsParseException(ParserException):
    """货物解析异常"""
    pass


class FeeParseException(ParserException):
    """费用解析异常"""
    pass


class SummaryParseException(ParserException):
    """汇总解析异常"""
    pass


class ValidationException(ParserException):
    """数据验证异常"""
    pass


class ConfigurationException(ParserException):
    """配置异常"""
    pass


class DataFormatException(ParserException):
    """数据格式异常"""
    pass


# 异常处理装饰器
from functools import wraps
import logging


def handle_parser_exception(exception_class=ParserException, default_return=None):
    """
    解析器异常处理装饰器
    
    用法:
    @handle_parser_exception(RouteParseException, default_return=[])
    def parse_route(self, text):
        # 解析逻辑
        pass
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            logger = logging.getLogger(func.__module__)
            try:
                return func(*args, **kwargs)
            except exception_class as e:
                logger.error(f"{func.__name__} 解析失败: {e}")
                return default_return
            except Exception as e:
                logger.error(f"{func.__name__} 发生未预期的错误: {e}", exc_info=True)
                return default_return
        return wrapper
    return decorator