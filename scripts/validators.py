# scripts/validators.py
"""
数据验证系统
使用 Pydantic 进行数据模型验证
"""

from pydantic import BaseModel, Field, validator, field_validator
from typing import Optional, List
from decimal import Decimal


class RouteAgentModel(BaseModel):
    """代理商路线数据模型"""
    代理商: Optional[str] = Field(None, min_length=2, max_length=100)
    运输方式: Optional[str] = Field(None, max_length=20)
    贸易类型: Optional[str] = Field(None, max_length=20)
    代理备注: Optional[str] = Field(None, max_length=500)
    时效: Optional[str] = Field(None, max_length=50)
    时效备注: Optional[str] = Field(None, max_length=200)
    是否赔付: str = Field("0", pattern=r"^[01]$")
    赔付内容: Optional[str] = Field(None, max_length=200)
    
    class Config:
        str_strip_whitespace = True  # 自动去除首尾空格
        
    @field_validator('是否赔付')
    @classmethod
    def validate_compensation(cls, v):
        if v not in ['0', '1']:
            return '0'
        return v


class GoodsDetailModel(BaseModel):
    """货物明细数据模型"""
    货物名称: Optional[str] = Field(None, min_length=1, max_length=100)
    是否新品: bool = False
    货物种类: Optional[str] = Field(None, max_length=50)
    数量: Optional[float] = Field(None, ge=0)
    单价: Optional[float] = Field(None, ge=0)
    币种: str = Field("RMB", max_length=10)
    重量: Optional[float] = Field(None, ge=0)
    备注: Optional[str] = Field(None, max_length=500)
    
    class Config:
        str_strip_whitespace = True
    
    @field_validator('数量', '单价', '重量')
    @classmethod
    def validate_positive(cls, v):
        if v is not None and v < 0:
            raise ValueError('数值不能为负数')
        return v


class GoodsTotalModel(BaseModel):
    """货物汇总数据模型"""
    货物名称: Optional[str] = Field(None, max_length=100)
    实际重量: Optional[float] = Field(None, ge=0)
    货值: Optional[float] = Field(None, ge=0)
    总体积: Optional[str] = Field(None, max_length=50)
    备注: Optional[str] = Field(None, max_length=500)
    
    class Config:
        str_strip_whitespace = True


class FeeItemModel(BaseModel):
    """费用明细数据模型"""
    费用类型: Optional[str] = Field(None, max_length=50)
    单价: Optional[float] = Field(None, ge=0)
    单位: Optional[str] = Field(None, max_length=20)
    数量: Optional[float] = Field(None, ge=0)
    币种: str = Field("RMB", max_length=10)
    备注: Optional[str] = Field(None, max_length=500)
    
    class Config:
        str_strip_whitespace = True


class FeeTotalModel(BaseModel):
    """整单费用数据模型"""
    费用名称: Optional[str] = Field(None, max_length=50)
    原币金额: Optional[float] = Field(None, ge=0)
    币种: str = Field("RMB", max_length=10)
    备注: Optional[str] = Field(None, max_length=500)
    
    class Config:
        str_strip_whitespace = True


class SummaryModel(BaseModel):
    """汇总信息数据模型"""
    税率: Optional[float] = Field(None, ge=0, le=100)
    汇损率: Optional[float] = Field(None, ge=0, le=100)
    汇损: Optional[float] = Field(None, ge=0)
    不含: Optional[str] = Field(None, max_length=500)
    备注: Optional[str] = Field(None, max_length=500)
    
    class Config:
        str_strip_whitespace = True
    
    @field_validator('税率', '汇损率')
    @classmethod
    def validate_percentage(cls, v):
        if v is not None and (v < 0 or v > 100):
            raise ValueError('百分比必须在 0-100 之间')
        return v


# 验证器工具函数
class DataValidator:
    """数据验证工具类"""
    
    @staticmethod
    def validate_route_agent(data: dict) -> tuple[bool, Optional[str], Optional[dict]]:
        """
        验证代理商数据
        
        Returns:
            (是否有效, 错误信息, 验证后的数据)
        """
        try:
            validated = RouteAgentModel(**data)
            return True, None, validated.model_dump()
        except Exception as e:
            return False, str(e), None
    
    @staticmethod
    def validate_goods_detail(data: dict) -> tuple[bool, Optional[str], Optional[dict]]:
        """验证货物明细数据"""
        try:
            validated = GoodsDetailModel(**data)
            return True, None, validated.model_dump()
        except Exception as e:
            return False, str(e), None
    
    @staticmethod
    def validate_goods_total(data: dict) -> tuple[bool, Optional[str], Optional[dict]]:
        """验证货物汇总数据"""
        try:
            validated = GoodsTotalModel(**data)
            return True, None, validated.model_dump()
        except Exception as e:
            return False, str(e), None
    
    @staticmethod
    def validate_fee_item(data: dict) -> tuple[bool, Optional[str], Optional[dict]]:
        """验证费用明细数据"""
        try:
            validated = FeeItemModel(**data)
            return True, None, validated.model_dump()
        except Exception as e:
            return False, str(e), None
    
    @staticmethod
    def validate_fee_total(data: dict) -> tuple[bool, Optional[str], Optional[dict]]:
        """验证整单费用数据"""
        try:
            validated = FeeTotalModel(**data)
            return True, None, validated.model_dump()
        except Exception as e:
            return False, str(e), None
    
    @staticmethod
    def validate_summary(data: dict) -> tuple[bool, Optional[str], Optional[dict]]:
        """验证汇总信息数据"""
        try:
            validated = SummaryModel(**data)
            return True, None, validated.model_dump()
        except Exception as e:
            return False, str(e), None
    
    @staticmethod
    def validate_batch(data_list: List[dict], model_class) -> tuple[List[dict], List[str]]:
        """
        批量验证数据
        
        Returns:
            (有效数据列表, 错误信息列表)
        """
        valid_data = []
        errors = []
        
        for i, data in enumerate(data_list):
            try:
                validated = model_class(**data)
                valid_data.append(validated.model_dump())
            except Exception as e:
                errors.append(f"第 {i+1} 条数据验证失败: {e}")
        
        return valid_data, errors