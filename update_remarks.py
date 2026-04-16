#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sqlite3
import os
import sys
from config import DB_PATH

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SQL_FILE_PATH = os.path.join(SCRIPT_DIR, 'sql', 'update_profile_item_remarks.sql')


def read_sql_file(file_path: str) -> str:
    with open(file_path, 'r', encoding='utf-8') as f:
        return f.read()


def execute_sql_file(db_path: str, sql_file_path: str):
    if not os.path.exists(db_path):
        print(f"错误：数据库文件不存在 - {db_path}")
        return False

    if not os.path.exists(sql_file_path):
        print(f"错误：SQL 文件不存在 - {sql_file_path}")
        return False

    sql_content = read_sql_file(sql_file_path)

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.executescript(sql_content)
        conn.commit()
        print("SQL 脚本执行成功！")
        return True
    except sqlite3.Error as e:
        print(f"SQL 执行错误：{e}")
        return False
    finally:
        if conn:
            conn.close()


if __name__ == '__main__':
    print(f"数据库路径: {DB_PATH}")
    print(f"SQL 文件路径: {SQL_FILE_PATH}")
    print("开始执行...")
    success = execute_sql_file(DB_PATH, SQL_FILE_PATH)
    sys.exit(0 if success else 1)
