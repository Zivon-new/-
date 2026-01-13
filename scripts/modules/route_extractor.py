# scripts/modules/route_extractor.py
"""
路线提取器 v3.1（优化版）
主要改进：
1. 增强地点清理逻辑 - 更彻底地移除业务关键词
2. 优化正则模式匹配
3. 改进fallback策略
"""

import re
from typing import Optional, Tuple
try:
    from scripts.data.location_whitelist import is_valid_location, clean_location_text
except ImportError:
    from data.location_whitelist import is_valid_location, clean_location_text


class RouteExtractor:
    """路线提取器"""
    
    def __init__(self):
        # ⭐ 扩展路线分隔符
        self.route_separators = [
            "→", "->", "--", "—", "－",  # 箭头和长横线
            "-",  # 短横线（需要排除负数和型号）
            "~", "至", "到"  # 中文分隔符
        ]
        
        # 重量模式
        self.weight_pattern = re.compile(
            r'(\d+(?:\.\d+)?)\s*(?:kgs?|KGS?|千克|公斤)',
            re.IGNORECASE
        )
        
        # 体积模式
        self.volume_pattern = re.compile(
            r'(\d+(?:\.\d+)?)\s*(?:cbm|CBM|立方|方)',
            re.IGNORECASE
        )
        
        # 货值模式
        self.value_pattern = re.compile(
            r'(\d+(?:\.\d+)?)\s*(?:元|rmb|RMB|¥|usd|USD|\$)',
            re.IGNORECASE
        )
        
        # ⭐ 路线模式（更灵活）
        self.route_pattern = re.compile(
            r'([\u4e00-\u9fa5a-zA-Z]{2,20})'  # 起点（中英文，2-20字符）
            r'\s*'
            r'(→|->|--?|—|~|至|到)'  # 分隔符
            r'\s*'
            r'([\u4e00-\u9fa5a-zA-Z]{2,20})'  # 终点
            r'(?:'  # 可选的途径地
            r'\s*'
            r'(→|->|--?|—|~|至|到)'
            r'\s*'
            r'([\u4e00-\u9fa5a-zA-Z]{2,20})'
            r')?'
        )
        
        # ⭐ v3.1: 扩展业务关键词列表（用于清理）
        self.business_keywords = [
            # 运输方式
            '海运', '空运', '快递', '铁路', '陆运', '卡车', '快件',
            '航空', '海派', '空派', '铁运',
            # 服务类型
            '专线', '正清', '双清', '包税', '到门', '到港', '预估',
            'DDP', 'DAP', 'DDU', 'FOB', 'CIF',
            # 贸易类型
            '一般贸易', '贸代', '贸易',
            # 业务词汇
            '成本', '询价', '方案', '代理', '过港', '报价', '明细',
            '费用', '汇总', '预算', '核算', '结算', '货交', '货到',
            # 货物描述
            '宣传册', '伴手礼', '货物', '样品', '设备', '产品',
            '客户', '提供', '重量', '数量'
        ]

    def extract_route(self, text: str, fallback_start: str = None) -> dict:
        """
        从文本中提取路线信息
        
        Args:
            text: 原始文本
            fallback_start: 当无法提取起点时的fallback值（如sheet名称）
            
        Returns:
            {
                'origin': str,  # 起点
                'destination': str,  # 终点
                'via': str,  # 途径地（可选）
                'trade_remark': str,  # 贸易备注
                'weight': float,  # 实际重量
                'volume': float,  # 总体积
                'value': float,  # 货值
                '_raw': str  # 原始文本
            }
        """
        result = {
            'origin': None,
            'destination': None,
            'via': None,
            'trade_remark': None,
            'weight': None,
            'volume': None,
            'value': None,
            '_raw': text
        }
        
        if not text:
            return result
        
        # ========== 1. 提取路线地点 ==========
        route_parts = self._extract_route_parts(text)
        
        if route_parts:
            result['origin'] = route_parts.get('origin')
            result['destination'] = route_parts.get('destination')
            result['via'] = route_parts.get('via')
            result['trade_remark'] = route_parts.get('trade_remark')
        
        # ========== 2. Fallback：使用sheet名作为起点 ==========
        if not result['origin'] and fallback_start:
            # 清理fallback_start
            cleaned_start = self._deep_clean_location(fallback_start)
            if is_valid_location(cleaned_start):
                result['origin'] = cleaned_start
        
        # ========== 3. 提取重量、体积、货值 ==========
        result['weight'] = self._extract_weight(text)
        result['volume'] = self._extract_volume(text)
        result['value'] = self._extract_value(text)
        
        return result

    def _extract_route_parts(self, text: str) -> Optional[dict]:
        """
        提取路线各部分
        
        Returns:
            {
                'origin': str,
                'destination': str,
                'via': str,
                'trade_remark': str
            }
        """
        # 尝试正则匹配
        match = self.route_pattern.search(text)
        
        if match:
            # ⭐ v4.0: 修复三地点顺序
            # route_pattern有5个捕获组：
            # group(1)=起点, group(2)=分隔符, group(3)=第二地点, 
            # group(4)=分隔符2(可选), group(5)=第三地点(可选)
            
            origin_raw = match.group(1)
            second_loc = match.group(3)
            third_loc = match.group(5) if match.lastindex >= 5 else None
            
            # ⭐ 关键：如果有3个地点，中间的是途径地，最后的是目的地
            if third_loc:
                # A-B-C: 起始地A，途径地B，目的地C
                via_raw = second_loc
                destination_raw = third_loc
            else:
                # A-B: 起始地A，目的地B
                via_raw = None
                destination_raw = second_loc
            
            # ⭐ v3.1: 深度清理地点
            origin = self._deep_clean_location(origin_raw)
            destination = self._deep_clean_location(destination_raw)
            via = self._deep_clean_location(via_raw) if via_raw else None
            
            # 白名单验证
            if not is_valid_location(origin):
                origin = None
            if not is_valid_location(destination):
                destination = None
            if via and not is_valid_location(via):
                via = None
            
            # 提取贸易备注（路线后的其他信息）
            trade_remark = None
            if match.end() < len(text):
                remaining = text[match.end():].strip()
                if remaining:
                    # 移除重量、体积等数字信息
                    remaining = re.sub(r'\d+(?:\.\d+)?\s*(?:kg|KG|cbm|CBM|元|¥)', '', remaining)
                    remaining = remaining.strip()
                    if remaining:
                        trade_remark = remaining[:100]  # 限制长度
            
            # 至少需要起点和终点
            if origin and destination:
                return {
                    'origin': origin,
                    'destination': destination,
                    'via': via,
                    'trade_remark': trade_remark
                }
        
        # ========== 手动分隔符分割（fallback） ==========
        return self._manual_split_route(text)

    def _manual_split_route(self, text: str) -> Optional[dict]:
        """
        手动分割路线（当正则匹配失败时）
        """
        # 寻找分隔符
        for sep in self.route_separators:
            if sep in text:
                # 分割
                parts = [p.strip() for p in text.split(sep)]
                
                if len(parts) >= 2:
                    # ⭐ v3.1: 深度清理各部分
                    cleaned_parts = [
                        self._deep_clean_location(p) 
                        for p in parts 
                        if p
                    ]
                    
                    # 过滤有效地点
                    valid_parts = [
                        p for p in cleaned_parts 
                        if p and is_valid_location(p)
                    ]
                    
                    if len(valid_parts) >= 2:
                        return {
                            'origin': valid_parts[0],
                            'destination': valid_parts[1],
                            'via': valid_parts[2] if len(valid_parts) > 2 else None,
                            'trade_remark': None
                        }
        
        return None

    def _deep_clean_location(self, location: str) -> str:
        """
        ⭐ v3.1: 深度清理地点文本
        策略：
        1. 使用白名单模块的基础清理
        2. 移除所有业务关键词
        3. 多轮清理直到稳定
        """
        if not location:
            return ""
        
        # 第1轮：使用白名单模块的清理函数
        cleaned = clean_location_text(location)
        
        # 第2轮：移除业务关键词（多次迭代）
        max_iterations = 3
        for _ in range(max_iterations):
            prev = cleaned
            
            for keyword in self.business_keywords:
                if keyword in cleaned:
                    # ⭐ 策略1: 在关键词处截断
                    parts = cleaned.split(keyword)
                    # 选择非空的第一部分，或者第二部分（如果第一部分为空）
                    if parts[0].strip():
                        cleaned = parts[0].strip()
                        break
                    elif len(parts) > 1 and parts[1].strip():
                        cleaned = parts[1].strip()
                        break
            
            # 如果没有变化，停止迭代
            if cleaned == prev:
                break
        
        # 第3轮：移除首尾的特殊字符和空格
        cleaned = cleaned.strip('：:,，。.、 \t\n[]【】()')
        
        # 第4轮：如果清理后为空或太短，尝试提取核心地名
        if not cleaned or len(cleaned) < 2:
            # 尝试从原始文本中提取白名单中的地名
            for wl_location in ['深圳', '上海', '北京', '广州', '香港', '澳门',
                               '新加坡', '印度', '泰国', '越南', '马来西亚', '马来',
                               '菲律宾', '印尼', '雅加达', '胡志明', '柬埔寨',
                               '沙特', '迪拜', '巴基斯坦', '英国', '法国', '德国',
                               '法兰克福', '荷兰', '西班牙', '意大利', '达拉斯',
                               '迈阿密', '圣何塞', '巴西', '巴拿马', '墨西哥',
                               '澳洲', '澳大利亚', '新西兰', '首尔', '日本', '韩国',
                               '柔佛', '国内', '中国']:
                if wl_location in location:
                    cleaned = wl_location
                    break
        
        return cleaned

    def _extract_weight(self, text: str) -> Optional[float]:
        """提取重量"""
        match = self.weight_pattern.search(text)
        if match:
            try:
                return float(match.group(1))
            except (ValueError, AttributeError):
                pass
        return None

    def _extract_volume(self, text: str) -> Optional[float]:
        """提取体积"""
        match = self.volume_pattern.search(text)
        if match:
            try:
                return float(match.group(1))
            except (ValueError, AttributeError):
                pass
        return None

    def _extract_value(self, text: str) -> Optional[float]:
        """提取货值"""
        match = self.value_pattern.search(text)
        if match:
            try:
                return float(match.group(1))
            except (ValueError, AttributeError):
                pass
        return None


# ========== 便捷函数 ==========

def quick_extract_route(text: str, fallback_start: str = None) -> tuple:
    """
    快捷提取路线
    
    Returns:
        (起点, 终点, 途径地)
    """
    extractor = RouteExtractor()
    result = extractor.extract_route(text, fallback_start)
    
    return (
        result.get('origin'),
        result.get('destination'),
        result.get('via')
    )


__all__ = ['RouteExtractor', 'quick_extract_route']