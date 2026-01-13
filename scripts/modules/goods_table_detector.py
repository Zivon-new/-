"""
货物表格识别器
用于识别和解析Excel中的货物表格（简单和复杂两种）
"""

import re
from typing import Dict, List, Optional, Tuple


class GoodsTableDetector:
    """货物表格检测器"""
    
    def __init__(self):
        """初始化检测器"""
        
        # 货物表格的标志关键词
        self.goods_keywords = [
            '货物', '物流地址', '新/旧', '货物种类', '型号', '规格',
            '数量', '单价', '总价', '重量', '体积', '件', '台'
        ]
        
        # 简单表格的模式（只有名称+尺寸/规格+重量）
        self.simple_patterns = [
            # 展示柜    尺寸    重量
            r'^[\u4e00-\u9fa5\w\s]+\s+[\d\*x×]+\s+[\d\.]+',
            # 粮食标本:   规格    数量
            r'^[\u4e00-\u9fa5]+[:：]\s+[\d\.\*x×]+\s+[\d\.]+',
        ]
        
        # 复杂表格的标志（有多列详细信息）
        self.complex_indicators = [
            '物流地址', '新/旧', '货物种类', '型号', '单价', '总价', 
            'CE88', 'Nokia', 'Dell', 'QSFP', 'PowerEdge'
        ]
    
    def detect_goods_table(self, sheet_rows: List[List], sheet_name: str = None) -> Optional[Dict]:
        """
        检测sheet中是否有货物表格
        
        Args:
            sheet_rows: sheet的所有行
            sheet_name: sheet名称
        
        Returns:
            Dict: {
                "table_type": "simple" | "complex" | None,
                "start_row": int,
                "end_row": int,
                "goods_list": List[Dict]
            }
        """
        # 1. 先尝试检测复杂表格（优先）
        complex_table = self._detect_complex_table(sheet_rows)
        if complex_table:
            return complex_table
        
        # 2. 再检测简单表格
        simple_table = self._detect_simple_table(sheet_rows)
        if simple_table:
            return simple_table
        
        return None
    
    def _detect_complex_table(self, sheet_rows: List[List]) -> Optional[Dict]:
        """
        检测复杂货物表格（有物流地址、新/旧、货物种类等多列）
        
        Returns:
            Dict: {
                "table_type": "complex",
                "start_row": int,
                "end_row": int,
                "headers": List[str],
                "goods_list": List[Dict]
            }
        """
        for row_idx, row in enumerate(sheet_rows):
            if not row or len(row) < 4:
                continue
            
            row_text = ' '.join([str(cell) for cell in row if cell is not None])
            
            # 检查是否包含复杂表格的标志
            has_complex_indicator = any(indicator in row_text for indicator in self.complex_indicators)
            
            # 或者检查是否有典型的复杂表格模式（多列且包含新/旧、型号等）
            has_pattern = False
            if len(row) >= 5:
                # 检查是否有"新"或"旧"在某一列
                for cell in row[1:4]:
                    if cell and str(cell).strip() in ['新', '旧']:
                        has_pattern = True
                        break
            
            if has_complex_indicator or has_pattern:
                # 找到表格起始行，解析表格
                table_info = self._parse_complex_table(sheet_rows, row_idx)
                if table_info:
                    return table_info
        
        return None
    
    def _detect_simple_table(self, sheet_rows: List[List]) -> Optional[Dict]:
        """
        检测简单货物表格（只有货物名称、规格、重量等）
        
        例如：
        2件展示柜      210*130*100        910
        粮食标本:      3.68*3.68*3.68mm   5
        电子屏:        61x35x1mm          10
        酿酒陶坛       25*15*6 mm         5
        
        Returns:
            Dict: {
                "table_type": "simple",
                "start_row": int,
                "end_row": int,
                "goods_list": List[Dict]
            }
        """
        goods_list = []
        start_row = None
        end_row = None
        
        # ⭐ 过滤关键词 - 这些行不应该被识别为货物
        filter_keywords = [
            '小计', '总计', '合计', '税率', '税金', '汇损', '不含',
            '实报实销', '注：', '备注', '最低收费', 'local', '报关费',
            '按照', '请贴好', '标签', '卸货', '等有了', '最终'
        ]
        
        for row_idx, row in enumerate(sheet_rows):
            if not row or len(row) < 2:
                continue
            
            # 转换为字符串
            col0 = str(row[0]) if row[0] else ""
            col1 = str(row[1]) if len(row) > 1 and row[1] else ""
            col2 = str(row[2]) if len(row) > 2 and row[2] else ""
            
            # ⭐ 过滤汇总行和备注行
            row_text = col0 + ' ' + col1 + ' ' + col2
            if any(keyword in row_text for keyword in filter_keywords):
                continue
            
            # 检查是否是货物行
            is_goods_row = False
            
            # 模式1: 货物名称 + 规格/尺寸 + 重量/数量
            # 例如: "2件展示柜", "210*130*100", "910"
            if col0 and col1 and col2:
                # col0是中文或包含"件"、"台"等
                if re.search(r'[\u4e00-\u9fa5]', col0) or any(unit in col0 for unit in ['件', '台', '个', '盒', '箱']):
                    # col1是尺寸规格（含*、x、×、mm等）
                    if re.search(r'[\d\.]+[\*x×]', col1) or 'mm' in col1 or 'cm' in col1:
                        # col2是数字
                        if re.search(r'^\d+\.?\d*$', col2):
                            is_goods_row = True
            
            # 模式2: 货物名称: + 规格 + 数量
            # 例如: "粮食标本:", "3.68*3.68*3.68mm", "5"
            if col0 and ('：' in col0 or ':' in col0):
                if col1 and col2:
                    if re.search(r'\d', col1) and re.search(r'^\d+\.?\d*$', col2):
                        is_goods_row = True
            
            if is_goods_row:
                if start_row is None:
                    start_row = row_idx
                end_row = row_idx
                
                # 提取货物信息
                goods_name = col0.rstrip('：:').strip()
                spec = col1.strip()
                
                # 尝试提取重量/数量
                try:
                    weight = float(col2)
                except:
                    weight = 0.0
                
                goods_list.append({
                    "货物名称": goods_name,
                    "规格": spec,
                    "重量": weight,
                    "row_index": row_idx
                })
        
        if goods_list:
            return {
                "table_type": "simple",
                "start_row": start_row,
                "end_row": end_row,
                "goods_list": goods_list
            }
        
        return None
    
    def _parse_complex_table(self, sheet_rows: List[List], start_idx: int) -> Optional[Dict]:
        """
        解析复杂货物表格
        
        返回格式：
        {
            "table_type": "complex",
            "start_row": int,
            "end_row": int,
            "headers": List[str],
            "goods_list": List[Dict]
        }
        """
        # 当前行就是第一行数据（可能包含标题信息）
        current_row = sheet_rows[start_idx]
        
        # 尝试识别列的含义
        # 通常格式：物流地址 | 机房名 | 新/旧 | 货物种类 | 型号 | 数量 | 单价 | 总价
        
        # 简化处理：直接将当前行及后续行作为数据行
        goods_list = []
        
        for row_idx in range(start_idx, min(start_idx + 20, len(sheet_rows))):
            row = sheet_rows[row_idx]
            
            if not row or len(row) < 4:
                break
            
            # 检查是否有"新"或"旧"标志（表示是货物行）
            has_goods_indicator = False
            new_old_col = None
            
            for col_idx, cell in enumerate(row):
                if cell and str(cell).strip() in ['新', '旧']:
                    has_goods_indicator = True
                    new_old_col = col_idx
                    break
            
            if has_goods_indicator and new_old_col is not None:
                # 解析货物信息
                goods_dict = {}
                
                # 根据列位置提取信息
                if len(row) > new_old_col + 1:
                    goods_dict["新/旧"] = str(row[new_old_col]).strip()
                    
                    # 货物种类（new_old后一列）
                    if len(row) > new_old_col + 1 and row[new_old_col + 1]:
                        goods_dict["货物种类"] = str(row[new_old_col + 1]).strip()
                    
                    # 型号（new_old后两列）
                    if len(row) > new_old_col + 2 and row[new_old_col + 2]:
                        goods_dict["型号"] = str(row[new_old_col + 2]).strip()
                    
                    # 数量（new_old后三列）
                    if len(row) > new_old_col + 3 and row[new_old_col + 3]:
                        try:
                            goods_dict["数量"] = float(row[new_old_col + 3])
                        except:
                            goods_dict["数量"] = str(row[new_old_col + 3]).strip()
                    
                    # 单价（new_old后四列）
                    if len(row) > new_old_col + 4 and row[new_old_col + 4]:
                        try:
                            goods_dict["单价"] = float(row[new_old_col + 4])
                        except:
                            goods_dict["单价"] = str(row[new_old_col + 4]).strip()
                    
                    # 物流地址（通常在第一列或第二列）
                    if new_old_col >= 2 and row[1]:
                        goods_dict["物流地址"] = str(row[1]).strip()
                    elif new_old_col >= 1 and row[0]:
                        goods_dict["物流地址"] = str(row[0]).strip()
                    
                    goods_dict["row_index"] = row_idx
                    goods_list.append(goods_dict)
        
        if goods_list:
            return {
                "table_type": "complex",
                "start_row": start_idx,
                "end_row": start_idx + len(goods_list) - 1,
                "headers": ["物流地址", "新/旧", "货物种类", "型号", "数量", "单价"],
                "goods_list": goods_list
            }
        
        return None


def test_detector():
    """测试检测器"""
    detector = GoodsTableDetector()
    
    print("=" * 70)
    print("测试1: 简单货物表格（国内-澳门）")
    print("-" * 70)
    
    rows1 = [
        ['国内-澳门', '', '', ''],
        ['2件展示柜', '210*130*100', '910', ''],
        ['粮食标本：', '3.68*3.68*3.68mm', '5', '预估'],
        ['电子屏：', '61x35x1mm', '10', '预估'],
        ['酿酒陶坛', '25*15*6 mm', '5', '预估'],
        ['总重量：', '', '930', ''],
    ]
    
    result1 = detector.detect_goods_table(rows1, "国内-澳门")
    if result1:
        print(f"表格类型: {result1['table_type']}")
        print(f"起始行: {result1['start_row']}, 结束行: {result1['end_row']}")
        print(f"货物数量: {len(result1['goods_list'])}")
        for goods in result1['goods_list']:
            print(f"  - {goods['货物名称']}: {goods['规格']}, {goods['重量']}kg")
    else:
        print("未检测到表格")
    
    print()
    print("=" * 70)
    print("测试2: 复杂货物表格（新加坡）")
    print("-" * 70)
    
    rows2 = [
        ['物流指定地址', '新加坡GS机房', '新', '网络设备', 'Nokia 7750-SR-1', '2', '132631', '=G2*F2'],
        ['', '', '新', '网络设备', 'OTNS8600-DCI8', '4', '2500', '=G3*F3'],
        ['', '', '新', '网络设备', 'OTMT2光转换单元', '8', '37000', '=G4*F4'],
    ]
    
    result2 = detector.detect_goods_table(rows2, "新加坡")
    if result2:
        print(f"表格类型: {result2['table_type']}")
        print(f"起始行: {result2['start_row']}, 结束行: {result2['end_row']}")
        print(f"货物数量: {len(result2['goods_list'])}")
        for goods in result2['goods_list']:
            print(f"  - {goods}")
    else:
        print("未检测到表格")


if __name__ == "__main__":
    test_detector()