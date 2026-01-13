# scripts/modules/goods_parser.py
"""
货物信息解析器（重构版）
- 添加完整的异常处理
- 集成日志系统
- 优化正则表达式性能
- 数据验证
"""

import re
from typing import Dict, List, Optional, Tuple
from scripts.logger_config import get_logger
from scripts.exceptions import GoodsParseException, handle_parser_exception
from scripts.utils import TextUtils, CurrencyUtils, ValidationUtils, ParseUtils
from scripts.validators import DataValidator, GoodsDetailModel, GoodsTotalModel


class GoodsParser:
    """
    解析货物信息
    对应数据库表：
    - goods_details (货物明细)
    - goods_total (货物汇总)
    """
    
    def __init__(self):
        self.logger = get_logger(__name__)
        
        # 货物名称关键词
        self.goods_keywords = [
            "服务器", "电视", "空调", "设备", "机器", "产品",
            "样品", "货物", "物品", "柜", "宣传册", "伴手礼",
            "电脑", "手机", "家具", "配件", "零件"
        ]
        
        # 单位关键词（从配置导入）
        self.detail_units = ["台", "件", "个", "pcs", "套", "只", "箱", "ctns"]
        self.total_units = ["kg", "吨", "cbm", "方", "立方"]
        
        # 新旧关键词
        self.newness_keywords = {
            "新": ["新", "新品", "品牌新", "全新"],
            "旧": ["旧", "二手", "used", "旧货"]
        }
        
        # 预编译正则表达式（性能优化）
        self._compile_patterns()
        
        self.logger.debug("GoodsParser 初始化完成")
    
    def _compile_patterns(self):
        """预编译所有正则表达式"""
        # 数量模式：数字 + 单位
        detail_units_pattern = "|".join(self.detail_units)
        self.quantity_pattern = re.compile(
            rf"(\d+\.?\d*)\s*({detail_units_pattern})",
            re.IGNORECASE
        )
        
        # 重量模式
        self.weight_pattern = re.compile(r"(\d+\.?\d*)\s*k?g", re.IGNORECASE)
        
        # 价格模式
        self.price_pattern = re.compile(
            r"(\d+\.?\d*)\s*(元|rmb|usd|cny)?[\s/]*",
            re.IGNORECASE
        )
        
        # 体积模式
        total_units_pattern = "|".join(self.total_units)
        self.volume_pattern = re.compile(
            rf"(\d+\.?\d*)\s*({total_units_pattern})",
            re.IGNORECASE
        )
        
        # 货值模式
        self.value_patterns = [
            re.compile(r"货值[:：]?\s*(\d+\.?\d*)"),
            re.compile(r"价值[:：]?\s*(\d+\.?\d*)"),
            re.compile(r"(\d+\.?\d*)\s*(元|rmb|cny)", re.IGNORECASE)
        ]
    
    @handle_parser_exception(GoodsParseException, default_return={"goods_details": [], "goods_total": []})
    def parse_all(self, lines: List[str]) -> Dict[str, List[Dict]]:
        """
        解析所有货物信息
        
        Args:
            lines: 文本行列表
            
        Returns:
            {
                "goods_details": [...],
                "goods_total": [...]
            }
        """
        if not lines:
            self.logger.warning("输入的行列表为空")
            return {"goods_details": [], "goods_total": []}
        
        self.logger.debug(f"开始解析货物信息，共 {len(lines)} 行")
        
        details = []
        total = []
        
        for line in lines:
            try:
                text = TextUtils.normalize_text(line)
                
                if not text:
                    continue
                
                # 判断是明细还是汇总
                if self._is_goods_detail(text):
                    item = self._parse_detail(text)
                    if item:
                        # 验证数据
                        is_valid, error, validated_data = DataValidator.validate_goods_detail(item)
                        if is_valid:
                            details.append(validated_data)
                        else:
                            self.logger.warning(f"货物明细数据验证失败: {error}, 原始数据: {text}")
                
                elif self._is_goods_total(text):
                    item = self._parse_total(text)
                    if item:
                        # 验证数据
                        is_valid, error, validated_data = DataValidator.validate_goods_total(item)
                        if is_valid:
                            total.append(validated_data)
                        else:
                            self.logger.warning(f"货物汇总数据验证失败: {error}, 原始数据: {text}")
            
            except Exception as e:
                self.logger.error(f"解析行失败: {line}, 错误: {e}", exc_info=True)
                continue
        
        self.logger.info(f"货物信息解析完成: 明细 {len(details)} 条, 汇总 {len(total)} 条")
        
        return {
            "goods_details": details,
            "goods_total": total
        }
    
    def _is_goods_detail(self, text: str) -> bool:
        """
        判断是否为货物明细
        特征：货物名称 + 数量 + 单位(台/件/pcs)
        """
        try:
            has_goods_name = any(kw in text for kw in self.goods_keywords)
            has_detail_unit = any(unit in text.lower() for unit in self.detail_units)
            has_number = bool(re.search(r"\d+", text))
            
            return has_goods_name and has_detail_unit and has_number
        except Exception as e:
            self.logger.error(f"判断货物明细失败: {text}, 错误: {e}")
            return False
    
    def _is_goods_total(self, text: str) -> bool:
        """
        判断是否为货物汇总
        特征：总重量/总体积 + 大单位(kg/吨/cbm)
        """
        try:
            has_total_keyword = any(kw in text for kw in ["总", "合计", "共计", "实际"])
            has_total_unit = any(unit in text.lower() for unit in self.total_units)
            has_number = bool(re.search(r"\d+", text))
            
            return has_total_keyword and has_total_unit and has_number
        except Exception as e:
            self.logger.error(f"判断货物汇总失败: {text}, 错误: {e}")
            return False
    
    def _parse_detail(self, text: str) -> Optional[Dict]:
        """
        解析货物明细
        对应 goods_details 表字段
        """
        try:
            result = {
                "货物名称": None,
                "是否新品": False,
                "货物种类": None,
                "数量": None,
                "单价": None,
                "币种": "RMB",
                "重量": None,
                "备注": None,
                "_raw": text
            }
            
            # 1. 货物名称
            for kw in self.goods_keywords:
                if kw in text:
                    result["货物名称"] = kw
                    break
            
            if not result["货物名称"]:
                self.logger.debug(f"未识别到货物名称: {text}")
                return None
            
            # 2. 是否新品
            for key, keywords in self.newness_keywords.items():
                if any(kw in text for kw in keywords):
                    result["是否新品"] = (key == "新")
                    break
            
            # 3. 数量 - 使用预编译的正则
            quantity_match = self.quantity_pattern.search(text)
            if quantity_match:
                result["数量"] = ParseUtils.safe_parse_float(quantity_match.group(1))
            
            # 4. 重量
            weight_match = self.weight_pattern.search(text)
            if weight_match:
                result["重量"] = ParseUtils.safe_parse_float(weight_match.group(1))
            
            # 5. 单价
            price_match = self.price_pattern.search(text)
            if price_match:
                result["单价"] = ParseUtils.safe_parse_float(price_match.group(1))
                if price_match.group(2):
                    currency = CurrencyUtils.detect_currency(price_match.group(2))
                    if currency:
                        result["币种"] = currency
            
            # 6. 币种检测（全局）
            currency = CurrencyUtils.detect_currency(text)
            if currency:
                result["币种"] = currency
            
            return result
        
        except Exception as e:
            self.logger.error(f"解析货物明细失败: {text}, 错误: {e}", exc_info=True)
            return None
    
    def _parse_total(self, text: str) -> Optional[Dict]:
        """
        解析货物汇总
        对应 goods_total 表字段
        """
        try:
            result = {
                "货物名称": None,
                "实际重量": None,
                "货值": None,
                "总体积": None,
                "备注": None,
                "_raw": text
            }
            
            # 1. 货物名称
            for kw in self.goods_keywords:
                if kw in text:
                    result["货物名称"] = kw
                    break
            
            # 如果没有具体名称，使用"整单货物"
            if not result["货物名称"]:
                result["货物名称"] = "整单货物"
            
            # 2. 实际重量
            weight = TextUtils.extract_weight(text)
            if weight:
                result["实际重量"] = weight
            
            # 3. 货值
            for pattern in self.value_patterns:
                match = pattern.search(text)
                if match:
                    result["货值"] = ParseUtils.safe_parse_float(match.group(1))
                    break
            
            # 4. 总体积
            volume = TextUtils.extract_volume(text)
            if volume:
                result["总体积"] = volume
            
            return result
        
        except Exception as e:
            self.logger.error(f"解析货物汇总失败: {text}, 错误: {e}", exc_info=True)
            return None
    
    def parse_details(self, lines: List[str]) -> List[Dict]:
        """仅解析明细（向后兼容）"""
        result = self.parse_all(lines)
        return result["goods_details"]
    
    def parse_total(self, lines: List[str]) -> List[Dict]:
        """仅解析汇总（向后兼容）"""
        result = self.parse_all(lines)
        return result["goods_total"]