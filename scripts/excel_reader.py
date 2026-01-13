# scripts/excel_reader.py
"""
Excel 读取器（重构版）
- 添加完整的异常处理
- 集成日志系统
- 添加文件缓存
- 性能优化
"""

import os
from pathlib import Path
from typing import Dict, List, Optional
from functools import lru_cache
import pandas as pd
import numpy as np

from scripts.logger_config import get_logger, log_performance
from scripts.exceptions import FileReadException, ExcelParseException


class ExcelReader:
    """
    负责：
    - 打开 Excel
    - 按 sheet 读取
    - 将所有单元格转成「行文本列表」
    - 保留行结构，方便后续切分
    """
    
    def __init__(self):
        self.logger = get_logger(__name__)
        self.logger.debug("ExcelReader 初始化完成")
    
    @log_performance
    def read_excel(self, 
                   file_path: str, 
                   keep_row_structure: bool = False,
                   use_cache: bool = True) -> Dict[str, List[str]]:
        """
        读取 Excel 文件
        
        Args:
            file_path: Excel 文件的【绝对路径】
            keep_row_structure: 是否保留行结构（True时每行的多个单元格会保留）
            use_cache: 是否使用缓存（仅对相同参数的重复读取有效）
            
        Returns:
            {
                "Sheet1": ["xxx", "yyy", ...],
                "Sheet2": [...]
            }
            
        Raises:
            FileReadException: 文件不存在或无法读取
            ExcelParseException: Excel 解析失败
        """
        # 验证文件路径
        file_path = self._validate_file_path(file_path)
        
        self.logger.info(f"开始读取 Excel：{os.path.basename(file_path)}")
        
        try:
            # 如果使用缓存，调用缓存版本
            if use_cache:
                return self._read_excel_cached(file_path, keep_row_structure)
            else:
                return self._read_excel_internal(file_path, keep_row_structure)
        
        except FileReadException:
            raise
        except ExcelParseException:
            raise
        except Exception as e:
            self.logger.error(f"读取 Excel 时发生未预期的错误: {e}", exc_info=True)
            raise ExcelParseException(f"Excel 文件解析失败: {e}", original_exception=e)
    
    def _validate_file_path(self, file_path: str) -> str:
        """验证文件路径"""
        if not file_path:
            raise FileReadException("文件路径不能为空")
        
        path = Path(file_path)
        
        if not path.exists():
            self.logger.error(f"文件不存在: {file_path}")
            raise FileReadException(f"Excel 文件不存在: {file_path}")
        
        if not path.is_file():
            self.logger.error(f"路径不是文件: {file_path}")
            raise FileReadException(f"路径不是文件: {file_path}")
        
        # 检查文件扩展名
        valid_extensions = ['.xlsx', '.xls', '.xlsm']
        if path.suffix.lower() not in valid_extensions:
            self.logger.warning(f"文件扩展名不是标准 Excel 格式: {path.suffix}")
        
        return str(path.absolute())
    
    @lru_cache(maxsize=10)
    def _read_excel_cached(self, 
                          file_path: str, 
                          keep_row_structure: bool) -> Dict[str, List[str]]:
        """
        缓存版本的 Excel 读取
        使用 LRU 缓存避免重复读取相同文件
        """
        self.logger.debug(f"使用缓存读取: {file_path}")
        return self._read_excel_internal(file_path, keep_row_structure)
    
    def _read_excel_internal(self, 
                            file_path: str, 
                            keep_row_structure: bool) -> Dict[str, List[str]]:
        """内部 Excel 读取实现"""
        try:
            xls = pd.ExcelFile(file_path)
        except Exception as e:
            self.logger.error(f"无法打开 Excel 文件: {e}", exc_info=True)
            raise ExcelParseException(f"Excel 文件打开失败: {e}", original_exception=e)
        
        sheets_data = {}
        total_sheets = len(xls.sheet_names)
        
        self.logger.info(f"Excel 包含 {total_sheets} 个工作表")
        
        for idx, sheet_name in enumerate(xls.sheet_names, 1):
            try:
                self.logger.debug(f"正在读取工作表 [{idx}/{total_sheets}]: {sheet_name}")
                
                df = xls.parse(sheet_name, header=None)
                
                if keep_row_structure:
                    lines = self._extract_with_row_structure(df)
                else:
                    lines = self._extract_flattened(df)
                
                sheets_data[sheet_name] = lines
                self.logger.debug(f"工作表 {sheet_name} 读取完成，共 {len(lines)} 行有效数据")
            
            except Exception as e:
                self.logger.error(f"读取工作表 {sheet_name} 失败: {e}", exc_info=True)
                # 继续处理其他工作表，不中断整个流程
                sheets_data[sheet_name] = []
        
        self.logger.info(f"Excel 读取完成，共处理 {len(sheets_data)} 个工作表")
        return sheets_data
    
    def _extract_with_row_structure(self, df: pd.DataFrame) -> List[str]:
        """
        保留行结构：一行多个单元格用 \t 连接
        """
        lines = []
        
        for row_idx, row in enumerate(df.itertuples(index=False)):
            row_cells = []
            
            for cell in row:
                cell_text = self._clean_cell(cell)
                if cell_text:
                    row_cells.append(cell_text)
            
            # 如果这一行有内容，加入结果
            if row_cells:
                # 用制表符连接同一行的多个单元格
                lines.append("\t".join(row_cells))
        
        return lines
    
    def _extract_flattened(self, df: pd.DataFrame) -> List[str]:
        """
        扁平化：每个单元格独立一行
        """
        lines = []
        
        for row in df.itertuples(index=False):
            for cell in row:
                cell_text = self._clean_cell(cell)
                if cell_text:
                    lines.append(cell_text)
        
        return lines
    
    def _clean_cell(self, cell) -> Optional[str]:
        """
        清理单元格内容
        
        Args:
            cell: 单元格值
            
        Returns:
            清理后的文本，如果无效则返回 None
        """
        # 过滤 None 和 NaN
        if cell is None or pd.isna(cell):
            return None
        
        if isinstance(cell, float) and np.isnan(cell):
            return None
        
        # 转换为字符串并清理
        text = str(cell).strip()
        
        # 过滤 "nan" 字符串
        if text.lower() == "nan":
            return None
        
        # 过滤空字符串
        if not text:
            return None
        
        return text
    
    @log_performance
    def read_excel_structured(self, file_path: str) -> Dict[str, List[List[str]]]:
        """
        返回结构化数据（保留行列关系）
        
        Returns:
            {
                "Sheet1": [
                    ["cell1", "cell2", "cell3"],  # 第1行
                    ["cell4", "cell5"],           # 第2行
                    ...
                ]
            }
        """
        file_path = self._validate_file_path(file_path)
        
        self.logger.info(f"开始读取 Excel (结构化)：{os.path.basename(file_path)}")
        
        try:
            xls = pd.ExcelFile(file_path)
        except Exception as e:
            self.logger.error(f"无法打开 Excel 文件: {e}", exc_info=True)
            raise ExcelParseException(f"Excel 文件打开失败: {e}", original_exception=e)
        
        sheets_data = {}
        
        for sheet_name in xls.sheet_names:
            try:
                df = xls.parse(sheet_name, header=None)
                
                rows = []
                for row in df.itertuples(index=False):
                    row_cells = []
                    for cell in row:
                        cell_text = self._clean_cell(cell)
                        if cell_text:
                            row_cells.append(cell_text)
                    
                    # 只保留有内容的行
                    if row_cells:
                        rows.append(row_cells)
                
                sheets_data[sheet_name] = rows
                self.logger.debug(f"工作表 {sheet_name} 读取完成，共 {len(rows)} 行")
            
            except Exception as e:
                self.logger.error(f"读取工作表 {sheet_name} 失败: {e}", exc_info=True)
                sheets_data[sheet_name] = []
        
        self.logger.info(f"Excel (结构化) 读取完成")
        return sheets_data
    
    def clear_cache(self):
        """清除读取缓存"""
        self._read_excel_cached.cache_clear()
        self.logger.info("Excel 读取缓存已清除")
    
    def get_cache_info(self) -> dict:
        """获取缓存信息"""
        cache_info = self._read_excel_cached.cache_info()
        return {
            "hits": cache_info.hits,
            "misses": cache_info.misses,
            "maxsize": cache_info.maxsize,
            "currsize": cache_info.currsize
        }