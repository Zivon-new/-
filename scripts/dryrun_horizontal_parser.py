# scripts/dryrun_horizontal_parser.py
"""
横向对比表格解析主程序（完全修复版）
修复：
1. 参数顺序错误
2. 返回值格式不匹配
3. 正确处理 QuoteBlock 数据结构
4. ⭐ v3.2 修复：将sheet_goods_info的数据正确写入routes表
"""

import os
import json
from pathlib import Path
from typing import Dict, List, Optional

from scripts.config import PathConfig
from scripts.logger_config import LoggerConfig, get_logger, log_performance
from scripts.exceptions import FileReadException, ExcelParseException
from scripts.excel_reader import ExcelReader
from scripts.json_writer import JSONWriter
from scripts.modules.horizontal_table_parser import HorizontalTableParser
from scripts.modules.sheet_goods_scanner import SheetGoodsScanner  # ⭐ 新增
from scripts.modules.goods_table_detector import GoodsTableDetector  # ⭐ 新增：货物表格检测器
from scripts.debug_logger import DebugLogger  # ⭐ 添加DebugLogger


class HorizontalParserRunner:
    """横向解析器运行器"""
    
    def __init__(self):
        self.logger = get_logger(__name__)
        
        # 初始化组件
        self.reader = ExcelReader()
        self.parser = HorizontalTableParser()
        self.parser.logger = self.logger  # ⭐ 设置解析器的日志
        
        # ⭐ 新增：初始化SheetGoodsScanner
        self.sheet_scanner = SheetGoodsScanner()
        
        # ⭐ 新增：初始化GoodsTableDetector
        self.goods_table_detector = GoodsTableDetector()
        
        # ⭐ 初始化DebugLogger
        self.debug_logger = DebugLogger()
        self.parser.debug_logger = self.debug_logger
        
        self.writer = JSONWriter(str(PathConfig.CLEAN_DATA_DIR))
        
        # 数据容器
        self.routes = []
        self.route_agents = []
        self.goods_details = []
        self.goods_total = []
        self.fee_items = []
        self.fee_total = []
        self.summaries = []
        
        # ID 计数器
        self.route_id = 1
        self.agent_route_id = 1
        self.goods_detail_id = 1
        self.goods_total_id = 1
        self.fee_item_id = 1
        self.fee_total_id = 1
        self.summary_id = 1
        
        # ⭐ 路线去重映射
        self.route_key_to_id = {}  # route_key -> route_id
        
        # 统计
        self.total_sheets = 0
        self.current_sheet = 0
        
        self.logger.info("HorizontalParserRunner 初始化完成")
    
    @log_performance
    def run(self):
        """主运行方法"""
        self.logger.info("=" * 60)
        self.logger.info(" 横向对比表格解析器 v3.2")  # ⭐ 版本更新
        self.logger.info("=" * 60)
        
        try:
            # 获取所有 Excel 文件
            excel_files = self._get_excel_files()
            
            if not excel_files:
                self.logger.warning(f"未在 {PathConfig.RAW_DATA_DIR} 找到 Excel 文件")
                return
            
            self.logger.info(f"找到 {len(excel_files)} 个 Excel 文件")
            
            # 处理每个文件
            for fname in excel_files:
                self._process_file(fname)
            
            # 输出结果
            self._write_results()
            
            # ⭐ 输出debug blocks
            self._write_debug_blocks()
            
            # 输出统计
            self._print_statistics()
            
            self.logger.info("解析完成！")
            
        except Exception as e:
            self.logger.error(f"解析过程发生错误: {e}", exc_info=True)
            raise
    
    def _get_excel_files(self) -> List[str]:
        """获取所有 Excel 文件"""
        try:
            raw_dir = PathConfig.RAW_DATA_DIR
            files = [f for f in os.listdir(raw_dir) if f.endswith(".xlsx") and not f.startswith("~")]
            return sorted(files)
        except Exception as e:
            self.logger.error(f"读取文件列表失败: {e}")
            raise FileReadException(f"无法读取文件列表: {e}", original_exception=e)
    
    @log_performance
    def _process_file(self, filename: str):
        """处理单个 Excel 文件"""
        self.logger.info("")
        self.logger.info(f"📄 处理文件: {filename}")
        
        # ⭐ Debug: 检查parser的route_enhancer状态
        self.logger.info(f"  🔍 [DEBUG] parser.route_enhancer = {self.parser.route_enhancer}")
        if self.parser.route_enhancer:
            self.logger.info(f"  ✅ [DEBUG] RouteFieldsEnhancer已初始化")
            # 测试日期提取
            test_start, test_end = self.parser.route_enhancer.extract_transaction_dates(filename)
            self.logger.info(f"  🔍 [DEBUG] 测试日期提取: {test_start} 至 {test_end}")
        else:
            self.logger.warning(f"  ⚠️ [DEBUG] RouteFieldsEnhancer未初始化，日期提取将失败！")
        
        # ⭐ Debug: 开始处理文件
        self.debug_logger.start_file(filename)
        
        # ⭐⭐⭐ 方案2: 每个文件重置去重映射，避免跨文件去重
        # 这样不同文件的同名sheet（如10.20-10.24的Sheet12和10.9-10.17的Sheet5都叫"香港-新加坡"）
        # 就不会被当作重复路线而过滤掉
        self.route_key_to_id = {}
        
        file_path = PathConfig.RAW_DATA_DIR / filename
        
        try:
            # 读取 Excel（结构化模式）
            sheets = self.reader.read_excel_structured(str(file_path))
            
            self.total_sheets = len(sheets)
            self.logger.info(f"   ✅ 读取到 {self.total_sheets} 个 Sheet")
            
            # 处理每个 Sheet
            self.current_sheet = 0
            for sheet_name, rows in sheets.items():
                self.current_sheet += 1
                self._process_sheet(sheet_name, rows, filename)
        
        except FileReadException as e:
            self.logger.error(f"文件读取失败: {filename}, 错误: {e}")
        except ExcelParseException as e:
            self.logger.error(f"Excel 解析失败: {filename}, 错误: {e}")
        except Exception as e:
            self.logger.error(f"处理文件时发生未预期错误: {filename}, 错误: {e}", exc_info=True)
    
    def _process_sheet(self, sheet_name: str, rows: List[List[str]], filename: str = None):
        """处理单个 Sheet"""
        self.logger.info("")
        self.logger.info(f"  {'='*60}")
        self.logger.info(f"  📋 Sheet {self.current_sheet}/{self.total_sheets}: {sheet_name}")
        self.logger.info(f"  {'='*60}")

        # ⭐⭐⭐ 在这里添加调试（第150行左右）
        self.logger.info(f"  🔍 DEBUG: sheet_name参数 = '{sheet_name}'")
        self.logger.info(f"  🔍 DEBUG: 类型 = {type(sheet_name).__name__}")
        self.logger.info(f"  🔍 DEBUG: 是否None = {sheet_name is None}")
        self.logger.info(f"  🔍 DEBUG: 是否空字符串 = {sheet_name == ''}")
        
        try:
            # ⭐ 新增：全sheet扫描，提取货物信息
            sheet_goods_info = self.sheet_scanner.scan_sheet(rows, sheet_name)
            if self.logger:
                self.logger.info(f"      📦 Sheet扫描结果: 重量={sheet_goods_info.get('实际重量')}, " +
                                 f"计费重量={sheet_goods_info.get('计费重量')}, " +
                                 f"体积={sheet_goods_info.get('总体积')}, 货值={sheet_goods_info.get('货值')}")
            
            # ⭐ 新增：货物表格检测
            goods_table = self.goods_table_detector.detect_goods_table(rows, sheet_name)
            if goods_table:
                table_type = goods_table.get('table_type')
                goods_count = len(goods_table.get('goods_list', []))
                if self.logger:
                    self.logger.info(f"      检测到{table_type}货物表格: {goods_count}种货物")
            
            # 解析QuoteBlocks
            quote_blocks = self.parser.parse_sheet(rows, sheet_name, filename)

            if quote_blocks and len(quote_blocks) > 0:
                for i, qb in enumerate(quote_blocks[:2], 1):  # 只检查前2个
                    self.logger.info(f"  🔍 DEBUG: QuoteBlock #{i} 的 _sheet_name = '{qb.route._sheet_name}'")
            
            if not quote_blocks:
                self.logger.warning(f"  ⚠️  Sheet {sheet_name} 未解析出有效数据")
                return
            
            self.logger.info(f"  解析到 {len(quote_blocks)} 个报价块")
            
            # ⭐ 修复2: 正确处理 QuoteBlock 列表
            for quote_block in quote_blocks:
                self._process_quote_block(quote_block, sheet_goods_info, goods_table)  # ⭐ 传递sheet_goods_info和goods_table
            
            self.logger.info(f"  📊 此 Sheet 处理完成")
        
        except Exception as e:
            self.logger.error(f"处理 Sheet {sheet_name} 时发生错误: {e}", exc_info=True)
    
    def _process_quote_block(self, quote_block, sheet_goods_info=None, goods_table=None):
        """
        处理单个 QuoteBlock
        
        Args:
            quote_block: QuoteBlock对象
            sheet_goods_info: 全sheet扫描的货物信息（可选）
            goods_table: 货物表格检测结果（可选）
        
        ⭐ 新增：处理单个 QuoteBlock
        QuoteBlock 结构：
        {
            route: Route,
            agent: Agent,
            fee_items: List[FeeItem],
            fee_total: FeeTotal,
            summary: Summary
        }
        """
        try:
            # 1. ⭐ 路线去重：检查路线是否已存在
            route_dict = quote_block.route.to_dict()
            route_key = quote_block.route.get_unique_key()
            
            # ⭐⭐⭐ v3.2 关键修复：用sheet_goods_info补充route_dict的数据 ⭐⭐⭐
            # 这是修复计费重量和货值丢失的核心代码！
            if sheet_goods_info:
                # 如果route_dict中没有重量数据，使用sheet_goods_info的数据
                if route_dict.get("实际重量") is None and sheet_goods_info.get("实际重量") is not None:
                    route_dict["实际重量"] = sheet_goods_info.get("实际重量")
                    self.logger.debug(f"      ✅ 从sheet扫描补充实际重量: {sheet_goods_info.get('实际重量')}")
                
                if route_dict.get("计费重量") is None and sheet_goods_info.get("计费重量") is not None:
                    route_dict["计费重量"] = sheet_goods_info.get("计费重量")
                    self.logger.debug(f"      ✅ 从sheet扫描补充计费重量: {sheet_goods_info.get('计费重量')}")
                
                if route_dict.get("总体积") is None and sheet_goods_info.get("总体积") is not None:
                    route_dict["总体积"] = sheet_goods_info.get("总体积")
                    self.logger.debug(f"      ✅ 从sheet扫描补充总体积: {sheet_goods_info.get('总体积')}")
                
                if route_dict.get("货值") is None and sheet_goods_info.get("货值") is not None:
                    route_dict["货值"] = sheet_goods_info.get("货值")
                    self.logger.debug(f"      ✅ 从sheet扫描补充货值: {sheet_goods_info.get('货值')}")
            # ⭐⭐⭐ 修复结束 ⭐⭐⭐
            
            if route_key in self.route_key_to_id:
                # 路线已存在，复用已有的route_id
                current_route_id = self.route_key_to_id[route_key]
                self.logger.debug(f"     路线已存在，复用 route_id={current_route_id}: {route_dict.get('起始地')} -> {route_dict.get('目的地')}")
            else:
                # 路线不存在，创建新路线
                current_route_id = self._add_route(route_dict)
                if current_route_id:
                    self.route_key_to_id[route_key] = current_route_id
                    
                    # ⭐ 添加整单货物信息（goods_total）
                    # 确保路线ID与routes表一致
                    # ⭐ 处理货物数据
                    if goods_table:
                        # 有货物表格，处理多条记录
                        self._process_goods_table(goods_table, current_route_id)
                    else:
                        # 没有货物表格，使用原有逻辑（单条记录）
                        self._add_goods_total(route_dict, current_route_id, sheet_goods_info)
                else:
                    self.logger.warning(f"  ⚠️ 跳过QuoteBlock：路线添加失败 - {route_dict.get('起始地')} -> {route_dict.get('目的地')}")
                    # ⭐ Debug记录
                    if hasattr(self, 'skipped_quote_blocks'):
                        self.skipped_quote_blocks.append({
                            'reason': '路线添加失败',
                            'route': f"{route_dict.get('起始地')} -> {route_dict.get('目的地')}",
                            'agent': quote_block.agent.代理商
                        })
                    return
            
            # 2. 添加代理商
            agent_dict = self._agent_to_dict(quote_block.agent)
            agent_route_id = self._add_route_agent(agent_dict, current_route_id)
            
            if not agent_route_id:
                self.logger.warning(f"  ⚠️ 跳过QuoteBlock：代理商添加失败 - {quote_block.agent.代理商}")
                # ⭐ Debug记录
                if hasattr(self, 'skipped_quote_blocks'):
                    self.skipped_quote_blocks.append({
                        'reason': '代理商添加失败',
                        'route': f"{route_dict.get('起始地')} -> {route_dict.get('目的地')}",
                        'agent': quote_block.agent.代理商
                    })
                return
            
            # 3. 添加费用明细
            for fee_item in quote_block.fee_items:
                fee_dict = self._fee_item_to_dict(fee_item)
                self._add_fee_item(fee_dict, agent_route_id, route_dict)
            
            # 4. 添加整单费用
            if quote_block.fee_total and quote_block.fee_total.费用总价:
                fee_total_dict = self._fee_total_to_dict(quote_block.fee_total)
                self._add_fee_total(fee_total_dict, agent_route_id)
            
            # 5. 添加汇总信息
            if quote_block.summary:
                summary_dict = self._summary_to_dict(quote_block.summary)
                self._add_summary(summary_dict, agent_route_id)
        
        except Exception as e:
            self.logger.error(f"处理 QuoteBlock 失败: {e}", exc_info=True)
    
    def _agent_to_dict(self, agent) -> Dict:
        """Agent 对象转字典"""
        return {
            "代理商": agent.代理商,
            "运输方式": agent.运输方式,
            "贸易类型": agent.贸易类型,
            "代理备注": agent.代理备注,
            "时效": agent.时效,
            "时效备注": None,  # Agent 类没有这个字段
            "不含": agent.不含,
            "是否赔付": agent.是否赔付,
            "赔付内容": agent.赔付内容,
        }
    
    def _fee_item_to_dict(self, fee_item) -> Dict:
        """FeeItem 对象转字典"""
        # ⭐ 适配新数据库v2结构
        return {
            "费用类型": fee_item.费用类型,
            "单价": fee_item.单价,
            "单位": fee_item.单位,
            "数量": fee_item.数量,
            "币种": "RMB",  # FeeItem 类没有币种字段，默认RMB
            "原币金额": fee_item.单价 * fee_item.数量 if fee_item.单价 and fee_item.数量 else 0,  # ⭐ 新增
            "人民币金额": fee_item.单价 * fee_item.数量 if fee_item.单价 and fee_item.数量 else 0,  # ⭐ 新增（RMB所以与原币金额相同）
            "备注": None
            # ❌ 删除：_raw字段
        }
    
    def _fee_total_to_dict(self, fee_total) -> Dict:
        """FeeTotal 对象转字典"""
        # ⭐ 适配新数据库v2结构
        return {
            "费用名称": "运费总计",
            "原币金额": fee_total.费用总价,
            "币种": "RMB",
            "人民币金额": fee_total.费用总价,  # ⭐ 新增（RMB所以与原币金额相同）
            "备注": None
            # ❌ 删除：_raw字段
        }
    
    def _summary_to_dict(self, summary) -> Dict:
        """Summary 对象转字典"""
        return {
            "小计": summary.小计,
            "税率": summary.税率,
            "税金": summary.税金,
            "汇损率": summary.汇损率,
            "汇损": summary.汇损,
            "总计": summary.总计,
            "备注": summary.备注,
        }
    
    def _add_route(self, route_info: Dict) -> int:
        """添加路线"""
        try:
            # ⭐ v9.0: 使用新字段结构
            # ⭐ 适配新数据库v2结构
            self.routes.append({
                "路线ID": self.route_id,  # ← ID字段中文化
                "起始地": route_info.get("起始地"),
                "目的地": route_info.get("目的地"),
                "途径地": route_info.get("途径地"),
                # ❌ 删除：贸易备注字段（新数据库没有）
                # ⭐ 交易日期字段
                "交易开始日期": route_info.get("交易开始日期"),
                "交易结束日期": route_info.get("交易结束日期"),
                # ⭐ 重量和体积字段（带单位标注）
                "实际重量(/kg)": route_info.get("实际重量"),
                "计费重量(/kg)": route_info.get("计费重量"),
                "总体积(/cbm)": route_info.get("总体积"),
                "货值": route_info.get("货值")
                # ❌ 删除：_raw字段
            })
            
            route_id = self.route_id
            self.route_id += 1
            
            self.logger.debug(f"     添加路线: {route_info.get('起始地')} -> {route_info.get('目的地')}")
            
            return route_id
        
        except Exception as e:
            self.logger.error(f"添加路线失败: {e}", exc_info=True)
            return None
    
    def _add_route_agent(self, agent_data: Dict, route_id: int) -> int:
        """添加代理商"""
        try:
            # ⭐ 适配新数据库v2结构
            self.route_agents.append({
                "代理路线ID": self.agent_route_id,  # ← ID字段中文化
                "路线ID": route_id,  # ← ID字段中文化
                "代理商": agent_data.get("代理商"),
                "运输方式": agent_data.get("运输方式"),
                "贸易类型": agent_data.get("贸易类型"),
                "代理备注": agent_data.get("代理备注"),
                "时效": agent_data.get("时效"),
                "时效备注": agent_data.get("时效备注"),
                "不含": agent_data.get("不含"),
                "是否赔付": agent_data.get("是否赔付", "0"),
                "赔付内容": agent_data.get("赔付内容")
            })
            
            agent_id = self.agent_route_id
            self.agent_route_id += 1
            
            self.logger.debug(f"     添加代理商: {agent_data.get('代理商')}")
            
            return agent_id
        
        except Exception as e:
            self.logger.error(f"添加代理商失败: {e}", exc_info=True)
            return None
    
    def _add_fee_item(self, fee_item: Dict, agent_route_id: int, route_info: Dict):
        """添加费用明细"""
        try:
            # 如果没有数量，从路线信息获取
            quantity = fee_item.get("数量")
            if not quantity and route_info:
                unit = fee_item.get("单位", "").upper()
                if unit == "KG" and route_info.get("实际重量"):
                    quantity = route_info.get("实际重量")
                elif unit == "CBM" and route_info.get("总体积"):
                    quantity = route_info.get("总体积")
                else:
                    quantity = 1
            
            # ⭐ 适配新数据库v2结构
            self.fee_items.append({
                "费用ID": self.fee_item_id,  # ← ID字段中文化
                "代理路线ID": agent_route_id,  # ← ID字段中文化
                "费用类型": fee_item.get("费用类型"),
                "单价": fee_item.get("单价"),
                "单位": fee_item.get("单位"),
                "数量": quantity,
                "币种": fee_item.get("币种", "RMB"),
                "原币金额": fee_item.get("原币金额", 0),  # ⭐ 新增
                "人民币金额": fee_item.get("人民币金额", 0),  # ⭐ 新增
                "备注": fee_item.get("备注")
                # ❌ 删除：_raw字段
            })
            
            self.fee_item_id += 1
        
        except Exception as e:
            self.logger.error(f"添加费用明细失败: {e}", exc_info=True)
    
    def _add_fee_total(self, fee_total: Dict, agent_route_id: int):
        """添加整单费用"""
        try:
            # ⭐ 适配新数据库v2结构
            self.fee_total.append({
                "整单费用ID": self.fee_total_id,  # ← ID字段中文化
                "代理路线ID": agent_route_id,  # ← ID字段中文化
                "费用名称": fee_total.get("费用名称"),
                "原币金额": fee_total.get("原币金额"),
                "币种": fee_total.get("币种", "RMB"),
                "人民币金额": fee_total.get("人民币金额", 0),  # ⭐ 新增
                "备注": fee_total.get("备注")
                # ❌ 删除：_raw字段
            })
            
            self.fee_total_id += 1
        
        except Exception as e:
            self.logger.error(f"添加整单费用失败: {e}", exc_info=True)
    
    def _add_summary(self, summary: Dict, agent_route_id: int):
        """添加汇总信息"""
        try:
            # ⭐ 适配新数据库v2结构
            self.summaries.append({
                "汇总ID": self.summary_id,  # ← ID字段中文化
                "代理路线ID": agent_route_id,  # ← ID字段中文化
                "小计": summary.get("小计"),
                "税率": summary.get("税率"),
                "税金": summary.get("税金"),
                "汇损率": summary.get("汇损率"),
                "汇损": summary.get("汇损"),
                "总计": summary.get("总计"),
                "备注": summary.get("备注")
            })
            
            self.summary_id += 1
        
        except Exception as e:
            self.logger.error(f"添加汇总信息失败: {e}", exc_info=True)
    
    @log_performance

    
    def _add_goods_total(self, route_dict: Dict, route_id: int, sheet_goods_info: Dict = None):
        """
        添加整单货物信息
        
        ⭐ 数据来源优先级：
        1. 全sheet扫描结果（sheet_goods_info）- 最准确，扫描整个sheet
        2. route_dict（Route.to_dict()）- 只从第一行提取
        3. 默认值
        
        ⭐ 关键：route_id必须与routes表的路线ID一致
        ⭐ 注意：货值在routes表中，不在goods_total表中
        
        Args:
            route_dict: route字典（来自Route.to_dict()）
            route_id: routes表的路线ID（外键，必须一致！）
            sheet_goods_info: 全sheet扫描的货物信息（可选，优先使用）
        """
        try:
            # ⭐ 优先使用全sheet扫描结果
            if sheet_goods_info:
                actual_weight = sheet_goods_info.get("实际重量")
                billing_weight = sheet_goods_info.get("计费重量")
                total_volume = sheet_goods_info.get("总体积")
                # 货值不再从sheet_goods_info提取，在routes表中
                goods_name = sheet_goods_info.get("货物名称")
                
                if self.logger:
                    self.logger.debug(f"      使用全sheet扫描结果: 重量={actual_weight}, 体积={total_volume}")
            else:
                # Fallback: 使用route_dict（只从第一行提取）
                actual_weight = route_dict.get("实际重量")
                billing_weight = route_dict.get("计费重量")
                total_volume = route_dict.get("总体积")
                # 货值不再从route_dict提取，在routes表中
                goods_name = self._extract_goods_name(route_dict)
                
                if self.logger:
                    self.logger.debug(f"      使用route_dict: 重量={actual_weight}, 体积={total_volume}")
            
            # 如果两个字段都没有值，就不添加goods_total
            if actual_weight is None and total_volume is None:
                self.logger.debug(f"      路线{route_id}无货物数据，跳过goods_total")
                return
            
            # ⭐ 添加goods_total，路线ID与routes表一致（不包含货值）
            self.goods_total.append({
                "整单货物ID": self.goods_total_id,  # 自增ID
                "路线ID": route_id,  # ⭐⭐⭐ 外键：必须与routes表的路线ID一致！
                "货物名称": goods_name,
                "实际重量(/kg)": actual_weight if actual_weight else 0.0,
                "总体积(/cbm)": total_volume if total_volume else 0.0,
                "备注": None
            })
            
            self.goods_total_id += 1
            
            if self.logger:
                self.logger.debug(f"      ✅ 添加goods_total: 路线ID={route_id}, 重量={actual_weight}, 体积={total_volume}")
        
        except Exception as e:
            self.logger.error(f"添加整单货物信息失败: {e}", exc_info=True)
    
    def _process_goods_table(self, goods_table: Dict, route_id: int):
        """
        处理货物表格数据
        
        Args:
            goods_table: 货物表格检测结果 {
                "table_type": "simple" | "complex",
                "goods_list": [...],
                "total_weight": float,
                "total_volume": float,
                ...
            }
            route_id: 路线ID
        """
        if not goods_table:
            return
        
        goods_list = goods_table.get("goods_list", [])
        table_type = goods_table.get("table_type", "unknown")
        
        if not goods_list:
            return
        
        if table_type == "simple":
            # 简单表格：只有货物名称
            for goods in goods_list:
                self.goods_details.append({
                    "货物明细ID": self.goods_detail_id,
                    "路线ID": route_id,
                    "货物名称": goods.get("name", "未知货物"),
                    "是否新品": None,
                    "货物种类": None,
                    "数量": goods.get("quantity", 1),
                    "单价": None,
                    "币种": None,
                    "重量(/kg)": goods.get("weight"),
                    "总重量(/kg)": goods.get("total_weight"),
                    "总价": goods.get("total_value"),
                    "备注": None
                })
                self.goods_detail_id += 1
            
            if self.logger:
                self.logger.info(f"      ✅ 创建{len(goods_list)}条goods_details记录（简单表格）")
        
        elif table_type == "complex":
            # 复杂表格：有完整的货物信息
            for goods in goods_list:
                self.goods_details.append({
                    "货物明细ID": self.goods_detail_id,
                    "路线ID": route_id,
                    "货物名称": goods.get("name", "未知货物"),
                    "是否新品": goods.get("is_new"),
                    "货物种类": goods.get("category"),
                    "数量": goods.get("quantity", 1),
                    "单价": goods.get("unit_price"),
                    "币种": goods.get("currency"),
                    "重量(/kg)": goods.get("weight"),
                    "总重量(/kg)": goods.get("total_weight"),
                    "总价": goods.get("total_value"),
                    "备注": None
                })
                self.goods_detail_id += 1
            
            if self.logger:
                self.logger.info(f"      ✅ 创建{len(goods_list)}条goods_details记录（复杂表格）")

    def _extract_goods_name(self, route_dict: Dict) -> str:
        """
        从route信息中提取货物名称
        
        提取顺序：
        1. 从贸易备注字段提取（优先）
        2. 从_raw字段提取
        3. 如果都没有，返回"混合货物"
        
        Args:
            route_dict: route字典（来自Route.to_dict()）
        
        Returns:
            货物名称字符串
        """
        import re
        
        # ⭐ 过滤关键词 - 这些内容不是货物名称
        filter_keywords = [
            '小计', '总计', '合计', '税率', '税金', '汇损', '不含',
            '实报实销', '注：', '备注', '最低收费', 'local', '报关费',
            '按照', '请贴好', '标签', '卸货', '等有了', '最终', '托盘计算'
        ]
        
        # 货物关键词
        goods_keywords = [
            '电池', '设备', '货物', '产品', '伞', '扇', '屏', '柜',
            '服务器', '交换机', '模块', '网线', '板卡', '标本', '陶坛',
            '宣传册', '伴手礼', '展示柜', 'Dell', 'PowerEdge', 'Nokia'
        ]
        
        def clean_goods_name(text: str) -> Optional[str]:
            """清理货物名称"""
            if not text:
                return None
            
            # 检查是否包含过滤关键词
            if any(keyword in text for keyword in filter_keywords):
                return None
            
            # ⭐ 清理路线前缀
            cleaned = text
            route_patterns = [
                r'^[\u4e00-\u9fa5]+-[\u4e00-\u9fa5]+海运专线\s+',  # "国内-西班牙海运专线 "
                r'^[\u4e00-\u9fa5]+-[\u4e00-\u9fa5]+空运专线\s+',  # "香港-新加坡空运专线 "
                r'^[\u4e00-\u9fa5]+-[\u4e00-\u9fa5]+专线\s+',      # "国内-澳门专线 "
                r'^[\u4e00-\u9fa5]+-[\u4e00-\u9fa5]+\s+',          # "国内-西班牙 " "北京-沙特 "
                r'^[\u4e00-\u9fa5]+专线\s+',                       # "马尼拉专线 "
                r'^香港-[\u4e00-\u9fa5]+\s+',                      # "香港-菲律宾 "
            ]
            
            for pattern in route_patterns:
                cleaned = re.sub(pattern, '', cleaned)
            
            # 移除"客户提供"、"预估"等前缀
            cleaned = re.sub(r'^(客户提供|预估|合计|重量[:：]|体积[:：]|货值[:：])\s*', '', cleaned).strip()
            
            # 移除后面的描述性内容
            cleaned = re.sub(r'(客户提供|预估|合计|重量|体积|货值).*$', '', cleaned).strip()
            
            # 移除重量和体积标注
            cleaned = re.sub(r'\d+\.?\d*\s*(?:kg|KG|kgs|KGS|cbm|CBM)', '', cleaned).strip()
            
            # ⭐ 移除"//"等格式错误
            cleaned = re.sub(r'/+', '', cleaned).strip()
            
            # 移除多余空格
            cleaned = re.sub(r'\s+', ' ', cleaned).strip()
            
            if cleaned and len(cleaned) >= 2 and len(cleaned) <= 50:
                return cleaned
            
            return None
        
        # 尝试从贸易备注提取
        trade_remark = route_dict.get("贸易备注", "")
        if trade_remark:
            cleaned_remark = clean_goods_name(trade_remark)
            if cleaned_remark:
                return cleaned_remark
        
        # 尝试从_raw提取
        raw_text = route_dict.get("_raw", "")
        if raw_text:
            # 尝试查找包含货物关键词的部分
            for keyword in goods_keywords:
                if keyword in raw_text:
                    # 提取包含关键词的短语
                    idx = raw_text.find(keyword)
                    start = max(0, idx - 10)
                    end = min(len(raw_text), idx + len(keyword) + 30)
                    phrase = raw_text[start:end].strip()
                    
                    cleaned_phrase = clean_goods_name(phrase)
                    if cleaned_phrase:
                        return cleaned_phrase
            
            # 如果没找到关键词，尝试清理整个raw_text
            cleaned_raw = clean_goods_name(raw_text)
            if cleaned_raw:
                return cleaned_raw
        
        # 如果都提取不到，返回默认值
        return "混合货物"

    def _write_results(self):
        """输出所有结果"""
        self.logger.info("")
        self.logger.info("=" * 60)
        self.logger.info(" 输出结果")
        self.logger.info("=" * 60)
        
        try:
            # 写入主要数据表
            self.writer.write_table("routes", self.routes)
            self.writer.write_table("route_agents", self.route_agents)
            self.writer.write_table("goods_details", self.goods_details)
            self.writer.write_table("goods_total", self.goods_total)
            self.writer.write_table("fee_items", self.fee_items)
            self.writer.write_table("fee_total", self.fee_total)
            self.writer.write_table("summary", self.summaries)
            
            # 写入统计计数
            counts = self._get_counts()
            counts_path = PathConfig.CLEAN_DATA_DIR / "summary_counts.json"
            with open(counts_path, "w", encoding="utf-8") as f:
                json.dump(counts, f, ensure_ascii=False, indent=2)
            self.logger.info(f"✅ 统计数据: {counts_path}")
            
        except Exception as e:
            self.logger.error(f"写入结果失败: {e}", exc_info=True)
            raise
    
    def _write_debug_blocks(self):
        """写入debug blocks到JSON文件"""
        try:
            # 写入debug_blocks.json
            debug_path = PathConfig.CLEAN_DATA_DIR / "debug_blocks.json"
            self.debug_logger.write_to_file(str(debug_path))
            
            # 打印摘要
            summary = self.debug_logger.get_summary()
            self.logger.info("")
            self.logger.info("=" * 60)
            self.logger.info(" Debug Blocks 统计")
            self.logger.info("=" * 60)
            self.logger.info(f"  总文件数: {summary['total_files']}")
            self.logger.info(f"  总Sheet数: {summary['total_sheets']}")
            self.logger.info(f"  总Block数: {summary['total_blocks']}")
            self.logger.info(f"  成功: {summary['successful_blocks']}")
            self.logger.info(f"  失败: {summary['failed_blocks']}")
            self.logger.info(f"  跳过: {summary['skipped_blocks']}")
            self.logger.info(f"  成功率: {summary['success_rate']}")
            self.logger.info(f"✅ Debug blocks: {debug_path}")
            
        except Exception as e:
            self.logger.error(f"写入debug blocks失败: {e}", exc_info=True)
    
    def _get_counts(self) -> Dict:
        """获取统计计数"""
        return {
            "routes": len(self.routes),
            "route_agents": len(self.route_agents),
            "goods_details": len(self.goods_details),
            "goods_total": len(self.goods_total),
            "fee_items": len(self.fee_items),
            "fee_total": len(self.fee_total),
            "summaries": len(self.summaries)
        }
    
    def _print_statistics(self):
        """打印统计信息"""
        counts = self._get_counts()
        
        self.logger.info("")
        self.logger.info("=" * 60)
        self.logger.info(" 解析统计")
        self.logger.info("=" * 60)
        
        for key, value in counts.items():
            self.logger.info(f"{key:20s}: {value:5d}")
        
        self.logger.info("=" * 60)


def run():
    """主入口函数"""
    # 初始化日志系统
    LoggerConfig.setup(
        log_level="INFO",
        console_output=True,
        file_output=True,
        max_bytes=10*1024*1024,
        backup_count=5
    )
    
    logger = get_logger(__name__)
    
    try:
        # 创建并运行解析器
        runner = HorizontalParserRunner()
        runner.run()
        
        logger.info("✅ 程序执行成功！")
        
    except KeyboardInterrupt:
        logger.warning("程序被用户中断")
    except Exception as e:
        logger.error(f"程序执行失败: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    run()