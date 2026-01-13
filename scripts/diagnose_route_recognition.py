# scripts/diagnose_route_recognition.py
"""
路线识别诊断工具
帮助定位为什么路线信息不全
"""

import os
import json
from pathlib import Path
from typing import List, Dict

from scripts.config import PathConfig
from scripts.logger_config import LoggerConfig, get_logger
from scripts.excel_reader import ExcelReader
from scripts.modules.horizontal_table_parser import HorizontalTableParser


class RouteRecognitionDiagnostics:
    """路线识别诊断器"""
    
    def __init__(self):
        self.logger = get_logger(__name__)
        self.reader = ExcelReader()
        self.parser = HorizontalTableParser()
        self.parser.logger = self.logger
        
        # 检查是否使用了优化的模块
        self._check_optimized_modules()
    
    def _check_optimized_modules(self):
        """检查是否正确加载了优化模块"""
        self.logger.info("=" * 70)
        self.logger.info("🔍 检查优化模块是否正确加载")
        self.logger.info("=" * 70)
        
        # 检查RouteExtractor
        if hasattr(self.parser, 'route_extractor') and self.parser.route_extractor:
            self.logger.info("✅ RouteExtractor 已加载")
            
            # 测试基本功能
            test_result = self.parser.route_extractor.extract_route("深圳-香港 120KGS")
            self.logger.info(f"   测试结果: {test_result['origin']} -> {test_result['destination']}")
            
            if test_result['origin'] == '深圳' and test_result['destination'] == '香港':
                self.logger.info("   ✅ RouteExtractor 工作正常")
            else:
                self.logger.warning("   ⚠️ RouteExtractor 可能有问题")
        else:
            self.logger.warning("❌ RouteExtractor 未加载，使用fallback逻辑")
            self.logger.warning("   建议：确认 route_extractor.py 已放置在 scripts/modules/")
        
        # 检查白名单
        try:
            from scripts.data.location_whitelist import LOCATION_WHITELIST
            self.logger.info(f"✅ 地点白名单已加载，包含 {len(LOCATION_WHITELIST)} 个地点")
        except ImportError:
            self.logger.error("❌ 地点白名单未加载")
            self.logger.error("   建议：确认 location_whitelist.py 已放置在 scripts/data/")
        
        self.logger.info("")
    
    def diagnose_all_files(self):
        """诊断所有Excel文件"""
        self.logger.info("=" * 70)
        self.logger.info("📊 开始诊断所有Excel文件")
        self.logger.info("=" * 70)
        self.logger.info("")
        
        # 获取文件列表
        raw_dir = PathConfig.RAW_DATA_DIR
        files = [f for f in os.listdir(raw_dir) if f.endswith(".xlsx") and not f.startswith("~")]
        
        if not files:
            self.logger.error(f"未在 {raw_dir} 找到Excel文件")
            return
        
        self.logger.info(f"找到 {len(files)} 个Excel文件")
        self.logger.info("")
        
        all_issues = []
        total_sheets = 0
        sheets_with_routes = 0
        sheets_without_routes = 0
        
        # 处理每个文件
        for filename in files:
            file_path = raw_dir / filename
            
            self.logger.info("=" * 70)
            self.logger.info(f"📄 文件: {filename}")
            self.logger.info("=" * 70)
            
            try:
                # 读取Excel
                sheets = self.reader.read_excel_structured(str(file_path))
                
                for sheet_name, rows in sheets.items():
                    total_sheets += 1
                    
                    self.logger.info("")
                    self.logger.info(f"  📋 Sheet: {sheet_name}")
                    self.logger.info(f"     行数: {len(rows)}")
                    
                    # 显示前3行原始数据
                    self.logger.info(f"     前3行数据:")
                    for i, row in enumerate(rows[:3], 1):
                        row_preview = str(row[:3])[:80]
                        self.logger.info(f"       {i}. {row_preview}")
                    
                    # 尝试解析
                    quotes = self.parser.parse_sheet(rows, sheet_name)
                    
                    if quotes and len(quotes) > 0:
                        sheets_with_routes += 1
                        self.logger.info(f"     ✅ 成功提取 {len(quotes)} 个报价")
                        
                        for i, quote in enumerate(quotes, 1):
                            self.logger.info(f"       报价{i}:")
                            self.logger.info(f"         起点: {quote.route.起始地}")
                            self.logger.info(f"         终点: {quote.route.目的地}")
                            self.logger.info(f"         途径: {quote.route.途径地}")
                            self.logger.info(f"         代理: {quote.agent.代理商}")
                            if quote.route.实际重量:
                                self.logger.info(f"         重量: {quote.route.实际重量}")
                    else:
                        sheets_without_routes += 1
                        self.logger.warning(f"     ❌ 未能提取路线")
                        
                        # 记录问题
                        issue = {
                            "file": filename,
                            "sheet": sheet_name,
                            "rows": len(rows),
                            "first_row": str(rows[0][:3]) if rows else "空",
                            "reason": self._diagnose_failure(rows, sheet_name)
                        }
                        all_issues.append(issue)
                        
                        self.logger.warning(f"     原因: {issue['reason']}")
            
            except Exception as e:
                self.logger.error(f"处理文件失败: {filename}, 错误: {e}", exc_info=True)
        
        # 输出汇总
        self.logger.info("")
        self.logger.info("=" * 70)
        self.logger.info("📈 诊断汇总")
        self.logger.info("=" * 70)
        self.logger.info(f"总文件数: {len(files)}")
        self.logger.info(f"总Sheet数: {total_sheets}")
        self.logger.info(f"成功提取路线的Sheet: {sheets_with_routes}")
        self.logger.info(f"未提取路线的Sheet: {sheets_without_routes}")
        
        if sheets_without_routes > 0:
            success_rate = (sheets_with_routes / total_sheets * 100) if total_sheets > 0 else 0
            self.logger.info(f"识别成功率: {success_rate:.1f}%")
        
        # 输出问题清单
        if all_issues:
            self.logger.info("")
            self.logger.info("=" * 70)
            self.logger.info("❌ 问题清单")
            self.logger.info("=" * 70)
            
            for i, issue in enumerate(all_issues, 1):
                self.logger.info(f"\n{i}. 文件: {issue['file']}")
                self.logger.info(f"   Sheet: {issue['sheet']}")
                self.logger.info(f"   行数: {issue['rows']}")
                self.logger.info(f"   第一行: {issue['first_row']}")
                self.logger.info(f"   原因: {issue['reason']}")
        
        # 保存诊断报告
        self._save_report(all_issues, {
            "total_files": len(files),
            "total_sheets": total_sheets,
            "sheets_with_routes": sheets_with_routes,
            "sheets_without_routes": sheets_without_routes,
        })
    
    def _diagnose_failure(self, rows: List[List[str]], sheet_name: str) -> str:
        """诊断为什么提取失败"""
        if not rows or len(rows) == 0:
            return "Sheet为空"
        
        if len(rows) < 2:
            return f"数据行数不足（只有{len(rows)}行）"
        
        # 检查第一行
        first_row_text = ' '.join(str(cell) for cell in rows[0] if cell)
        
        # 检查是否包含路线模式
        if '-' not in first_row_text and '→' not in first_row_text and '至' not in first_row_text:
            return f"第一行不包含路线分隔符（-/→/至），内容: {first_row_text[:60]}"
        
        # 尝试手动提取
        try:
            test_route = self.parser._extract_route_from_text(first_row_text, sheet_name)
            
            if not test_route.起始地 and not test_route.目的地:
                return f"无法从第一行提取路线，内容: {first_row_text[:60]}"
            elif not test_route.起始地:
                return f"缺少起始地，目的地: {test_route.目的地}"
            elif not test_route.目的地:
                return f"缺少目的地，起始地: {test_route.起始地}"
        except Exception as e:
            return f"路线提取抛出异常: {str(e)}"
        
        return "未知原因（可能是白名单过滤或其他问题）"
    
    def _save_report(self, issues: List[Dict], summary: Dict):
        """保存诊断报告"""
        report = {
            "summary": summary,
            "issues": issues
        }
        
        report_path = PathConfig.CLEAN_DATA_DIR / "route_diagnosis_report.json"
        
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        self.logger.info("")
        self.logger.info(f"✅ 诊断报告已保存: {report_path}")
    
    def test_specific_route(self, route_text: str):
        """测试特定路线文本的识别"""
        self.logger.info("")
        self.logger.info("=" * 70)
        self.logger.info(f"🧪 测试路线识别: {route_text}")
        self.logger.info("=" * 70)
        
        # 测试路线提取
        route = self.parser._extract_route_from_text(route_text, None)
        
        self.logger.info(f"结果:")
        self.logger.info(f"  起始地: {route.起始地}")
        self.logger.info(f"  目的地: {route.目的地}")
        self.logger.info(f"  途径地: {route.途径地}")
        self.logger.info(f"  实际重量: {route.实际重量}")
        self.logger.info(f"  计费重量: {route.计费重量}")
        self.logger.info(f"  总体积: {route.总体积}")
        self.logger.info(f"  货值: {route.货值}")
        
        # 判断是否成功
        if route.起始地 and route.目的地:
            self.logger.info("✅ 路线识别成功")
        else:
            self.logger.warning("❌ 路线识别失败")
            
            # 给出建议
            if not route.起始地:
                self.logger.warning("  问题: 起始地未识别")
                self.logger.warning("  建议: 检查起始地是否在白名单中")
            
            if not route.目的地:
                self.logger.warning("  问题: 目的地未识别")
                self.logger.warning("  建议: 检查目的地是否在白名单中")


def run_diagnostics():
    """运行诊断"""
    # 初始化日志
    LoggerConfig.setup(
        log_level="INFO",
        console_output=True,
        file_output=True
    )
    
    logger = get_logger(__name__)
    
    logger.info("")
    logger.info("=" * 70)
    logger.info(" 路线识别诊断工具 v1.0")
    logger.info("=" * 70)
    logger.info("")
    
    try:
        diagnostics = RouteRecognitionDiagnostics()
        
        # 运行完整诊断
        diagnostics.diagnose_all_files()
        
        # 可选：测试特定路线
        # diagnostics.test_specific_route("深圳-香港 120KGS")
        # diagnostics.test_specific_route("北京-沙特 宣传册&伴手礼")
        
        logger.info("")
        logger.info("=" * 70)
        logger.info("✅ 诊断完成")
        logger.info("=" * 70)
        
    except Exception as e:
        logger.error(f"诊断过程出错: {e}", exc_info=True)


if __name__ == "__main__":
    run_diagnostics()