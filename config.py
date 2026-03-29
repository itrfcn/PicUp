#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# ========================== 配置参数 ==========================
# 课程页面URL（可自定义）
COURSE_URL = os.getenv('COURSE_URL', '')

# Cookie信息（字符串格式，只需要remember_student部分，s=部分会自动获取）
COOKIE_STRING = os.getenv('COOKIE_STRING', '')
# =============================================================
