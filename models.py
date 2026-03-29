from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

# 创建数据库实例
db = SQLAlchemy()

# 用户模型
class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(20), default='user')  # 'user' 或 'admin'
    status = db.Column(db.String(20), default='active')  # 'active' 或 'banned'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 定义与UploadRecord的关系
    upload_records = db.relationship('UploadRecord', backref='user', lazy=True)
    
    # 设置密码的方法
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    # 验证密码的方法
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    # 检查是否为管理员
    def is_admin(self):
        return self.role == 'admin'
    
    # 检查用户是否活跃
    def is_active(self):
        return self.status == 'active'

# 文件上传记录模型
class UploadRecord(db.Model):
    __tablename__ = 'upload_records'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    filename = db.Column(db.String(255), nullable=False)  # OSS上的文件名
    original_filename = db.Column(db.String(255), nullable=False)  # 原始真实文件名
    file_url = db.Column(db.String(512), nullable=False)
    file_size = db.Column(db.Integer, nullable=False)
    file_type = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<UploadRecord {self.filename}>'
