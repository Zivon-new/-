# scripts/logger_config.py
"""
统一日志配置系统
提供项目级别的日志管理
"""

import logging
import os
import sys
from datetime import datetime
from logging.handlers import RotatingFileHandler


class LoggerConfig:
    """日志配置管理器"""
    
    _initialized = False
    
    @classmethod
    def setup(cls, 
              log_dir: str = "logs",
              log_level: str = "INFO",
              console_output: bool = True,
              file_output: bool = True,
              max_bytes: int = 10 * 1024 * 1024,  # 10MB
              backup_count: int = 5):
        """
        设置全局日志配置
        
        Args:
            log_dir: 日志文件目录
            log_level: 日志级别 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            console_output: 是否输出到控制台
            file_output: 是否输出到文件
            max_bytes: 单个日志文件最大大小
            backup_count: 保留的日志文件数量
        """
        if cls._initialized:
            return
        
        # 创建日志目录
        os.makedirs(log_dir, exist_ok=True)
        
        # 配置根日志记录器
        root_logger = logging.getLogger()
        root_logger.setLevel(getattr(logging, log_level.upper()))
        
        # 清除现有处理器
        root_logger.handlers.clear()
        
        # 日志格式
        detailed_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        simple_formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # 控制台输出
        if console_output:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(logging.INFO)
            console_handler.setFormatter(simple_formatter)
            root_logger.addHandler(console_handler)
        
        # 文件输出
        if file_output:
            # 主日志文件（所有级别）
            main_log_file = os.path.join(log_dir, 'parser.log')
            main_file_handler = RotatingFileHandler(
                main_log_file,
                maxBytes=max_bytes,
                backupCount=backup_count,
                encoding='utf-8'
            )
            main_file_handler.setLevel(logging.DEBUG)
            main_file_handler.setFormatter(detailed_formatter)
            root_logger.addHandler(main_file_handler)
            
            # 错误日志文件（ERROR及以上）
            error_log_file = os.path.join(log_dir, 'error.log')
            error_file_handler = RotatingFileHandler(
                error_log_file,
                maxBytes=max_bytes,
                backupCount=backup_count,
                encoding='utf-8'
            )
            error_file_handler.setLevel(logging.ERROR)
            error_file_handler.setFormatter(detailed_formatter)
            root_logger.addHandler(error_file_handler)
        
        cls._initialized = True
        
        # 记录日志系统启动
        logger = logging.getLogger(__name__)
        logger.info("=" * 60)
        logger.info("日志系统已启动")
        logger.info(f"日志级别: {log_level}")
        logger.info(f"日志目录: {os.path.abspath(log_dir)}")
        logger.info("=" * 60)
    
    @classmethod
    def get_logger(cls, name: str) -> logging.Logger:
        """
        获取指定名称的logger
        
        Args:
            name: logger名称，通常使用 __name__
            
        Returns:
            Logger对象
        """
        if not cls._initialized:
            cls.setup()
        
        return logging.getLogger(name)


# 便捷函数
def get_logger(name: str = None) -> logging.Logger:
    """
    获取logger的快捷方式
    
    用法:
        from scripts.logger_config import get_logger
        logger = get_logger(__name__)
    """
    if name is None:
        import inspect
        frame = inspect.currentframe().f_back
        name = frame.f_globals['__name__']
    
    return LoggerConfig.get_logger(name)


# 性能监控装饰器
def log_performance(func):
    """
    记录函数执行时间的装饰器
    """
    from functools import wraps
    import time
    
    @wraps(func)
    def wrapper(*args, **kwargs):
        logger = logging.getLogger(func.__module__)
        start_time = time.time()
        
        try:
            result = func(*args, **kwargs)
            elapsed = time.time() - start_time
            logger.debug(f"{func.__name__} 执行完成，耗时: {elapsed:.3f}秒")
            return result
        except Exception as e:
            elapsed = time.time() - start_time
            logger.error(f"{func.__name__} 执行失败，耗时: {elapsed:.3f}秒，错误: {e}")
            raise
    
    return wrapper