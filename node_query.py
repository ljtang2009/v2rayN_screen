#!/usr/bin/env python3
"""
节点查询公共模块
===============

提取 query_top_nodes.py 中的查询逻辑，供其他脚本复用。

功能：
    1. 读取 SQL 文件并提取"查询1"语句
    2. 连接 SQLite 数据库执行查询
    3. 返回优秀节点列表（包含 IndexId 等字段）
"""

import sqlite3
import os
import re
from typing import Optional, List, Tuple, Any, Dict

from config import DB_PATH, SQL_FILE_PATH


def read_sql_file(file_path: str) -> Optional[str]:
    """读取 SQL 文件内容"""
    try:
        if not os.path.exists(file_path):
            print(f"错误：SQL 文件不存在 - {file_path}")
            return None
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        print(f"错误：读取 SQL 文件失败 - {e}")
        return None


def extract_query1(sql_content: str, limit: int = 100) -> Optional[str]:
    """从 SQL 文件内容中提取'查询1'语句"""
    try:
        pattern = r'--\s*查询1[^;]*;(?:--|SELECT)'
        match = re.search(pattern, sql_content, re.IGNORECASE | re.DOTALL)

        if match:
            start_marker = "-- =====================================================\n-- 查询1:"
            start_idx = sql_content.find(start_marker)
            if start_idx == -1:
                start_idx = sql_content.lower().find("-- 查询1")

            if start_idx != -1:
                end_marker = "-- =====================================================\n-- 查询2:"
                end_idx = sql_content.find(end_marker)
                if end_idx == -1:
                    end_idx = sql_content.lower().find("-- 查询2")

                if end_idx != -1:
                    query_section = sql_content[start_idx:end_idx]
                else:
                    query_section = sql_content[start_idx:]

                select_match = re.search(r'SELECT\s+.*?;', query_section, re.IGNORECASE | re.DOTALL)
                if select_match:
                    sql = select_match.group(0)
                    sql = re.sub(r'\s*LIMIT\s+\d+\s*;?\s*$', '', sql, flags=re.IGNORECASE)
                    sql = sql.rstrip(';').strip()
                    sql += f" LIMIT {limit};"
                    return sql

        select_pattern = r'(SELECT\s+p\.IndexId.*?LIMIT\s+100;)'
        select_match = re.search(select_pattern, sql_content, re.IGNORECASE | re.DOTALL)
        if select_match:
            sql = select_match.group(1)
            sql = re.sub(r'\s*LIMIT\s+\d+\s*;?\s*$', '', sql, flags=re.IGNORECASE)
            sql = sql.rstrip(';').strip()
            sql += f" LIMIT {limit};"
            return sql

        print("错误：无法从 SQL 文件中提取查询1语句")
        return None

    except Exception as e:
        print(f"错误：提取查询1失败 - {e}")
        return None


def execute_query(db_path: str, sql: str) -> Optional[Tuple[List[Tuple[Any, ...]], List[str]]]:
    """执行 SQL 查询"""
    conn = None
    try:
        if not os.path.exists(db_path):
            print(f"错误：数据库文件不存在 - {db_path}")
            return None
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute(sql)
        columns = [description[0] for description in cursor.description]
        results = cursor.fetchall()
        return results, columns
    except sqlite3.Error as e:
        print(f"错误：数据库操作失败 - {e}")
        return None
    except Exception as e:
        print(f"错误：查询执行失败 - {e}")
        return None
    finally:
        if conn:
            conn.close()


def get_top_nodes(db_path: str = DB_PATH, sql_file_path: str = SQL_FILE_PATH, limit: int = 100) -> List[Dict[str, Any]]:
    """
    查询优秀节点，返回节点列表（字典格式）

    参数：
        db_path: 数据库路径
        sql_file_path: SQL 文件路径
        limit: 最大查询数量

    返回：
        节点字典列表，每个字典包含查询结果的所有列
    """
    sql_content = read_sql_file(sql_file_path)
    if sql_content is None:
        return []

    sql_query = extract_query1(sql_content, limit)
    if sql_query is None:
        return []

    result = execute_query(db_path, sql_query)
    if result is None:
        return []

    results, columns = result
    nodes = []
    for row in results:
        node = {}
        for i, col in enumerate(columns):
            node[col] = row[i]
        nodes.append(node)

    return nodes


def display_nodes(nodes: List[Dict[str, Any]], exclude_columns: Optional[set] = None) -> None:
    """
    以列表格式展示节点

    参数：
        nodes: 节点字典列表
        exclude_columns: 要隐藏的列名集合（默认隐藏 IndexId）
    """
    if not nodes:
        print("查询结果为空")
        return

    if exclude_columns is None:
        exclude_columns = {'IndexId', 'indexid', 'INDEXID'}

    columns = [col for col in nodes[0].keys() if col not in exclude_columns]
    if not columns:
        print("没有可显示的列")
        return

    colors = [
        '\033[94m', '\033[92m', '\033[93m', '\033[95m',
        '\033[96m', '\033[91m', '\033[97m',
    ]
    reset_color = '\033[0m'

    print("\n" + "=" * 120)
    print(f"查询结果：共 {len(nodes)} 条记录")
    print("=" * 120)

    col_widths = []
    for col in columns:
        max_width = len(str(col))
        for node in nodes:
            cell = node.get(col)
            cell_width = len(str(cell) if cell is not None else "NULL")
            max_width = max(max_width, min(cell_width, 50))
        col_widths.append(max_width)

    header_parts = []
    for i, col in enumerate(columns):
        color = colors[i % len(colors)]
        header_parts.append(f"{color}{str(col).ljust(col_widths[i])}{reset_color}")
    header_line = " | ".join(header_parts)
    print(header_line)
    print("-" * len(header_line))

    for node in nodes:
        row_parts = []
        for i, col in enumerate(columns):
            color = colors[i % len(colors)]
            cell = node.get(col)
            cell_str = str(cell if cell is not None else "NULL")
            cell_str = cell_str.ljust(col_widths[i])[:col_widths[i]]
            row_parts.append(f"{color}{cell_str}{reset_color}")
        row_line = " | ".join(row_parts)
        print(row_line)

    print("=" * 120)
