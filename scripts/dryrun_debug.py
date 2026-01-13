# scripts/dryrun_horizontal_parser_v5_DEDUP.py
"""
横向解析器 v5.0 - 正确的去重逻辑
关键修复：
1. ✅ horizontal_table_parser返回所有QuoteBlock（不去重）
2. ✅ 在dryrun层面去重路线
3. ✅ 所有代理商信息都保留
"""

import os
import json
from pathlib import Path
from typing import Dict, List

from scripts.config import PathConfig
from scripts.logger_config import LoggerConfig, get_logger, log_performance
from scripts.exceptions import FileReadException, ExcelParseException
from scripts.excel_reader import ExcelReader
from scripts.json_writer import JSONWriter
from scripts.modules.horizontal_table_parser import HorizontalTableParser


class HorizontalParserRunnerV5:
    """横向解析器运行器 v5.0 - 正确的去重"""
    
    def __init__(self):
        self.logger = get_logger(__name__)
        
        # 初始化组件
        self.reader = ExcelReader()
        self.parser = HorizontalTableParser()
        self.parser.logger = self.logger
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
        self.fee_item_id = 1
        self.fee_total_id = 1
        self.summary_id = 1
        
        # ⭐ 路线去重映射：route_key -> route_id
        self.route_key_to_id = {}
        
        # 统计
        self.total_sheets = 0
        self.current_sheet = 0
        
        self.logger.info("HorizontalParserRunnerV5 初始化完成（正确去重版本）")
    
    @log_performance
    def run(self):
        """主运行方法"""
        self.logger.info("=" * 60)
        self.logger.info(" 横向对比表格解析器 v5.0 (正确去重)")
        self.logger.info("=" * 60)
        
        try:
            excel_files = self._get_excel_files()
            
            if not excel_files:
                self.logger.warning(f"未在 {PathConfig.RAW_DATA_DIR} 找到 Excel 文件")
                return
            
            self.logger.info(f"找到 {len(excel_files)} 个 Excel 文件")
            
            for fname in excel_files:
                self._process_file(fname)
            
            self._write_results()
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
                self._process_sheet(sheet_name, rows)
        
        except FileReadException as e:
            self.logger.error(f"文件读取失败: {filename}, 错误: {e}")
        except ExcelParseException as e:
            self.logger.error(f"Excel 解析失败: {filename}, 错误: {e}")
        except Exception as e:
            self.logger.error(f"处理文件时发生未预期错误: {filename}, 错误: {e}", exc_info=True)
    
    def _process_sheet(self, sheet_name: str, rows: List[List[str]]):
        """处理单个 Sheet"""
        self.logger.info("")
        self.logger.info(f"  {'='*60}")
        self.logger.info(f"  📋 Sheet {self.current_sheet}/{self.total_sheets}: {sheet_name}")
        self.logger.info(f"  {'='*60}")
        
        try:
            # ⭐ 解析sheet，返回所有QuoteBlock（不去重）
            quote_blocks = self.parser.parse_sheet(rows, sheet_name)
            
            if not quote_blocks:
                self.logger.warning(f"  ⚠️  Sheet {sheet_name} 未解析出有效数据")
                return
            
            self.logger.info(f"  解析到 {len(quote_blocks)} 个报价块")
            
            # ⭐ 处理每个QuoteBlock，在这里去重路线
            for quote_block in quote_blocks:
                self._process_quote_block(quote_block)
            
            self.logger.info(f"  📊 此 Sheet 处理完成")
        
        except Exception as e:
            self.logger.error(f"处理 Sheet {sheet_name} 时发生错误: {e}", exc_info=True)
    
    def _process_quote_block(self, quote_block):
        """
        ⭐ 核心方法：处理单个 QuoteBlock，正确去重
        """
        try:
            # 1. ⭐ 路线去重：检查路线是否已存在
            route_dict = quote_block.route.to_dict()
            route_key = quote_block.route.get_unique_key()
            
            if route_key in self.route_key_to_id:
                # 路线已存在，复用已有的route_id
                current_route_id = self.route_key_to_id[route_key]
                self.logger.debug(f"     路线已存在，复用 route_id={current_route_id}: {quote_block.route.起始地} -> {quote_block.route.目的地}")
            else:
                # 路线不存在，创建新路线
                current_route_id = self._add_route(route_dict)
                if current_route_id:
                    self.route_key_to_id[route_key] = current_route_id
                    self.logger.debug(f"     添加新路线 route_id={current_route_id}: {quote_block.route.起始地} -> {quote_block.route.目的地}")
                else:
                    self.logger.warning(f"     跳过：路线添加失败")
                    return
            
            # 2. ⭐ 代理商信息总是添加（不去重）
            agent_dict = self._agent_to_dict(quote_block.agent)
            agent_route_id = self._add_route_agent(agent_dict, current_route_id)
            
            if not agent_route_id:
                self.logger.warning(f"     跳过：代理商添加失败")
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
            "时效备注": None,
            "不含": agent.不含,
            "是否赔付": agent.是否赔付,
            "赔付内容": agent.赔付内容,
        }
    
    def _fee_item_to_dict(self, fee_item) -> Dict:
        """FeeItem 对象转字典"""
        return {
            "费用类型": fee_item.费用类型,
            "单价": fee_item.单价,
            "单位": fee_item.单位,
            "数量": fee_item.数量,
            "币种": "RMB",
            "备注": None,
            "_raw": None
        }
    
    def _fee_total_to_dict(self, fee_total) -> Dict:
        """FeeTotal 对象转字典"""
        return {
            "费用名称": "运费总计",
            "原币金额": fee_total.费用总价,
            "币种": "RMB",
            "备注": None,
            "_raw": None
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
            self.routes.append({
                "route_id": self.route_id,
                "起始地": route_info.get("起始地"),
                "目的地": route_info.get("目的地"),
                "途径地": route_info.get("途径地"),
                "贸易备注": route_info.get("贸易备注"),
                "交易时间": route_info.get("交易时间"),
                "实际重量": route_info.get("实际重量"),
                "计费重量": route_info.get("计费重量"),
                "总体积": route_info.get("总体积"),
                "货值": route_info.get("货值"),
                "_raw": route_info.get("_raw")
            })
            
            route_id = self.route_id
            self.route_id += 1
            
            return route_id
        
        except Exception as e:
            self.logger.error(f"添加路线失败: {e}", exc_info=True)
            return None
    
    def _add_route_agent(self, agent_data: Dict, route_id: int) -> int:
        """添加代理商"""
        try:
            self.route_agents.append({
                "agent_route_id": self.agent_route_id,
                "route_id": route_id,
                "代理商": agent_data.get("代理商"),
                "运输方式": agent_data.get("运输方式"),
                "贸易类型": agent_data.get("贸易类型"),
                "代理备注": agent_data.get("代理备注"),
                "时效": agent_data.get("时效"),
                "时效备注": agent_data.get("时效备注"),
                "不含": agent_data.get("不含"),
                "是否赔付": agent_data.get("是否赔付", "0"),
                "赔付内容": agent_data.get("赔付内容"),
            })
            
            agent_id = self.agent_route_id
            self.agent_route_id += 1
            
            self.logger.debug(f"     添加代理商 agent_route_id={agent_id}: {agent_data.get('代理商')} (route_id={route_id})")
            
            return agent_id
        
        except Exception as e:
            self.logger.error(f"添加代理商失败: {e}", exc_info=True)
            return None
    
    def _add_fee_item(self, fee_item: Dict, agent_route_id: int, route_info: Dict):
        """添加费用明细"""
        try:
            quantity = fee_item.get("数量")
            if not quantity and route_info:
                unit = fee_item.get("单位", "").upper()
                if unit == "KG" and route_info.get("实际重量"):
                    quantity = route_info.get("实际重量")
                elif unit == "CBM" and route_info.get("总体积"):
                    quantity = route_info.get("总体积")
                else:
                    quantity = 1
            
            self.fee_items.append({
                "fee_item_id": self.fee_item_id,
                "agent_route_id": agent_route_id,
                "费用类型": fee_item.get("费用类型"),
                "单价": fee_item.get("单价"),
                "单位": fee_item.get("单位"),
                "数量": quantity,
                "币种": fee_item.get("币种", "RMB"),
                "备注": fee_item.get("备注"),
                "_raw": fee_item.get("_raw")
            })
            
            self.fee_item_id += 1
        
        except Exception as e:
            self.logger.error(f"添加费用明细失败: {e}", exc_info=True)
    
    def _add_fee_total(self, fee_total: Dict, agent_route_id: int):
        """添加整单费用"""
        try:
            self.fee_total.append({
                "fee_total_id": self.fee_total_id,
                "agent_route_id": agent_route_id,
                "费用名称": fee_total.get("费用名称"),
                "原币金额": fee_total.get("原币金额"),
                "币种": fee_total.get("币种", "RMB"),
                "备注": fee_total.get("备注"),
                "_raw": fee_total.get("_raw")
            })
            
            self.fee_total_id += 1
        
        except Exception as e:
            self.logger.error(f"添加整单费用失败: {e}", exc_info=True)
    
    def _add_summary(self, summary: Dict, agent_route_id: int):
        """添加汇总信息"""
        try:
            self.summaries.append({
                "summary_id": self.summary_id,
                "agent_route_id": agent_route_id,
                "小计": summary.get("小计"),
                "税率": summary.get("税率"),
                "税金": summary.get("税金"),
                "汇损率": summary.get("汇损率"),
                "汇损": summary.get("汇损"),
                "总计": summary.get("总计"),
                "备注": summary.get("备注"),
            })
            
            self.summary_id += 1
        
        except Exception as e:
            self.logger.error(f"添加汇总信息失败: {e}", exc_info=True)
    
    @log_performance
    def _write_results(self):
        """输出所有结果"""
        self.logger.info("")
        self.logger.info("=" * 60)
        self.logger.info(" 输出结果")
        self.logger.info("=" * 60)
        
        try:
            self.writer.write_table("routes", self.routes)
            self.writer.write_table("route_agents", self.route_agents)
            self.writer.write_table("goods_details", self.goods_details)
            self.writer.write_table("goods_total", self.goods_total)
            self.writer.write_table("fee_items", self.fee_items)
            self.writer.write_table("fee_total", self.fee_total)
            self.writer.write_table("summary", self.summaries)
            
            counts = self._get_counts()
            counts_path = PathConfig.CLEAN_DATA_DIR / "summary_counts.json"
            with open(counts_path, "w", encoding="utf-8") as f:
                json.dump(counts, f, ensure_ascii=False, indent=2)
            self.logger.info(f"✅ 统计数据: {counts_path}")
            
        except Exception as e:
            self.logger.error(f"写入结果失败: {e}", exc_info=True)
            raise
    
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
        self.logger.info(f"路线去重数量: {len(self.route_key_to_id)}")
        self.logger.info("=" * 60)


def run():
    """主入口函数"""
    LoggerConfig.setup(
        log_level="INFO",
        console_output=True,
        file_output=True,
        max_bytes=10*1024*1024,
        backup_count=5
    )
    
    logger = get_logger(__name__)
    
    try:
        runner = HorizontalParserRunnerV5()
        runner.run()
        
        logger.info("✅ 程序执行成功！")
        
    except KeyboardInterrupt:
        logger.warning("程序被用户中断")
    except Exception as e:
        logger.error(f"程序执行失败: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    run()