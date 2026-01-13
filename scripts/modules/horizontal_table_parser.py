"""
横向对比表格解析器 v9.0 - 数据库结构适配版
核心修改：
1. ⭐ 适配新数据库结构（交易开始日期/结束日期替代交易时间）
2. ⭐ 字段重命名：实际重量(/kg)、计费重量(/kg)、总体积(/cbm)
3. ⭐ 集成RouteFieldsEnhancer提取交易日期
4. ✅ 保持路线识别100%准确率（RouteExtractor完全不改动）
5. ✅ 继承v7.0所有功能和修复

基于v7.0，完全兼容新数据库结构。
"""

import re
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field, asdict

# 导入依赖
# ⭐ v9.0: 分别处理每个模块的导入，避免一个失败导致所有失败

# 1. 导入LOCATION_WHITELIST
try:
    from scripts.data.location_whitelist import LOCATION_WHITELIST, is_valid_location
except ImportError:
    try:
        from data.location_whitelist import LOCATION_WHITELIST, is_valid_location
    except ImportError:
        # Fallback: 使用内置白名单
        LOCATION_WHITELIST = {
            "深圳", "上海", "北京", "广州", "香港", "澳门", "国内", "中国",
            "新加坡", "日本", "韩国", "马来西亚", "马来", "泰国", "越南",
            "菲律宾", "印尼", "印度", "沙特", "迪拜", "巴基斯坦",
            "英国", "法国", "德国", "法兰克福", "荷兰", "西班牙", "意大利",
            "美国", "达拉斯", "迈阿密", "圣何塞", "加拿大", "墨西哥", "巴西", "巴拿马",
            "澳洲", "澳大利亚", "新西兰", "柔佛", "雅加达", "胡志明", "首尔",
            "柬埔寨", "台中", "天津", "巴尔博亚", "宁波", "印度尼西亚"
        }
        
        def is_valid_location(location: str) -> bool:
            if not location:
                return False
            return any(wl_loc in location.lower() or location.lower() in wl_loc.lower() for wl_loc in LOCATION_WHITELIST)

# 2. 导入RouteExtractor
try:
    from scripts.modules.route_extractor import RouteExtractor
except ImportError:
    try:
        from route_extractor import RouteExtractor
    except ImportError:
        RouteExtractor = None

# 3. 导入RouteFieldsEnhancer
try:
    from scripts.modules.route_fields_enhancer import RouteFieldsEnhancer
except ImportError:
    try:
        from route_fields_enhancer import RouteFieldsEnhancer
    except ImportError:
        RouteFieldsEnhancer = None


@dataclass
class Route:
    """路线信息 - 适配新数据库结构"""
    起始地: Optional[str] = None
    目的地: Optional[str] = None
    途径地: Optional[str] = None
    贸易备注: Optional[str] = None
    
    # ⭐ v9.0: 交易日期字段（替代交易时间字符串）
    交易开始日期: Optional[str] = None  # DATE格式："YYYY-MM-DD"
    交易结束日期: Optional[str] = None  # DATE格式："YYYY-MM-DD"
    
    # ⭐ v9.0: 带单位标注的字段名（符合数据库结构）
    # 注意：这里只存储数字，单位在字段名中标注
    实际重量: Optional[float] = None  # 对应数据库: 实际重量(/kg)
    计费重量: Optional[float] = None  # 对应数据库: 计费重量(/kg)
    总体积: Optional[float] = None    # 对应数据库: 总体积(/cbm)
    货值: Optional[float] = None
    
    _raw: Optional[str] = None
    _sheet_name: Optional[str] = None
    
    def to_dict(self):
        """保留_raw，但排除_sheet_name"""
        d = asdict(self)
        return {k: v for k, v in d.items() if k != '_sheet_name'}
    
    @staticmethod
    def normalize_location(location: Optional[str]) -> Optional[str]:
        """
        标准化地理位置名称，用于更智能的路线去重
        
        规则：
        1. 移除国家前缀（如"奥地利维也纳" → "维也纳"）
        2. 统一常见地名（如"马来西亚" → "马来"）
        3. 移除多余空格和符号
        
        Examples:
            "奥地利维也纳" → "维也纳"
            "马来西亚" → "马来"
            "中国香港" → "香港"
        """
        if not location:
            return location
        
        location = str(location).strip()
        
        # 地理位置标准化映射表
        # 格式：完整名称 → 标准名称
        location_normalization_map = {
            # 欧洲
            '奥地利维也纳': '维也纳',
            '德国法兰克福': '法兰克福',
            '荷兰阿姆斯特丹': '阿姆斯特丹',
            '英国伦敦': '伦敦',
            '法国巴黎': '巴黎',
            
            # 亚洲
            '马来西亚': '马来',
            '印度尼西亚': '印尼',
            '中国香港': '香港',
            '中国深圳': '深圳',
            '中国广州': '广州',
            '中国北京': '北京',
            '中国上海': '上海',
            
            # 美洲
            '美国达拉斯': '达拉斯',
            '美国迈阿密': '迈阿密',
            '美国圣何塞': '圣何塞',
            
            # 其他常见变体
            '新加坡共和国': '新加坡',
            '越南河内': '河内',
            '泰国曼谷': '曼谷',
            '菲律宾马尼拉': '马尼拉',
            '印尼雅加达': '雅加达',
            '马来柔佛': '柔佛',
        }
        
        # 应用标准化映射
        for full_name, standard_name in location_normalization_map.items():
            if full_name in location:
                location = location.replace(full_name, standard_name)
        
        return location
    
    def get_unique_key(self) -> str:
        """生成唯一键用于去重（包含_sheet_name）"""
        return f"{self.起始地}|{self.目的地}|{self.途径地}|{self._sheet_name}"
    
    def get_route_signature(self) -> str:
        """
        生成路线签名用于Sheet内去重（使用标准化地名）
        
        使用标准化后的地名进行比较，这样：
        - "国内-奥地利维也纳" 和 "国内-维也纳" 会被识别为同一路线
        - "深圳-马来西亚" 和 "深圳-马来" 会被识别为同一路线
        """
        起始地_标准 = self.normalize_location(self.起始地)
        目的地_标准 = self.normalize_location(self.目的地)
        途径地_标准 = self.normalize_location(self.途径地) if self.途径地 else None
        
        return f"{起始地_标准}|{目的地_标准}|{途径地_标准}"



@dataclass
class Agent:
    """代理商信息"""
    代理商: Optional[str] = None
    运输方式: Optional[str] = None
    贸易类型: Optional[str] = None
    代理备注: Optional[str] = None
    不含: Optional[str] = None
    时效: Optional[str] = None
    是否赔付: str = "0"
    赔付内容: Optional[str] = None


@dataclass
class FeeItem:
    """费用明细"""
    费用类型: str = "按重量收费"
    费用名称: Optional[str] = None
    单价: Optional[float] = None
    单位: Optional[str] = None
    数量: Optional[float] = None


@dataclass
class FeeTotal:
    """费用汇总"""
    费用总价: Optional[float] = None


@dataclass
class Summary:
    """汇总信息"""
    小计: Optional[float] = None
    税率: Optional[float] = None
    税金: Optional[float] = None
    汇损率: Optional[float] = None
    汇损: Optional[float] = None
    总计: Optional[float] = None
    备注: Optional[str] = None


@dataclass
class QuoteBlock:
    """一个完整的报价块"""
    route: Route
    agent: Agent
    fee_items: List[FeeItem] = field(default_factory=list)
    fee_total: FeeTotal = field(default_factory=FeeTotal)
    summary: Summary = field(default_factory=Summary)


class HorizontalTableParser:
    """横向对比表格解析器 v7.0 - 最终完善版"""
    
    def __init__(self):
        self.logger = None
        self.debug_logger = None
        
        if RouteExtractor:
            self.route_extractor = RouteExtractor()
        else:
            self.route_extractor = None
        
        # ⭐ v9.0: 初始化路线字段增强器
        if RouteFieldsEnhancer:
            self.route_enhancer = RouteFieldsEnhancer()
            print(f"[DEBUG] ✅ RouteFieldsEnhancer初始化成功: {self.route_enhancer}")
        else:
            self.route_enhancer = None
            print(f"[DEBUG] ⚠️ RouteFieldsEnhancer导入失败，route_enhancer=None")
        
        # 正则表达式
        self.weight_pattern = re.compile(r'(\d+(?:\.\d+)?)\s*(?:kgs?|KGS?|千克|公斤)', re.IGNORECASE)
        self.volume_pattern = re.compile(r'(\d+(?:\.\d+)?)\s*(?:cbm|CBM|立方|方)', re.IGNORECASE)
        self.value_pattern = re.compile(r'(\d+(?:\.\d+)?)\s*(?:元|rmb|RMB|¥|usd|USD|\$)', re.IGNORECASE)
        
        # 路线模式
        self.route_pattern = re.compile(
            r'([\u4e00-\u9fa5a-zA-Z]{2,20})\s*[-—→>至到]+\s*'
            r'([\u4e00-\u9fa5a-zA-Z]{2,20})'
            r'(?:\s*[-—→>至到]+\s*([\u4e00-\u9fa5a-zA-Z]{2,20}))?'
        )
        
        # ⭐ v7.0: 更精确的表格标题行模式
        self.table_header_pattern = re.compile(
            r'^(?:货交)?([\u4e00-\u9fa5a-zA-Z]{2,15})\s*[-—→>]+\s*([\u4e00-\u9fa5a-zA-Z]{2,15})'
        )
        
        self.price_unit_pattern = re.compile(r'(\d+(?:\.\d+)?)\s*/\s*(kg|KG|CBM|cbm|票)', re.IGNORECASE)
        self.timeliness_pattern = re.compile(r'(\d+)\s*[-~至到]\s*(\d+)\s*(?:天|工作日|个工作日)?')
        
        # 关键词
        self.agent_keywords = ['代理', '货代', '公司']
        self.fee_keywords = ['费用', '明细', '收费', '单价']
        self.summary_keywords = ['小计', '合计', '总计', '总价']
        self.remark_keywords = ['备注', '说明', '注意']
        self.timeliness_keywords = ['时效', '时间', '工期', '交期']
        self.compensation_keywords = ['赔付', '理赔', '保险']
        
        # ⭐ v7.0: 业务后缀（需要清理）
        self.business_suffixes = [
            '小货的', '快递', '价格', '成本', '方案', '询价', '预估',
            '贸易代理', '贸代', '专线', '海运', '空运', '正清', '双清',
            '包税', '到门', '到港', '的', '之', '啊', '吧', '呢'
        ]
        
        # 运输方式和贸易类型
        self.transport_keywords = {
            '海运': ['海运', '海派', 'sea', 'ocean'],
            '空运': ['空运', '空派', 'air'],
            '铁路': ['铁路', '铁运', 'rail'],
            '快递': ['快递', 'express', 'courier', 'DHL', 'FedEx', 'UPS'],
            '卡车': ['卡车', 'truck', '陆运']
        }
        
        self.trade_keywords = {
            '专线': ['专线'],
            '包税': ['包税', 'DDP'],
            '双清': ['双清'],
            '正清': ['正清'],
            '到门': ['到门', 'door'],
            '到港': ['到港', 'port']
        }
    
    def parse_sheet(self, sheet_data: List[List], sheet_name: str = None, filename: str = None) -> List[QuoteBlock]:
        """解析一个sheet的数据"""
        if self.debug_logger:
            self.debug_logger.start_sheet(sheet_name or "未命名Sheet")
        
        if not sheet_data:
            if self.debug_logger:
                self.debug_logger.log_block(
                    block_index=0,
                    lines=[],
                    status="skipped",
                    reason="sheet数据为空"
                )
            return []
        
        if self.logger:
            self.logger.info(f"  📋 解析Sheet: {sheet_name}, 行数: {len(sheet_data)}")
        
        # 1. 扫描sheet，找到所有横向表格的边界
        table_boundaries = self._find_table_boundaries(sheet_data)
        
        if self.logger:
            self.logger.info(f"  发现 {len(table_boundaries)} 个横向表格")
        
        # 2. 解析每个横向表格
        all_quotes = []
        seen_routes = set()
        has_content_route = False
        
        for table_idx, (start_row, end_row, route_text) in enumerate(table_boundaries, 1):
            if self.logger:
                self.logger.debug(f"  处理表格 {table_idx}: 第{start_row+1}-{end_row+1}行, 路线: {route_text}")
            
            table_data = sheet_data[start_row:end_row+1]
            quotes = self._parse_single_table(table_data, route_text, sheet_name)
            
            # Debug日志
            if self.debug_logger:
                lines = [' '.join(str(c) for c in row if c) for row in table_data]
                
                if quotes and len(quotes) > 0:
                    for quote in quotes:
                        extracted = {
                            "起始地": quote.route.起始地,
                            "目的地": quote.route.目的地,
                            "代理商": quote.agent.代理商,
                            "_sheet_name": quote.route._sheet_name,
                            "_raw": quote.route._raw[:50] if quote.route._raw else None
                        }
                        if quote.route.实际重量:
                            extracted["实际重量"] = quote.route.实际重量
                        
                        self.debug_logger.log_block(
                            block_index=table_idx - 1,
                            lines=lines,
                            status="success",
                            extracted=extracted,
                            row_range=(start_row, end_row)
                        )
                else:
                    self.debug_logger.log_block(
                        block_index=table_idx - 1,
                        lines=lines,
                        status="failed",
                        reason="解析失败（route不完整或无代理商）",
                        row_range=(start_row, end_row)
                    )
            
            # Sheet内去重
            for quote in quotes:
                if quote and quote.route:
                    route_signature = quote.route.get_route_signature()
                    
                    if quote.route._raw and quote.route._raw != sheet_name:
                        has_content_route = True
                    
                    if route_signature not in seen_routes:
                        seen_routes.add(route_signature)
                        all_quotes.append(quote)
                        
                        if self.logger:
                            self.logger.debug(f"    ✅ 添加QuoteBlock: {quote.route.起始地} -> {quote.route.目的地}")
                    else:
                        if self.logger:
                            self.logger.debug(f"    ⏭️ 跳过重复路线: {quote.route.起始地} -> {quote.route.目的地}")
        
        # Fallback策略
        if not all_quotes and not has_content_route and sheet_name:
            if self.logger:
                self.logger.debug(f"  内容中未提取到QuoteBlock，尝试从sheet名提取: {sheet_name}")
            
            sheet_route = self._extract_route_from_text(sheet_name, sheet_name)
            
            if sheet_route.起始地 and sheet_route.目的地:
                quote = QuoteBlock(
                    route=sheet_route,
                    agent=Agent(代理商=f"{sheet_name}-sheet名提取"),
                    fee_items=[],
                    fee_total=FeeTotal(),
                    summary=Summary()
                )
                all_quotes.append(quote)
                if self.logger:
                    self.logger.debug(f"    ✅ 从sheet名添加QuoteBlock: {sheet_route.起始地} -> {sheet_route.目的地}")
        
        # ⭐ v9.0: 统一为所有quotes添加交易日期（从filename提取）
        # ⭐ Debug信息
        if self.logger:
            self.logger.info(f"  🔍 [日期提取] 检查条件:")
            self.logger.info(f"      filename = {filename}")
            self.logger.info(f"      route_enhancer = {self.route_enhancer}")
            self.logger.info(f"      all_quotes数量 = {len(all_quotes) if all_quotes else 0}")
        
        if filename and self.route_enhancer and all_quotes:
            if self.logger:
                self.logger.info(f"  🔍 [日期提取] 开始提取，文件名: {filename}")
            
            start_date, end_date = self.route_enhancer.extract_transaction_dates(filename)
            
            if self.logger:
                self.logger.info(f"  🔍 [日期提取] 提取结果: {start_date} 至 {end_date}")
            
            if start_date and end_date:
                for quote in all_quotes:
                    if quote and quote.route:
                        quote.route.交易开始日期 = start_date
                        quote.route.交易结束日期 = end_date
                
                if self.logger:
                    self.logger.info(f"  ✅ [日期提取] 已为 {len(all_quotes)} 个routes添加交易日期: {start_date} 至 {end_date}")
            else:
                if self.logger:
                    self.logger.warning(f"  ⚠️ [日期提取] 日期提取失败：start={start_date}, end={end_date}")
        else:
            if self.logger:
                self.logger.warning(f"  ⚠️ [日期提取] 条件不满足，跳过日期提取")
                if not filename:
                    self.logger.warning(f"      原因：filename为None或空")
                if not self.route_enhancer:
                    self.logger.warning(f"      原因：route_enhancer未初始化")
                if not all_quotes:
                    self.logger.warning(f"      原因：all_quotes为空")
        
        if self.logger:
            self.logger.info(f"  ✅ Sheet解析完成: 提取 {len(all_quotes)} 个QuoteBlock (去重后)")
        
        return all_quotes
    
    def _find_table_boundaries(self, sheet_data: List[List]) -> List[Tuple[int, int, str]]:
        """
        ⭐ v7.0: 优化table边界识别
        1. 识别"货交XXX-XXX："格式（多路线sheet）
        2. 识别"深圳-泰国："格式（保留冒号结尾的真实路线）
        3. 排除"XXX-XXX："格式（单纯费用标题，如"香港-马来："）
        """
        boundaries = []
        current_start = None
        current_route_text = None
        
        for row_idx, row in enumerate(sheet_data):
            if not row or not row[0]:
                continue
            
            first_cell = str(row[0]).strip()
            
            # 长度限制
            if len(first_cell) > 80:
                continue
            
            # ⭐ v7.0: 判断是否是有效的table标题
            is_valid_title = False
            
            # 规则1: "货交XXX-XXX："格式（多路线sheet必须识别）
            if first_cell.startswith('货交') and (':' in first_cell or '：' in first_cell):
                match = self.table_header_pattern.search(first_cell)
                if match:
                    origin = match.group(1)
                    destination = match.group(2)
                    if is_valid_location(origin) and is_valid_location(destination):
                        is_valid_title = True
                        if self.logger:
                            self.logger.debug(f"        规则1匹配: 货交路线 {first_cell[:40]}")
            
            # 规则2: "深圳-泰国："格式（真实路线，虽然以冒号结尾）
            # 必须满足：以路线开头 + 以冒号结尾 + 路线长度合理(<30字符)
            elif (':' in first_cell or '：' in first_cell):
                # 移除冒号后的部分
                route_part = first_cell.rstrip('：:').strip()
                
                # 检查是否是纯路线（不包含其他词汇）
                if len(route_part) < 30:  # 路线部分长度限制
                    match = self.route_pattern.search(route_part)
                    if match:
                        origin = match.group(1)
                        destination = match.group(2)
                        
                        # 验证起点和终点
                        if is_valid_location(origin) and is_valid_location(destination):
                            # ⭐ 排除"XXX-XXX："（无其他内容，纯费用标题）
                            # 保留"深圳-泰国："（真实路线标题）
                            # 判断依据：是否紧跟代理商行或费用行
                            next_row_is_agent = False
                            if row_idx + 1 < len(sheet_data):
                                next_row = sheet_data[row_idx + 1]
                                if next_row and next_row[0]:
                                    next_cell = str(next_row[0]).strip().lower()
                                    # 检查下一行是否是代理商行或特殊标记
                                    if any(kw in next_cell for kw in self.agent_keywords) or next_cell in ['/', '-', '']:
                                        next_row_is_agent = True
                            
                            if next_row_is_agent:
                                is_valid_title = True
                                if self.logger:
                                    self.logger.debug(f"        规则2匹配: 冒号路线 {first_cell[:40]}")
                            else:
                                if self.logger:
                                    self.logger.debug(f"        规则2排除: 费用标题 {first_cell[:40]}")
            
            # 规则3: 普通路线（不以冒号结尾）
            elif not first_cell.endswith('：') and not first_cell.endswith(':'):
                match = self.table_header_pattern.match(first_cell)
                if match:
                    origin = match.group(1)
                    destination = match.group(2)
                    
                    if is_valid_location(origin) and is_valid_location(destination):
                        is_valid_title = True
                        if self.logger:
                            self.logger.debug(f"        规则3匹配: 普通路线 {first_cell[:40]}")
            
            # 如果是有效标题，创建新table边界
            if is_valid_title:
                # 结束上一个表格
                if current_start is not None:
                    boundaries.append((current_start, row_idx - 1, current_route_text))
                
                # 开始新表格
                current_start = row_idx
                current_route_text = first_cell
                
                if self.logger:
                    self.logger.debug(f"      识别到表格标题行{row_idx+1}: {first_cell[:50]}")
        
        # 结束最后一个表格
        if current_start is not None:
            boundaries.append((current_start, len(sheet_data) - 1, current_route_text))
        
        # 策略2: 如果没有找到，使用第一行
        if not boundaries and sheet_data and len(sheet_data) > 0:
            if self.logger:
                self.logger.debug(f"      未找到标准标题行，尝试使用第一行")
            
            if sheet_data[0]:
                first_cell = str(sheet_data[0][0]).strip() if sheet_data[0] else ""
                route_part = first_cell.split('|')[0].strip() if '|' in first_cell else first_cell
                
                if route_part and len(route_part) < 100:
                    if self.route_pattern.search(route_part):
                        boundaries.append((0, len(sheet_data) - 1, first_cell))
                        if self.logger:
                            self.logger.debug(f"        使用第一行作为路线: {first_cell[:60]}")
        
        return boundaries
    
    def _parse_single_table(
        self,
        table_data: List[List],
        route_text: str,
        sheet_name: str = None
    ) -> List[QuoteBlock]:
        """解析单个横向表格"""
        
        if not table_data or len(table_data) < 2:
            return []
        
        # 1. 提取路线
        base_route = self._extract_route_from_text(route_text, sheet_name)
        
        # ⭐ v9.0: 提取交易日期（从parse_sheet传入的filename）
        # 注意：filename需要通过parse_sheet的参数传递到这里
        # 这里先预留逻辑，实际实现需要在parse_sheet中传递filename
        
        # Fallback策略
        if (not base_route.起始地 or not base_route.目的地) and sheet_name:
            if self.logger:
                self.logger.debug(f"      路线不完整，尝试从sheet名提取")
            
            sheet_route = self._extract_route_from_text(sheet_name, sheet_name)
            
            if sheet_route.起始地 and sheet_route.目的地:
                base_route = sheet_route
                if self.logger:
                    self.logger.debug(f"      ✅ 使用sheet名提取的路线: {base_route.起始地} -> {base_route.目的地}")
            elif not base_route.起始地 and not base_route.目的地:
                if self.logger:
                    self.logger.debug(f"      sheet名和内容都无法提取完整路线，跳过此表格")
                return []
        elif not base_route.起始地 and not base_route.目的地:
            if self.logger:
                self.logger.debug(f"      路线无效且无sheet名，跳过此表格")
            return []
        
        # 2. 识别表格结构
        structure = self._identify_structure(table_data)
        if not structure:
            return []
        
        # 判断是否为单列表格
        is_single_column = structure['num_cols'] <= 2
        
        if not is_single_column and structure['agent_row'] is not None:
            agent_row_data = table_data[structure['agent_row']] if structure['agent_row'] < len(table_data) else []
            has_multi_agents = len(agent_row_data) > 1 and any(agent_row_data[i] for i in range(1, len(agent_row_data)))
            
            if not has_multi_agents:
                is_single_column = True
        elif structure['agent_row'] is None:
            is_single_column = True
        
        # 单列表格处理
        if is_single_column:
            if self.logger:
                self.logger.debug(f"      检测到单列表格（num_cols={structure['num_cols']}）")
            
            agent = Agent()
            if structure['agent_row'] is not None:
                agent_row_data = table_data[structure['agent_row']]
                
                if len(agent_row_data) >= 2 and any(kw in str(agent_row_data[0]) for kw in self.agent_keywords):
                    agent_cell = self._get_cell(table_data, structure['agent_row'], 1)
                else:
                    agent_cell = self._get_cell(table_data, structure['agent_row'], 0)
                
                if agent_cell:
                    agent.代理商 = str(agent_cell).strip()
            
            if not agent.代理商:
                if sheet_name:
                    agent.代理商 = f"{sheet_name}-单列报价"
                else:
                    agent.代理商 = "未标注代理商"
            
            if base_route.起始地 and base_route.目的地:
                quote = QuoteBlock(
                    route=base_route,
                    agent=agent,
                    fee_items=[],
                    fee_total=FeeTotal(),
                    summary=Summary()
                )
                return [quote]
            else:
                return []
        
        # 3. 多列横向表格
        quotes = []
        
        for col_idx in range(1, structure['num_cols']):
            try:
                quote = self._extract_column_quote(
                    table_data,
                    col_idx,
                    structure,
                    base_route,
                    sheet_name
                )
                
                if quote:
                    quotes.append(quote)
                            
            except Exception as e:
                if self.logger:
                    self.logger.error(f"解析第 {col_idx} 列失败: {e}")
                continue
        
        return quotes
    
    def _extract_route_from_text(self, text: str, sheet_name: str) -> Route:
        """
        ⭐ v7.0: 从文本中提取路线信息
        改进：
        1. 支持"|"分隔符
        2. 清理业务后缀
        3. 修复三地点顺序
        """
        route = Route()
        route._sheet_name = sheet_name
        route._raw = text[:100] if text else None
        
        if self.logger:
            self.logger.debug(f"    路线文本: {text[:60] if text else 'None'}...")
        
        if not text:
            return route
        
        # 如果文本包含"|"，只取第一部分作为路线
        route_part = text.split('|')[0].strip() if '|' in text else text
        
        # 移除冒号
        route_part = route_part.rstrip('：:').strip()
        
        # 使用 RouteExtractor
        if self.route_extractor:
            route_info = self.route_extractor.extract_route(route_part, fallback_start=sheet_name)
            
            route.起始地 = route_info.get('origin')
            route.目的地 = route_info.get('destination')
            route.途径地 = route_info.get('via')
            route.贸易备注 = route_info.get('trade_remark')
            route.实际重量 = route_info.get('weight')
            route.总体积 = route_info.get('volume')
            route.货值 = route_info.get('value')
            
            if route.实际重量 and not route.计费重量:
                route.计费重量 = route.实际重量
            
            # ⭐ v7.0: 清理地点后缀
            if route.目的地:
                route.目的地 = self._clean_location_suffix(route.目的地)
            
            if self.logger:
                self.logger.debug(f"    ✅ RouteExtractor识别: {route.起始地} -> {route.目的地}" +
                                (f" (途径: {route.途径地})" if route.途径地 else ""))
            
            return route
        
        # Fallback: 使用原有逻辑
        route_match = self.route_pattern.search(route_part)
        if route_match:
            start_raw = route_match.group(1).strip()
            end_raw = route_match.group(2).strip()
            via_raw = route_match.group(3).strip() if route_match.lastindex >= 3 and route_match.group(3) else None
            
            if is_valid_location(start_raw):
                route.起始地 = start_raw
            
            # ⭐ v7.0: 修复三地点顺序
            # A-B-C: 起始地A，途径地B，目的地C
            if via_raw and is_valid_location(via_raw):
                # 有三个地点
                if is_valid_location(end_raw):
                    route.途径地 = end_raw
                    route.目的地 = via_raw
            elif is_valid_location(end_raw):
                # 只有两个地点
                route.目的地 = end_raw
            
            # ⭐ v7.0: 清理地点后缀
            if route.目的地:
                route.目的地 = self._clean_location_suffix(route.目的地)
            
            if self.logger:
                self.logger.debug(f"    Fallback识别: {route.起始地} -> {route.目的地}" +
                                (f" (途径: {route.途径地})" if route.途径地 else ""))
        
        # 提取重量、体积、货值
        weight_match = self.weight_pattern.search(text)
        if weight_match:
            route.实际重量 = float(weight_match.group(1))
            route.计费重量 = route.实际重量
        
        volume_match = self.volume_pattern.search(text)
        if volume_match:
            route.总体积 = float(volume_match.group(1))
        
        value_match = self.value_pattern.search(text)
        if value_match:
            route.货值 = float(value_match.group(1))
        
        return route
    
    def _clean_location_suffix(self, location: str) -> str:
        """
        ⭐ v7.0: 清理地点的业务后缀（多轮迭代）
        例如："印度小货的快递" → "印度"
        """
        if not location:
            return location
        
        cleaned = location
        
        # ⭐ 多轮迭代清理（最多3轮）
        for iteration in range(3):
            prev = cleaned
            
            # 移除业务后缀
            for suffix in self.business_suffixes:
                if cleaned.endswith(suffix):
                    cleaned = cleaned[:-len(suffix)].strip()
                    break
            
            # 如果没有变化，停止迭代
            if cleaned == prev:
                break
        
        # 如果清理后太短或为空，返回原始值
        if len(cleaned) < 2:
            return location
        
        return cleaned
    
    def _identify_structure(self, table_data: List[List]) -> Optional[Dict]:
        """
        ⭐ v7.0: 识别表格结构（优化代理商行识别）
        """
        if not table_data:
            return None
        
        max_cols = max(len(row) for row in table_data if row)
        
        structure = {
            'num_cols': max_cols,
            'agent_row': None,
            'fee_row': None,
            'total_row': None
        }
        
        # 查找代理商行
        for row_idx, row in enumerate(table_data):
            if not row:
                continue
            
            first_cell = str(row[0]).strip().lower() if row[0] else ""
            
            # 方法1: 包含"代理"关键词
            if any(kw in first_cell for kw in self.agent_keywords):
                structure['agent_row'] = row_idx
                if self.logger:
                    self.logger.debug(f"        找到代理商行(方法1): 第{row_idx+1}行")
                break
            
            # 方法2: 第一列是特殊标记
            if first_cell in ['/', '-', '']:
                if len(row) > 1:
                    has_content = False
                    for col_idx in range(1, min(len(row), 5)):
                        cell = self._get_cell(table_data, row_idx, col_idx)
                        if cell and len(cell) > 1:
                            has_content = True
                            break
                    
                    if has_content:
                        structure['agent_row'] = row_idx
                        if self.logger:
                            self.logger.debug(f"        找到代理商行(方法2): 第{row_idx+1}行")
                        break
        
        return structure
    
    def _extract_column_quote(
        self,
        table_data: List[List],
        col_idx: int,
        structure: Dict,
        base_route: Route,
        sheet_name: str = None
    ) -> Optional[QuoteBlock]:
        """提取某一列的报价信息"""
        
        # 为这一列创建独立的route副本
        route = Route(
            起始地=base_route.起始地,
            目的地=base_route.目的地,
            途径地=base_route.途径地,
            贸易备注=base_route.贸易备注,
            实际重量=base_route.实际重量,
            计费重量=base_route.计费重量,
            总体积=base_route.总体积,
            货值=base_route.货值,
            _raw=base_route._raw,
            _sheet_name=sheet_name
        )
        
        # 提取代理商
        agent = Agent()
        if structure['agent_row'] is not None:
            agent_cell = self._get_cell(table_data, structure['agent_row'], col_idx)
            if agent_cell:
                agent.代理商 = str(agent_cell).strip()
        
        # 如果没有代理商，跳过这一列
        if not agent.代理商:
            return None
        
        # 创建QuoteBlock
        quote = QuoteBlock(
            route=route,
            agent=agent,
            fee_items=[],
            fee_total=FeeTotal(),
            summary=Summary()
        )
        
        return quote
    
    def _get_cell(self, table_data: List[List], row_idx: int, col_idx: int) -> Optional[str]:
        """安全获取单元格内容"""
        if row_idx < 0 or row_idx >= len(table_data):
            return None
        
        row = table_data[row_idx]
        if col_idx < 0 or col_idx >= len(row):
            return None
        
        cell = row[col_idx]
        if cell is None or str(cell).strip().lower() in ['nan', 'none', '']:
            return None
        
        return str(cell).strip()


# ========== 便捷函数 ==========

def quick_parse(sheet_data: List[List], sheet_name: str = None) -> List[QuoteBlock]:
    """快捷解析函数"""
    parser = HorizontalTableParser()
    return parser.parse_sheet(sheet_data, sheet_name)


__all__ = [
    'Route', 'Agent', 'FeeItem', 'FeeTotal', 'Summary', 'QuoteBlock',
    'HorizontalTableParser', 'quick_parse'
]