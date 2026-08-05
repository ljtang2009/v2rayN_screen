#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sqlite3
import os
import sys
from config import DB_PATH

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SQL_FILE_PATH = os.path.join(SCRIPT_DIR, 'sql', 'update_allow_insecure.sql')


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

        # 先查询受影响的行数
        cursor.execute("SELECT COUNT(*) FROM ProfileItem WHERE AllowInsecure = 'true'")
        count = cursor.fetchone()[0]
        print(f"将更新 {count} 条记录（AllowInsecure: true -> false）")

        if count == 0:
            print("没有需要更新的记录")
            return True

        cursor.executescript(sql_content)
        conn.commit()
        print(f"SQL 脚本执行成功！已更新 {cursor.rowcount} 条记录")
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
