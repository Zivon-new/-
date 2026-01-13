"""
全Sheet货物信息扫描器
用于从整个sheet中智能提取：
- 实际重量/计费重量
- 总体积
- 货值
- 货物名称
"""

import re
from typing import Dict, List, Optional, Tuple


class SheetGoodsScanner:
    """全Sheet货物信息扫描器"""
    
    def __init__(self):
        """初始化扫描器"""
        
        # 重量模式（支持多种格式）
        self.weight_patterns = [
            # 标准格式：1740kg, 1740KG, 1740KGS
            re.compile(r'(\d+\.?\d*)\s*(?:kg|KG|kgs|KGS|Kg)\b', re.I),
            # 带说明：客户提供重量1740KG, 预估重量150KGS
            re.compile(r'(?:重量|实际重量|散货).*?(\d+\.?\d*)\s*(?:kg|KG)', re.I),
            # 分离格式：重量：1740
            re.compile(r'重量[：:]\s*(\d+\.?\d*)', re.I),
            # ⭐ KG在前，数字在后：重量：散货KG 2600
            re.compile(r'(?:kg|KG|kgs|KGS)\s+(\d+)', re.I),
        ]
        
        # 计费重量模式
        self.billing_weight_patterns = [
            re.compile(r'(?:托盘|计费重量|计费).*?(\d+\.?\d*)\s*(?:kg|KG)', re.I),
            re.compile(r'计费[：:]\s*(\d+\.?\d*)', re.I),
            # ⭐ 托盘KG 3000
            re.compile(r'(?:托盘|计费)\s*(?:kg|KG)?\s+(\d+\.?\d*)', re.I),
        ]
        
        # 体积模式
        self.volume_patterns = [
            # 标准格式：3cbm, 5.46CBM
            re.compile(r'(\d+\.?\d*)\s*(?:cbm|CBM|立方)', re.I),
            # 分离格式：体积：3
            re.compile(r'(?:体积|总体积)[：:]\s*(\d+\.?\d*)', re.I),
        ]
        
        # 货值模式（支持多种格式）
        self.value_patterns = [
            # 明确标注：货值 100000, 客户提供货值 CNY 119,764.00
            re.compile(r'(?:货值|客户提供货值|货物价值).*?(?:CNY|RMB|人民币)?\s*([0-9,]+\.?\d*)', re.I),
            # 大额表示：200万人民币, 100万元
            re.compile(r'(\d+)\s*万\s*(?:元|人民币|RMB)', re.I),
            # 分离格式：货值：100000
            re.compile(r'货值[：:]\s*([0-9,]+\.?\d*)', re.I),
        ]
        
        # 货物名称关键词
        self.goods_keywords = [
            '电池', '设备', '货物', '产品', '伞', '扇', '屏', '柜',
            '服务器', '交换机', '模块', '网线', '板卡', '标本', '陶坛',
            '宣传册', '伴手礼', '展示柜', 'Dell', 'PowerEdge', 'Nokia'
        ]
    
    def scan_sheet(self, sheet_rows: List[List], sheet_name: str = None) -> Dict:
        """
        扫描整个sheet，提取货物信息
        
        Args:
            sheet_rows: sheet的所有行数据
            sheet_name: sheet名称（用于debug）
        
        Returns:
            Dict: {
                "实际重量": float,
                "计费重量": float,
                "总体积": float,
                "货值": float,
                "货物名称": str,
                "_debug": {...}  # 调试信息
            }
        """
        result = {
            "实际重量": None,
            "计费重量": None,
            "总体积": None,
            "货值": None,
            "货物名称": None,
            "_debug": {
                "扫描行数": len(sheet_rows),
                "找到的重量行": [],
                "找到的体积行": [],
                "找到的货值行": []
            }
        }
        
        # 扫描每一行
        for row_idx, row in enumerate(sheet_rows):
            # 将行转换为字符串
            row_text = ' '.join([str(cell) for cell in row if cell is not None and str(cell).strip()])
            
            if not row_text.strip():
                continue
            
            # ⭐ 特殊处理：检查是否有标签在第一列，数据在第二列的情况
            # 例如：['重量：散货KG', '2600', ''] 或 ['托盘KG', '3000', '']
            if len(row) >= 2:
                label = str(row[0]) if row[0] else ""
                value = str(row[1]) if row[1] else ""
                
                # 如果第一列是标签，第二列是数字，组合它们
                if label and value and value.replace('.', '').isdigit():
                    combined_text = f"{label} {value}"
                    # 尝试从组合文本提取
                    weight_info = self._extract_weight_from_text(combined_text, row_idx)
                    if weight_info:
                        if weight_info['type'] == 'billing':
                            if result["计费重量"] is None:
                                result["计费重量"] = weight_info['value']
                                result["_debug"]["找到的重量行"].append(f"行{row_idx+1}(计费,多列): {combined_text}")
                        else:
                            if result["实际重量"] is None:
                                result["实际重量"] = weight_info['value']
                                result["_debug"]["找到的重量行"].append(f"行{row_idx+1}(实际,多列): {combined_text}")
                    
                    # 尝试提取体积
                    volume = self._extract_volume_from_text(combined_text)
                    if volume and result["总体积"] is None:
                        result["总体积"] = volume
                        result["_debug"]["找到的体积行"].append(f"行{row_idx+1}(多列): {combined_text}")
            
            # 1. 提取重量
            weight_info = self._extract_weight_from_text(row_text, row_idx)
            if weight_info:
                if weight_info['type'] == 'billing':
                    if result["计费重量"] is None:
                        result["计费重量"] = weight_info['value']
                        result["_debug"]["找到的重量行"].append(f"行{row_idx+1}(计费): {row_text[:80]}")
                else:
                    if result["实际重量"] is None:
                        result["实际重量"] = weight_info['value']
                        result["_debug"]["找到的重量行"].append(f"行{row_idx+1}(实际): {row_text[:80]}")
            
            # 2. 提取体积
            volume = self._extract_volume_from_text(row_text)
            if volume and result["总体积"] is None:
                result["总体积"] = volume
                result["_debug"]["找到的体积行"].append(f"行{row_idx+1}: {row_text[:80]}")
            
            # 3. 提取货值
            value = self._extract_value_from_text(row_text)
            if value and result["货值"] is None:
                result["货值"] = value
                result["_debug"]["找到的货值行"].append(f"行{row_idx+1}: {row_text[:80]}")
            
            # 4. 提取货物名称
            if result["货物名称"] is None:
                goods_name = self._extract_goods_name_from_text(row_text)
                if goods_name:
                    result["货物名称"] = goods_name
        
        # 如果没有计费重量，使用实际重量
        if result["计费重量"] is None and result["实际重量"] is not None:
            result["计费重量"] = result["实际重量"]
        
        # 如果没有货物名称，使用sheet名或默认值
        if result["货物名称"] is None:
            if sheet_name:
                result["货物名称"] = self._extract_goods_name_from_text(sheet_name) or "混合货物"
            else:
                result["货物名称"] = "混合货物"
        
        return result
    
    def _extract_weight_from_text(self, text: str, row_idx: int) -> Optional[Dict]:
        """
        从文本中提取重量
        
        Returns:
            Dict: {"value": float, "type": "actual"|"billing"} 或 None
        """
        # 优先检查计费重量
        for pattern in self.billing_weight_patterns:
            match = pattern.search(text)
            if match:
                try:
                    weight = float(match.group(1))
                    return {"value": weight, "type": "billing"}
                except (ValueError, IndexError):
                    continue
        
        # 检查实际重量
        for pattern in self.weight_patterns:
            match = pattern.search(text)
            if match:
                try:
                    weight = float(match.group(1))
                    return {"value": weight, "type": "actual"}
                except (ValueError, IndexError):
                    continue
        
        return None
    
    def _extract_volume_from_text(self, text: str) -> Optional[float]:
        """从文本中提取体积"""
        for pattern in self.volume_patterns:
            match = pattern.search(text)
            if match:
                try:
                    return float(match.group(1))
                except (ValueError, IndexError):
                    continue
        return None
    
    def _extract_value_from_text(self, text: str) -> Optional[float]:
        """从文本中提取货值"""
        for pattern in self.value_patterns:
            match = pattern.search(text)
            if match:
                try:
                    value_str = match.group(1).replace(',', '')  # 移除千位分隔符
                    value = float(value_str)
                    
                    # 如果是"万"单位，需要乘以10000
                    if '万' in text:
                        value = value * 10000
                    
                    return value
                except (ValueError, IndexError):
                    continue
        return None
    
    def _extract_goods_name_from_text(self, text: str) -> Optional[str]:
        """从文本中提取货物名称"""
        # ⭐ 过滤汇总行和描述性内容
        filter_keywords = [
            '小计', '总计', '合计', '税率', '税金', '汇损', '不含',
            '实报实销', '注：', '备注', '最低收费', 'local', '报关费',
            '按照', '请贴好', '标签', '卸货', '等有了', '最终', '托盘计算'
        ]
        
        if any(keyword in text for keyword in filter_keywords):
            return None
        
        # ⭐ 过滤纯数字和货币相关文本
        # "10433.89", "10万港币", "US$10,433.89", "CNY 119,764.00"
        currency_pattern = r'^[\d,\.\s]+$|^\d+万|^US\$|^CNY|^RMB|港币|人民币|美元'
        if re.search(currency_pattern, text, re.I):
            return None
        
        # ⭐ 清理路线前缀（如"马尼拉专线"、"国内-西班牙海运专线"）
        cleaned_text = text
        
        # 移除路线前缀模式（增强版）
        route_patterns = [
            r'^[\u4e00-\u9fa5]+-[\u4e00-\u9fa5]+海运专线\s+',  # "国内-西班牙海运专线 "
            r'^[\u4e00-\u9fa5]+-[\u4e00-\u9fa5]+空运专线\s+',  # "香港-新加坡空运专线 "
            r'^[\u4e00-\u9fa5]+-[\u4e00-\u9fa5]+专线\s+',      # "国内-澳门专线 "
            r'^[\u4e00-\u9fa5]+-[\u4e00-\u9fa5]+\s+',          # "国内-西班牙 " "北京-沙特 "
            r'^[\u4e00-\u9fa5]+专线\s+',                       # "马尼拉专线 "
            r'^香港-[\u4e00-\u9fa5]+\s+',                      # "香港-菲律宾 "
        ]
        
        for pattern in route_patterns:
            cleaned_text = re.sub(pattern, '', cleaned_text)
        
        # 查找包含货物关键词的部分
        for keyword in self.goods_keywords:
            if keyword in cleaned_text:
                # 提取包含关键词的短语
                idx = cleaned_text.find(keyword)
                start = max(0, idx - 10)
                end = min(len(cleaned_text), idx + len(keyword) + 30)
                phrase = cleaned_text[start:end].strip()
                
                # ⭐ 清理多余内容
                # 移除"客户提供"、"预估"等前缀
                phrase = re.sub(r'^(客户提供|预估|合计|重量[:：]|体积[:：]|货值[:：])\s*', '', phrase).strip()
                
                # 移除后面的描述性内容
                phrase = re.sub(r'(客户提供|预估|合计|重量|体积|货值).*$', '', phrase).strip()
                
                # 移除重量和体积标注
                phrase = re.sub(r'\d+\.?\d*\s*(?:kg|KG|kgs|KGS|cbm|CBM)', '', phrase).strip()
                
                # ⭐ 移除"//"等格式错误
                phrase = re.sub(r'/+', '', phrase).strip()
                
                # 移除多余空格
                phrase = re.sub(r'\s+', ' ', phrase).strip()
                
                if phrase and len(phrase) >= 2:
                    return phrase[:50]
        
        # 如果没有找到关键词，尝试直接提取（移除路线前缀后）
        if cleaned_text and cleaned_text != text:
            # 移除明显的描述性内容
            cleaned_text = re.sub(r'(客户提供|预估|合计|重量|体积|货值).*$', '', cleaned_text).strip()
            cleaned_text = re.sub(r'\d+\.?\d*\s*(?:kg|KG|kgs|KGS|cbm|CBM)', '', cleaned_text).strip()
            cleaned_text = re.sub(r'/+', '', cleaned_text).strip()
            cleaned_text = re.sub(r'\s+', ' ', cleaned_text).strip()
            
            # ⭐ 再次检查是否是纯数字或货币
            if re.search(currency_pattern, cleaned_text, re.I):
                return None
            
            if cleaned_text and len(cleaned_text) >= 2 and len(cleaned_text) <= 50:
                return cleaned_text
        
        return None


def test_scanner():
    """测试扫描器"""
    scanner = SheetGoodsScanner()
    
    # 测试案例1：国内-西班牙
    print("=" * 70)
    print("测试1: 国内-西班牙海运专线")
    print("-" * 70)
    
    rows1 = [
        ['国内-西班牙海运专线 碱性电池 客户提供重量1740KGS'],
        ['代理', '融迅', '银顺达'],
        ['国内-西班牙海运专线', '货交深圳 3cbm/1740kg\n海运运费CNY18/kg...'],
    ]
    
    result1 = scanner.scan_sheet(rows1, "国内-西班牙")
    print(f"实际重量: {result1['实际重量']}")
    print(f"总体积: {result1['总体积']}")
    print(f"货值: {result1['货值']}")
    print(f"货物名称: {result1['货物名称']}")
    print(f"Debug: {result1['_debug']['找到的体积行']}")
    
    # 测试案例2：国内-新加坡& 英国
    print("\n" + "=" * 70)
    print("测试2: 国内-新加坡& 英国")
    print("-" * 70)
    
    rows2 = [
        ['2件展示柜/5.46cbm/910kg', '', '货值 100000'],
        ['', '', ''],
        ['货交深圳-新加坡：', '', ''],
    ]
    
    result2 = scanner.scan_sheet(rows2, "国内-新加坡")
    print(f"实际重量: {result2['实际重量']}")
    print(f"总体积: {result2['总体积']}")
    print(f"货值: {result2['货值']}")
    print(f"货物名称: {result2['货物名称']}")
    
    # 测试案例3：香港-菲律宾
    print("\n" + "=" * 70)
    print("测试3: 香港-菲律宾")
    print("-" * 70)
    
    rows3 = [
        ['香港-菲律宾马尼拉专线   4台Dell PowerEdge R7625  预估重量150KGS'],
        ['代理', '融迅'],
        ['...'],
        ['...'],
        ['...'],
        ['...'],
        ['...'],
        ['客户提供货值', 'CNY 119,764.00'],
    ]
    
    result3 = scanner.scan_sheet(rows3, "香港-菲律宾")
    print(f"实际重量: {result3['实际重量']}")
    print(f"总体积: {result3['总体积']}")
    print(f"货值: {result3['货值']}")
    print(f"货物名称: {result3['货物名称']}")
    
    # 测试案例4：日本（区分实际重量和计费重量）
    print("\n" + "=" * 70)
    print("测试4: 日本（区分实际重量和计费重量）")
    print("-" * 70)
    
    rows4 = [
        ['深圳-香港-日本', '', '200万人民币'],
        ['一般贸易正清', '', ''],
        ['重量：散货KG', '2600', ''],
        ['托盘KG', '3000', ''],
    ]
    
    result4 = scanner.scan_sheet(rows4, "日本")
    print(f"实际重量: {result4['实际重量']}")
    print(f"计费重量: {result4['计费重量']}")
    print(f"总体积: {result4['总体积']}")
    print(f"货值: {result4['货值']}")
    print(f"货物名称: {result4['货物名称']}")


if __name__ == "__main__":
    test_scanner()  