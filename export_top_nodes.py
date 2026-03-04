#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
v2rayN 优秀节点导出工具
========================

功能说明：
    1. 从 SQLite 数据库中查询评分最高的节点
    2. 按照 v2rayN 原生格式生成分享链接
    3. 导出到指定的 .txt 文件

使用方法：
    直接运行此脚本，或修改下方配置变量后运行

依赖：
    Python 3.6+（使用内置 sqlite3、json、base64 等模块，无需安装额外依赖）

创建时间：2026-03-01
"""

import sqlite3
import json
import base64
import urllib.parse
import os
import sys
import re
import logging
from datetime import datetime
from typing import Optional, Dict, List, Any, Tuple

# =====================================================
# 配置变量（用户可根据需要修改）
# =====================================================

# SQLite 数据库文件路径
DB_PATH = r"D:\APP\v2rayN-windows-64-SelfContained\guiConfigs\guiNDB.db"

# SQL 脚本文件路径
SQL_FILE_PATH = r"d:\Projects\v2rayN_screen\sql\query_top_performing_nodes.sql"

# 导出文件目录
EXPORT_DIR = r"E:\Download"

# 最大导出节点数量
MAX_NODES = 100

# 日志级别（DEBUG, INFO, WARNING, ERROR）
LOG_LEVEL = logging.INFO

# =====================================================
# 协议类型映射（与 v2rayN 源码 EConfigType 枚举对应）
# =====================================================

CONFIG_TYPE_MAP = {
    1: "VMess",
    2: "Custom",
    3: "Shadowsocks",
    4: "SOCKS",
    5: "VLESS",
    6: "Trojan",
    7: "Hysteria2",
    8: "TUIC",
    9: "WireGuard",
    10: "HTTP",
    11: "Anytls",
    101: "PolicyGroup",
    102: "ProxyChain"
}

# 协议前缀（与 v2rayN 源码 Global.ProtocolShares 对应）
PROTOCOL_PREFIX = {
    1: "vmess://",
    3: "ss://",
    4: "socks://",
    5: "vless://",
    6: "trojan://",
    7: "hysteria2://",
    8: "tuic://",
    9: "wireguard://",
    11: "anytls://"
}

# 默认网络传输协议
DEFAULT_NETWORK = "tcp"

# 默认加密方式（VMess）
DEFAULT_SECURITY = "auto"

# 默认 TLS 安全类型
STREAM_SECURITY_TLS = "tls"

# =====================================================
# 日志配置
# =====================================================

logging.basicConfig(
    level=LOG_LEVEL,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


# =====================================================
# 工具函数
# =====================================================

def base64_encode(data: str, url_safe: bool = False) -> str:
    """
    Base64 编码函数
    
    参数：
        data: 待编码字符串
        url_safe: 是否使用 URL 安全编码
    
    返回：
        Base64 编码后的字符串
    """
    if not data:
        return ""
    
    encoded = base64.b64encode(data.encode('utf-8')).decode('utf-8')
    
    if url_safe:
        encoded = encoded.replace('+', '-').replace('/', '_').rstrip('=')
    
    return encoded


def url_encode(data: str) -> str:
    """
    URL 编码函数
    
    参数：
        data: 待编码字符串
    
    返回：
        URL 编码后的字符串
    """
    if not data:
        return ""
    return urllib.parse.quote(data, safe='')


def url_decode(data: str) -> str:
    """
    URL 解码函数
    
    参数：
        data: 待解码字符串
    
    返回：
        URL 解码后的字符串
    """
    if not data:
        return ""
    return urllib.parse.unquote(data)


def remove_indexid_suffix(remarks: str) -> str:
    """
    移除 Remarks 字段中的 IndexId 后缀
    
    说明：
        根据项目文档，节点 Remarks 字段可能包含 "_{IndexId}" 格式的后缀。
        当节点导出后重新导入时，IndexId 会被重新生成，保留旧后缀会导致
        数据关联错误。此函数用于在导出时移除该后缀。
    
    参数：
        remarks: 原始 Remarks 字符串
    
    返回：
        移除 IndexId 后缀后的 Remarks 字符串
    """
    if not remarks:
        return ""
    
    pattern = r'_\d+$'
    
    return re.sub(pattern, '', remarks).strip()


def get_ipv6_address(address: str) -> str:
    """
    处理 IPv6 地址格式
    
    参数：
        address: IP 地址
    
    返回：
        格式化后的地址（IPv6 地址添加方括号）
    """
    if not address:
        return ""
    
    if ':' in address and not address.startswith('['):
        return f"[{address}]"
    
    return address


def is_valid_guid(guid: str) -> bool:
    """
    检查是否为有效的 GUID/UUID 格式
    
    参数：
        guid: 待检查的字符串
    
    返回：
        是否为有效 GUID
    """
    if not guid:
        return False
    
    pattern = r'^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$'
    return bool(re.match(pattern, guid))


def parse_proto_extra(proto_extra: Any) -> Dict[str, Any]:
    """
    安全解析 ProtoExtra 字段
    
    参数：
        proto_extra: ProtoExtra 字段值（可能是字符串、字典或 None）
    
    返回：
        解析后的字典
    """
    if not proto_extra:
        return {}
    
    if isinstance(proto_extra, dict):
        return proto_extra
    
    if isinstance(proto_extra, str):
        try:
            result = json.loads(proto_extra)
            return result if isinstance(result, dict) else {}
        except (json.JSONDecodeError, TypeError):
            return {}
    
    return {}


# =====================================================
# 分享链接生成函数
# =====================================================

def build_query_string(params: Dict[str, str]) -> str:
    """
    构建查询字符串
    
    参数：
        params: 参数字典
    
    返回：
        查询字符串（不含 ? 前缀）
    """
    if not params:
        return ""
    
    return "&".join([f"{k}={v}" for k, v in params.items() if v])


def generate_vmess_uri(node: Dict[str, Any]) -> Optional[str]:
    """
    生成 VMess 协议分享链接
    
    格式：vmess://Base64(JSON)
    
    参数：
        node: 节点数据字典
    
    返回：
        VMess 分享链接
    """
    try:
        config_type = node.get('ConfigType')
        if config_type != 1:
            return None
        
        password = node.get('Password', '')
        if not password or not is_valid_guid(password):
            logger.warning(f"VMess 节点 {node.get('Remarks')} 的 UUID 无效: {password}")
            return None
        
        proto_extra = parse_proto_extra(node.get('ProtoExtra'))
        
        scy = proto_extra.get('VmessSecurity', '') or node.get('Security', '') or DEFAULT_SECURITY
        
        vmess_data = {
            "v": 2,
            "ps": remove_indexid_suffix(node.get('Remarks', '')) if node.get('Remarks') else "",
            "add": node.get('Address', ''),
            "port": node.get('Port', 443),
            "id": password,
            "aid": int(proto_extra.get('AlterId', 0)) if proto_extra.get('AlterId') else 0,
            "scy": scy,
            "net": node.get('Network', DEFAULT_NETWORK) or DEFAULT_NETWORK,
            "type": node.get('HeaderType', 'none') or 'none',
            "host": node.get('RequestHost', '') or "",
            "path": node.get('Path', '') or "",
            "tls": node.get('StreamSecurity', '') or "",
            "sni": node.get('Sni', '') or "",
            "alpn": node.get('Alpn', '') or "",
            "fp": node.get('Fingerprint', '') or "",
            "insecure": "1" if node.get('AllowInsecure') else "0"
        }
        
        json_str = json.dumps(vmess_data, separators=(',', ':'), ensure_ascii=False)
        encoded = base64_encode(json_str)
        
        return f"vmess://{encoded}"
        
    except Exception as e:
        logger.error(f"生成 VMess 链接失败: {e}")
        return None


def generate_vless_uri(node: Dict[str, Any]) -> Optional[str]:
    """
    生成 VLESS 协议分享链接
    
    格式：vless://UUID@地址:端口?参数#备注
    
    参数：
        node: 节点数据字典
    
    返回：
        VLESS 分享链接
    """
    try:
        config_type = node.get('ConfigType')
        if config_type != 5:
            return None
        
        password = url_encode(node.get('Password', ''))
        if not password:
            logger.warning(f"VLESS 节点 {node.get('Remarks')} 缺少密码")
            return None
        
        address = get_ipv6_address(node.get('Address', ''))
        port = node.get('Port', 443)
        
        proto_extra = parse_proto_extra(node.get('ProtoExtra'))
        
        params = {}
        
        encryption = proto_extra.get('VlessEncryption', '') or node.get('Security', '') or 'none'
        params['encryption'] = encryption
        
        flow = proto_extra.get('Flow', '')
        if flow:
            params['flow'] = flow
        
        stream_security = node.get('StreamSecurity', '')
        if stream_security:
            params['security'] = stream_security
        
        sni = node.get('Sni', '')
        if sni:
            params['sni'] = url_encode(sni)
        
        fingerprint = node.get('Fingerprint', '')
        if fingerprint:
            params['fp'] = url_encode(fingerprint)
        
        public_key = node.get('PublicKey', '')
        if public_key:
            params['pbk'] = url_encode(public_key)
        
        short_id = node.get('ShortId', '')
        if short_id:
            params['sid'] = url_encode(short_id)
        
        spider_x = node.get('SpiderX', '')
        if spider_x:
            params['spx'] = url_encode(spider_x)
        
        network = node.get('Network', DEFAULT_NETWORK) or DEFAULT_NETWORK
        params['type'] = network
        
        if network == 'tcp':
            header_type = node.get('HeaderType', 'none') or 'none'
            params['headerType'] = header_type
            request_host = node.get('RequestHost', '')
            if request_host:
                params['host'] = url_encode(request_host)
        
        elif network in ('ws', 'httpupgrade'):
            request_host = node.get('RequestHost', '')
            if request_host:
                params['host'] = url_encode(request_host)
            path = node.get('Path', '')
            if path:
                params['path'] = url_encode(path)
        
        elif network == 'grpc':
            request_host = node.get('RequestHost', '')
            if request_host:
                params['authority'] = url_encode(request_host)
            path = node.get('Path', '')
            if path:
                params['serviceName'] = url_encode(path)
            header_type = node.get('HeaderType', '')
            if header_type in ('gun', 'multi'):
                params['mode'] = url_encode(header_type)
        
        elif network in ('http', 'h2'):
            params['type'] = 'http'
            request_host = node.get('RequestHost', '')
            if request_host:
                params['host'] = url_encode(request_host)
            path = node.get('Path', '')
            if path:
                params['path'] = url_encode(path)
        
        query_string = build_query_string(params)
        
        remark = ""
        if node.get('Remarks'):
            remark = "#" + url_encode(remove_indexid_suffix(node['Remarks']))
        
        uri = f"vless://{password}@{address}:{port}"
        if query_string:
            uri += f"?{query_string}"
        uri += remark
        
        return uri
        
    except Exception as e:
        logger.error(f"生成 VLESS 链接失败: {e}")
        return None


def generate_trojan_uri(node: Dict[str, Any]) -> Optional[str]:
    """
    生成 Trojan 协议分享链接
    
    格式：trojan://密码@地址:端口?参数#备注
    
    参数：
        node: 节点数据字典
    
    返回：
        Trojan 分享链接
    """
    try:
        config_type = node.get('ConfigType')
        if config_type != 6:
            return None
        
        password = url_encode(node.get('Password', ''))
        if not password:
            logger.warning(f"Trojan 节点 {node.get('Remarks')} 缺少密码")
            return None
        
        address = get_ipv6_address(node.get('Address', ''))
        port = node.get('Port', 443)
        
        proto_extra = parse_proto_extra(node.get('ProtoExtra'))
        
        params = {}
        
        flow = proto_extra.get('Flow', '')
        if flow:
            params['flow'] = flow
        
        stream_security = node.get('StreamSecurity', '')
        if stream_security:
            params['security'] = stream_security
        
        sni = node.get('Sni', '')
        if sni:
            params['sni'] = url_encode(sni)
        
        fingerprint = node.get('Fingerprint', '')
        if fingerprint:
            params['fp'] = url_encode(fingerprint)
        
        public_key = node.get('PublicKey', '')
        if public_key:
            params['pbk'] = url_encode(public_key)
        
        short_id = node.get('ShortId', '')
        if short_id:
            params['sid'] = url_encode(short_id)
        
        alpn = node.get('Alpn', '')
        if alpn:
            params['alpn'] = url_encode(alpn)
        
        network = node.get('Network', DEFAULT_NETWORK) or DEFAULT_NETWORK
        params['type'] = network
        
        if network == 'tcp':
            header_type = node.get('HeaderType', 'none') or 'none'
            params['headerType'] = header_type
            request_host = node.get('RequestHost', '')
            if request_host:
                params['host'] = url_encode(request_host)
        
        elif network in ('ws', 'httpupgrade'):
            request_host = node.get('RequestHost', '')
            if request_host:
                params['host'] = url_encode(request_host)
            path = node.get('Path', '')
            if path:
                params['path'] = url_encode(path)
        
        elif network == 'grpc':
            request_host = node.get('RequestHost', '')
            if request_host:
                params['authority'] = url_encode(request_host)
            path = node.get('Path', '')
            if path:
                params['serviceName'] = url_encode(path)
        
        query_string = build_query_string(params)
        
        remark = ""
        if node.get('Remarks'):
            remark = "#" + url_encode(remove_indexid_suffix(node['Remarks']))
        
        uri = f"trojan://{password}@{address}:{port}"
        if query_string:
            uri += f"?{query_string}"
        uri += remark
        
        return uri
        
    except Exception as e:
        logger.error(f"生成 Trojan 链接失败: {e}")
        return None


def generate_shadowsocks_uri(node: Dict[str, Any]) -> Optional[str]:
    """
    生成 Shadowsocks 协议分享链接
    
    格式：ss://Base64(方法:密码)@地址:端口#备注
    
    参数：
        node: 节点数据字典
    
    返回：
        Shadowsocks 分享链接
    """
    try:
        config_type = node.get('ConfigType')
        if config_type != 3:
            return None
        
        password = node.get('Password', '')
        if not password:
            logger.warning(f"Shadowsocks 节点 {node.get('Remarks')} 缺少密码")
            return None
        
        proto_extra = parse_proto_extra(node.get('ProtoExtra'))
        
        method = proto_extra.get('SsMethod', '') or node.get('Security', '')
        if not method:
            logger.warning(f"Shadowsocks 节点 {node.get('Remarks')} 缺少加密方法")
            return None
        
        address = get_ipv6_address(node.get('Address', ''))
        port = node.get('Port', 8388)
        
        user_info = base64_encode(f"{method}:{password}", url_safe=True)
        
        remark = ""
        if node.get('Remarks'):
            remark = "#" + url_encode(remove_indexid_suffix(node['Remarks']))
        
        return f"ss://{user_info}@{address}:{port}{remark}"
        
    except Exception as e:
        logger.error(f"生成 Shadowsocks 链接失败: {e}")
        return None


def generate_socks_uri(node: Dict[str, Any]) -> Optional[str]:
    """
    生成 SOCKS 协议分享链接
    
    格式：socks://Base64(用户名:密码)@地址:端口#备注
    
    参数：
        node: 节点数据字典
    
    返回：
        SOCKS 分享链接
    """
    try:
        config_type = node.get('ConfigType')
        if config_type != 4:
            return None
        
        address = get_ipv6_address(node.get('Address', ''))
        port = node.get('Port', 1080)
        
        username = node.get('Username', '')
        password = node.get('Password', '')
        
        user_info = ""
        if username or password:
            user_info = base64_encode(f"{username}:{password}", url_safe=True)
        
        remark = ""
        if node.get('Remarks'):
            remark = "#" + url_encode(remove_indexid_suffix(node['Remarks']))
        
        if user_info:
            return f"socks://{user_info}@{address}:{port}{remark}"
        else:
            return f"socks://{address}:{port}{remark}"
        
    except Exception as e:
        logger.error(f"生成 SOCKS 链接失败: {e}")
        return None


def generate_hysteria2_uri(node: Dict[str, Any]) -> Optional[str]:
    """
    生成 Hysteria2 协议分享链接
    
    格式：hysteria2://密码@地址:端口?参数#备注
    
    参数：
        node: 节点数据字典
    
    返回：
        Hysteria2 分享链接
    """
    try:
        config_type = node.get('ConfigType')
        if config_type != 7:
            return None
        
        password = node.get('Password', '')
        
        address = get_ipv6_address(node.get('Address', ''))
        port = node.get('Port', 443)
        
        params = {}
        
        sni = node.get('Sni', '')
        if sni:
            params['sni'] = url_encode(sni)
        
        alpn = node.get('Alpn', '')
        if alpn:
            params['alpn'] = url_encode(alpn)
        
        proto_extra = parse_proto_extra(node.get('ProtoExtra'))
        
        salamander_pass = proto_extra.get('SalamanderPass', '')
        if salamander_pass:
            params['obfs'] = 'salamander'
            params['obfs-password'] = url_encode(salamander_pass)
        
        ports = proto_extra.get('Ports', '')
        if ports:
            params['mport'] = url_encode(ports.replace(':', '-'))
        
        cert_sha = node.get('CertSha', '')
        if cert_sha:
            sha = cert_sha.split(',')[0] if ',' in cert_sha else cert_sha
            params['pinSHA256'] = url_encode(sha)
        
        query_string = build_query_string(params)
        
        remark = ""
        if node.get('Remarks'):
            remark = "#" + url_encode(remove_indexid_suffix(node['Remarks']))
        
        uri = f"hysteria2://{password}@{address}:{port}"
        if query_string:
            uri += f"?{query_string}"
        uri += remark
        
        return uri
        
    except Exception as e:
        logger.error(f"生成 Hysteria2 链接失败: {e}")
        return None


def generate_tuic_uri(node: Dict[str, Any]) -> Optional[str]:
    """
    生成 TUIC 协议分享链接
    
    格式：tuic://UUID:密码@地址:端口?参数#备注
    
    参数：
        node: 节点数据字典
    
    返回：
        TUIC 分享链接
    """
    try:
        config_type = node.get('ConfigType')
        if config_type != 8:
            return None
        
        username = node.get('Username', '')
        password = node.get('Password', '')
        
        if not password:
            logger.warning(f"TUIC 节点 {node.get('Remarks')} 缺少密码")
            return None
        
        address = get_ipv6_address(node.get('Address', ''))
        port = node.get('Port', 443)
        
        params = {}
        
        sni = node.get('Sni', '')
        if sni:
            params['sni'] = url_encode(sni)
        
        alpn = node.get('Alpn', '')
        if alpn:
            params['alpn'] = url_encode(alpn)
        
        header_type = node.get('HeaderType', '')
        if header_type:
            params['congestion_control'] = header_type
        
        query_string = build_query_string(params)
        
        remark = ""
        if node.get('Remarks'):
            remark = "#" + url_encode(remove_indexid_suffix(node['Remarks']))
        
        user_info = f"{username}:{password}" if username else password
        
        uri = f"tuic://{user_info}@{address}:{port}"
        if query_string:
            uri += f"?{query_string}"
        uri += remark
        
        return uri
        
    except Exception as e:
        logger.error(f"生成 TUIC 链接失败: {e}")
        return None


def generate_wireguard_uri(node: Dict[str, Any]) -> Optional[str]:
    """
    生成 WireGuard 协议分享链接
    
    格式：wireguard://私钥@地址:端口?参数#备注
    
    参数：
        node: 节点数据字典
    
    返回：
        WireGuard 分享链接
    """
    try:
        config_type = node.get('ConfigType')
        if config_type != 9:
            return None
        
        password = node.get('Password', '')
        if not password:
            logger.warning(f"WireGuard 节点 {node.get('Remarks')} 缺少私钥")
            return None
        
        address = get_ipv6_address(node.get('Address', ''))
        port = node.get('Port', 51820)
        
        params = {}
        
        proto_extra = parse_proto_extra(node.get('ProtoExtra'))
        
        public_key = proto_extra.get('WgPublicKey', '')
        if public_key:
            params['publickey'] = url_encode(public_key)
        
        reserved = proto_extra.get('WgReserved', '')
        if reserved:
            params['reserved'] = url_encode(reserved)
        
        interface_address = proto_extra.get('WgInterfaceAddress', '')
        if interface_address:
            params['address'] = url_encode(interface_address)
        
        mtu = proto_extra.get('WgMtu', 1280)
        params['mtu'] = str(mtu) if mtu else '1280'
        
        query_string = build_query_string(params)
        
        remark = ""
        if node.get('Remarks'):
            remark = "#" + url_encode(remove_indexid_suffix(node['Remarks']))
        
        uri = f"wireguard://{password}@{address}:{port}"
        if query_string:
            uri += f"?{query_string}"
        uri += remark
        
        return uri
        
    except Exception as e:
        logger.error(f"生成 WireGuard 链接失败: {e}")
        return None


def generate_anytls_uri(node: Dict[str, Any]) -> Optional[str]:
    """
    生成 Anytls 协议分享链接
    
    格式：anytls://密码@地址:端口?参数#备注
    
    参数：
        node: 节点数据字典
    
    返回：
        Anytls 分享链接
    """
    try:
        config_type = node.get('ConfigType')
        if config_type != 11:
            return None
        
        password = url_encode(node.get('Password', ''))
        if not password:
            logger.warning(f"Anytls 节点 {node.get('Remarks')} 缺少密码")
            return None
        
        address = get_ipv6_address(node.get('Address', ''))
        port = node.get('Port', 443)
        
        params = {}
        
        stream_security = node.get('StreamSecurity', '')
        if stream_security:
            params['security'] = stream_security
        
        sni = node.get('Sni', '')
        if sni:
            params['sni'] = url_encode(sni)
        
        fingerprint = node.get('Fingerprint', '')
        if fingerprint:
            params['fp'] = url_encode(fingerprint)
        
        public_key = node.get('PublicKey', '')
        if public_key:
            params['pbk'] = url_encode(public_key)
        
        short_id = node.get('ShortId', '')
        if short_id:
            params['sid'] = url_encode(short_id)
        
        spider_x = node.get('SpiderX', '')
        if spider_x:
            params['spx'] = url_encode(spider_x)
        
        mldsa65_verify = node.get('Mldsa65Verify', '')
        if mldsa65_verify:
            params['pqv'] = url_encode(mldsa65_verify)
        
        ech_config_list = node.get('EchConfigList', '')
        if ech_config_list:
            params['ech'] = url_encode(ech_config_list)
        
        cert_sha = node.get('CertSha', '')
        if cert_sha:
            params['pcs'] = url_encode(cert_sha)
        
        finalmask = node.get('Finalmask', '')
        if finalmask:
            try:
                finalmask_obj = json.loads(finalmask)
                finalmask_str = json.dumps(finalmask_obj, separators=(',', ':'), ensure_ascii=False)
                params['fm'] = url_encode(finalmask_str)
            except (json.JSONDecodeError, TypeError):
                params['fm'] = url_encode(finalmask)
        
        alpn = node.get('Alpn', '')
        if alpn:
            params['alpn'] = url_encode(alpn)
        
        allow_insecure = node.get('AllowInsecure', False)
        if allow_insecure:
            params['insecure'] = '1'
            params['allowInsecure'] = '1'
        else:
            params['insecure'] = '0'
            params['allowInsecure'] = '0'
        
        network = node.get('Network', DEFAULT_NETWORK) or DEFAULT_NETWORK
        params['type'] = network
        
        if network == 'tcp':
            header_type = node.get('HeaderType', 'none') or 'none'
            params['headerType'] = header_type
            request_host = node.get('RequestHost', '')
            if request_host:
                params['host'] = url_encode(request_host)
        
        elif network in ('ws', 'httpupgrade'):
            request_host = node.get('RequestHost', '')
            if request_host:
                params['host'] = url_encode(request_host)
            path = node.get('Path', '')
            if path:
                params['path'] = url_encode(path)
        
        elif network == 'grpc':
            request_host = node.get('RequestHost', '')
            if request_host:
                params['authority'] = url_encode(request_host)
            path = node.get('Path', '')
            if path:
                params['serviceName'] = url_encode(path)
            header_type = node.get('HeaderType', '')
            if header_type in ('gun', 'multi'):
                params['mode'] = url_encode(header_type)
        
        elif network in ('http', 'h2'):
            params['type'] = 'http'
            request_host = node.get('RequestHost', '')
            if request_host:
                params['host'] = url_encode(request_host)
            path = node.get('Path', '')
            if path:
                params['path'] = url_encode(path)
        
        elif network == 'kcp':
            header_type = node.get('HeaderType', 'none') or 'none'
            params['headerType'] = header_type
            path = node.get('Path', '')
            if path:
                params['seed'] = url_encode(path)
        
        elif network == 'quic':
            header_type = node.get('HeaderType', 'none') or 'none'
            params['headerType'] = header_type
            quic_security = node.get('RequestHost', '')
            if quic_security:
                params['quicSecurity'] = url_encode(quic_security)
            path = node.get('Path', '')
            if path:
                params['key'] = url_encode(path)
        
        query_string = build_query_string(params)
        
        remark = ""
        if node.get('Remarks'):
            remark = "#" + url_encode(remove_indexid_suffix(node['Remarks']))
        
        uri = f"anytls://{password}@{address}:{port}"
        if query_string:
            uri += f"?{query_string}"
        uri += remark
        
        return uri
        
    except Exception as e:
        logger.error(f"生成 Anytls 链接失败: {e}")
        return None


def generate_share_uri(node: Dict[str, Any]) -> Optional[str]:
    """
    根据节点类型生成对应的分享链接
    
    参数：
        node: 节点数据字典
    
    返回：
        分享链接字符串
    """
    config_type = node.get('ConfigType')
    
    generators = {
        1: generate_vmess_uri,
        3: generate_shadowsocks_uri,
        4: generate_socks_uri,
        5: generate_vless_uri,
        6: generate_trojan_uri,
        7: generate_hysteria2_uri,
        8: generate_tuic_uri,
        9: generate_wireguard_uri,
        11: generate_anytls_uri,
    }
    
    generator = generators.get(config_type)
    
    if generator:
        return generator(node)
    else:
        logger.warning(f"不支持的协议类型: {config_type} ({CONFIG_TYPE_MAP.get(config_type, 'Unknown')})")
        return None


# =====================================================
# SQL 相关函数
# =====================================================

def read_sql_file(file_path: str) -> Optional[str]:
    """
    读取 SQL 文件内容
    
    参数：
        file_path: SQL 文件路径
    
    返回：
        SQL 文件内容
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        logger.info(f"成功读取 SQL 文件: {file_path}")
        return content
    except FileNotFoundError:
        logger.error(f"SQL 文件不存在: {file_path}")
        return None
    except PermissionError:
        logger.error(f"无权限读取 SQL 文件: {file_path}")
        return None
    except Exception as e:
        logger.error(f"读取 SQL 文件失败: {e}")
        return None


def extract_query1(sql_content: str) -> Optional[str]:
    """
    从 SQL 文件中提取查询1的内容
    
    参数：
        sql_content: SQL 文件内容
    
    返回：
        查询1的 SQL 语句
    """
    try:
        pattern = r'--\s*查询1:.*?(?=--\s*查询2:|--\s*关键筛选条件说明|$)'
        match = re.search(pattern, sql_content, re.DOTALL | re.IGNORECASE)
        
        if match:
            query = match.group(0)
            lines = query.split('\n')
            sql_lines = [line for line in lines if not line.strip().startswith('--')]
            sql = '\n'.join(sql_lines).strip()
            
            sql = re.sub(r'\s*LIMIT\s+\d+\s*;?\s*$', '', sql, flags=re.IGNORECASE)
            
            sql = sql.rstrip(';').strip()
            
            sql += f" LIMIT {MAX_NODES};"
            
            logger.info("成功提取查询1的 SQL 语句")
            return sql
        else:
            logger.error("无法从 SQL 文件中提取查询1")
            return None
            
    except Exception as e:
        logger.error(f"提取查询1失败: {e}")
        return None


def execute_query(db_path: str, sql: str) -> Optional[List[Dict[str, Any]]]:
    """
    执行 SQL 查询
    
    参数：
        db_path: 数据库文件路径
        sql: SQL 查询语句
    
    返回：
        查询结果列表
    """
    conn = None
    try:
        if not os.path.exists(db_path):
            logger.error(f"数据库文件不存在: {db_path}")
            return None
        
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute(sql)
        rows = cursor.fetchall()
        
        results = [dict(row) for row in rows]
        
        logger.info(f"查询成功，返回 {len(results)} 条记录")
        return results
        
    except sqlite3.Error as e:
        logger.error(f"数据库查询错误: {e}")
        return None
    except Exception as e:
        logger.error(f"执行查询失败: {e}")
        return None
    finally:
        if conn:
            conn.close()
            logger.info("数据库连接已关闭")


def get_full_node_data(db_path: str, index_ids: List[str]) -> Optional[List[Dict[str, Any]]]:
    """
    根据 IndexId 列表获取完整的节点数据
    
    参数：
        db_path: 数据库文件路径
        index_ids: IndexId 列表
    
    返回：
        完整节点数据列表
    
    注意：
        数据库中的 Id 字段存储密码/UUID（旧版本字段名），
        Password 字段为空。需要将 Id 字段值作为密码使用。
    """
    if not index_ids:
        return []
    
    conn = None
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        placeholders = ','.join(['?' for _ in index_ids])
        sql = f"""
            SELECT 
                IndexId, ConfigType, Remarks, Address, Port, 
                Id, Password, Username, Network, HeaderType, RequestHost,
                Path, StreamSecurity, AllowInsecure, Sni, Alpn,
                Fingerprint, PublicKey, ShortId, SpiderX, ProtoExtra,
                CertSha, Extra, Security
            FROM ProfileItem 
            WHERE IndexId IN ({placeholders})
        """
        
        cursor.execute(sql, index_ids)
        rows = cursor.fetchall()
        
        results = []
        for row in rows:
            node = dict(row)
            if node.get('Password') is None or node.get('Password') == '':
                node['Password'] = node.get('Id')
            results.append(node)
        
        logger.info(f"获取到 {len(results)} 个节点的完整数据")
        return results
        
    except sqlite3.Error as e:
        logger.error(f"获取节点数据错误: {e}")
        return None
    finally:
        if conn:
            conn.close()


# =====================================================
# 文件导出函数
# =====================================================

def get_export_file_path(base_dir: str) -> str:
    """
    生成导出文件路径
    
    如果文件已存在，则添加时间戳或序号以区分
    
    参数：
        base_dir: 导出目录
    
    返回：
        完整的导出文件路径
    """
    today = datetime.now()
    date_str = today.strftime("%m%d")
    
    base_name = f"{date_str}.txt"
    file_path = os.path.join(base_dir, base_name)
    
    if not os.path.exists(file_path):
        return file_path
    
    time_str = today.strftime("%H%M")
    file_path = os.path.join(base_dir, f"{date_str}_{time_str}.txt")
    
    if not os.path.exists(file_path):
        return file_path
    
    counter = 1
    while True:
        file_path = os.path.join(base_dir, f"{date_str}_{time_str}_{counter}.txt")
        if not os.path.exists(file_path):
            return file_path
        counter += 1
        
        if counter > 1000:
            file_path = os.path.join(base_dir, f"{date_str}_{today.strftime('%H%M%S')}.txt")
            return file_path


def export_to_file(file_path: str, share_links: List[str]) -> bool:
    """
    将分享链接导出到文件
    
    参数：
        file_path: 导出文件路径
        share_links: 分享链接列表
    
    返回：
        是否导出成功
    """
    try:
        dir_path = os.path.dirname(file_path)
        if dir_path and not os.path.exists(dir_path):
            os.makedirs(dir_path)
            logger.info(f"创建导出目录: {dir_path}")
        
        content = '\n'.join(share_links)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        logger.info(f"成功导出 {len(share_links)} 个节点到: {file_path}")
        return True
        
    except PermissionError:
        logger.error(f"无权限写入文件: {file_path}")
        return False
    except Exception as e:
        logger.error(f"导出文件失败: {e}")
        return False


# =====================================================
# 主函数
# =====================================================

def main():
    """
    主函数：执行完整的导出流程
    """
    logger.info("=" * 60)
    logger.info("v2rayN 优秀节点导出工具启动")
    logger.info("=" * 60)
    
    logger.info(f"数据库路径: {DB_PATH}")
    logger.info(f"SQL 文件路径: {SQL_FILE_PATH}")
    logger.info(f"导出目录: {EXPORT_DIR}")
    logger.info(f"最大导出节点数: {MAX_NODES}")
    
    sql_content = read_sql_file(SQL_FILE_PATH)
    if not sql_content:
        logger.error("无法读取 SQL 文件，程序退出")
        return 1
    
    query_sql = extract_query1(sql_content)
    if not query_sql:
        logger.error("无法提取查询语句，程序退出")
        return 1
    
    logger.info("执行查询以获取优秀节点列表...")
    query_results = execute_query(DB_PATH, query_sql)
    
    if query_results is None:
        logger.error("查询执行失败，程序退出")
        return 1
    
    if not query_results:
        logger.warning("查询结果为空，没有找到符合条件的节点")
        return 0
    
    logger.info(f"查询返回 {len(query_results)} 个节点")
    
    index_ids = [row.get('IndexId') for row in query_results if row.get('IndexId')]
    
    if not index_ids:
        logger.error("无法获取节点的 IndexId，程序退出")
        return 1
    
    logger.info("获取节点完整数据...")
    full_nodes = get_full_node_data(DB_PATH, index_ids)
    
    if not full_nodes:
        logger.error("获取节点数据失败，程序退出")
        return 1
    
    id_to_node = {node.get('IndexId'): node for node in full_nodes}
    
    share_links = []
    success_count = 0
    fail_count = 0
    
    logger.info("生成分享链接...")
    for row in query_results:
        index_id = row.get('IndexId')
        node = id_to_node.get(index_id)
        
        if not node:
            logger.warning(f"未找到节点 {index_id} 的完整数据")
            fail_count += 1
            continue
        
        uri = generate_share_uri(node)
        
        if uri:
            share_links.append(uri)
            success_count += 1
            logger.debug(f"成功生成: {node.get('Remarks', index_id)}")
        else:
            fail_count += 1
            logger.warning(f"生成失败: {node.get('Remarks', index_id)}")
    
    logger.info(f"链接生成完成: 成功 {success_count} 个，失败 {fail_count} 个")
    
    if not share_links:
        logger.error("没有成功生成任何分享链接，程序退出")
        return 1
    
    file_path = get_export_file_path(EXPORT_DIR)
    logger.info(f"导出文件路径: {file_path}")
    
    if export_to_file(file_path, share_links):
        logger.info("=" * 60)
        logger.info(f"导出成功！共导出 {len(share_links)} 个节点")
        logger.info(f"文件位置: {file_path}")
        logger.info("=" * 60)
        return 0
    else:
        logger.error("导出文件失败，程序退出")
        return 1


if __name__ == "__main__":
    sys.exit(main())
