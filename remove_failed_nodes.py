#!/usr/bin/env python3
"""
删除测速报 "运行 Core 失败" 的节点
功能：
1. 查询 ProfileExItem 中 Message 包含 "运行 Core 失败" 的节点
2. 显示节点详情和数量
3. 询问用户是否删除
4. 确认后自动备份数据库并删除节点（ProfileItem + ProfileExItem）
5. 触发器会自动清理 ProfileExItemHistory 中的历史记录

使用方法：
    python remove_failed_nodes.py         # 交互模式，先查询后询问是否删除
    python remove_failed_nodes.py --yes   # 自动确认删除（慎用）
    python remove_failed_nodes.py --dry-run  # 只查询，不删除
"""

import sqlite3
import shutil
import os
import sys
import argparse
from datetime import datetime
from typing import List, Dict, Any

from config import DB_PATH


def get_failed_nodes(db_path: str) -> List[Dict[str, Any]]:
    """查询测速失败的节点"""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            p.IndexId,
            p.Address,
            p.Port,
            p.Remarks,
            p.Network,
            p.Security,
            e.Delay,
            e.Speed,
            e.Message
        FROM ProfileItem p
        JOIN ProfileExItem e ON p.IndexId = e.IndexId
        WHERE e.Message LIKE '%运行 Core 失败%'
        ORDER BY p.Remarks
    """)

    rows = cursor.fetchall()
    nodes = [dict(row) for row in rows]
    conn.close()
    return nodes


def display_nodes(nodes: List[Dict[str, Any]]) -> None:
    """显示节点列表"""
    if not nodes:
        print("没有找到测速报 '运行 Core 失败' 的节点。")
        return

    print(f"\n{'=' * 80}")
    print(f"找到 {len(nodes)} 个测速报 '运行 Core 失败' 的节点：")
    print(f"{'=' * 80}")
    print(f"{'序号':<6}{'备注':<70}")
    print("-" * 80)

    for i, node in enumerate(nodes, 1):
        remarks = (node.get('Remarks') or '')[:68]
        print(f"{i:<6}{remarks:<70}")

    print(f"{'=' * 80}\n")


def backup_database(db_path: str) -> str:
    """备份数据库到当前目录"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    db_name = os.path.basename(db_path)
    backup_path = os.path.join(os.getcwd(), f"{db_name}.backup_{timestamp}")
    shutil.copy2(db_path, backup_path)
    return backup_path


def delete_failed_nodes(db_path: str, nodes: List[Dict[str, Any]]) -> Dict[str, int]:
    """删除测速失败的节点，返回删除统计"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    index_ids = [node['IndexId'] for node in nodes]

    # 使用占位符构建 IN 查询
    placeholders = ','.join('?' * len(index_ids))

    try:
        # 先删除 ProfileExItem（触发器会自动清理 ProfileExItemHistory）
        cursor.execute(f"""
            DELETE FROM ProfileExItem
            WHERE IndexId IN ({placeholders})
        """, index_ids)
        deleted_ex = cursor.rowcount

        # 再删除 ProfileItem
        cursor.execute(f"""
            DELETE FROM ProfileItem
            WHERE IndexId IN ({placeholders})
        """, index_ids)
        deleted_main = cursor.rowcount

        conn.commit()
        return {
            'ProfileItem': deleted_main,
            'ProfileExItem': deleted_ex
        }
    except sqlite3.Error as e:
        conn.rollback()
        raise e
    finally:
        conn.close()


def main():
    parser = argparse.ArgumentParser(
        description='删除测速报 "运行 Core 失败" 的节点'
    )
    parser.add_argument(
        '--yes', '-y',
        action='store_true',
        help='自动确认删除，不询问（慎用）'
    )
    parser.add_argument(
        '--dry-run', '-n',
        action='store_true',
        help='只查询显示，不执行删除'
    )
    args = parser.parse_args()

    # 检查数据库是否存在
    if not os.path.exists(DB_PATH):
        print(f"错误：数据库文件不存在：{DB_PATH}")
        sys.exit(1)

    # 查询节点
    nodes = get_failed_nodes(DB_PATH)
    display_nodes(nodes)

    if not nodes:
        return

    if args.dry_run:
        print("【干运行模式】已显示节点列表，未执行删除。")
        return

    # 询问确认
    if not args.yes:
        print(f"即将删除上述 {len(nodes)} 个节点（包括 ProfileItem 和 ProfileExItem 记录）。")
        print("触发器会自动清理 ProfileExItemHistory 中的相关历史记录。")
        answer = input("确认删除吗？输入 'yes' 继续：").strip().lower()
        if answer != 'yes':
            print("已取消删除操作。")
            return

    # 备份数据库
    print("\n正在备份数据库...")
    backup_path = backup_database(DB_PATH)
    print(f"数据库已备份到：{backup_path}")

    # 执行删除
    print(f"\n正在删除 {len(nodes)} 个节点...")
    try:
        stats = delete_failed_nodes(DB_PATH, nodes)
        print(f"删除完成：")
        print(f"  - ProfileItem  删除：{stats['ProfileItem']} 条")
        print(f"  - ProfileExItem 删除：{stats['ProfileExItem']} 条")
        print(f"  - ProfileExItemHistory 由触发器自动清理")
    except sqlite3.Error as e:
        print(f"删除失败：{e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
