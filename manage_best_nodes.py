#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
优秀节点管理脚本
================

功能说明：
    1. 查询优秀节点（基于 ProfileExItemHistory 测速历史）
    2. 查找或创建 "best_nodes" 订阅分组
    3. 清空该分组下的现有节点（解除关联，Subid 置空）
    4. 将优秀节点关联到 "best_nodes" 分组

使用方法：
    python manage_best_nodes.py         # 交互模式，默认查询 100 个优秀节点
    python manage_best_nodes.py -l 50   # 查询 50 个优秀节点
    python manage_best_nodes.py -y      # 自动确认，不询问
    python manage_best_nodes.py -n      # 干运行模式，只显示不修改

注意事项：
    - 执行前请先关闭 v2rayN，避免数据库锁定
    - 脚本会自动备份数据库到当前目录
"""

import sqlite3
import shutil
import os
import sys
import argparse
import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any

from config import DB_PATH
from node_query import get_top_nodes


BEST_GROUP_REMARKS = "best_nodes"


def backup_database(db_path: str) -> str:
    """备份数据库到当前目录"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    db_name = os.path.basename(db_path)
    backup_path = os.path.join(os.getcwd(), f"{db_name}.backup_{timestamp}")
    shutil.copy2(db_path, backup_path)
    return backup_path


def get_sub_item_by_remarks(db_path: str, remarks: str) -> Optional[Dict[str, Any]]:
    """根据 Remarks 查询订阅分组"""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM SubItem WHERE Remarks = ?", (remarks,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return dict(row)
    return None


def create_sub_item(db_path: str, remarks: str) -> str:
    """创建订阅分组，返回新分组的 Id"""
    sub_id = str(uuid.uuid4()).replace("-", "")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO SubItem (Id, Remarks, Url, MoreUrl, Enabled, UserAgent, Sort, AutoUpdateInterval, UpdateTime)
        VALUES (?, ?, '', '', 1, '', 0, 0, 0)
    """, (sub_id, remarks))
    conn.commit()
    conn.close()
    return sub_id


def get_nodes_by_subid(db_path: str, subid: str) -> List[Dict[str, Any]]:
    """查询指定分组下的所有节点"""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("""
        SELECT IndexId, Remarks, Address, Port, ConfigType, Subid
        FROM ProfileItem
        WHERE Subid = ?
    """, (subid,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def clear_sub_group(db_path: str, subid: str) -> int:
    """
    解除指定分组下所有节点的关联（Subid 置空）
    根据 V2rayN 源码，MoveToGroup 通过修改 Subid 实现分组关联，
    解除关联即将 Subid 置为空字符串（与 ProfileItem 默认值一致）。
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("UPDATE ProfileItem SET Subid = '' WHERE Subid = ?", (subid,))
    updated = cursor.rowcount
    conn.commit()
    conn.close()
    return updated


def assign_nodes_to_group(db_path: str, index_ids: List[str], subid: str) -> int:
    """将节点关联到指定分组"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    placeholders = ','.join('?' * len(index_ids))
    cursor.execute(f"""
        UPDATE ProfileItem SET Subid = ?
        WHERE IndexId IN ({placeholders})
    """, (subid, *index_ids))
    updated = cursor.rowcount
    conn.commit()
    conn.close()
    return updated


def display_simple_nodes(nodes: List[Dict[str, Any]], title: str = "节点列表") -> None:
    """简化显示节点列表"""
    if not nodes:
        print(f"  {title}：无")
        return

    print(f"\n  {title}（共 {len(nodes)} 个）：")
    print(f"  {'序号':<6}{'备注':<50}")
    print(f"  {'-' * 56}")
    for i, node in enumerate(nodes, 1):
        remarks = (node.get('Remarks') or node.get('节点名称') or '')[:48]
        print(f"  {i:<6}{remarks:<50}")


def main():
    parser = argparse.ArgumentParser(
        description='优秀节点管理脚本：将优秀节点归类到 best_nodes 分组',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='示例:\n  python manage_best_nodes.py -l 50\n  python manage_best_nodes.py -y -l 30'
    )
    parser.add_argument('-l', '--limit', type=int, default=100,
                        help='要查询的优秀节点数量 (默认: 100)')
    parser.add_argument('-y', '--yes', action='store_true',
                        help='自动确认，不询问（慎用）')
    parser.add_argument('-n', '--dry-run', action='store_true',
                        help='干运行模式，只显示不修改')
    args = parser.parse_args()

    # 检查数据库
    if not os.path.exists(DB_PATH):
        print(f"错误：数据库文件不存在：{DB_PATH}")
        sys.exit(1)

    print("=" * 60)
    print("优秀节点管理脚本")
    print("=" * 60)
    print(f"数据库路径: {DB_PATH}")
    print(f"查询节点数量: {args.limit}")
    print(f"目标分组名: {BEST_GROUP_REMARKS}")
    print()

    # 步骤1：查询优秀节点
    print("步骤1：查询优秀节点...")
    top_nodes = get_top_nodes(limit=args.limit)
    if not top_nodes:
        print("未找到优秀节点，操作终止。")
        return

    print(f"找到 {len(top_nodes)} 个优秀节点")
    display_simple_nodes(top_nodes, "优秀节点")

    # 步骤2：查找或创建 best_nodes 分组
    print("\n步骤2：查找目标订阅分组...")
    group = get_sub_item_by_remarks(DB_PATH, BEST_GROUP_REMARKS)

    if group:
        group_id = group['Id']
        print(f"找到分组 '{BEST_GROUP_REMARKS}' (Id: {group_id[:8]}...)")
    else:
        print(f"分组 '{BEST_GROUP_REMARKS}' 不存在。")
        if args.dry_run:
            print("【干运行】将创建新分组。")
            group_id = "<dry-run-generated-id>"
        else:
            answer = input(f"是否创建新分组 '{BEST_GROUP_REMARKS}'？(yes/no)：").strip().lower()
            if answer != 'yes':
                print("已取消操作。")
                return
            group_id = create_sub_item(DB_PATH, BEST_GROUP_REMARKS)
            print(f"已创建分组 '{BEST_GROUP_REMARKS}' (Id: {group_id[:8]}...)")

    # 步骤3：查询该分组下现有节点
    print("\n步骤3：检查分组下现有节点...")
    existing_nodes = get_nodes_by_subid(DB_PATH, group_id) if group else []
    if existing_nodes:
        print(f"分组下现有 {len(existing_nodes)} 个节点，将解除关联。")
        display_simple_nodes(existing_nodes, "现有节点")
    else:
        print("分组下无现有节点。")

    # 步骤4：确认操作
    if args.dry_run:
        print("\n【干运行模式】以上是要执行的操作预览，未实际修改数据库。")
        return

    if not args.yes:
        print(f"\n即将执行：")
        print(f"  1. 解除 {len(existing_nodes)} 个节点与 '{BEST_GROUP_REMARKS}' 的关联")
        print(f"  2. 将 {len(top_nodes)} 个优秀节点关联到 '{BEST_GROUP_REMARKS}'")
        answer = input("\n确认执行吗？输入 'yes' 继续：").strip().lower()
        if answer != 'yes':
            print("已取消操作。")
            return

    # 步骤5：备份数据库
    print("\n正在备份数据库...")
    backup_path = backup_database(DB_PATH)
    print(f"数据库已备份到：{backup_path}")

    # 步骤6：执行操作
    print("\n步骤4：执行数据库更新...")

    if existing_nodes:
        cleared = clear_sub_group(DB_PATH, group_id)
        print(f"  ✓ 已解除 {cleared} 个节点的分组关联")

    index_ids = [node['IndexId'] for node in top_nodes]
    assigned = assign_nodes_to_group(DB_PATH, index_ids, group_id)
    print(f"  ✓ 已将 {assigned} 个优秀节点关联到 '{BEST_GROUP_REMARKS}'")

    print("\n操作完成！")
    print(f"提示：请重新打开 v2rayN，在左侧订阅列表中找到 '{BEST_GROUP_REMARKS}' 分组进行速度测试。")


if __name__ == '__main__':
    main()
