# scripts/modules/agent_parser.py

import re
from scripts.config import Config
from scripts.modules.text_cleaner import normalize_text


class AgentParser:
    """
    解析代理商信息，对应数据库表：
    - route_agents (代理路线表)
    """

    def __init__(self):
        # 代理商关键词
        self.agent_keywords = [
            "货运", "物流", "国际", "供应链", "代理", "公司", 
            "快递", "速运", "运输", "集团", "有限公司"
        ]
        
        # 运输方式 (从 Config 导入)
        self.transport_keywords = Config.TRANSPORT_KEYWORDS
        
        # 贸易类型 (从 Config 导入)
        self.trade_keywords = Config.TRADE_KEYWORDS
        
        # 时效分隔符
        self.leadtime_separators = Config.LEADTIME_SEPARATORS

    def parse(self, lines):
        """
        解析代理商信息
        对应 route_agents 表字段
        返回: {
            "代理商": "XX货运公司",
            "运输方式": "海运",
            "贸易类型": "DDP",
            "代理备注": None,
            "时效": "5-7天",
            "时效备注": None,
            "是否赔付": "0",
            "赔付内容": None,
            "_raw": "原始文本"
        }
        """
        result = {
            "代理商": None,
            "运输方式": None,
            "贸易类型": None,
            "代理备注": None,
            "时效": None,
            "时效备注": None,
            "是否赔付": "0",
            "赔付内容": None,
            "_raw": "\n".join(lines)
        }

        full_text = " ".join(lines)

        # 1. 代理商识别
        agent_name = self._extract_agent_name(full_text)
        if agent_name:
            result["代理商"] = agent_name

        # 2. 运输方式识别
        for keyword, value in self.transport_keywords.items():
            if keyword in full_text:
                result["运输方式"] = value
                break

        # 3. 贸易类型识别
        for keyword, value in self.trade_keywords.items():
            if keyword.upper() in full_text.upper():
                result["贸易类型"] = value
                break

        # 4. 时效识别
        leadtime = self._extract_leadtime(full_text)
        if leadtime:
            result["时效"] = leadtime

        # 5. 赔付识别
        if any(kw in full_text for kw in ["赔付", "理赔", "保险"]):
            result["是否赔付"] = "1"
            # 提取赔付内容
            compensation_match = re.search(r"赔付[:：]?(.{0,50})", full_text)
            if compensation_match:
                result["赔付内容"] = compensation_match.group(1).strip()

        # 6. 备注信息（如果包含特殊说明）
        if any(kw in full_text for kw in ["备注", "说明", "注意"]):
            remark_match = re.search(r"(备注|说明|注意)[:：]?(.{0,100})", full_text)
            if remark_match:
                result["代理备注"] = remark_match.group(2).strip()

        return result

    def _extract_agent_name(self, text):
        """
        提取代理商名称
        策略：
        1. 查找包含公司关键词的文本
        2. 提取公司名称
        """
        # 模式1：明确的公司名称 "XX货运公司"
        company_patterns = [
            r"([\u4e00-\u9fa5]{2,10}(?:货运|物流|国际|快递|速运|供应链)(?:公司|集团)?)",
            r"([\u4e00-\u9fa5]{2,10}有限公司)",
            r"([A-Z][A-Za-z\s&]{3,20}(?:Logistics|Freight|Express|Shipping))"
        ]
        
        for pattern in company_patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(1).strip()
        
        # 模式2：包含代理关键词的短语
        for keyword in self.agent_keywords:
            if keyword in text:
                # 提取关键词前后的词组
                context_match = re.search(rf"([\u4e00-\u9fa5]{{2,10}}{keyword})", text)
                if context_match:
                    return context_match.group(1).strip()
        
        return None

    def _extract_leadtime(self, text):
        """
        提取时效
        支持格式：
        - 5-7天
        - 3~5工作日
        - 时效：7天
        """
        # 模式1：范围时效 "5-7天"
        range_patterns = [
            r"(\d+\s*[-–~]\s*\d+\s*(?:天|工作日|自然日))",
            r"时效[:：]?\s*(\d+\s*[-–~]\s*\d+\s*(?:天|工作日))"
        ]
        
        for pattern in range_patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(1).strip()
        
        # 模式2：单一时效 "7天"
        single_match = re.search(r"(\d+\s*(?:天|工作日))", text)
        if single_match:
            return single_match.group(1).strip()
        
        return None

    def is_agent_line(self, text):
        """
        判断是否为代理商相关行
        """
        text = normalize_text(text)
        
        # 包含代理商关键词
        has_agent_keyword = any(kw in text for kw in self.agent_keywords)
        
        # 包含运输或贸易关键词
        has_transport = any(kw in text for kw in self.transport_keywords.keys())
        has_trade = any(kw.upper() in text.upper() for kw in self.trade_keywords.keys())
        
        return has_agent_keyword or has_transport or has_trade