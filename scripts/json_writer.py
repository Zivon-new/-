import json
import os


class JSONWriter:

    def __init__(self, output_dir):
        """
        output_dir：保存 json 的文件夹，例如 data_clean/
        """
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    # ------------------------------------------------------------
    # 写入一个表的数据
    # ------------------------------------------------------------
    def write_table(self, table_name, data_list):
        """
        table_name: routes / goods_details / fee_items ...
        data_list: [ {}, {}, ... ]
        """
        file_path = os.path.join(self.output_dir, f"{table_name}.json")

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data_list, f, ensure_ascii=False, indent=4)

        print(f"[OK] {table_name}.json 已写入 → {file_path}")

    # ------------------------------------------------------------
    # 写入所有 7 张表
    # ------------------------------------------------------------
    def write_all(self, tables_dict):
        """
        tables_dict 示例：
        {
            "routes": [...],
            "route_agents": [...],
            "goods_details": [...],
            "goods_total": [...],
            "fee_items": [...],
            "fee_total": [...],
            "summary": [...]
        }
        """
        for table_name, records in tables_dict.items():
            self.write_table(table_name, records)

        print("\n[ALL DONE] 所有 JSON 文件已写入！")
