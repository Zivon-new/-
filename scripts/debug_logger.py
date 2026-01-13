# scripts/debug_logger.py
"""
调试日志记录器 - 用于生成debug_blocks.json
记录所有解析过程，包括成功和失败的情况
"""

from typing import List, Dict, Any, Optional
from pathlib import Path
import json


class DebugBlock:
    """调试用的block数据结构"""
    
    def __init__(
        self,
        file: str,
        sheet: str,
        block_index: int,
        type: str = "route"
    ):
        self.file = file
        self.sheet = sheet
        self.block_index = block_index
        self.type = type
        self.status = "unknown"  # success, failed, skipped
        self.reason = None
        self.lines = []
        self.extracted = {}
        self.fallback = {}
        self.has_remark = False
        self.has_exclude = False
        self.row_range = None  # (start, end)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        result = {
            "file": self.file,
            "sheet": self.sheet,
            "block_index": self.block_index,
            "type": self.type,
            "status": self.status,
            "lines": self.lines,
        }
        
        if self.reason:
            result["reason"] = self.reason
        
        if self.extracted:
            result["extracted"] = self.extracted
        
        if self.fallback:
            result["fallback"] = self.fallback
        
        if self.row_range:
            result["row_range"] = f"{self.row_range[0]}-{self.row_range[1]}"
        
        result["has_remark"] = self.has_remark
        result["has_exclude"] = self.has_exclude
        
        return result


class DebugLogger:
    """调试日志记录器"""
    
    def __init__(self):
        self.blocks: List[DebugBlock] = []
        self.current_file = None
        self.current_sheet = None
        
        # 统计
        self.total_files = 0
        self.total_sheets = 0
        self.successful_blocks = 0
        self.failed_blocks = 0
        self.skipped_blocks = 0
    
    def start_file(self, filename: str):
        """开始处理一个文件"""
        self.current_file = filename
        self.total_files += 1
    
    def start_sheet(self, sheet_name: str):
        """开始处理一个sheet"""
        self.current_sheet = sheet_name
        self.total_sheets += 1
    
    def log_block(
        self,
        block_index: int,
        lines: List[str],
        status: str,
        reason: str = None,
        extracted: Dict = None,
        fallback: Dict = None,
        row_range: tuple = None
    ):
        """
        记录一个block
        
        Args:
            block_index: block索引
            lines: 文本行
            status: 状态 (success, failed, skipped)
            reason: 失败原因
            extracted: 提取到的数据
            fallback: fallback数据
            row_range: 行范围 (start, end)
        """
        block = DebugBlock(
            file=self.current_file,
            sheet=self.current_sheet,
            block_index=block_index,
            type="route"
        )
        
        block.status = status
        block.reason = reason
        block.lines = lines
        block.row_range = row_range
        
        if extracted:
            block.extracted = extracted
        
        if fallback:
            block.fallback = fallback
        
        # 检查是否有备注和不含
        text = ' '.join(lines)
        block.has_remark = any(kw in text for kw in ['备注', '说明', '注意'])
        block.has_exclude = '不含' in text
        
        self.blocks.append(block)
        
        # 更新统计
        if status == "success":
            self.successful_blocks += 1
        elif status == "failed":
            self.failed_blocks += 1
        elif status == "skipped":
            self.skipped_blocks += 1
    
    def log_boundary(
        self,
        boundary_index: int,
        start_row: int,
        end_row: int,
        route_text: str,
        status: str,
        reason: str = None,
        quote_blocks: List = None
    ):
        """
        记录一个boundary的解析结果
        
        Args:
            boundary_index: boundary索引
            start_row: 起始行
            end_row: 结束行
            route_text: 路线文本
            status: 状态
            reason: 失败原因
            quote_blocks: 生成的QuoteBlock列表
        """
        # 提取文本行
        lines = [route_text]
        if quote_blocks and len(quote_blocks) > 0:
            # 如果有QuoteBlock，记录成功
            qb = quote_blocks[0]
            extracted = {
                "起始地": qb.route.起始地,
                "目的地": qb.route.目的地,
                "代理商": qb.agent.代理商,
            }
            
            if qb.route.实际重量:
                extracted["重量"] = qb.route.实际重量
            
            self.log_block(
                block_index=boundary_index,
                lines=lines,
                status="success",
                extracted=extracted,
                row_range=(start_row, end_row)
            )
        else:
            # 失败
            self.log_block(
                block_index=boundary_index,
                lines=lines,
                status="failed",
                reason=reason or "未知原因",
                row_range=(start_row, end_row)
            )
    
    def log_sheet_fallback(
        self,
        sheet_name: str,
        reason: str,
        quote_block = None
    ):
        """
        记录sheet名fallback
        
        Args:
            sheet_name: sheet名
            reason: fallback原因
            quote_block: 生成的QuoteBlock
        """
        if quote_block:
            extracted = {
                "起始地": quote_block.route.起始地,
                "目的地": quote_block.route.目的地,
            }
            fallback = {
                "used_sheet_name": True,
                "sheet_name": sheet_name
            }
            
            self.log_block(
                block_index=0,
                lines=[f"Sheet名: {sheet_name}"],
                status="success",
                reason=reason,
                extracted=extracted,
                fallback=fallback
            )
        else:
            self.log_block(
                block_index=0,
                lines=[f"Sheet名: {sheet_name}"],
                status="failed",
                reason=reason
            )
    
    def write_to_file(self, output_path: str):
        """写入到JSON文件"""
        total_blocks = len(self.blocks)
        success_rate = (
            f"{(self.successful_blocks / total_blocks * 100):.1f}%"
            if total_blocks > 0
            else "0.0%"
        )
        
        output = {
            "summary": {
                "total_files": self.total_files,
                "total_sheets": self.total_sheets,
                "total_blocks": total_blocks,
                "successful_blocks": self.successful_blocks,
                "failed_blocks": self.failed_blocks,
                "skipped_blocks": self.skipped_blocks,
                "success_rate": success_rate
            },
            "blocks": [block.to_dict() for block in self.blocks]
        }
        
        # 写入文件
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output, f, ensure_ascii=False, indent=2)
        
        return output_file
    
    def get_summary(self) -> Dict[str, Any]:
        """获取统计摘要"""
        total_blocks = len(self.blocks)
        success_rate = (
            f"{(self.successful_blocks / total_blocks * 100):.1f}%"
            if total_blocks > 0
            else "0.0%"
        )
        
        return {
            "total_files": self.total_files,
            "total_sheets": self.total_sheets,
            "total_blocks": total_blocks,
            "successful_blocks": self.successful_blocks,
            "failed_blocks": self.failed_blocks,
            "skipped_blocks": self.skipped_blocks,
            "success_rate": success_rate
        }