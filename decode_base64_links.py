#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
解码Base64编码的分享链接文件

将Base64编码的单行文件解码为多行分享链接格式，
确保v2rayN能够正确导入。
"""

import sys
import base64
from pathlib import Path


def decode_base64_links(input_file: str, output_file: str = None) -> bool:
    """
    解码Base64编码的分享链接文件
    
    参数：
        input_file: 输入文件路径（Base64编码）
        output_file: 输出文件路径（默认为输入文件_decoded.txt）
    
    返回：
        是否成功
    """
    try:
        input_path = Path(input_file)
        if not input_path.exists():
            print(f"错误：文件不存在 - {input_file}")
            return False
        
        # 读取Base64编码内容
        with open(input_path, 'rb') as f:
            encoded_content = f.read()
        
        print(f"输入文件大小：{len(encoded_content)} 字节")
        
        # 尝试解码Base64
        try:
            decoded_content = base64.b64decode(encoded_content)
            print(f"Base64解码成功，解码后大小：{len(decoded_content)} 字节")
        except Exception as e:
            print(f"Base64解码失败：{e}")
            print("文件可能不是Base64编码格式")
            return False
        
        # 检测换行符格式
        crlf_count = decoded_content.count(b'\r\n')
        lf_count = decoded_content.count(b'\n') - crlf_count
        cr_count = decoded_content.count(b'\r') - crlf_count
        
        print(f"\n解码后换行符统计：")
        print(f"  CRLF (\\r\\n): {crlf_count}")
        print(f"  LF (\\n): {lf_count}")
        print(f"  CR (\\r): {cr_count}")
        
        # 转换为Unix格式（LF）
        decoded_content = decoded_content.replace(b'\r\n', b'\n')
        decoded_content = decoded_content.replace(b'\r', b'\n')
        
        # 移除多余的空行
        lines = decoded_content.decode('utf-8', errors='replace').split('\n')
        lines = [line.strip() for line in lines if line.strip()]
        
        print(f"\n有效链接数量：{len(lines)}")
        
        # 写入输出文件
        if output_file is None:
            output_file = str(input_path.with_suffix('')) + "_decoded.txt"
        
        output_path = Path(output_file)
        with open(output_path, 'w', encoding='utf-8', newline='\n') as f:
            f.write('\n'.join(lines))
        
        print(f"\n解码完成！")
        print(f"输出文件：{output_path}")
        print(f"文件格式：UTF-8，Unix换行符（LF）")
        
        # 显示前3行作为示例
        if lines:
            print(f"\n前3个链接示例：")
            for i, line in enumerate(lines[:3], 1):
                # 截断显示
                display = line[:80] + "..." if len(line) > 80 else line
                print(f"  {i}. {display}")
        
        return True
        
    except Exception as e:
        print(f"错误：{e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("用法：python decode_base64_links.py <输入文件> [输出文件]")
        print("示例：")
        print("  python decode_base64_links.py 由零开始.txt")
        print("  python decode_base64_links.py 由零开始.txt output.txt")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None
    
    success = decode_base64_links(input_file, output_file)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
