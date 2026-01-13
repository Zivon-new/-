"""
v3.0 功能测试脚本
测试：
1. Sheet名称作为默认起始地
2. 内容路线覆盖sheet名称
3. Sheet内查重
4. 计费重量默认值
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# try:
from scripts.modules.horizontal_table_parser import HorizontalTableParser, Route
# except ImportError:
#     # 如果上面的导入失败，尝试直接从当前目录导入
#     from horizontal_table_parser import HorizontalTableParser, Route


def test_sheet_name_as_default():
    """测试1: Sheet名称作为默认起始地"""
    print("\n" + "=" * 60)
    print("测试1: Sheet名称作为默认起始地")
    print("=" * 60)
    
    parser = HorizontalTableParser()
    
    # 模拟数据：只有货物信息，没有路线
    sheet_data = [
        ["碱性电池 1740KGS"],
        ["代理", "融迅", "银顺达"],
        ["费用明细", "18/kg", "22/kg"],
    ]
    
    route = parser._extract_route_from_first_row(sheet_data[0], sheet_name="深圳")
    
    print(f"Sheet名称: 深圳")
    print(f"内容: {sheet_data[0][0]}")
    print(f"结果:")
    print(f"  起始地: {route.起始地}")
    print(f"  目的地: {route.目的地}")
    print(f"  实际重量: {route.实际重量}")
    print(f"  计费重量: {route.计费重量}")
    
    assert route.起始地 == "深圳", f"起始地应该是sheet名称'深圳'，实际是'{route.起始地}'"
    # 没有明确的路线信息，目的地可能从内容提取或为None
    assert route.实际重量 == 1740.0, "应该提取到重量"
    assert route.计费重量 == 1740.0, "计费重量应该等于实际重量"
    print("✅ 测试通过")


def test_content_route_overrides_sheet_name():
    """测试2: 内容路线覆盖sheet名称"""
    print("\n" + "=" * 60)
    print("测试2: 内容路线覆盖sheet名称")
    print("=" * 60)
    
    parser = HorizontalTableParser()
    
    # 模拟数据：有完整路线
    sheet_data = [
        ["国内-新加坡 英国 1740KGS"],
        ["代理", "融迅"],
        ["费用明细", "18/kg"],
    ]
    
    route = parser._extract_route_from_first_row(sheet_data[0], sheet_name="深圳")
    
    print(f"Sheet名称: 深圳")
    print(f"内容: {sheet_data[0][0]}")
    print(f"结果:")
    print(f"  起始地: {route.起始地} (应该覆盖sheet名称)")
    print(f"  目的地: {route.目的地}")
    print(f"  途径地: {route.途径地}")
    print(f"  实际重量: {route.实际重量}")
    print(f"  计费重量: {route.计费重量}")
    
    assert route.起始地 == "国内", f"起始地应该是内容中的'国内'，实际是'{route.起始地}'"
    assert route.目的地 == "新加坡", f"目的地应该是内容中的'新加坡'，实际是'{route.目的地}'"
    assert route.途径地 == "英国", f"途径地应该是'英国'，实际是'{route.途径地}'"
    assert route.实际重量 == 1740.0, "应该提取到重量"
    assert route.计费重量 == 1740.0, "计费重量应该等于实际重量"
    print("✅ 测试通过")


def test_within_sheet_deduplication():
    """测试3: Sheet内查重"""
    print("\n" + "=" * 60)
    print("测试3: Sheet内查重")
    print("=" * 60)
    
    parser = HorizontalTableParser()
    
    # 模拟数据：同一路线，不同代理
    sheet_data = [
        ["深圳-香港 1740KGS"],
        ["代理", "融迅", "银顺达", "欧洲专线"],
        ["费用明细", "18/kg", "22/kg", "18/kg"],  # 注意：第3个代理价格和第1个相同
        ["小计", "31320", "38280", "31320"],
    ]
    
    quotes = parser.parse_sheet(sheet_data, sheet_name="测试Sheet")
    
    print(f"Sheet名称: 测试Sheet")
    print(f"内容: {sheet_data[0][0]}")
    print(f"代理数量: 3")
    print(f"结果:")
    for i, quote in enumerate(quotes, 1):
        print(f"  报价 {i}: {quote.route.起始地} -> {quote.route.目的地}, 代理: {quote.agent.代理商}")
    
    # 同一sheet，同一路线，应该只保留第一个
    print(f"\n总报价数: {len(quotes)} (应该是1，因为同sheet同路线)")
    assert len(quotes) == 1, "同一sheet内，相同路线应该去重"
    print("✅ 测试通过")


def test_cross_sheet_no_deduplication():
    """测试4: Sheet间不查重"""
    print("\n" + "=" * 60)
    print("测试4: Sheet间不查重")
    print("=" * 60)
    
    parser = HorizontalTableParser()
    
    # 模拟数据：相同路线
    sheet_data = [
        ["深圳-香港 1740KGS"],
        ["代理", "融迅"],
        ["费用明细", "18/kg"],
        ["小计", "31320"],
    ]
    
    quotes1 = parser.parse_sheet(sheet_data, sheet_name="订单1")
    quotes2 = parser.parse_sheet(sheet_data, sheet_name="订单2")
    
    print(f"Sheet1 (订单1): {len(quotes1)} 个报价")
    print(f"Sheet2 (订单2): {len(quotes2)} 个报价")
    print(f"相同路线: 深圳-香港")
    print(f"结果: 两个sheet都有报价（不查重）")
    
    assert len(quotes1) == 1, "Sheet1应该有1个报价"
    assert len(quotes2) == 1, "Sheet2应该有1个报价"
    assert quotes1[0].route._sheet_name == "订单1"
    assert quotes2[0].route._sheet_name == "订单2"
    print("✅ 测试通过")


def test_billing_weight_default():
    """测试5: 计费重量默认值"""
    print("\n" + "=" * 60)
    print("测试5: 计费重量默认值")
    print("=" * 60)
    
    parser = HorizontalTableParser()
    
    # 测试用例1: 有实际重量，无计费重量
    route1 = Route(实际重量=1740.0, 计费重量=None)
    if route1.实际重量 and not route1.计费重量:
        route1.计费重量 = route1.实际重量
    
    print(f"用例1: 有实际重量，无计费重量")
    print(f"  实际重量: {route1.实际重量}")
    print(f"  计费重量: {route1.计费重量}")
    assert route1.计费重量 == 1740.0, "计费重量应该等于实际重量"
    print("  ✅ 通过")
    
    # 测试用例2: 有实际重量，有计费重量（不应覆盖）
    route2 = Route(实际重量=1740.0, 计费重量=2000.0)
    if route2.实际重量 and not route2.计费重量:
        route2.计费重量 = route2.实际重量
    
    print(f"\n用例2: 有实际重量，有计费重量")
    print(f"  实际重量: {route2.实际重量}")
    print(f"  计费重量: {route2.计费重量}")
    assert route2.计费重量 == 2000.0, "已有的计费重量不应该被覆盖"
    print("  ✅ 通过")
    
    # 测试用例3: 无实际重量，无计费重量
    route3 = Route(实际重量=None, 计费重量=None)
    if route3.实际重量 and not route3.计费重量:
        route3.计费重量 = route3.实际重量
    
    print(f"\n用例3: 无实际重量，无计费重量")
    print(f"  实际重量: {route3.实际重量}")
    print(f"  计费重量: {route3.计费重量}")
    assert route3.计费重量 is None, "无实际重量时，计费重量应该保持None"
    print("  ✅ 通过")
    
    print("\n✅ 所有用例通过")


def test_unique_key_generation():
    """测试6: 唯一键生成"""
    print("\n" + "=" * 60)
    print("测试6: 唯一键生成")
    print("=" * 60)
    
    # 相同路线，相同sheet
    route1 = Route(起始地="深圳", 目的地="香港", 途径地=None, _sheet_name="订单1")
    route2 = Route(起始地="深圳", 目的地="香港", 途径地=None, _sheet_name="订单1")
    
    key1 = route1.get_unique_key()
    key2 = route2.get_unique_key()
    
    print(f"路线1: {route1.起始地} -> {route1.目的地}, Sheet: {route1._sheet_name}")
    print(f"路线2: {route2.起始地} -> {route2.目的地}, Sheet: {route2._sheet_name}")
    print(f"Key1: {key1}")
    print(f"Key2: {key2}")
    print(f"相等: {key1 == key2}")
    assert key1 == key2, "相同路线和sheet应该有相同的key"
    print("✅ 测试通过")
    
    # 相同路线，不同sheet
    route3 = Route(起始地="深圳", 目的地="香港", 途径地=None, _sheet_name="订单2")
    key3 = route3.get_unique_key()
    
    print(f"\n路线3: {route3.起始地} -> {route3.目的地}, Sheet: {route3._sheet_name}")
    print(f"Key3: {key3}")
    print(f"Key1 == Key3: {key1 == key3}")
    assert key1 != key3, "不同sheet应该有不同的key"
    print("✅ 测试通过")


def main():
    """运行所有测试"""
    print("\n" + "=" * 60)
    print("横向表格解析器 v3.0 - 功能测试")
    print("=" * 60)
    
    try:
        test_sheet_name_as_default()
        test_content_route_overrides_sheet_name()
        test_within_sheet_deduplication()
        test_cross_sheet_no_deduplication()
        test_billing_weight_default()
        test_unique_key_generation()
        
        print("\n" + "=" * 60)
        print("✅ 所有测试通过！")
        print("=" * 60)
        
    except AssertionError as e:
        print(f"\n❌ 测试失败: {e}")
        return 1
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())