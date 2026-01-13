# scripts/modules/route_detector.py
"""
路线检测器 v3.0（优化版）
主要改进：
1. 放宽长度限制（150 -> 250字符）
2. 减少硬性拒绝规则
3. 优化地点清理逻辑
4. 改进白名单匹配策略
5. 增加容错性
"""

import re
try:
    from scripts.data.location_whitelist import LOCATION_WHITELIST, is_valid_location, clean_location_text
except ImportError:
    from data.location_whitelist import LOCATION_WHITELIST, is_valid_location, clean_location_text


class RouteDetector:
    """
    路线检测器（白名单驱动）
    职责：判断文本是否为路线候选
    """

    def __init__(self):
        # 路线分隔符
        self.separators = ["--", "-", "→", "->", "—", "~", "至", "到"]

        # ⭐ 强拒绝关键词（大幅减少）
        # 只保留明确不可能是路线的关键词
        self.hard_reject_keywords = [
            "费用明细", "报价明细", "货物信息", "搬迁数量",
            "第一批", "第二批", "批次信息", "自建机房",
            "指定地址详情", "物流公司名称"
        ]

        # ⭐ 常见单位（避免误判为型号）
        self.unit_keywords = [
            "KGS", "KG", "CBM", "CM", "MM", "PCS", "CTNS",
            "吨", "千克", "公斤", "立方", "方"
        ]

        # 数字序号模式
        self.index_pattern = re.compile(r"^\d+[\.、)]")
        
        # ⭐ 型号模式（排除单位和货物描述后）
        self.model_pattern = re.compile(
            r"\d+[A-Z]{2,}(?!KGS|KG|CBM|CM|MM|PCS|CTNS)",
            re.IGNORECASE
        )
        
        # 百分比模式
        self.percent_pattern = re.compile(r"\d+\s*%")
        
        # 时间模式
        self.time_pattern = re.compile(r"\d+\s*(天|工作日|小时|分钟)")
        
        # ⭐ 放宽长度限制
        self.max_length = 250  # 150 -> 250

    def detect(self, text: str):
        """
        检测文本是否为路线
        
        Returns:
            {
                "is_route": bool,
                "reason": [str],
                "parts": [str]
            }
        """
        raw = text.strip()
        reasons = []

        # ========== 基础过滤 ==========
        if not raw:
            return self._reject("empty")

        if len(raw) > self.max_length:
            return self._reject("too_long", [f"长度:{len(raw)}"])

        # ⭐ 数字序号（如 "1. xxx"）
        if self.index_pattern.match(raw):
            return self._reject("index_prefix")

        # ========== 必须有分隔符 ==========
        sep = None
        for s in self.separators:
            if s in raw:
                sep = s
                break

        if not sep:
            return self._reject("no_separator")

        parts = [p.strip() for p in raw.split(sep) if p.strip()]
        if len(parts) < 2:
            return self._reject("not_enough_parts", parts)

        # ========== 强业务否决（大幅减少） ==========
        for kw in self.hard_reject_keywords:
            if kw in raw:
                return self._reject(f"business_keyword:{kw}", parts)

        # ⭐ 型号判断（先清理后判断）
        text_without_noise = self._remove_noise_for_model_check(raw)
        if self.model_pattern.search(text_without_noise):
            return self._reject("model_or_code", parts)

        # ⭐ 百分比（放宽：只有纯百分比才拒绝）
        if self.percent_pattern.search(raw) and len(re.findall(r'\d+', raw)) <= 2:
            return self._reject("percent_pattern", parts)

        # ⭐ 时间模式（放宽：只有纯时间才拒绝）
        if self.time_pattern.search(raw) and '工作日' in raw and len(parts) < 3:
            return self._reject("time_pattern", parts)

        # ========== 地点白名单裁决 ==========
        cleaned_parts = []
        for part in parts:
            cleaned = self._clean_location(part)
            if cleaned:
                cleaned_parts.append(cleaned)

        if len(cleaned_parts) < 2:
            return self._reject("not_enough_valid_parts", parts)

        # 首尾必须在白名单
        start = cleaned_parts[0]
        end = cleaned_parts[-1]

        if not self._is_in_whitelist(start):
            return self._reject(f"start_not_whitelisted:{start}", parts)

        if not self._is_in_whitelist(end):
            return self._reject(f"end_not_whitelisted:{end}", parts)

        # ========== ✅ 通过 ==========
        return {
            "is_route": True,
            "reason": ["pass_location_whitelist"],
            "parts": parts,
            "cleaned_parts": cleaned_parts
        }

    def _remove_noise_for_model_check(self, text: str) -> str:
        """
        移除噪声文本，为型号检查做准备
        """
        # 移除单位
        for unit in self.unit_keywords:
            text = text.replace(unit, "")
        
        # 移除常见货物描述
        noise_words = [
            "宣传册", "伴手礼", "货物", "设备", "产品", "样品",
            "服务器", "电视", "空调", "机器", "配件",
            "客户", "提供", "重量", "数量"
        ]
        for word in noise_words:
            text = text.replace(word, "")
        
        return text.strip()

    def _clean_location(self, text: str) -> str:
        """
        清理地点文本
        策略：温和清理，尽量保留信息
        """
        # 使用白名单模块的清理函数
        cleaned = clean_location_text(text)
        
        # 额外清理：移除首尾的特殊字符
        cleaned = cleaned.strip('：:,，。.、 \t\n')
        
        return cleaned

    def _is_in_whitelist(self, location: str) -> bool:
        """
        判断地点是否在白名单中
        支持部分匹配
        """
        return is_valid_location(location)

    def _reject(self, reason, parts=None):
        """构造拒绝结果"""
        return {
            "is_route": False,
            "reason": [reason],
            "parts": parts or []
        }


# ========== 辅助函数 ==========

def quick_detect(text: str) -> bool:
    """快速判断是否为路线（返回布尔值）"""
    detector = RouteDetector()
    result = detector.detect(text)
    return result["is_route"]


def extract_route_parts(text: str) -> list:
    """提取路线各部分"""
    detector = RouteDetector()
    result = detector.detect(text)
    
    if result["is_route"]:
        return result.get("cleaned_parts", result.get("parts", []))
    
    return []


__all__ = ['RouteDetector', 'quick_detect', 'extract_route_parts']