# scripts/modules/block_splitter.py (宽松切分版)

import re
from typing import List


class BlockSplitter:
    """
    职责：只负责 block 边界切分，尽可能保留信息
    原则：宽松切分，让 BlockParser 做精细清洗
    """

    def __init__(self):
        # ✅ 路线强特征（仅用于"起 block"）
        self.route_patterns = [
            r".+[-–~—→>].+",        # 深圳-香港 / 香港→达拉斯
            r".+到.+",               # 深圳到香港
            r"^路线[:：]",           # 路线：
        ]

        # ✅ Excel 垃圾值（严格限制，避免误杀）
        self.invalid_patterns = [
            r"^nan$",
            r"^none$",
            r"^null$"
        ]

    def _is_invalid_line(self, line: str) -> bool:
        """
        判断是否为 Excel 垃圾行
        ⚠️ 只过滤明确的垃圾，不过滤有用信息
        """
        if not line:
            return True

        text = line.strip().lower()

        # 只过滤单独的 nan / none
        if text in ["nan", "none", "null"]:
            return True

        # nan 重复3次以上才过滤（如 "nan nan nan"）
        if re.fullmatch(r"(nan\s*){3,}", text):
            return True

        return False

    def is_route_line(self, line: str) -> bool:
        """
        判断是否为 block 起始行（路线行）
        ⚠️ 严格判断，避免误判
        """
        text = line.strip()
        
        # ✅ 排除明确不是路线的特征
        not_route_keywords = [
            "备注", "说明", "不含", "费用", "赔付",
            "时效", "工作日", "保险", "查验"
        ]
        
        # 如果包含这些关键词，大概率不是路线
        if any(kw in text for kw in not_route_keywords):
            return False
        
        # 检查路线模式
        for pat in self.route_patterns:
            if re.search(pat, text):
                return True
        
        return False

    def split(self, lines: List[str]) -> List[dict]:
        """
        返回结构化 blocks
        ✅ 宽松策略：保留尽可能多的信息
        
        [
            {
                "block_index": 0,
                "lines": [...],
                "type": "route" | "content"  # 标记类型
            }
        ]
        """
        blocks = []
        current_block = []
        block_index = 0
        current_type = "content"  # 默认类型

        for raw in lines:
            if raw is None:
                continue

            # 支持一个单元格里有多行（用\n或\t分隔）
            sub_lines = []
            if "\t" in str(raw):
                # 制表符分隔的多列，保持在一起
                sub_lines = [str(raw)]
            else:
                # 换行符分隔的多行
                sub_lines = str(raw).splitlines()
            
            for line in sub_lines:
                clean = line.strip()

                if not clean:
                    continue

                # ✅ 只过滤明确的垃圾
                if self._is_invalid_line(clean):
                    continue

                # 检查是否为新 block 起点
                if self.is_route_line(clean):
                    # 保存上一个 block
                    if current_block:
                        blocks.append({
                            "block_index": block_index,
                            "lines": current_block,
                            "type": current_type
                        })
                        block_index += 1
                    
                    # 开始新 block（路线类型）
                    current_block = [clean]
                    current_type = "route"
                else:
                    # ✅ 所有非路线内容都保留
                    if current_block:
                        current_block.append(clean)
                        # 如果已经有内容，维持原类型
                    else:
                        # 尚未出现路线前的内容
                        current_block = [clean]
                        current_type = "content"

        # 保存最后一个 block
        if current_block:
            blocks.append({
                "block_index": block_index,
                "lines": current_block,
                "type": current_type
            })

        return blocks
    
    def split_simple(self, lines: List[str]) -> List[List[str]]:
        """
        ✅ 简化版：只返回 lines 列表（向后兼容）
        """
        blocks = self.split(lines)
        return [block["lines"] for block in blocks]