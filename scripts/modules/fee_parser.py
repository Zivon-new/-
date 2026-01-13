# scripts/modules/fee_parser.py
"""
费用信息解析器（重构版）
- 添加完整的异常处理
- 集成日志系统
- 优化正则表达式性能
- 数据验证
"""

import re
from typing import Dict, List, Optional
from scripts.logger_config import get_logger
from scripts.exceptions import FeeParseException, handle_parser_exception
from scripts.utils import TextUtils, CurrencyUtils, ParseUtils
from scripts.validators import DataValidator


class FeeParser:
    """
    解析费用信息
    对应数据库表：
    - fee_items (费用明细)
    - fee_total (整单费用)
    """
    
    def __init__(self):
        self.logger = get_logger(__name__)
        
        # 费用类型关键词
        self.fee_types = {
            "海运费": ["海运费", "海运", "ocean freight"],
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
        
        # 单位关键词
        self.unit_keywords = ["kg", "cbm", "票", "柜", "单", "次", "人", "天"]
        
        # 预编译正则表达式
        self._compile_patterns()
        
        self.logger.debug("FeeParser 初始化完成")
    
    def _compile_patterns(self):
        """预编译所有正则表达式"""
        # 单价模式：数字/单位
        unit_pattern = "|".join(self.unit_keywords)
        self.unit_price_pattern = re.compile(
            rf"(\d+\.?\d*)\s*/\s*({unit_pattern})",
            re.IGNORECASE
        )
        
        # 金额模式
        self.amount_pattern = re.compile(
            r"(\d+\.?\d*)\s*(元|rmb|usd|cny)?",
            re.IGNORECASE
        )
        
        # 总费用关键词模式
        self.total_keywords_pattern = re.compile(
            r"(总费用|操作费|杂费|合计)",
            re.IGNORECASE
        )
    
    @handle_parser_exception(FeeParseException, default_return={"fee_items": [], "fee_total": []})
    def parse_all(self, lines: List[str]) -> Dict[str, List[Dict]]:
        """
        解析所有费用信息
        
        Args:
            lines: 文本行列表
            
        Returns:
            {
                "fee_items": [...],
                "fee_total": [...]
            }
        """
        if not lines:
            self.logger.warning("输入的行列表为空")
            return {"fee_items": [], "fee_total": []}
        
        self.logger.debug(f"开始解析费用信息，共 {len(lines)} 行")
        
        items = []
        total = []
        
        for line in lines:
            try:
                text = TextUtils.normalize_text(line)
                
                if not text:
                    continue
                
                # 判断是明细还是汇总
                if self._is_fee_item(text):
                    item = self._parse_item(text)
                    if item:
                        # 验证数据
                        is_valid, error, validated_data = DataValidator.validate_fee_item(item)
                        if is_valid:
                            items.append(validated_data)
                        else:
                            self.logger.warning(f"费用明细数据验证失败: {error}, 原始数据: {text}")
                
                elif self._is_fee_total(text):
                    item = self._parse_total(text)
                    if item:
                        # 验证数据
                        is_valid, error, validated_data = DataValidator.validate_fee_total(item)
                        if is_valid:
                            total.append(validated_data)
                        else:
                            self.logger.warning(f"整单费用数据验证失败: {error}, 原始数据: {text}")
            
            except Exception as e:
                self.logger.error(f"解析行失败: {line}, 错误: {e}", exc_info=True)
                continue
        
        self.logger.info(f"费用信息解析完成: 明细 {len(items)} 条, 汇总 {len(total)} 条")
        
        return {
            "fee_items": items,
            "fee_total": total
        }
    
    def _is_fee_item(self, text: str) -> bool:
        """
        判断是否为费用明细
        特征：单价格式 (例如：25/kg, 100/cbm)
        """
        try:
            # 检查是否有 "数字/单位" 格式
            has_unit_price = bool(self.unit_price_pattern.search(text))
            
            # 或者包含费用关键词 + 数字
            has_fee_keyword = any(
                any(kw in text.lower() for kw in keywords)
                for keywords in self.fee_types.values()
            )
            has_number = bool(re.search(r"\d+", text))
            
            return has_unit_price or (has_fee_keyword and has_number)
        
        except Exception as e:
            self.logger.error(f"判断费用明细失败: {text}, 错误: {e}")
            return False
    
    def _is_fee_total(self, text: str) -> bool:
        """
        判断是否为整单费用
        特征：总费用/操作费等 + 整数金额（不带单位）
        """
        try:
            has_total_keyword = bool(self.total_keywords_pattern.search(text))
            has_amount = bool(re.search(r"\d{3,}", text))  # 至少3位数
            no_unit_price = "/" not in text  # 不是单价格式
            
            return has_total_keyword and has_amount and no_unit_price
        
        except Exception as e:
            self.logger.error(f"判断整单费用失败: {text}, 错误: {e}")
            return False
    
    def _parse_item(self, text: str) -> Optional[Dict]:
        """
        解析费用明细
        对应 fee_items 表字段
        """
        try:
            result = {
                "费用类型": None,
                "单价": None,
                "单位": None,
                "数量": None,
                "币种": "RMB",
                "备注": None,
                "_raw": text
            }
            
            # 1. 费用类型识别
            for fee_type, keywords in self.fee_types.items():
                if any(kw in text.lower() for kw in keywords):
                    result["费用类型"] = fee_type
                    break
            
            # 如果没有匹配到，使用原文作为费用类型
            if not result["费用类型"]:
                # 提取中文或英文词组作为费用类型
                type_match = re.search(r"([\u4e00-\u9fa5]+费?|[A-Za-z\s]+)", text)
                if type_match:
                    result["费用类型"] = type_match.group(1).strip()
                else:
                    result["费用类型"] = "其他费用"
            
            # 2. 单价/单位 - 使用预编译的正则
            unit_price_match = self.unit_price_pattern.search(text)
            if unit_price_match:
                result["单价"] = ParseUtils.safe_parse_float(unit_price_match.group(1))
                result["单位"] = unit_price_match.group(2).upper()
            
            # 3. 数量 - 提取独立的数字（如果有单价，则寻找另一个数字作为数量）
            if result["单价"]:
                all_numbers = TextUtils.extract_all_numbers(text)
                if len(all_numbers) > 1:
                    for num in all_numbers:
                        if num != result["单价"]:
                            result["数量"] = num
                            break
            else:
                # 如果没有单价格式，尝试提取整体金额
                amount_match = self.amount_pattern.search(text)
                if amount_match:
                    result["单价"] = ParseUtils.safe_parse_float(amount_match.group(1))
                    result["单位"] = "次"  # 默认单位
                    result["数量"] = 1
            
            # 4. 币种检测
            currency = CurrencyUtils.detect_currency(text)
            if currency:
                result["币种"] = currency
            
            return result if result["单价"] else None
        
        except Exception as e:
            self.logger.error(f"解析费用明细失败: {text}, 错误: {e}", exc_info=True)
            return None
    
    def _parse_total(self, text: str) -> Optional[Dict]:
        """
        解析整单费用
        对应 fee_total 表字段
        """
        try:
            result = {
                "费用名称": None,
                "原币金额": None,
                "币种": "RMB",
                "备注": None,
                "_raw": text
            }
            
            # 1. 费用名称 - 提取费用关键词
            for fee_type, keywords in self.fee_types.items():
                if any(kw in text.lower() for kw in keywords):
                    result["费用名称"] = fee_type
                    break
            
            # 如果没有匹配，提取中文词组
            if not result["费用名称"]:
                name_match = re.search(r"([\u4e00-\u9fa5]+费?)", text)
                if name_match:
                    result["费用名称"] = name_match.group(1)
                else:
                    result["费用名称"] = "其他费用"
            
            # 2. 金额 - 提取数字
            amount = TextUtils.extract_number(text)
            if amount:
                result["原币金额"] = amount
            
            # 3. 币种检测
            currency = CurrencyUtils.detect_currency(text)
            if currency:
                result["币种"] = currency
            
            return result if result["原币金额"] else None
        
        except Exception as e:
            self.logger.error(f"解析整单费用失败: {text}, 错误: {e}", exc_info=True)
            return None
    
    def parse_items(self, lines: List[str]) -> List[Dict]:
        """仅解析明细（向后兼容）"""
        result = self.parse_all(lines)
        return result["fee_items"]
    
    def parse_total(self, lines: List[str]) -> List[Dict]:
        """仅解析汇总（向后兼容）"""
        result = self.parse_all(lines)
        return result["fee_total"]