#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复导入文件格式问题

将Windows换行符(CRLF)转换为Unix换行符(LF)，
确保v2rayN能够正确导入分享链接。
"""

import sys
from pathlib import Path


def fix_line_endings(input_file: str, output_file: str = None) -> bool:
    """
    修复文件换行符格式
    
    参数：
        input_file: 输入文件路径
        output_file: 输出文件路径（默认为输入文件覆盖）
    
    返回：
        是否成功
    """
    try:
        input_path = Path(input_file)
        if not input_path.exists():
            print(f"错误：文件不存在 - {input_file}")
            return False
        
        # 读取文件内容
        with open(input_path, 'rb') as f:
            content = f.read()
        
        # 检测当前换行符格式
        crlf_count = content.count(b'\r\n')
        lf_count = content.count(b'\n') - crlf_count
        cr_count = content.count(b'\r') - crlf_count
        
        print(f"文件换行符统计：")
        print(f"  CRLF (\\r\\n): {crlf_count}")
        print(f"  LF (\\n): {lf_count}")
        print(f"  CR (\\r): {cr_count}")
        
        # 转换为Unix格式（LF）
        # 先统一转换为LF
        content = content.replace(b'\r\n', b'\n')
        content = content.replace(b'\r', b'\n')
        
        # 写入文件
        output_path = Path(output_file) if output_file else input_path
        with open(output_path, 'wb') as f:
            f.write(content)
        
        print(f"\n修复完成！")
        print(f"输出文件：{output_path}")
        
        # 验证修复结果
        with open(output_path, 'rb') as f:
            fixed_content = f.read()
        
        if b'\r' not in fixed_content:
            print("[OK] 所有 \\r 字符已成功移除")
            return True
        else:
            print("[WARN] 警告：文件中仍包含 \\r 字符")
            return False
            
    except Exception as e:
        print(f"错误：{e}")
        return False


def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("用法：python fix_import_format.py <输入文件> [输出文件]")
        print("示例：")
        print("  python fix_import_format.py 由零开始.txt")
        print("  python fix_import_format.py 由零开始.txt fixed.txt")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None
    
    success = fix_line_endings(input_file, output_file)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
