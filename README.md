# PicUp 图床系统

PicUp 是一个基于 Flask 的图床系统，支持用户上传图片到 OSS 存储，并提供上传记录管理和管理员后台功能。
核心亮点，利用了班级魔方的接口，实现了免费使用国内高速的OSS存储。同时可以直接使用班级魔方的域名访问图片。
不仅仅是图床，经过测试支持以下文件类型：
.png、.jpg、.jpeg、.txt、Word、PPT、Excel

如果你只想本地使用免费的OSS存储，不想部署网站可以访问这个项目：[FreePic](https://github.com/itrfcn/FreePic)

## 功能特点

### 用户功能
- 🔐 用户登录/登出
- 📤 文件上传（支持上传到 OSS）
- 📋 上传记录查看和管理
- 🗑️ 删除上传记录

### 管理员功能
- 👥 用户管理（查看、添加、删除用户）
- 🚫 用户状态管理（封禁/解封）
- 📊 全站上传记录监控

## 技术栈

- **后端框架**：Flask 3.1.2
- **数据库**：SQLite
- **ORM**：Flask-SQLAlchemy
- **认证**：Flask-Login
- **文件存储**：OSS（阿里云对象存储，免费使用）
- **模板引擎**：Jinja2
- **样式**：HTML5 + CSS3

## 安装部署

### 1. 环境要求

- Python 3.12+
- pip 或其他包管理工具

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 配置参数

添加环境变量：
- COURSE_URL：班级魔方课程页面URL
- COOKIE_STRING：班级魔方Cookie信息

#### 参数说明

需要微信扫码注册班级魔方教师账号和学生账号，一个微信就可以同时注册学生账号和教师账号。
教师账号创建班级，学生账号加入班级。
教师账号发布一个 填报/问卷 添加文件上传项，学生账号加入填报/问卷。
问卷的链接就是 COURSE_URL 参数。
COOKIE_STRING是学生账号的Cookie信息的remember_student部分，s=部分会自动获取。
Cookie有效期为5年放心使用。

### 4. 启动应用

```bash
python app.py
```

应用将在 `http://127.0.0.1:8080` 启动。

## 使用说明

### 登录系统

1. 访问 `http://127.0.0.1:8080/login`
2. 使用默认管理员账户登录：
   - 用户名：admin
   - 密码：admin123

### 文件上传

1. 登录后，点击 "上传文件" 菜单
2. 选择要上传的文件
3. 点击 "上传" 按钮
4. 上传成功后，将显示文件的访问链接

### 查看上传记录

1. 登录后，点击 "上传记录" 菜单
2. 可以查看所有上传的文件记录
3. 点击 "删除" 按钮可以删除不需要的记录

### 管理员后台

1. 登录管理员账户后，点击 "用户管理" 菜单
2. 可以查看所有用户列表
3. 可以添加新用户、删除用户或封禁/解封用户

## 项目结构

```
PicUp/
├── app.py              # 应用入口和路由
├── config.py           # 配置文件
├── models.py           # 数据库模型
├── free.py             # OSS上传模块
├── requirements.txt    # 依赖列表
├── templates/          # 模板文件
│   ├── admin/          # 管理员模板
│   │   ├── add_user.html
│   │   └── users.html
│   ├── index.html      # 首页
│   ├── login.html      # 登录页
│   ├── records.html    # 上传记录页
│   └── upload.html     # 上传页面
├── static/             # 静态资源
│   └── favicon.png
├── instance/           # 数据库文件目录
│   └── picup.db
├── temp/               # 临时文件目录
├── .gitignore          # Git忽略文件
└── README.md           # 项目说明
```

## 数据模型

### User（用户模型）

| 字段名 | 类型 | 描述 |
|--------|------|------|
| id | Integer | 用户ID |
| username | String(50) | 用户名 |
| password_hash | String(128) | 密码哈希 |
| role | String(20) | 角色（user/admin） |
| status | String(20) | 状态（active/banned） |
| created_at | DateTime | 创建时间 |
| updated_at | DateTime | 更新时间 |

### UploadRecord（上传记录模型）

| 字段名 | 类型 | 描述 |
|--------|------|------|
| id | Integer | 记录ID |
| user_id | Integer | 用户ID |
| filename | String(255) | OSS上的文件名 |
| original_filename | String(255) | 原始文件名 |
| file_url | String(512) | 文件访问URL |
| file_size | Integer | 文件大小（字节） |
| file_type | String(100) | 文件类型 |
| created_at | DateTime | 创建时间 |

## 默认账户

### 管理员账户
- 用户名：admin
- 密码：admin123
- 角色：管理员

## 注意事项

1. 系统使用 SQLite 数据库，数据文件位于 `instance/picup.db`
2. 上传的文件会先保存到 `temp/` 目录，上传完成后会自动删除临时文件
3. 用户注册功能已禁用，新用户只能由管理员添加
4. 管理员无法删除自己的账户
5. 管理员无法封禁自己的账户

## 更新日志

### v1.0.0
- 初始版本发布
- 实现基本的文件上传功能
- 实现用户认证和权限管理
- 实现管理员后台功能

## 许可证

MIT License
