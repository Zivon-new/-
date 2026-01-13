# scripts/debug_block_split.py
# Block 切分调试工具

import os
import json
from scripts.config import Config
from scripts.excel_reader import ExcelReader
from scripts.modules.block_splitter import BlockSplitter
from scripts.modules.block_parser import BlockParser


def debug_single_file(filename=None):
    """
    调试单个文件的 block 切分情况
    """
    reader = ExcelReader()
    splitter = BlockSplitter()
    parser = BlockParser()
    
    raw_dir = Config.RAW_DATA_DIR
    
    # 如果没有指定文件，使用第一个 Excel 文件
    if filename is None:
        files = [f for f in os.listdir(raw_dir) if f.endswith(".xlsx")]
        if not files:
            print("❌ 没有找到 Excel 文件")
            return
        filename = files[0]
    
    file_path = os.path.join(raw_dir, filename)
    
    print("=" * 80)
    print(f"📄 调试文件: {filename}")
    print("=" * 80)
    
    # 测试不同的读取模式
    print("\n🔹 模式1: 扁平化读取 (当前默认)")
    sheets = reader.read_excel(file_path, keep_row_structure=False)
    debug_sheets(sheets, splitter, parser, mode="扁平化")
    
    print("\n" + "=" * 80)
    print("🔹 模式2: 保留行结构")
    sheets = reader.read_excel(file_path, keep_row_structure=True)
    debug_sheets(sheets, splitter, parser, mode="行结构")


def debug_sheets(sheets, splitter, parser, mode=""):
    """
    调试 sheet 的切分和解析
    """
    for sheet_name, lines in sheets.items():
        print(f"\n  📋 Sheet: {sheet_name} ({mode})")
        print(f"  原始行数: {len(lines)}")
        
        # 显示前3行原始数据
        print(f"\n  前3行原始数据:")
        for i, line in enumerate(lines[:3], 1):
            preview = line[:100] + "..." if len(line) > 100 else line
            print(f"    {i}. {preview}")
        
        # 切分 blocks
        blocks = splitter.split(lines)
        print(f"\n  切分后 Block 数: {len(blocks)}")
        
        # 显示每个 block
        for i, block in enumerate(blocks, 1):
            block_lines = block.get("lines", [])
            block_type = block.get("type", "unknown")
            
            print(f"\n  📦 Block {i} [类型: {block_type}]")
            print(f"     行数: {len(block_lines)}")
            
            # 显示前5行
            for j, line in enumerate(block_lines[:5], 1):
                preview = line[:80] + "..." if len(line) > 80 else line
                print(f"       {j}. {preview}")
            
            if len(block_lines) > 5:
                print(f"       ... (还有 {len(block_lines) - 5} 行)")
            
            # 尝试解析
            parsed = parser.parse_block(block_lines)
            if parsed:
                print(f"\n     ✅ 解析结果:")
                
                if parsed.get("route_agent"):
                    agent = parsed["route_agent"]
                    print(f"       代理商: {agent.get('代理商')}")
                    print(f"       运输方式: {agent.get('运输方式')}")
                    print(f"       贸易类型: {agent.get('贸易类型')}")
                    if agent.get("代理备注"):
                        remark = agent["代理备注"][:60] + "..." if len(agent.get("代理备注", "")) > 60 else agent.get("代理备注")
                        print(f"       代理备注: {remark}")
                    if agent.get("不含"):
                        exclude = agent["不含"][:60] + "..." if len(agent.get("不含", "")) > 60 else agent.get("不含")
                        print(f"       不含: {exclude}")
                
                if parsed.get("goods_details"):
                    print(f"       货物明细: {len(parsed['goods_details'])} 条")
                
                if parsed.get("fee_items"):
                    print(f"       费用明细: {len(parsed['fee_items'])} 条")
                
                if parsed.get("summary"):
                    summary = parsed["summary"]
                    if summary.get("不含"):
                        exclude = summary["不含"][:60] + "..." if len(summary.get("不含", "")) > 60 else summary.get("不含")
                        print(f"       汇总-不含: {exclude}")


def search_keyword_in_blocks(keyword="备注"):
    """
    搜索包含特定关键词的 block
    """
    reader = ExcelReader()
    splitter = BlockSplitter()
    
    raw_dir = Config.RAW_DATA_DIR
    files = [f for f in os.listdir(raw_dir) if f.endswith(".xlsx")]
    
    print("=" * 80)
    print(f"🔍 搜索关键词: '{keyword}'")
    print("=" * 80)
    
    found_count = 0
    
    for filename in files:
        file_path = os.path.join(raw_dir, filename)
        sheets = reader.read_excel(file_path)
        
        for sheet_name, lines in sheets.items():
            blocks = splitter.split(lines)
            
            for i, block in enumerate(blocks, 1):
                block_lines = block.get("lines", [])
                
                # 检查是否包含关键词
                for line in block_lines:
                    if keyword in line:
                        found_count += 1
                        print(f"\n✅ 找到 [{filename} - {sheet_name} - Block {i}]")
                        print(f"   完整内容:")
                        for j, bl in enumerate(block_lines, 1):
                            print(f"     {j}. {bl}")
                        print()
                        break
    
    print(f"\n总共找到 {found_count} 个包含 '{keyword}' 的 block")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "search" and len(sys.argv) > 2:
            keyword = sys.argv[2]
            search_keyword_in_blocks(keyword)
        elif command == "file" and len(sys.argv) > 2:
            filename = sys.argv[2]
            debug_single_file(filename)
        else:
            print("用法:")
            print("  python scripts/debug_block_split.py              # 调试第一个文件")
            print("  python scripts/debug_block_split.py file xxx.xlsx   # 调试指定文件")
            print("  python scripts/debug_block_split.py search 备注     # 搜索关键词")
    else:
        # 默认：调试第一个文件
        debug_single_file()