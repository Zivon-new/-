# test_route_recognition.py
"""
路线识别测试脚本 v3.0
测试优化后的路线识别系统
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from scripts.modules.route_detector import RouteDetector
from scripts.modules.route_normalizer import RouteNormalizer, normalize_route
from scripts.modules.route_extractor import RouteExtractor, quick_extract_route


def test_basic_routes():
    """测试基本路线格式"""
    print("=" * 80)
    print("测试1: 基本路线格式")
    print("=" * 80)
    
    test_cases = [
        "深圳-香港",
        "国内-新加坡",
        "北京→达拉斯",
        "上海--迪拜",
        "广州至泰国",
        "香港到马来西亚",
    ]
    
    detector = RouteDetector()
    
    for text in test_cases:
        result = detector.detect(text)
        status = "✅ 通过" if result["is_route"] else "❌ 失败"
        print(f"{status} | {text}")
        if result["is_route"]:
            print(f"     parts: {result.get('cleaned_parts', result['parts'])}")
        else:
            print(f"     原因: {result['reason']}")
        print()


def test_complex_routes():
    """测试复杂路线格式（带描述）"""
    print("=" * 80)
    print("测试2: 复杂路线格式（带业务描述）")
    print("=" * 80)
    
    test_cases = [
        "深圳-香港 快递",
        "国内-新加坡 海运 DDP",
        "北京-沙特 宣传册&伴手礼 客户提供重量120KGS",
        "货交深圳-泰国：",
        "香港-马来西亚柔佛 专线",
        "上海-达拉斯-英国 空运",  # 三段路线
    ]
    
    detector = RouteDetector()
    
    for text in test_cases:
        result = detector.detect(text)
        status = "✅ 通过" if result["is_route"] else "❌ 失败"
        print(f"{status} | {text}")
        if result["is_route"]:
            print(f"     parts: {result.get('cleaned_parts', result['parts'])}")
        else:
            print(f"     原因: {result['reason']}")
        print()


def test_route_extraction():
    """测试路线提取功能"""
    print("=" * 80)
    print("测试3: 路线提取（提取起点、终点、途径地）")
    print("=" * 80)
    
    test_cases = [
        ("深圳-香港 120KGS", None),
        ("国内-新加坡-英国 空运", None),
        ("宣传册&伴手礼 客户提供重量120KGS", "北京-沙特"),  # 从完整文本提取
        ("香港-柔佛 DDP专线", None),
    ]
    
    extractor = RouteExtractor()
    
    for text, full_text in test_cases:
        if full_text:
            route = extractor.extract_route(full_text)
        else:
            route = extractor.extract_route(text)
        
        print(f"文本: {full_text or text}")
        print(f"  起点: {route['origin']}")
        print(f"  终点: {route['destination']}")
        print(f"  途径: {route['via']}")
        print(f"  重量: {route['weight']}")
        print(f"  贸易备注: {route['trade_remark']}")
        print()


def test_edge_cases():
    """测试边界情况"""
    print("=" * 80)
    print("测试4: 边界情况（应该被正确拒绝）")
    print("=" * 80)
    
    # 这些不应该被识别为路线
    test_cases = [
        "费用明细-报价单",  # 业务词汇
        "13%-15%",  # 百分比
        "5-7工作日",  # 时间
        "ABC123-XYZ456",  # 型号
        "1. 第一批货物",  # 序号
        "",  # 空文本
    ]
    
    detector = RouteDetector()
    
    for text in test_cases:
        result = detector.detect(text)
        status = "✅ 正确拒绝" if not result["is_route"] else "❌ 误判为路线"
        print(f"{status} | {text}")
        if not result["is_route"]:
            print(f"     拒绝原因: {result['reason']}")
        print()


def test_normalization():
    """测试路线标准化"""
    print("=" * 80)
    print("测试5: 路线标准化（清理业务关键词）")
    print("=" * 80)
    
    test_cases = [
        "深圳 快递-香港 专线",
        "货交国内-新加坡 DDP",
        "北京-沙特 宣传册 120KGS",
        "上海 海运-达拉斯 空运",
    ]
    
    for text in test_cases:
        cleaned = normalize_route(text)
        print(f"原始: {text}")
        print(f"清理: {cleaned}")
        print()


def test_fallback_from_sheet_name():
    """测试从sheet名称fallback"""
    print("=" * 80)
    print("测试6: Sheet名称Fallback（当无法从内容提取时）")
    print("=" * 80)
    
    test_cases = [
        ("宣传册&伴手礼 120KGS", "深圳"),  # 内容无路线，sheet名是"深圳"
        ("货物明细", "香港-新加坡"),  # 内容无路线，sheet名是路线
    ]
    
    extractor = RouteExtractor()
    
    for content, sheet_name in test_cases:
        route = extractor.extract_route(content, fallback_start=sheet_name)
        
        print(f"内容: {content}")
        print(f"Sheet名: {sheet_name}")
        print(f"  提取结果:")
        print(f"    起点: {route['origin']}")
        print(f"    终点: {route['destination']}")
        print()


def run_all_tests():
    """运行所有测试"""
    print("\n" + "=" * 80)
    print("路线识别系统 v3.0 - 完整测试")
    print("=" * 80 + "\n")
    
    try:
        test_basic_routes()
        test_complex_routes()
        test_route_extraction()
        test_edge_cases()
        test_normalization()
        test_fallback_from_sheet_name()
        
        print("\n" + "=" * 80)
        print("✅ 所有测试完成！")
        print("=" * 80)
        
    except Exception as e:
        print(f"\n❌ 测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit(run_all_tests())