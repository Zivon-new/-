import re


class RouteBlockDetector:
    """
    判断一个 block 是否是「报价路线 block」
    """

    def is_route_block(self, lines: list[str]) -> bool:
        if not lines:
            return False

        text = " ".join(lines)

        # ① 必须有路线形态
        has_route_shape = any(
            sep in lines[0]
            for sep in ["→", "-", "至", "到"]
        )

        if not has_route_shape:
            return False

        # ② 必须有至少一个业务实体
        has_business = any([
            re.search(r"(kg|cbm|吨|方)", text),
            re.search(r"(新|旧|新品|二手)", text),
            re.search(r"/kg|/cbm", text),
            re.search(r"(费用|运费|报价)", text),
        ])

        if not has_business:
            return False

        return True
