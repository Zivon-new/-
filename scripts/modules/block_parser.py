# scripts/modules/block_parser.py

import re  # ✅ 添加 re 模块
from scripts.modules.route_detector import RouteDetector
from scripts.modules.goods_parser import GoodsParser
from scripts.modules.fee_parser import FeeParser
from scripts.modules.agent_parser import AgentParser
from scripts.modules.summary_parser import SummaryParser


class BlockParser:
    """
    Block 解析协调器
    职责：
    1. 过滤掉路线行
    2. 将剩余行分发给各个专业解析器
    3. 汇总结果
    """

    def __init__(self):
        self.route_detector = RouteDetector()
        self.goods_parser = GoodsParser()
        self.fee_parser = FeeParser()
        self.agent_parser = AgentParser()
        self.summary_parser = SummaryParser()

    def parse_block(self, lines):
        """
        解析一个完整的 block
        ✅ 加强对备注、不含的识别
        """
        if not lines:
            return None

        # 过滤掉路线行
        non_route_lines = []
        for line in lines:
            detected = self.route_detector.detect(line)
            if not detected["is_route"]:
                non_route_lines.append(line)

        if not non_route_lines:
            return None

        # ✅ 预处理：提取"备注"和"不含"信息
        explicit_remarks = []
        explicit_excludes = []
        remaining_lines = []
        
        for line in non_route_lines:
            # 识别显式的"备注："行
            if line.startswith("备注") or line.startswith("说明"):
                # 提取冒号后的内容
                if "：" in line or ":" in line:
                    content = re.split(r"[：:]", line, 1)[1].strip()
                else:
                    content = line[2:].strip()  # 去掉"备注"两字
                
                # 进一步检查是否包含"不含"
                if "不含" in content:
                    # 分离备注和不含
                    parts = content.split("不含")
                    if parts[0].strip():
                        explicit_remarks.append(parts[0].strip())
                    if len(parts) > 1:
                        explicit_excludes.append("不含" + parts[1])
                else:
                    explicit_remarks.append(content)
                continue
            
            # 识别显式的"不含："行
            if "不含：" in line or "不含:" in line:
                explicit_excludes.append(line)
                continue
            
            remaining_lines.append(line)

        # 分类行（提升解析准确度）
        agent_lines = []
        goods_lines = []
        fee_lines = []
        summary_lines = []
        exclude_lines = []
        other_lines = []

        for line in remaining_lines:
            # ✅ 优先识别"不含"项目
            if self._is_exclude_line(line):
                exclude_lines.append(line)
            elif self.summary_parser.is_summary_line(line):
                summary_lines.append(line)
            elif self.agent_parser.is_agent_line(line):
                agent_lines.append(line)
            elif self.goods_parser._is_goods_detail(line) or self.goods_parser._is_goods_total(line):
                goods_lines.append(line)
            elif self.fee_parser._is_fee_item(line) or self.fee_parser._is_fee_total(line):
                fee_lines.append(line)
            else:
                other_lines.append(line)

        # 调用各个解析器
        result = {
            "route_agent": None,
            "goods_details": [],
            "goods_total": [],
            "fee_items": [],
            "fee_total": [],
            "summary": None
        }

        # 1. 解析代理商信息
        if agent_lines:
            result["route_agent"] = self.agent_parser.parse(agent_lines)
        elif other_lines:
            result["route_agent"] = self.agent_parser.parse(other_lines)

        # ✅ 合并显式备注
        if result["route_agent"]:
            if explicit_remarks:
                existing = result["route_agent"].get("代理备注") or ""
                combined = "\n".join(explicit_remarks)
                result["route_agent"]["代理备注"] = f"{combined}\n{existing}".strip() if existing else combined

        # 2. 解析货物信息
        if goods_lines:
            goods_result = self.goods_parser.parse_all(goods_lines)
            result["goods_details"] = goods_result["goods_details"]
            result["goods_total"] = goods_result["goods_total"]

        # 3. 解析费用信息
        if fee_lines:
            fee_result = self.fee_parser.parse_all(fee_lines)
            result["fee_items"] = fee_result["fee_items"]
            result["fee_total"] = fee_result["fee_total"]

        # 4. 解析汇总信息
        if summary_lines or exclude_lines or explicit_excludes:
            all_summary_lines = summary_lines + exclude_lines + explicit_excludes
            result["summary"] = self.summary_parser.parse(all_summary_lines)

        # 5. 未分类的行添加到备注
        if other_lines and result["route_agent"]:
            if not result["route_agent"].get("代理备注"):
                result["route_agent"]["代理备注"] = "\n".join(other_lines)

        return result
    
    def _is_exclude_line(self, text):
        """
        识别"不含"项目
        例如：保险费，查验费，待时费，国内转运费
        """
        exclude_keywords = [
            "不含", "费用实报实销", "实报实销",
            "保险费", "查验费", "待时费", "仓储费", 
            "转运费", "包装费", "杂费"
        ]
        
        # 如果包含多个费用项目，很可能是"不含"列表
        fee_count = sum(1 for kw in ["费", "费用"] if kw in text)
        if fee_count >= 2:
            return True
        
        return any(kw in text for kw in exclude_keywords)

    def parse_block_simple(self, lines):
        """
        简化版解析（兼容旧代码）
        不进行预分类，直接交给各解析器处理
        """
        if not lines:
            return None

        # 过滤路线行
        non_route_lines = [
            line for line in lines
            if not self.route_detector.detect(line)["is_route"]
        ]

        if not non_route_lines:
            return None

        # 全部交给解析器处理
        result = {
            "route_agent": self.agent_parser.parse(non_route_lines),
            "goods_details": self.goods_parser.parse_details(non_route_lines),
            "goods_total": self.goods_parser.parse_total(non_route_lines),
            "fee_items": self.fee_parser.parse_items(non_route_lines),
            "fee_total": self.fee_parser.parse_total(non_route_lines),
            "summary": self.summary_parser.parse(non_route_lines)
        }

        return result