# scripts/config.py
"""
配置管理系统（重构版）
分离路径配置和业务规则配置
"""

import os
from pathlib import Path
from typing import Dict, List


class PathConfig:
    """
    路径配置类
    管理所有文件系统相关的路径
    """
    
    # ===============================================
    # 项目根目录
    # ===============================================
    ROOT = Path(__file__).parent.parent.absolute()
    
    # ===============================================
    # 数据目录
    # ===============================================
    DATA_DIR = ROOT / "data"
    RAW_DATA_DIR = DATA_DIR / "raw"          # 原始 Excel
    CLEAN_DATA_DIR = DATA_DIR / "clean"      # 清洗后 JSON
    TEMP_DATA_DIR = DATA_DIR / "temp"        # 临时文件
    
    # ===============================================
    # 日志目录
    # ===============================================
    LOG_DIR = ROOT / "logs"
    
    # ===============================================
    # 配置目录
    # ===============================================
    CONFIG_DIR = ROOT / "config"
    
    @classmethod
    def create_directories(cls):
        """创建所有必需的目录"""
        directories = [
            cls.RAW_DATA_DIR,
            cls.CLEAN_DATA_DIR,
            cls.TEMP_DATA_DIR,
            cls.LOG_DIR,
            cls.CONFIG_DIR
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
    
    @classmethod
    def get_output_path(cls, filename: str) -> Path:
        """获取输出文件的完整路径"""
        return cls.CLEAN_DATA_DIR / filename
    
    @classmethod
    def get_log_path(cls, filename: str) -> Path:
        """获取日志文件的完整路径"""
        return cls.LOG_DIR / filename


class BusinessConfig:
    """
    业务规则配置类
    管理所有业务相关的配置
    """
    
    # ===============================================
    # 币种配置
    # ===============================================
    SUPPORTED_CURRENCIES: List[str] = [
        "CNY", "RMB", "USD", "EUR", "GBP", "JPY", 
        "HKD", "SGD", "MYR", "AUD", "CAD"
    ]
    
    CURRENCY_ALIAS: Dict[str, str] = {
        "¥": "CNY",
        "RMB": "CNY",
        "CNY": "CNY",
        "人民币": "CNY",
        "USD": "USD",
        "美金": "USD",
        "美元": "USD",
        "$": "USD",
        "EUR": "EUR",
        "€": "EUR",
        "欧元": "EUR",
        "GBP": "GBP",
        "£": "GBP",
        "英镑": "GBP",
        "JPY": "JPY",
        "日元": "JPY",
        "HKD": "HKD",
        "港币": "HKD",
        "SGD": "SGD",
        "新币": "SGD",
    }
    
    # ===============================================
    # 运输方式配置
    # ===============================================
    TRANSPORT_KEYWORDS: Dict[str, str] = {
        "海运": "海运",
        "ocean": "海运",
        "sea": "海运",
        "空运": "空运",
        "air": "空运",
        "航空": "空运",
        "陆运": "陆运",
        "land": "陆运",
        "铁路": "铁路",
        "rail": "铁路",
        "快递": "快递",
        "express": "快递",
        "courier": "快递",
    }
    
    # ===============================================
    # 贸易类型配置
    # ===============================================
    TRADE_KEYWORDS: Dict[str, str] = {
        "DDP": "DDP",
        "DAP": "DAP",
        "DDU": "DDU",
        "FOB": "FOB",
        "EXW": "EXW",
        "CIF": "CIF",
        "CFR": "CFR",
        "FCA": "FCA",
        "一般贸易": "一般贸易",
        "专线": "专线",
        "正清": "正清",
        "双清": "双清",
    }
    
    # ===============================================
    # 新旧货物配置
    # ===============================================
    NEWNESS_KEYWORDS: Dict[str, str] = {
        "新": "新",
        "新品": "新",
        "品牌新": "新",
        "全新": "新",
        "旧": "旧",
        "二手": "旧",
        "used": "旧",
        "旧货": "旧",
    }
    
    # ===============================================
    # 单位配置
    # ===============================================
    UNIT_KEYWORDS: Dict[str, List[str]] = {
        "details": ["台", "件", "个", "pcs", "套", "只", "箱", "ctns", "cartons"],
        "total": ["kg", "吨", "cbm", "方", "立方", "m³"],
        "weight": ["kg", "公斤", "吨", "t", "kgs"],
        "volume": ["cbm", "方", "立方", "m³"],
    }
    
    # ===============================================
    # 时效配置
    # ===============================================
    LEADTIME_SEPARATORS: List[str] = ["-", "~", "–", "--", "至", "到"]
    
    # ===============================================
    # 路线分隔符配置
    # ===============================================
    ROUTE_SEPARATORS: List[str] = ["--", "-", "→", "->", "—", "~", "至", "到"]
    
    # ===============================================
    # 费用类型配置
    # ===============================================
    FEE_TYPES: Dict[str, List[str]] = {
        "海运费": ["海运费", "海运", "ocean freight", "sea freight"],
        "空运费": ["空运费", "空运", "air freight"],
        "陆运费": ["陆运费", "陆运", "land freight"],
        "报关费": ["报关", "报关费", "customs clearance"],
        "清关费": ["清关", "清关费", "customs"],
        "仓储费": ["仓储", "仓储费", "仓租", "warehouse"],
        "操作费": ["操作费", "操作", "handling fee"],
        "文件费": ["文件费", "文件", "documentation"],
        "THC": ["thc", "码头", "terminal"],
        "查验费": ["查验", "查验费", "inspection"],
        "派送费": ["派送", "派送费", "delivery"],
        "保险费": ["保险", "保险费", "insurance"],
        "包装费": ["包装", "包装费", "packing"],
        "杂费": ["杂费", "其他费用", "miscellaneous"],
    }
    
    # ===============================================
    # 解析配置
    # ===============================================
    # 最大行长度（超过此长度的行可能不是有效数据）
    MAX_LINE_LENGTH: int = 200
    
    # 最小有效数字（用于过滤噪声数据）
    MIN_VALID_NUMBER: float = 0.01
    
    # 价格范围验证
    MIN_PRICE: float = 0
    MAX_PRICE: float = 1000000  # 单价不超过100万
    
    # 重量范围验证
    MIN_WEIGHT: float = 0.01
    MAX_WEIGHT: float = 100000  # 不超过10万kg
    
    # 百分比范围
    MIN_PERCENTAGE: float = 0
    MAX_PERCENTAGE: float = 100


class Config:
    """
    统一配置入口
    兼容旧代码，同时提供新的配置访问方式
    """
    
    # 向后兼容：保留旧的属性名
    ROOT = str(PathConfig.ROOT)
    RAW_DATA_DIR = str(PathConfig.RAW_DATA_DIR)
    CLEAN_DATA_DIR = str(PathConfig.CLEAN_DATA_DIR)
    LOG_DIR = str(PathConfig.LOG_DIR)
    
    OUTPUT_JSON = str(PathConfig.get_output_path("parsed_result.json"))
    OUTPUT_UNCLASSIFIED = str(PathConfig.get_output_path("unclassified_review.txt"))
    
    # 业务配置
    SUPPORTED_CURRENCIES = BusinessConfig.SUPPORTED_CURRENCIES
    CURRENCY_ALIAS = BusinessConfig.CURRENCY_ALIAS
    TRANSPORT_KEYWORDS = BusinessConfig.TRANSPORT_KEYWORDS
    TRADE_KEYWORDS = BusinessConfig.TRADE_KEYWORDS
    NEWNESS_KEYWORDS = BusinessConfig.NEWNESS_KEYWORDS
    LEADTIME_SEPARATORS = BusinessConfig.LEADTIME_SEPARATORS
    
    @classmethod
    def initialize(cls):
        """初始化配置（创建必需的目录）"""
        PathConfig.create_directories()
    
    @classmethod
    def get_path_config(cls) -> PathConfig:
        """获取路径配置对象"""
        return PathConfig
    
    @classmethod
    def get_business_config(cls) -> BusinessConfig:
        """获取业务配置对象"""
        return BusinessConfig


# 自动初始化
Config.initialize()