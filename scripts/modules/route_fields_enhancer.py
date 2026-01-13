"""
路线字段增强器 v2.0
适配新数据库结构
主要修改：
1. 提取交易开始日期、交易结束日期（DATE格式）
2. 体积只提取数字（不带单位）
3. 所有重量字段只提取数字
"""

import re
from datetime import datetime
from typing import Optional, Tuple


class RouteFieldsEnhancer:
    """路线字段增强器 - 补全routes表的字段"""
    
    def __init__(self, default_year: int = None):
        """
        Args:
            default_year: 默认年份，如果文件名中没有年份则使用此值
        """
        self.default_year = default_year or datetime.now().year
        
        # 日期提取模式（6种格式）
        self.date_patterns = [
            # 格式1: 10_20-10_24 或 10-20至10-24
            re.compile(r'(\d{1,2})[-_](\d{1,2})\s*[-至到~]\s*(\d{1,2})[-_](\d{1,2})'),
            
            # 格式2: 2024-10-20至2024-10-24（完整日期，用-分隔）
            re.compile(r'(\d{4})[.](\d{1,2})[.](\d{1,2})\s*[-至到~]\s*(\d{4})[.](\d{1,2})[.](\d{1,2})'),
            
            # ⭐ 格式2b: 2024_10_20-2024_10_24（完整日期，用_分隔）NEW!
            re.compile(r'(\d{4})[_](\d{1,2})[_](\d{1,2})[-~](\d{4})[_](\d{1,2})[_](\d{1,2})'),
            
            # 格式3: 20241020-20241024（8位数字，无分隔符）
            re.compile(r'(\d{4})(\d{2})(\d{2})[-_](\d{4})(\d{2})(\d{2})'),
            
            # 格式4: 10月20日-10月24日（中文格式）
            re.compile(r'(\d{1,2})月(\d{1,2})日\s*[-至到~]\s*(\d{1,2})月(\d{1,2})日'),
            
            # 格式5: 1020-1024（4位数字，简化格式）
            re.compile(r'(?<!\d)(\d{2})(\d{2})[-_](\d{2})(\d{2})(?!\d)'),
        ]
        
        # 体积提取模式（只提取数字）
        self.volume_pattern = re.compile(
            r'(\d+(?:\.\d+)?)\s*(?:cbm|CBM|立方|方|m³|M³)',
            re.IGNORECASE
        )
    
    def extract_transaction_dates(self, filename: str) -> Tuple[Optional[str], Optional[str]]:
        """
        从文件名提取交易日期区间
        
        Args:
            filename: Excel文件名，如 "国际部成本汇总10_20-10_24.xlsx"
        
        Returns:
            (start_date, end_date) 格式为 "YYYY-MM-DD"
            如果提取失败则返回 (None, None)
        
        Examples:
            "10_20-10_24" → ("2024-10-20", "2024-10-24")
            "2024-10-20至2024-10-24" → ("2024-10-20", "2024-10-24")
            "20241020-20241024" → ("2024-10-20", "2024-10-24")
            "10月20日-10月24日" → ("2024-10-20", "2024-10-24")
            "1020-1024" → ("2024-10-20", "2024-10-24")
        """
        if not filename:
            return None, None
        
        # 尝试各种格式
        for pattern in self.date_patterns:
            match = pattern.search(filename)
            if match:
                groups = match.groups()
                
                # 根据不同格式处理
                if len(groups) == 4:
                    # 格式1、4、5: 月日-月日
                    m1, d1, m2, d2 = groups
                    year = self._infer_year(int(m1))
                    start_date = f"{year}-{int(m1):02d}-{int(d1):02d}"
                    end_date = f"{year}-{int(m2):02d}-{int(d2):02d}"
                    
                elif len(groups) == 6:
                    # 格式2: 完整日期
                    y1, m1, d1, y2, m2, d2 = groups
                    start_date = f"{y1}-{int(m1):02d}-{int(d1):02d}"
                    end_date = f"{y2}-{int(m2):02d}-{int(d2):02d}"
                
                else:
                    continue
                
                # 验证日期有效性
                try:
                    datetime.strptime(start_date, '%Y-%m-%d')
                    datetime.strptime(end_date, '%Y-%m-%d')
                    return start_date, end_date
                except ValueError:
                    continue
        
        return None, None
    
    def _infer_year(self, month: int) -> int:
        """
        智能推断年份
        
        规则：
        1. 如果月份 > 当前月份 + 2：使用上一年
        2. 否则：使用当年
        
        Examples:
            当前：2024年1月
            月份10 → 2023年（去年10月）
            月份1 → 2024年（今年1月）
        """
        current = datetime.now()
        current_month = current.month
        
        # 如果文件月份比当前月份大很多，很可能是去年的
        if month > current_month + 2:
            return current.year - 1
        else:
            return current.year
    
    def extract_volume_number(self, text: str) -> Optional[float]:
        """
        提取体积数字（不带单位）
        
        Args:
            text: 包含体积信息的文本
        
        Returns:
            体积数字（float），如果未找到则返回None
        
        Examples:
            "120CBM" → 120.0
            "5.5立方" → 5.5
            "100 cbm" → 100.0
        """
        if not text:
            return None
        
        match = self.volume_pattern.search(text)
        if match:
            try:
                return float(match.group(1))
            except (ValueError, IndexError):
                return None
        
        return None
    
    def enhance_route(self, route: dict, filename: str = None, route_text: str = None) -> dict:
        """
        增强单个route字典
        
        Args:
            route: route字典（由RouteExtractor返回）
            filename: Excel文件名
            route_text: 路线原始文本（用于提取体积）
        
        Returns:
            增强后的route字典
        """
        # 1. 提取交易日期
        if filename:
            start_date, end_date = self.extract_transaction_dates(filename)
            route['交易开始日期'] = start_date
            route['交易结束日期'] = end_date
        
        # 2. 提取体积数字（如果route_text有提供）
        if route_text and 'volume' in route and route['volume'] is None:
            volume = self.extract_volume_number(route_text)
            if volume:
                route['volume'] = volume
        
        return route
    
    def batch_enhance_routes(self, routes: list, filename: str = None) -> list:
        """
        批量增强routes
        
        Args:
            routes: route字典列表
            filename: Excel文件名
        
        Returns:
            增强后的routes列表
        """
        enhanced = []
        for route in routes:
            enhanced_route = self.enhance_route(route, filename)
            enhanced.append(enhanced_route)
        
        return enhanced


# ========== 测试代码 ==========
if __name__ == "__main__":
    enhancer = RouteFieldsEnhancer()
    
    # 测试1: 日期提取
    print("=" * 60)
    print("测试1: 交易日期提取")
    print("=" * 60)
    
    test_filenames = [
        "国际部成本汇总10_20-10_24.xlsx",
        "报价单2024-10-20至2024-10-24.xlsx",
        "成本20241020-20241024.xlsx",
        "汇总10月20日-10月24日.xlsx",
        "报价1020-1024.xlsx",
    ]
    
    for filename in test_filenames:
        start, end = enhancer.extract_transaction_dates(filename)
        print(f"文件名: {filename}")
        print(f"  → 开始: {start}, 结束: {end}")
        print()
    
    # 测试2: 体积提取
    print("=" * 60)
    print("测试2: 体积数字提取（不带单位）")
    print("=" * 60)
    
    test_texts = [
        "深圳-香港 120CBM",
        "上海-东京 5.5立方",
        "总体积：100 cbm",
        "体积80方",
        "50m³货物",
    ]
    
    for text in test_texts:
        volume = enhancer.extract_volume_number(text)
        print(f"文本: {text}")
        print(f"  → 体积: {volume}")
        print()
    
    # 测试3: Route增强
    print("=" * 60)
    print("测试3: Route字典增强")
    print("=" * 60)
    
    test_route = {
        'origin': '深圳',
        'destination': '香港',
        'via': None,
        'weight': 1740.0,
        'volume': None,
        'value': 50000.0
    }
    
    filename = "国际部成本汇总10_20-10_24.xlsx"
    route_text = "深圳-香港 1740kg 120CBM"
    
    enhanced = enhancer.enhance_route(test_route, filename, route_text)
    
    print(f"原始route: {test_route}")
    print(f"增强后: {enhanced}")
    print()
    
    print("✅ 所有测试完成！")