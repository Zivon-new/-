# scripts/diagnose_missing_routes.py
"""
诊断为什么QuoteBlock被成功提取，但routes.json中找不到
"""

import os
import json
from pathlib import Path
from typing import List, Dict

from scripts.config import PathConfig
from scripts.logger_config import LoggerConfig, get_logger
from scripts.excel_reader import ExcelReader
from scripts.modules.horizontal_table_parser import HorizontalTableParser


class MissingRoutesDiagnostics:
    """丢失路线诊断器"""
    
    def __init__(self):
        self.logger = get_logger(__name__)
        self.reader = ExcelReader()
        self.parser = HorizontalTableParser()
        self.parser.logger = self.logger
    
    def diagnose_missing_route(self, filename: str, sheet_name: str, expected_origin: str, expected_destination: str):
        """
        诊断为什么某条路线丢失了
        
        Args:
            filename: Excel文件名
            sheet_name: Sheet名
            expected_origin: 预期的起始地
            expected_destination: 预期的目的地
        """
        
        self.logger.info("=" * 80)
        self.logger.info("🔍 丢失路线诊断")
        self.logger.info("=" * 80)
        self.logger.info(f"文件: {filename}")
        self.logger.info(f"Sheet: {sheet_name}")
        self.logger.info(f"预期路线: {expected_origin} -> {expected_destination}")
        self.logger.info("")
        
        # 步骤1: 解析QuoteBlock
        self.logger.info("步骤1: 解析QuoteBlock")
        self.logger.info("-" * 80)
        
        file_path = PathConfig.RAW_DATA_DIR / filename
        sheets = self.reader.read_excel_structured(str(file_path))
        
        if sheet_name not in sheets:
            self.logger.error(f"❌ Sheet不存在")
            return
        
        rows = sheets[sheet_name]
        quote_blocks = self.parser.parse_sheet(rows, sheet_name)
        
        self.logger.info(f"提取到 {len(quote_blocks)} 个QuoteBlock")
        
        # 查找匹配的QuoteBlock
        matching_blocks = []
        for qb in quote_blocks:
            if qb.route.起始地 == expected_origin and qb.route.目的地 == expected_destination:
                matching_blocks.append(qb)
        
        if not matching_blocks:
            self.logger.error(f"❌ 没有找到匹配的QuoteBlock")
            self.logger.error(f"   预期: {expected_origin} -> {expected_destination}")
            self.logger.error(f"   实际提取的QuoteBlock:")
            for qb in quote_blocks:
                self.logger.error(f"     - {qb.route.起始地} -> {qb.route.目的地}")
            return
        
        self.logger.info(f"✅ 找到 {len(matching_blocks)} 个匹配的QuoteBlock")
        self.logger.info("")
        
        # 步骤2: 检查每个QuoteBlock的详细信息
        self.logger.info("步骤2: QuoteBlock详细信息")
        self.logger.info("-" * 80)
        
        for i, qb in enumerate(matching_blocks, 1):
            self.logger.info(f"\nQuoteBlock #{i}:")
            self.logger.info(f"  路线信息:")
            self.logger.info(f"    起始地: '{qb.route.起始地}'")
            self.logger.info(f"    目的地: '{qb.route.目的地}'")
            self.logger.info(f"    途径地: '{qb.route.途径地}'")
            self.logger.info(f"    Sheet名: '{qb.route._sheet_name}'")
            
            # 生成unique_key（这是去重的关键）
            unique_key = qb.route.get_unique_key()
            self.logger.info(f"    Unique Key: '{unique_key}'")
            
            # 检查代理商
            self.logger.info(f"  代理商信息:")
            self.logger.info(f"    代理商: '{qb.agent.代理商}'")
            self.logger.info(f"    代理商是否为空: {not qb.agent.代理商}")
            
            # 检查route.to_dict()的输出
            route_dict = qb.route.to_dict()
            self.logger.info(f"  route.to_dict()输出:")
            self.logger.info(f"    起始地: {route_dict.get('起始地')}")
            self.logger.info(f"    目的地: {route_dict.get('目的地')}")
            self.logger.info(f"    途径地: {route_dict.get('途径地')}")
        
        self.logger.info("")
        
        # 步骤3: 模拟dryrun的处理逻辑
        self.logger.info("步骤3: 模拟dryrun处理逻辑")
        self.logger.info("-" * 80)
        
        route_key_to_id = {}
        routes_created = []
        agents_created = []
        skipped_blocks = []
        
        route_id = 1
        agent_route_id = 1
        
        for i, qb in enumerate(matching_blocks, 1):
            self.logger.info(f"\n处理QuoteBlock #{i}:")
            
            # 生成route_key
            route_dict = qb.route.to_dict()
            route_key = qb.route.get_unique_key()
            
            self.logger.info(f"  Route Key: '{route_key}'")
            
            # 检查起始地和目的地
            if not route_dict.get("起始地"):
                self.logger.error(f"  ❌ 起始地为空或None！")
                skipped_blocks.append({
                    'block': i,
                    'reason': '起始地为空',
                    'route_dict': route_dict
                })
                continue
            
            if not route_dict.get("目的地"):
                self.logger.error(f"  ❌ 目的地为空或None！")
                skipped_blocks.append({
                    'block': i,
                    'reason': '目的地为空',
                    'route_dict': route_dict
                })
                continue
            
            # 路线去重
            if route_key in route_key_to_id:
                current_route_id = route_key_to_id[route_key]
                self.logger.info(f"  ✓ 路线已存在，复用 route_id={current_route_id}")
            else:
                # 模拟_add_route
                self.logger.info(f"  ✓ 创建新路线 route_id={route_id}")
                
                routes_created.append({
                    "route_id": route_id,
                    "起始地": route_dict.get("起始地"),
                    "目的地": route_dict.get("目的地"),
                    "途径地": route_dict.get("途径地"),
                })
                
                current_route_id = route_id
                route_key_to_id[route_key] = current_route_id
                route_id += 1
            
            # 检查代理商
            if not qb.agent.代理商:
                self.logger.warning(f"  ⚠️ 代理商为空，QuoteBlock会被跳过")
                skipped_blocks.append({
                    'block': i,
                    'reason': '代理商为空',
                    'agent': qb.agent.代理商
                })
                continue
            
            # 创建代理商
            self.logger.info(f"  ✓ 创建代理商 agent_route_id={agent_route_id}")
            agents_created.append({
                "agent_route_id": agent_route_id,
                "route_id": current_route_id,
                "代理商": qb.agent.代理商,
            })
            agent_route_id += 1
        
        # 步骤4: 汇总模拟结果
        self.logger.info("")
        self.logger.info("步骤4: 模拟结果汇总")
        self.logger.info("-" * 80)
        self.logger.info(f"匹配的QuoteBlock: {len(matching_blocks)}")
        self.logger.info(f"应创建的routes记录: {len(routes_created)}")
        self.logger.info(f"应创建的route_agents记录: {len(agents_created)}")
        self.logger.info(f"被跳过的QuoteBlock: {len(skipped_blocks)}")
        
        if skipped_blocks:
            self.logger.warning(f"\n⚠️ 跳过的QuoteBlock详情:")
            for skip in skipped_blocks:
                self.logger.warning(f"  Block #{skip['block']}: {skip['reason']}")
                if 'route_dict' in skip:
                    self.logger.warning(f"    route_dict: {skip['route_dict']}")
        
        self.logger.info("")
        
        # 步骤5: 对比实际JSON
        self.logger.info("步骤5: 对比实际JSON文件")
        self.logger.info("-" * 80)
        
        routes_file = PathConfig.CLEAN_DATA_DIR / "routes.json"
        agents_file = PathConfig.CLEAN_DATA_DIR / "route_agents.json"
        
        if not routes_file.exists():
            self.logger.warning("❌ routes.json 不存在")
            return
        
        with open(routes_file, 'r', encoding='utf-8') as f:
            actual_routes = json.load(f)
        
        with open(agents_file, 'r', encoding='utf-8') as f:
            actual_agents = json.load(f)
        
        # 查找实际的路线
        actual_matching_routes = []
        for route in actual_routes:
            if route.get('起始地') == expected_origin and route.get('目的地') == expected_destination:
                actual_matching_routes.append(route)
        
        self.logger.info(f"实际JSON中的匹配路线: {len(actual_matching_routes)} 条")
        
        if not actual_matching_routes:
            self.logger.error(f"❌ 实际JSON中找不到这条路线！")
            self.logger.error(f"   预期: {expected_origin} -> {expected_destination}")
            
            # 分析原因
            self.logger.error(f"\n可能的原因:")
            if skipped_blocks:
                self.logger.error(f"  1. QuoteBlock被跳过（详见上面的跳过详情）")
            
            if len(routes_created) == 0:
                self.logger.error(f"  2. 模拟也没有创建routes记录，说明数据有问题")
            else:
                self.logger.error(f"  3. 模拟创建了{len(routes_created)}条routes，但实际没有")
                self.logger.error(f"     可能是dryrun运行时出错，或者是路线被重复去重")
        else:
            self.logger.info(f"✅ 找到匹配的路线:")
            for route in actual_matching_routes:
                self.logger.info(f"  route_id={route['route_id']}: {route['起始地']} -> {route['目的地']}")
                
                # 查找这个路线的代理商
                route_agents = [a for a in actual_agents if a['route_id'] == route['route_id']]
                self.logger.info(f"  代理商数量: {len(route_agents)}")
                for agent in route_agents:
                    self.logger.info(f"    - {agent['代理商']}")
        
        # 步骤6: 检查日志文件
        self.logger.info("")
        self.logger.info("步骤6: 检查dryrun日志")
        self.logger.info("-" * 80)
        
        log_file = Path("logs/parser.log")
        if log_file.exists():
            self.logger.info(f"✅ 日志文件存在: {log_file}")
            self.logger.info(f"   建议: 搜索日志中的 '跳过QuoteBlock' 或 '路线添加失败'")
            self.logger.info(f"   命令: grep -n '跳过QuoteBlock\\|路线添加失败' logs/parser.log")
        else:
            self.logger.warning(f"⚠️ 日志文件不存在")


def run_diagnostics():
    """运行诊断"""
    import sys
    
    LoggerConfig.setup(log_level="INFO", console_output=True, file_output=False)
    
    if len(sys.argv) >= 5:
        filename = sys.argv[1]
        sheet_name = sys.argv[2]
        origin = sys.argv[3]
        destination = sys.argv[4]
    else:
        print("用法: python diagnose_missing_routes.py <文件名> <Sheet名> <起始地> <目的地>")
        print("示例: python diagnose_missing_routes.py 报价单.xlsx 深圳-新加坡专线成本 深圳 新加坡")
        return
    
    diagnostics = MissingRoutesDiagnostics()
    diagnostics.diagnose_missing_route(filename, sheet_name, origin, destination)


if __name__ == "__main__":
    run_diagnostics()