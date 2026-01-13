# scripts/modules/summary_parser.py

import re
from scripts.modules.text_cleaner import normalize_text


class SummaryParser:
    """
    解析汇总信息，对应数据库表：
    - summary (汇总表)
    
    注意：小计、税金、总计等字段由数据库存储过程自动计算
    这里只提取用户手动输入的税率、汇损率等参数
    """

    def __init__(self):
        pass

    def parse(self, lines):
        """
        解析汇总信息
        对应 summary 表字段
        返回: {
            "税率": 13.0,          # 百分比，数据库存储为 decimal(10,4)
            "汇损率": 2.5,         # 百分比
            "汇损": 60.13,         # 如果手动指定了汇损金额
            "不含": "不含保险",     # 不含项目说明
            "备注": None,
            "_raw": "原始文本"
        }
        """
        result = {
            "税率": None,
            "汇损率": None,
            "汇损": None,
            "不含": None,
            "备注": None,
            "_raw": "\n".join(lines)
        }

        full_text = " ".join(lines)

        # 1. 税率识别
        # 支持格式：税率 13%  税率：13  增值税 13%
        tax_patterns = [
            r"税率[:：]?\s*(\d+\.?\d*)\s*%?",
            r"增值税[:：]?\s*(\d+\.?\d*)\s*%?",
            r"税[:：]?\s*(\d+\.?\d*)\s*%"
        ]
        
        for pattern in tax_patterns:
            match = re.search(pattern, full_text)
            if match:
                result["税率"] = float(match.group(1))
                break

        # 2. 汇损率识别
        # 支持格式：汇损率 2.5%  汇损：2.5%
        exchange_rate_patterns = [
            r"汇损率[:：]?\s*(\d+\.?\d*)\s*%?",
            r"汇率损失[:：]?\s*(\d+\.?\d*)\s*%?"
        ]
        
        for pattern in exchange_rate_patterns:
            match = re.search(pattern, full_text)
            if match:
                result["汇损率"] = float(match.group(1))
                break

        # 3. 汇损金额识别（如果手动指定）
        # 支持格式：汇损 60.13元  汇损金额：60.13
        exchange_loss_patterns = [
            r"汇损[:：]?\s*(\d+\.?\d*)\s*元?",
            r"汇损金额[:：]?\s*(\d+\.?\d*)"
        ]
        
        # 只有明确写了"汇损 XX元"才提取，避免和汇损率混淆
        for pattern in exchange_loss_patterns:
            match = re.search(pattern, full_text)
            if match and "率" not in full_text[max(0, match.start()-5):match.start()]:
                result["汇损"] = float(match.group(1))
                break

        # 4. 不含项目识别
        # 支持格式：不含XXX  不含：XXX  注：不含XXX
        exclude_patterns = [
            r"不含[:：]?\s*([^\n。；，]{2,30})",
            r"注[:：]?\s*不含\s*([^\n。；，]{2,30})"
        ]
        
        for pattern in exclude_patterns:
            match = re.search(pattern, full_text)
            if match:
                result["不含"] = match.group(1).strip()
                break

        # 5. 备注信息
        # 识别包含"备注"、"说明"、"注意"等关键词的内容
        remark_keywords = ["备注", "说明", "注意", "提示"]
        for keyword in remark_keywords:
            if keyword in full_text:
                remark_match = re.search(rf"{keyword}[:：]?\s*([^\n]{{0,100}})", full_text)
                if remark_match:
                    result["备注"] = remark_match.group(1).strip()
                    break

        return result

    def is_summary_line(self, text):
        """
        判断是否为汇总相关行
        """
        text = normalize_text(text)
        
        summary_keywords = [
            "小计", "税", "税率", "税金", 
            "汇损", "汇损率", "汇率",
            "总计", "合计", "不含",
            "备注", "说明"
        ]
        
        return any(kw in text for kw in summary_keywords)

    def extract_subtotal(self, text):
        """
        提取小计金额（用于验证，实际由数据库计算）
        """
        match = re.search(r"小计[:：]?\s*(\d+\.?\d*)", text)
        if match:
            return float(match.group(1))
        return None

    def extract_total(self, text):
        """
        提取总计金额（用于验证，实际由数据库计算）
        """
        patterns = [
            r"总计[:：]?\s*(\d+\.?\d*)",
            r"合计[:：]?\s*(\d+\.?\d*)",
            r"总价[:：]?\s*(\d+\.?\d*)"
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return float(match.group(1))
        
        return None