# scripts/modules/route_normalizer.py
"""
路线标准化器 v3.0（优化版）
主要改进：
1. 减少BAD_KEYWORDS（避免误杀）
2. 优化_is_place判断逻辑
3. 放宽长度限制
4. 改进清理策略
"""

import re
try:
    from scripts.data.location_whitelist import is_valid_location
except ImportError:
    from data.location_whitelist import is_valid_location


class RouteNormalizer:
    """
    路线标准化器
    职责：清洗路线各部分，返回有效地点
    """

    def __init__(self):
        # ⭐ 大幅减少BAD_KEYWORDS（只保留明确的业务词汇）
        self.BAD_KEYWORDS = [
            # 费用相关
            "费用", "成本", "价格", "报价", "询价",
            # 保险/税务
            "保险", "税", "税率",
            # 仓储物流服务
            "仓储", "包装", "过港", "派送", "查验", "报关",
            # 明确的非地名词汇
            "如", "可以", "建议", "预计", "不含", "需要",
            "工作日", "客户", "提供", "方案", "明细"
        ]
        
        # ⭐ 放宽长度限制
        self.max_location_length = 20  # 15 -> 20

    def normalize_parts(self, parts: list[str]) -> list[str]:
        """
        清洗并返回所有有效的地点（包括途径地）
        
        Args:
            parts: 原始地点部分列表
            
        Returns:
            清洗后的有效地点列表
        """
        cleaned = []

        for p in parts:
            p = p.strip()

            # ⭐ 1. 清理前缀
            p = self._clean_prefix(p)

            # ⭐ 2. 清理后缀
            p = self._clean_suffix(p)
            
            # ⭐ 3. 清理冒号后的内容
            p = self._clean_colon_content(p)

            # ⭐ 4. 清理空格+关键词
            p = self._clean_space_keywords(p)

            # ⭐ 5. 判断是否为有效地点
            if p and self._is_place(p):
                cleaned.append(p)

        # 至少需要2个地点（起点+终点）
        if len(cleaned) < 2:
            return []

        return cleaned

    def _clean_prefix(self, text: str) -> str:
        """清理前缀"""
        prefixes = ["货交", "从", "自", "按", "由"]
        
        for prefix in prefixes:
            if text.startswith(prefix):
                text = text[len(prefix):].strip()
        
        return text

    def _clean_suffix(self, text: str) -> str:
        """清理后缀业务关键词"""
        # 后缀关键词列表
        suffixes = [
            "专线", "一般贸易", "海运", "空运", "快递", "成本", 
            "询价", "方案", "贸易", "代理", "过港", "贸代",
            "快件", "正清", "双清", "包税", "DDP", "DAP", "DDU"
        ]
        
        for suffix in suffixes:
            # 在后缀关键词处截断
            if suffix in text:
                parts = text.split(suffix)
                text = parts[0].strip()
                break
        
        return text

    def _clean_colon_content(self, text: str) -> str:
        """清理冒号后的内容"""
        if "：" in text or ":" in text:
            text = re.split(r"[：:]", text)[0].strip()
        
        return text

    def _clean_space_keywords(self, text: str) -> str:
        """清理空格+关键词的情况"""
        # 例如："香港 快件" -> "香港"
        space_keywords = [
            "快件", "快递", "海运", "空运", "专线", 
            "正清", "双清", "货物", "宣传册", "伴手礼"
        ]
        
        for keyword in space_keywords:
            pattern = rf"\s+{keyword}.*$"
            text = re.sub(pattern, "", text).strip()
        
        return text

    def _is_place(self, text: str) -> bool:
        """
        判断文本是否为有效地点
        
        策略：
        1. 优先使用白名单验证
        2. 再进行基本规则过滤
        """
        if not text:
            return False

        t = text.strip()

        # ⭐ 优先：白名单验证
        if is_valid_location(t):
            return True

        # ========== 基本规则过滤 ==========
        
        # 1. 换行直接拒绝
        if "\n" in t:
            return False

        # 2. 长度限制
        if len(t) > self.max_location_length:
            return False

        # 3. 明确的货币单位
        if any(currency in t for currency in ["CNY", "USD", "RMB", "EUR", "GBP"]):
            return False

        # 4. 百分比
        if "%" in t:
            return False

        # ⭐ 5. 型号判断（放宽：排除单位后）
        if self._looks_like_model(t):
            return False

        # ⭐ 6. 数字判断（放宽：允许包含数字的地名）
        # 只有纯数字或"数字+非地名特征"才拒绝
        if re.search(r"^\d+$", t):  # 纯数字
            return False
        
        if re.search(r"\d+", t):
            # 有数字，检查是否有地名特征
            location_features = ["港", "市", "省", "国", "洲", "城", 
                               "拉斯", "加坡", "佛", "沙特", "京", "海", "圳"]
            if not any(feat in t for feat in location_features):
                # 可能是重量描述，如 "120KGS"
                if re.search(r"\d+\s*k?g", t, re.IGNORECASE):
                    return False

        # 7. 包含BAD_KEYWORDS
        for kw in self.BAD_KEYWORDS:
            if kw in t:
                return False

        # ========== 通过所有检查 ==========
        return True

    def _looks_like_model(self, text: str) -> bool:
        """判断是否看起来像型号"""
        # 排除常见单位
        units = ["KGS", "KG", "CBM", "CM", "MM", "PCS", "CTNS"]
        for unit in units:
            text = text.replace(unit, "").replace(unit.lower(), "")
        
        # 型号特征：字母+数字混合（如 "AB123"）
        # 但 "马尼拉" "柔佛" 等地名不应被判断为型号
        if re.search(r"[A-Za-z]+\d+|^\d+[A-Za-z]+$", text):
            # 排除已知地名模式
            known_patterns = ["拉", "佛", "尼", "斯"]
            if not any(pat in text for pat in known_patterns):
                return True
        
        return False


# ========== 辅助函数 ==========

def normalize_route(text: str) -> list[str]:
    """
    快捷函数：标准化路线文本
    
    Args:
        text: 原始路线文本（如 "深圳-香港 快递"）
        
    Returns:
        有效地点列表（如 ["深圳", "香港"]）
    """
    # 分隔符
    separators = ["--", "-", "→", "->", "—", "~", "至", "到"]
    
    # 找到分隔符并分割
    parts = []
    for sep in separators:
        if sep in text:
            parts = [p.strip() for p in text.split(sep) if p.strip()]
            break
    
    if not parts:
        return []
    
    # 标准化
    normalizer = RouteNormalizer()
    return normalizer.normalize_parts(parts)


__all__ = ['RouteNormalizer', 'normalize_route']