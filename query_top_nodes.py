#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SQL查询执行脚本
================

功能说明：
    1. 读取 SQL 文件并提取"查询1"语句
    2. 连接 SQLite 数据库执行查询
    3. 以列表格式在命令行展示结果

使用方法：
    直接运行此脚本

依赖：
    Python 3.6+（使用内置 sqlite3 模块）

创建时间：2026-03-02
"""

import argparse
from node_query import get_top_nodes, display_nodes


def main():
    parser = argparse.ArgumentParser(
        description='SQL 查询执行脚本',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='示例: python query_top_nodes.py --limit 50'
    )
    parser.add_argument('-l', '--limit', type=int, default=100,
                        help='要查询的节点数量 (默认: 100)')
    args = parser.parse_args()

    limit = args.limit

    print("=" * 60)
    print("SQL 查询执行脚本")
    print("=" * 60)
    print(f"查询节点数量: {limit}")
    print()

    print("正在查询优秀节点...")
    nodes = get_top_nodes(limit=limit)
    if not nodes:
        print("查询失败或未找到优秀节点")
        return

    display_nodes(nodes)
    print("\n执行完成！")


if __name__ == "__main__":
    main()
