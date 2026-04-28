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

import sqlite3
import os
import re
import argparse
from typing import Optional, List, Tuple, Any
from config import DB_PATH, SQL_FILE_PATH

def read_sql_file(file_path: str) -> Optional[str]:
    """
    读取 SQL 文件内容
    
    参数：
        file_path: SQL 文件路径
    
    返回：
        文件内容字符串，失败返回 None
    """
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
    """
    从 SQL 文件内容中提取"查询1"语句

    参数：
        sql_content: SQL 文件内容
        limit: 最大查询数量

    返回：
        查询1的 SQL 语句，失败返回 None
    """
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
    """
    执行 SQL 查询
    
    参数：
        db_path: 数据库文件路径
        sql: SQL 查询语句
    
    返回：
        (结果列表, 列名列表)，失败返回 None
    """
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


def display_results(results: List[Tuple[Any, ...]], columns: List[str]) -> None:
    """
    以列表格式展示查询结果
    
    参数：
        results: 查询结果列表
        columns: 列名列表
    """
    if not results:
        print("查询结果为空")
        return
    
    # 定义颜色代码
    colors = [
        '\033[94m',  # 蓝色
        '\033[92m',  # 绿色
        '\033[93m',  # 黄色
        '\033[95m',  # 紫色
        '\033[96m',  # 青色
        '\033[91m',  # 红色
        '\033[97m',  # 白色
        '\033[94m',  # 蓝色（循环）
        '\033[92m',  # 绿色（循环）
        '\033[93m',  # 黄色（循环）
        '\033[95m',  # 紫色（循环）
        '\033[96m',  # 青色（循环）
        '\033[91m',  # 红色（循环）
    ]
    reset_color = '\033[0m'
    
    print("\n" + "=" * 120)
    print(f"查询结果：共 {len(results)} 条记录")
    print("=" * 120)
    
    col_widths = []
    for i, col in enumerate(columns):
        max_width = len(str(col))
        for row in results:
            cell_width = len(str(row[i]) if row[i] is not None else "NULL")
            max_width = max(max_width, min(cell_width, 50))
        col_widths.append(max_width)
    
    # 打印表头
    header_parts = []
    for i, col in enumerate(columns):
        color = colors[i % len(colors)]
        header_parts.append(f"{color}{str(col).ljust(col_widths[i])}{reset_color}")
    header_line = " | ".join(header_parts)
    print(header_line)
    print("-" * len(header_line))
    
    # 打印数据行
    for row in results:
        row_parts = []
        for i, cell in enumerate(row):
            color = colors[i % len(colors)]
            cell_str = str(cell if cell is not None else "NULL")
            cell_str = cell_str.ljust(col_widths[i])[:col_widths[i]]
            row_parts.append(f"{color}{cell_str}{reset_color}")
        row_line = " | ".join(row_parts)
        print(row_line)
    
    print("=" * 120)


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
    print(f"数据库路径: {DB_PATH}")
    print(f"SQL 文件路径: {SQL_FILE_PATH}")
    print(f"查询节点数量: {limit}")
    print()

    print("正在读取 SQL 文件...")
    sql_content = read_sql_file(SQL_FILE_PATH)
    if sql_content is None:
        return

    print("正在提取查询1语句...")
    sql_query = extract_query1(sql_content, limit)
    if sql_query is None:
        return
    
    print(f"成功提取 SQL 语句（长度: {len(sql_query)} 字符）")
    
    print("\n正在执行查询...")
    result = execute_query(DB_PATH, sql_query)
    if result is None:
        return
    
    results, columns = result
    display_results(results, columns)
    
    print("\n执行完成！")


if __name__ == "__main__":
    main()
