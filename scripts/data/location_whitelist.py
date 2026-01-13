# scripts/data/location_whitelist.py
"""
物流地点白名单（v2.0 扩展版）
包含全球主要物流中心和常见地名
"""

LOCATION_WHITELIST = {
    # ========== 中国大陆 ==========
    "深圳", "广州", "上海", "北京", "天津", "重庆", "成都", "西安",
    "武汉", "杭州", "南京", "苏州", "宁波", "青岛", "大连", "厦门",
    "东莞", "佛山", "中山", "珠海", "惠州", "江门", "肇庆", "汕头",
    "福州", "泉州", "温州", "台州", "义乌", "郑州", "长沙", "合肥",
    "南昌", "沈阳", "哈尔滨", "长春", "呼和浩特", "乌鲁木齐", "兰州",
    "银川", "西宁", "昆明", "贵阳", "南宁", "海口", "三亚", "拉萨",
    "石家庄", "太原", "济南", "烟台", "威海", "淄博", "潍坊", "临沂",
    "国内", "中国", "内地", "大陆", "广东", "浙江", "江苏", "山东",
    "河北", "河南", "湖北", "湖南", "四川", "陕西", "福建", "安徽",
    
    # ========== 港澳台 ==========
    "香港", "澳门", "台湾", "台北", "高雄", "台中", "HK", "HongKong",
    
    # ========== 东亚 ==========
    "日本", "东京", "大阪", "名古屋", "横滨", "神户", "福冈", "札幌",
    "韩国", "首尔", "釜山", "仁川", "Seoul", "Busan",
    "朝鲜", "平壤",
    "蒙古", "乌兰巴托",
    
    # ========== 东南亚 ==========
    "新加坡", "Singapore", "SG", "狮城",
    "马来西亚", "马来", "吉隆坡", "槟城", "柔佛", "新山", "巴生港", "Malaysia",
    "泰国", "曼谷", "Bangkok", "清迈", "普吉",
    "越南", "河内", "胡志明", "Vietnam", "西贡",
    "菲律宾", "马尼拉", "Manila", "宿务",
    "印度尼西亚", "印尼", "雅加达", "Jakarta", "巴厘岛",
    "缅甸", "仰光", "Myanmar",
    "柬埔寨", "金边", "Cambodia",
    "老挝", "万象",
    "文莱", "斯里巴加湾",
    "东帝汶",
    
    # ========== 南亚 ==========
    "印度", "新德里", "孟买", "班加罗尔", "金奈", "加尔各答", "India", "Delhi",
    "巴基斯坦", "伊斯兰堡", "卡拉奇", "Pakistan",
    "孟加拉", "达卡", "Bangladesh",
    "斯里兰卡", "科伦坡", "SriLanka",
    "尼泊尔", "加德满都",
    "不丹", "廷布",
    "马尔代夫", "马累",
    
    # ========== 中东 ==========
    "沙特", "沙特阿拉伯", "利雅得", "吉达", "Saudi", "Riyadh",
    "阿联酋", "迪拜", "阿布扎比", "Dubai", "UAE", "AbuDhabi",
    "卡塔尔", "多哈", "Qatar", "Doha",
    "科威特", "Kuwait",
    "巴林", "Bahrain",
    "阿曼", "马斯喀特", "Oman",
    "伊朗", "德黑兰", "Iran",
    "伊拉克", "巴格达", "Iraq",
    "叙利亚", "大马士革",
    "约旦", "安曼", "Jordan",
    "以色列", "特拉维夫", "耶路撒冷", "Israel",
    "黎巴嫩", "贝鲁特",
    "也门", "萨那",
    "土耳其", "伊斯坦布尔", "安卡拉", "Turkey", "Istanbul",
    
    # ========== 欧洲 ==========
    # 西欧
    "英国", "伦敦", "曼彻斯特", "伯明翰", "UK", "London", "England",
    "法国", "巴黎", "马赛", "里昂", "France", "Paris",
    "德国", "柏林", "汉堡", "慕尼黑", "法兰克福", "Germany", "Frankfurt", "Berlin",
    "荷兰", "阿姆斯特丹", "鹿特丹", "Netherlands", "Amsterdam",
    "比利时", "布鲁塞尔", "安特卫普", "Belgium", "Brussels",
    "卢森堡", "Luxembourg",
    "瑞士", "苏黎世", "日内瓦", "Switzerland", "Zurich",
    "奥地利", "维也纳", "Austria", "Vienna",
    
    # 南欧
    "西班牙", "马德里", "巴塞罗那", "Spain", "Madrid", "Barcelona",
    "葡萄牙", "里斯本", "Portugal", "Lisbon",
    "意大利", "罗马", "米兰", "威尼斯", "Italy", "Rome", "Milan",
    "希腊", "雅典", "Greece", "Athens",
    "马耳他", "Malta",
    
    # 北欧
    "瑞典", "斯德哥尔摩", "Sweden", "Stockholm",
    "挪威", "奥斯陆", "Norway", "Oslo",
    "芬兰", "赫尔辛基", "Finland", "Helsinki",
    "丹麦", "哥本哈根", "Denmark", "Copenhagen",
    "冰岛", "雷克雅未克", "Iceland",
    
    # 东欧
    "俄罗斯", "莫斯科", "圣彼得堡", "Russia", "Moscow",
    "波兰", "华沙", "Poland", "Warsaw",
    "捷克", "布拉格", "Czech", "Prague",
    "匈牙利", "布达佩斯", "Hungary", "Budapest",
    "罗马尼亚", "布加勒斯特", "Romania",
    "保加利亚", "索非亚", "Bulgaria",
    "乌克兰", "基辅", "Ukraine", "Kiev","爱尔兰",
    
    # ========== 北美洲 ==========
    "美国", "USA", "US", "America", "美",
    "纽约", "洛杉矶", "芝加哥", "休斯顿", "凤凰城", "费城", "圣安东尼奥",
    "圣地亚哥", "达拉斯", "旧金山", "西雅图", "波士顿", "迈阿密", "亚特兰大",
    "NewYork", "LosAngeles", "Chicago", "Houston", "Dallas", "Seattle",
    "加拿大", "多伦多", "温哥华", "蒙特利尔", "Canada", "Toronto", "Vancouver",
    "墨西哥", "墨西哥城", "Mexico",
    
    # ========== 南美洲 ==========
    "巴西", "圣保罗", "里约热内卢", "Brazil", "SaoPaulo",
    "阿根廷", "布宜诺斯艾利斯", "Argentina", "BuenosAires",
    "智利", "圣地亚哥", "Chile", "Santiago",
    "秘鲁", "利马", "Peru", "Lima",
    "哥伦比亚", "波哥大", "Colombia", "Bogota",
    "委内瑞拉", "加拉加斯", "Venezuela",
    "厄瓜多尔", "基多", "Ecuador",
    "玻利维亚", "拉巴斯", "Bolivia",
    
    # ========== 大洋洲 ==========
    "澳大利亚", "澳洲", "悉尼", "墨尔本", "布里斯班", "珀斯", "Australia", "Sydney", "Melbourne",
    "新西兰", "奥克兰", "惠灵顿", "NewZealand", "Auckland",
    "斐济", "Fiji",
    "巴布亚新几内亚", "PNG",
    
    # ========== 非洲 ==========
    "南非", "约翰内斯堡", "开普敦", "SouthAfrica", "Johannesburg",
    "埃及", "开罗", "Egypt", "Cairo",
    "尼日利亚", "拉各斯", "Nigeria", "Lagos",
    "肯尼亚", "内罗毕", "Kenya", "Nairobi",
    "埃塞俄比亚", "亚的斯亚贝巴", "Ethiopia",
    "摩洛哥", "卡萨布兰卡", "Morocco",
    "阿尔及利亚", "阿尔及尔", "Algeria",
    "坦桑尼亚", "达累斯萨拉姆", "Tanzania",
    "加纳", "阿克拉", "Ghana",
    
    # ========== 特殊地区/港口 ==========
    "欧洲", "Europe", "亚洲", "Asia", "美洲", "Americas",
    "鹿特丹港", "安特卫普港", "汉堡港", "不来梅港",
    "洛杉矶港", "长滩港", "纽约港", "休斯顿港",
    "新加坡港", "香港港", "上海港", "深圳港", "宁波港",
    "盐田", "蛇口", "赤湾", "南沙", "黄埔",
    
    # ========== 其他常用简称 ==========
    "海外", "境外", "国际", "全球", "世界",
}


def is_valid_location(location: str) -> bool:
    """
    判断是否为有效地点
    支持部分匹配
    """
    if not location:
        return False
    
    location = location.strip()
    
    # 完全匹配
    if location in LOCATION_WHITELIST:
        return True
    
    # 部分匹配（地点在白名单中或白名单在地点中）
    for valid_loc in LOCATION_WHITELIST:
        if valid_loc in location or location in valid_loc:
            return True
    
    return False


def clean_location_text(text: str) -> str:
    """
    清理地点文本中的业务关键词
    保留地点名称
    """
    if not text:
        return ""
    
    # 移除常见前缀
    prefixes = ['货交', '从', '自', '按']
    for prefix in prefixes:
        if text.startswith(prefix):
            text = text[len(prefix):]
    
    # 移除常见后缀（在冒号或特定关键词处截断）
    import re
    text = re.split(r'[：:,，]', text)[0]
    
    # 移除业务关键词
    business_words = [
        '专线', '一般贸易', '海运', '空运', '快递', '方案', 
        '贸易', '代理', '贸代', '过港', '快件', '正清', '双清',
        '宣传册', '伴手礼', '货物', '客户', '提供', '重量', 'KGS', 'KG'
    ]
    
    for word in business_words:
        if word in text:
            # 在关键词处截断（保留关键词之前的部分）
            parts = text.split(word)
            text = parts[0].strip()
            break
    
    return text.strip()


__all__ = ['LOCATION_WHITELIST', 'is_valid_location', 'clean_location_text']