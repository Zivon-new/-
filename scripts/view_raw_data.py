# scripts/view_raw_data_html.py
"""
原始数据查看器 - HTML 版本
输出到浏览器，方便查看和分析
"""

import os
import sys
import datetime
from pathlib import Path
from scripts.config import Config, PathConfig
from scripts.excel_reader import ExcelReader


class HTMLViewer:
    """HTML 数据查看器"""
    
    def __init__(self):
        self.output_dir = PathConfig.CLEAN_DATA_DIR / "raw_view_html"
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def generate_html(self, title, content_html):
        """生成完整的 HTML 页面"""
        return f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Segoe UI', 'Microsoft YaHei', Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            line-height: 1.6;
        }}
        
        .container {{
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            border-radius: 12px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.2);
            overflow: hidden;
        }}
        
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }}
        
        .header h1 {{
            font-size: 2.5em;
            margin-bottom: 10px;
        }}
        
        .header .subtitle {{
            font-size: 1.1em;
            opacity: 0.9;
        }}
        
        .nav {{
            background: #f8f9fa;
            padding: 15px 30px;
            border-bottom: 2px solid #e9ecef;
            display: flex;
            gap: 15px;
            flex-wrap: wrap;
        }}
        
        .nav a {{
            padding: 8px 20px;
            background: white;
            border: 2px solid #667eea;
            border-radius: 6px;
            text-decoration: none;
            color: #667eea;
            transition: all 0.3s;
            font-weight: 500;
        }}
        
        .nav a:hover {{
            background: #667eea;
            color: white;
            transform: translateY(-2px);
        }}
        
        .content {{
            padding: 30px;
        }}
        
        .file-info {{
            background: #e7f3ff;
            border-left: 4px solid #2196F3;
            padding: 15px;
            margin-bottom: 20px;
            border-radius: 4px;
        }}
        
        .file-info strong {{
            color: #1976D2;
        }}
        
        .sheet {{
            margin-bottom: 40px;
            border: 1px solid #e0e0e0;
            border-radius: 8px;
            overflow: hidden;
        }}
        
        .sheet-header {{
            background: linear-gradient(135deg, #3f51b5 0%, #5a67d8 100%);
            color: white;
            padding: 15px 20px;
            font-size: 1.3em;
            font-weight: 600;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        
        .sheet-stats {{
            font-size: 0.9em;
            opacity: 0.95;
        }}
        
        .block {{
            margin: 15px;
            border: 2px solid #e0e0e0;
            border-radius: 6px;
            overflow: hidden;
            transition: all 0.3s;
        }}
        
        .block:hover {{
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
            border-color: #667eea;
        }}
        
        .block-header {{
            background: #f5f5f5;
            padding: 10px 15px;
            font-weight: 600;
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 2px solid #e0e0e0;
        }}
        
        .block-type {{
            padding: 4px 12px;
            border-radius: 4px;
            font-size: 0.85em;
            font-weight: 600;
        }}
        
        .block-type.route {{
            background: #4CAF50;
            color: white;
        }}
        
        .block-type.content {{
            background: #2196F3;
            color: white;
        }}
        
        .block-type.unknown {{
            background: #9e9e9e;
            color: white;
        }}
        
        .block-content {{
            padding: 15px;
            background: white;
        }}
        
        .line {{
            padding: 8px 12px;
            margin: 4px 0;
            background: #f9f9f9;
            border-left: 3px solid #667eea;
            border-radius: 4px;
            font-family: 'Consolas', 'Monaco', monospace;
            font-size: 0.95em;
        }}
        
        .line:hover {{
            background: #fff3cd;
            border-left-color: #ffc107;
        }}
        
        .line-number {{
            display: inline-block;
            min-width: 35px;
            color: #999;
            margin-right: 10px;
            font-weight: 600;
        }}
        
        .highlight {{
            background: #fff3cd;
            padding: 2px 6px;
            border-radius: 3px;
        }}
        
        .keyword {{
            background: #e7f3ff;
            color: #1976D2;
            padding: 2px 6px;
            border-radius: 3px;
            font-weight: 600;
        }}
        
        .stats {{
            background: #f8f9fa;
            padding: 20px;
            margin-top: 30px;
            border-radius: 8px;
            border: 2px solid #e9ecef;
        }}
        
        .stats h3 {{
            margin-bottom: 15px;
            color: #495057;
        }}
        
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
        }}
        
        .stat-item {{
            background: white;
            padding: 15px;
            border-radius: 6px;
            border-left: 4px solid #667eea;
        }}
        
        .stat-label {{
            font-size: 0.9em;
            color: #666;
            margin-bottom: 5px;
        }}
        
        .stat-value {{
            font-size: 1.8em;
            font-weight: 700;
            color: #667eea;
        }}
        
        .timestamp {{
            text-align: center;
            padding: 20px;
            color: #999;
            font-size: 0.9em;
        }}
        
        .search-box {{
            margin: 20px 0;
            padding: 15px;
            background: #f8f9fa;
            border-radius: 8px;
        }}
        
        .search-box input {{
            width: 100%;
            padding: 12px;
            border: 2px solid #e0e0e0;
            border-radius: 6px;
            font-size: 1em;
            transition: all 0.3s;
        }}
        
        .search-box input:focus {{
            outline: none;
            border-color: #667eea;
            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
        }}
        
        @media print {{
            body {{
                background: white;
                padding: 0;
            }}
            .nav, .search-box {{
                display: none;
            }}
        }}
    </style>
    <script>
        function searchContent() {{
            const searchTerm = document.getElementById('searchInput').value.toLowerCase();
            const lines = document.querySelectorAll('.line');
            
            lines.forEach(line => {{
                const text = line.textContent.toLowerCase();
                if (text.includes(searchTerm)) {{
                    line.style.display = 'block';
                    line.style.background = '#fff3cd';
                }} else {{
                    line.style.display = searchTerm ? 'none' : 'block';
                    line.style.background = '#f9f9f9';
                }}
            }});
        }}
        
        function highlightKeywords() {{
            const keywords = ['备注', '不含', '路线', '代理', '费用', '货物', '运费'];
            const lines = document.querySelectorAll('.line');
            
            lines.forEach(line => {{
                let html = line.innerHTML;
                keywords.forEach(keyword => {{
                    const regex = new RegExp(keyword, 'gi');
                    html = html.replace(regex, match => `<span class="keyword">${{match}}</span>`);
                }});
                line.innerHTML = html;
            }});
        }}
        
        window.onload = highlightKeywords;
    </script>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 {title}</h1>
            <div class="subtitle">原始数据查看器 - 便于分析和调试</div>
        </div>
        
        {content_html}
        
        <div class="timestamp">
            生成时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        </div>
    </div>
</body>
</html>
        """
    
    def view_excel_layer1(self, filename=None):
        """Layer 1: 查看 Excel 原始内容"""
        import pandas as pd
        
        raw_dir = PathConfig.RAW_DATA_DIR
        if filename is None:
            files = [f for f in os.listdir(raw_dir) if f.endswith(".xlsx")]
            if not files:
                print("❌ 没有找到 Excel 文件")
                return
            filename = files[0]
        
        file_path = raw_dir / filename
        
        content_parts = []
        content_parts.append(f'<div class="file-info"><strong>文件:</strong> {filename}</div>')
        
        xls = pd.ExcelFile(file_path)
        for sheet_name in xls.sheet_names:
            df = xls.parse(sheet_name, header=None)
            
            sheet_html = f"""
            <div class="sheet">
                <div class="sheet-header">
                    <span>📋 {sheet_name}</span>
                    <span class="sheet-stats">行数: {len(df)} | 列数: {len(df.columns)}</span>
                </div>
                <div class="block-content">
            """
            
            for idx, row in df.head(20).iterrows():
                row_html = '<div class="line">'
                row_html += f'<span class="line-number">行{idx}</span>'
                
                cells = []
                for col_idx, cell in enumerate(row):
                    if pd.notna(cell) and str(cell).strip():
                        cells.append(f'<strong>列{col_idx}:</strong> {cell}')
                
                row_html += ' | '.join(cells)
                row_html += '</div>'
                sheet_html += row_html
            
            sheet_html += """
                </div>
            </div>
            """
            content_parts.append(sheet_html)
        
        html = self.generate_html(f"Layer 1: Excel 原始数据 - {filename}", '\n'.join(content_parts))
        
        output_path = self.output_dir / f"layer1_{filename.replace('.xlsx', '')}.html"
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html)
        
        print(f"✅ HTML 已生成: {output_path}")
        print(f"   在浏览器中打开查看")
        
        # 尝试自动打开浏览器
        import webbrowser
        webbrowser.open(str(output_path.absolute()))
        
        return output_path
    
    def view_excel_layer2(self, filename=None):
        """Layer 2: 查看 ExcelReader 输出"""
        reader = ExcelReader()
        raw_dir = PathConfig.RAW_DATA_DIR
        
        if filename is None:
            files = [f for f in os.listdir(raw_dir) if f.endswith(".xlsx")]
            if not files:
                print("❌ 没有找到 Excel 文件")
                return
            filename = files[0]
        
        file_path = raw_dir / filename
        
        content_parts = []
        content_parts.append(f'<div class="file-info"><strong>文件:</strong> {filename}</div>')
        
        # 搜索框
        content_parts.append("""
        <div class="search-box">
            <input type="text" id="searchInput" placeholder="🔍 输入关键词搜索..." onkeyup="searchContent()">
        </div>
        """)
        
        sheets = reader.read_excel(str(file_path), keep_row_structure=True)
        
        for sheet_name, lines in sheets.items():
            sheet_html = f"""
            <div class="sheet">
                <div class="sheet-header">
                    <span>📋 {sheet_name}</span>
                    <span class="sheet-stats">行数: {len(lines)}</span>
                </div>
                <div class="block-content">
            """
            
            for i, line in enumerate(lines[:50], 1):
                sheet_html += f'<div class="line"><span class="line-number">{i}</span>{line}</div>'
            
            if len(lines) > 50:
                sheet_html += f'<div class="line"><em>... 还有 {len(lines) - 50} 行</em></div>'
            
            sheet_html += """
                </div>
            </div>
            """
            content_parts.append(sheet_html)
        
        html = self.generate_html(f"Layer 2: ExcelReader 输出 - {filename}", '\n'.join(content_parts))
        
        output_path = self.output_dir / f"layer2_{filename.replace('.xlsx', '')}.html"
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html)
        
        print(f"✅ HTML 已生成: {output_path}")
        
        import webbrowser
        webbrowser.open(str(output_path.absolute()))
        
        return output_path
    
    def view_excel_layer3(self, filename=None):
        """Layer 3: 查看 BlockSplitter 切分结果"""
        from scripts.modules.block_splitter import BlockSplitter
        
        reader = ExcelReader()
        splitter = BlockSplitter()
        raw_dir = PathConfig.RAW_DATA_DIR
        
        if filename is None:
            files = [f for f in os.listdir(raw_dir) if f.endswith(".xlsx")]
            if not files:
                print("❌ 没有找到 Excel 文件")
                return
            filename = files[0]
        
        file_path = raw_dir / filename
        
        content_parts = []
        content_parts.append(f'<div class="file-info"><strong>文件:</strong> {filename}</div>')
        
        # 搜索框
        content_parts.append("""
        <div class="search-box">
            <input type="text" id="searchInput" placeholder="🔍 输入关键词搜索..." onkeyup="searchContent()">
        </div>
        """)
        
        sheets = reader.read_excel(str(file_path), keep_row_structure=True)
        
        total_blocks = 0
        for sheet_name, lines in sheets.items():
            blocks = splitter.split(lines)
            total_blocks += len(blocks)
            
            sheet_html = f"""
            <div class="sheet">
                <div class="sheet-header">
                    <span>📋 {sheet_name}</span>
                    <span class="sheet-stats">切分后 Block 数: {len(blocks)}</span>
                </div>
            """
            
            for i, block_dict in enumerate(blocks, 1):
                block_lines = block_dict.get("lines", [])
                block_type = block_dict.get("type", "unknown")
                block_index = block_dict.get("block_index", i - 1)
                
                type_class = block_type if block_type in ['route', 'content'] else 'unknown'
                
                block_html = f"""
                <div class="block">
                    <div class="block-header">
                        <span>📦 Block {i} <small>(索引: {block_index})</small></span>
                        <span class="block-type {type_class}">{block_type}</span>
                    </div>
                    <div class="block-content">
                """
                
                for j, line in enumerate(block_lines, 1):
                    block_html += f'<div class="line"><span class="line-number">{j}</span>{line}</div>'
                
                block_html += """
                    </div>
                </div>
                """
                sheet_html += block_html
            
            sheet_html += "</div>"
            content_parts.append(sheet_html)
        
        # 统计信息
        stats_html = f"""
        <div class="stats">
            <h3>📊 统计信息</h3>
            <div class="stats-grid">
                <div class="stat-item">
                    <div class="stat-label">总 Block 数</div>
                    <div class="stat-value">{total_blocks}</div>
                </div>
                <div class="stat-item">
                    <div class="stat-label">Sheet 数</div>
                    <div class="stat-value">{len(sheets)}</div>
                </div>
            </div>
        </div>
        """
        content_parts.append(stats_html)
        
        html = self.generate_html(f"Layer 3: BlockSplitter 切分结果 - {filename}", '\n'.join(content_parts))
        
        output_path = self.output_dir / f"layer3_{filename.replace('.xlsx', '')}.html"
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html)
        
        print(f"✅ HTML 已生成: {output_path}")
        
        import webbrowser
        webbrowser.open(str(output_path.absolute()))
        
        return output_path


def main():
    viewer = HTMLViewer()
    
    if len(sys.argv) < 2:
        print("""
用法:
  python scripts/view_raw_data_html.py layer1 [file.xlsx]  # Excel 原始数据
  python scripts/view_raw_data_html.py layer2 [file.xlsx]  # ExcelReader 输出
  python scripts/view_raw_data_html.py layer3 [file.xlsx]  # BlockSplitter 切分
  python scripts/view_raw_data_html.py all [file.xlsx]     # 生成所有层
        """)
        return
    
    cmd = sys.argv[1]
    filename = sys.argv[2] if len(sys.argv) > 2 else None
    
    if cmd == "layer1":
        viewer.view_excel_layer1(filename)
    elif cmd == "layer2":
        viewer.view_excel_layer2(filename)
    elif cmd == "layer3":
        viewer.view_excel_layer3(filename)
    elif cmd == "all":
        print("生成所有层的 HTML...")
        viewer.view_excel_layer1(filename)
        viewer.view_excel_layer2(filename)
        viewer.view_excel_layer3(filename)
        print("\n✅ 所有层已生成完毕！")
    else:
        print("未知命令，请使用 layer1/layer2/layer3/all")


if __name__ == "__main__":
    main()