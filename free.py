#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import json
import os
import random
import string
import argparse
import hashlib
import time

# 导入配置参数
from config import COURSE_URL, COOKIE_STRING

# ========================== 配置参数 ==========================
# 调试模式（True=打印详细信息，False=只打印关键信息）
DEBUG = False

# 支持的文件格式 ，网站默认的是.png、.jpg、.jpeg，现在添加.txt、Word、PPT、Excel支持
SUPPORTED_FILE_FORMATS = ['.png', '.jpg', '.jpeg', '.txt', '.doc', '.docx', '.ppt', '.pptx', '.xls', '.xlsx']
# =============================================================

# 定义获取s=部分cookie的函数
def get_session_cookie(remember_cookie=None):
    """
    获取s=部分的session cookie
    
    参数:
        remember_cookie: remember_student部分的cookie（可选）
    
    返回:
        s=部分的cookie字符串
    """
    url = COURSE_URL
    
    # 构建基础请求头
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36",
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "accept-encoding": "gzip, deflate, br, zstd",
        "accept-language": "zh-CN,zh;q=0.9",
        "cache-control": "max-age=0"
    }
    
    # 如果提供了remember_cookie，添加到请求头中
    if remember_cookie:
        headers["cookie"] = remember_cookie
    
    try:
        # 发送GET请求获取Set-Cookie头
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        # 获取Set-Cookie头
        cookie_header = response.headers.get('Set-Cookie')
        if cookie_header:
            # 查找s=部分的cookie
            import re
            s_cookie_match = re.search(r's=([^;]+);', cookie_header)
            if s_cookie_match:
                s_cookie = f"s={s_cookie_match.group(1)}"
                return s_cookie
        
        return ""
        
    except requests.exceptions.RequestException as e:
        return ""

# 定义获取OSS上传密钥的函数
def get_oss_key(cookies=None):
    """
    获取OSS上传密钥
    
    参数:
        cookies: Cookie信息，字符串格式（可选）
    
    返回:
        OSS配置字典
    """
    url = "https://k8n.cn/student/oss-upload-key"
    
    # 构建基础请求头
    headers = {
        "accept": "*/*",
        "accept-encoding": "gzip, deflate, br, zstd",
        "accept-language": "zh-CN,zh;q=0.9",
        "priority": "u=1, i",
        "referer": COURSE_URL,
        "sec-ch-ua": '"Chromium";v="146", "Not-A.Brand";v="24", "Google Chrome";v="146"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": "Windows",
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36",
        "x-requested-with": "XMLHttpRequest"
    }
    
    # 设置Cookie
    if cookies:
        headers["cookie"] = cookies
    else:
        # 使用默认cookie
        headers["cookie"] = COOKIE_STRING
    
    try:
        # 发送GET请求获取OSS密钥
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # 检查请求是否成功
        
        # 解析响应
        oss_config = response.json()
        
        # 检查是否是错误响应
        if 'code' in oss_config and oss_config['code'] != 0:
            return None
        
        # 检查是否包含必要的键
        required_keys = ['accessid', 'host', 'policy', 'signature', 'expire', 'callback', 'dir']
        missing_keys = [key for key in required_keys if key not in oss_config]
        if missing_keys:
            return None
        
        return oss_config
        
    except requests.exceptions.RequestException as e:
        return None
    except json.JSONDecodeError as e:
        return None

# 定义生成随机文件名的函数
def generate_random_filename(file_extension):
    """
    生成随机文件名，格式：哈希值 + 原扩展名
    示例：a1b2c3d4e5f6g7h8i9j0.png
    """
    
    # 生成包含时间戳和随机字符串的哈希值
    timestamp = str(time.time())
    random_str = ''.join(random.choices(string.ascii_letters + string.digits, k=10))
    hash_input = f"{timestamp}{random_str}".encode('utf-8')
    
    # 使用SHA-256哈希算法生成文件名
    hash_name = hashlib.sha256(hash_input).hexdigest()[:19]  # 取前19位
    
    # 组合成完整的哈希文件名
    hash_filename = f"{hash_name}{file_extension}"
    
    return hash_filename

# 定义上传文件到OSS的函数
def upload_image_to_oss(oss_config, image_path):
    """
    上传文件到OSS
    
    参数:
        oss_config: OSS配置字典
        image_path: 文件本地路径
    
    返回:
        成功返回文件信息字典，失败返回None
    """
    if not oss_config:
        return None
    
    # 检查文件是否存在
    if not os.path.exists(image_path):
        return None
    
    # 检查文件是否为支持的格式
    file_extension = os.path.splitext(image_path)[1].lower()
    if file_extension not in SUPPORTED_FILE_FORMATS:
        return None
    
    # 获取OSS配置参数
    accessid = oss_config['accessid']
    host = oss_config['host']
    policy = oss_config['policy']
    signature = oss_config['signature']
    expire = oss_config['expire']
    callback = oss_config['callback']
    dir = oss_config['dir']
    
    # 生成随机文件名
    filename = generate_random_filename(file_extension)
    
    # 构建上传URL
    upload_url = host
    
    # 构建表单数据
    form_data = {
        'key': dir + '/' + filename,  # 完整的文件路径
        'OSSAccessKeyId': accessid,
        'policy': policy,
        'Signature': signature,
        'success_action_status': '200',  # 成功返回的状态码
        'callback': callback
    }
    
    try:
        # 打开文件并发送POST请求
        with open(image_path, 'rb') as f:
            # 设置正确的Content-Type
            if file_extension == '.txt':
                content_type = 'text/plain'
            elif file_extension in ['.doc', '.docx']:
                content_type = 'application/msword' if file_extension == '.doc' else 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
            elif file_extension in ['.ppt', '.pptx']:
                content_type = 'application/vnd.ms-powerpoint' if file_extension == '.ppt' else 'application/vnd.openxmlformats-officedocument.presentationml.presentation'
            elif file_extension in ['.xls', '.xlsx']:
                content_type = 'application/vnd.ms-excel' if file_extension == '.xls' else 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            else:
                content_type = f'image/{file_extension[1:]}'
            
            # 添加文件到表单数据
            files = {
                'file': (filename, f, content_type)
            }
            
            # 发送上传请求
            response = requests.post(upload_url, data=form_data, files=files)
            response.raise_for_status()  # 检查请求是否成功
            
            # 解析响应内容（如果是JSON格式）
            try:
                response_json = response.json()
                if response_json.get('data') and response_json['data'].get('file'):
                    data = response_json['data']
                    # 返回文件信息
                    return {
                        'name': data.get('name'),
                        'file': data.get('file'),
                        'size': data.get('size'),
                        'type': data.get('type')
                    }
            except json.JSONDecodeError:
                # 尝试从响应文本中提取文件信息
                return {
                    'name': filename,
                    'file': f"{host}/{dir}/{filename}",
                    'size': os.path.getsize(image_path),
                    'type': f"image/{file_extension[1:]}"
                }
            
            return None
            
    except requests.exceptions.RequestException as e:
        return None
    except Exception as e:
        return None

# 定义解析命令行参数的函数
def parse_args():
    """
    解析命令行参数
    
    返回:
        args: 解析后的参数对象
    """
    parser = argparse.ArgumentParser(description="文件上传功能的脚本")
    
    # 添加命令行参数
    parser.add_argument("-c", "--cookie", type=str, default=COOKIE_STRING, 
                      help="Cookie信息（字符串格式，只需要remember_student部分）")
    parser.add_argument("-i", "--image", type=str, required=True, 
                      help="要上传的文件路径")

    parser.add_argument("--debug", action="store_true", default=DEBUG, 
                      help="启用调试模式")
    
    return parser.parse_args()

# 主函数，接收文件路径，返回文件信息
def upload_file_to_oss(image_path, cookie=COOKIE_STRING, debug=DEBUG):
    """
    上传文件到OSS并返回文件信息
    
    参数:
        image_path: 文件本地路径
        cookie: Cookie信息（字符串格式，只需要remember_student部分）
        debug: 是否启用调试模式
    
    返回:
        成功返回包含文件信息的字典，失败返回None
        返回格式: {name, file, size, type}
    """
    # 使用传入的参数或默认值
    global COOKIE_STRING, DEBUG
    COOKIE_STRING = cookie or COOKIE_STRING
    DEBUG = debug or DEBUG
    
    # 步骤1: 使用配置的remember_student Cookie
    remember_cookie = COOKIE_STRING.strip()
    if not remember_cookie:
        return None
    
    # 检查是否已经包含s=部分
    if "s=" in remember_cookie and "remember_student" in remember_cookie:
        # 已经是完整的cookie字符串
        cookies = remember_cookie
    else:
        # 只包含remember_student部分，需要获取s=部分
        s_cookie = get_session_cookie(remember_cookie)
        
        # 合并两部分cookie
        if s_cookie:
            cookies = f"{remember_cookie}; {s_cookie}"
        else:
            # 如果获取不到s=部分，仍然使用remember_cookie尝试
            cookies = remember_cookie
    
    # 步骤2: 获取OSS上传密钥
    oss_config = get_oss_key(cookies)
    if not oss_config:
        return None
    
    # 步骤3: 上传文件到OSS
    # 处理相对路径
    if not os.path.isabs(image_path):
        image_path = os.path.abspath(image_path)
    
    file_info = upload_image_to_oss(oss_config, image_path)
    
    return file_info

if __name__ == "__main__":
    # 解析命令行参数
    args = parse_args()
    
    # 调用上传函数
    file_info = upload_file_to_oss(args.image, args.cookie, args.debug)
    
    if file_info:
        print(f"文件名: {file_info['name']}")
        print(f"文件URL: {file_info['file']}")
        print(f"文件大小: {file_info['size']} 字节")
        print(f"文件类型: {file_info['type']}")
    else:
        print("上传失败")
