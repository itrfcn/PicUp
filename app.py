from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from models import db, User, UploadRecord
from datetime import timedelta
import os
import sys

# 创建Flask应用实例
app = Flask(__name__)

# 配置应用
app.config['SECRET_KEY'] = os.urandom(24)  # 生成随机密钥用于会话管理
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///picup.db'  # SQLite数据库路径
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  # 关闭SQLAlchemy的修改跟踪
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)  # 设置会话有效期为7天

# 初始化数据库
with app.app_context():
    db.init_app(app)
    db.create_all()
    
    # 创建默认管理员用户
    admin = User.query.filter_by(username='admin').first()
    if not admin:
        admin = User(username='admin', role='admin')
        admin.set_password('admin123')
        db.session.add(admin)
        db.session.commit()

# 登录装饰器
def login_required(func):
    def wrapper(*args, **kwargs):
        if 'user_id' not in session:
            flash('请先登录！')
            return redirect(url_for('login'))
        return func(*args, **kwargs)
    wrapper.__name__ = func.__name__
    return wrapper

# 管理员装饰器
def admin_required(func):
    def wrapper(*args, **kwargs):
        if 'user_id' not in session:
            flash('请先登录！')
            return redirect(url_for('login'))
        user = User.query.get(session['user_id'])
        if not user or not user.is_admin():
            flash('权限不足！')
            return redirect(url_for('index'))
        return func(*args, **kwargs)
    wrapper.__name__ = func.__name__
    return wrapper

# 模板过滤器：将UTC时间转换为本地时间（东八区）
@app.template_filter('local_time')
def local_time(utc_datetime):
    from datetime import timedelta
    if not utc_datetime:
        return ''
    # 转换为东八区时间（UTC+8）
    local_datetime = utc_datetime + timedelta(hours=8)
    return local_datetime.strftime('%Y-%m-%d %H:%M:%S')

# 首页路由
@app.route('/')
def index():
    return render_template('index.html')

# 登录路由
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        # 查找用户
        user = User.query.filter_by(username=username).first()
        
        # 验证用户
        if user and user.check_password(password):
            if user.is_active():
                # 设置会话
                session['user_id'] = user.id
                session['username'] = user.username
                session['role'] = user.role
                session.permanent = True
                
                flash('登录成功！')
                return redirect(url_for('index'))
            else:
                flash('用户已被封禁！')
        else:
            flash('用户名或密码错误！')
    
    return render_template('login.html')

# 注册路由已禁用，用户只能由管理员创建
# @app.route('/register', methods=['GET', 'POST'])
# def register():
#     if request.method == 'POST':
#         username = request.form['username']
#         password = request.form['password']
#         confirm_password = request.form['confirm_password']
#         
#         # 验证密码是否一致
#         if password != confirm_password:
#             flash('两次输入的密码不一致！')
#             return redirect(url_for('register'))
#         
#         # 检查用户名是否已存在
#         if User.query.filter_by(username=username).first():
#             flash('用户名已存在！')
#             return redirect(url_for('register'))
#         
#         # 创建新用户
#         new_user = User(username=username)
#         new_user.set_password(password)
#         
#         try:
#             db.session.add(new_user)
#             db.session.commit()
#             flash('注册成功！请登录。')
#             return redirect(url_for('login'))
#         except Exception as e:
#             db.session.rollback()
#             flash('注册失败，请稍后重试！')
#             return redirect(url_for('register'))
#     
#     return render_template('register.html')

# 退出登录路由
@app.route('/logout')
def logout():
    # 清除会话
    session.clear()
    flash('已成功退出登录！')
    return redirect(url_for('login'))

# 文件上传路由
@app.route('/upload', methods=['GET', 'POST'])
@login_required
def upload():
    if request.method == 'POST':
        # 检查是否有文件上传
        if 'file' not in request.files:
            flash('没有选择文件！')
            return redirect(url_for('upload'))
        
        file = request.files['file']
        
        # 检查文件是否为空
        if file.filename == '':
            flash('没有选择文件！')
            return redirect(url_for('upload'))
        
        # 保存文件到临时目录
        temp_path = os.path.join(app.root_path, 'temp', file.filename)
        os.makedirs(os.path.dirname(temp_path), exist_ok=True)
        file.save(temp_path)
        
        try:
            # 导入上传模块
            sys.path.append(app.root_path)
            from free import upload_file_to_oss
            
            # 调用上传函数
            file_info = upload_file_to_oss(temp_path)
            
            if file_info:
                # 保存上传记录到数据库
                upload_record = UploadRecord(
                    user_id=session['user_id'],
                    filename=file_info['name'],
                    original_filename=file.filename,  # 保存原始文件名
                    file_url=file_info['file'],
                    file_size=file_info['size'],
                    file_type=file_info['type']
                )
                
                db.session.add(upload_record)
                db.session.commit()
                
                flash('文件上传成功！')
                
                # 传递上传成功的文件信息到模板
                uploaded_file = {
                    'url': upload_record.file_url,
                    'name': upload_record.original_filename
                }
                return render_template('upload.html', uploaded_file=uploaded_file)
            else:
                flash('文件上传失败！')
        except Exception as e:
            flash(f'文件上传失败：{str(e)}')
        finally:
            # 删除临时文件
            if os.path.exists(temp_path):
                os.remove(temp_path)
    
    return render_template('upload.html', uploaded_file=None)

# 用户上传记录路由
@app.route('/records')
@login_required
def records():
    # 获取当前用户的上传记录
    user_id = session['user_id']
    records = UploadRecord.query.filter_by(user_id=user_id).order_by(UploadRecord.created_at.desc()).all()
    
    return render_template('records.html', records=records)

# 删除上传记录路由
@app.route('/record/delete/<int:record_id>', methods=['POST'])
@login_required
def delete_record(record_id):
    try:
        # 获取当前用户ID
        user_id = session['user_id']
        
        # 查找记录
        record = UploadRecord.query.filter_by(id=record_id, user_id=user_id).first()
        
        if not record:
            flash('记录不存在或您没有权限删除！')
            return redirect(url_for('records'))
        
        # 删除记录
        db.session.delete(record)
        db.session.commit()
        
        flash('记录删除成功！')
        return redirect(url_for('records'))
    except Exception as e:
        db.session.rollback()
        flash(f'删除失败：{str(e)}')
        return redirect(url_for('records'))

# 管理员用户管理路由
@app.route('/admin/users')
@admin_required
def admin_users():
    # 获取所有用户
    users = User.query.all()
    
    return render_template('admin/users.html', users=users)

# 管理员添加用户路由
@app.route('/admin/user/add', methods=['GET', 'POST'])
@admin_required
def admin_add_user():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        role = request.form['role']
        
        # 检查用户名是否已存在
        if User.query.filter_by(username=username).first():
            flash('用户名已存在！')
            return redirect(url_for('admin_add_user'))
        
        # 创建新用户
        new_user = User(username=username, role=role)
        new_user.set_password(password)
        
        try:
            db.session.add(new_user)
            db.session.commit()
            flash('用户添加成功！')
            return redirect(url_for('admin_users'))
        except Exception as e:
            db.session.rollback()
            flash('用户添加失败，请稍后重试！')
            return redirect(url_for('admin_add_user'))
    
    return render_template('admin/add_user.html')

# 管理员删除用户路由
@app.route('/admin/user/delete/<int:user_id>')
@admin_required
def admin_delete_user(user_id):
    # 不能删除管理员自己
    if session['user_id'] == user_id:
        flash('不能删除当前登录的管理员账户！')
        return redirect(url_for('admin_users'))
    
    user = User.query.get(user_id)
    if user:
        try:
            # 删除用户的所有上传记录
            UploadRecord.query.filter_by(user_id=user_id).delete()
            # 删除用户
            db.session.delete(user)
            db.session.commit()
            flash('用户删除成功！')
        except Exception as e:
            db.session.rollback()
            flash('用户删除失败，请稍后重试！')
    else:
        flash('用户不存在！')
    
    return redirect(url_for('admin_users'))

# 管理员封禁/解封用户路由
@app.route('/admin/user/toggle_status/<int:user_id>')
@admin_required
def admin_toggle_status(user_id):
    # 不能封禁管理员自己
    if session['user_id'] == user_id:
        flash('不能封禁当前登录的管理员账户！')
        return redirect(url_for('admin_users'))
    
    user = User.query.get(user_id)
    if user:
        try:
            # 切换用户状态
            user.status = 'banned' if user.status == 'active' else 'active'
            db.session.commit()
            flash('用户状态已更新！')
        except Exception as e:
            db.session.rollback()
            flash('用户状态更新失败，请稍后重试！')
    else:
        flash('用户不存在！')
    
    return redirect(url_for('admin_users'))

# API: 获取OSS上传密钥
@app.route('/api/oss-key', methods=['POST'])
@login_required
def get_oss_upload_key():
    try:
        # 导入上传模块
        import sys
        sys.path.append(app.root_path)
        from free import get_oss_key, get_session_cookie, COOKIE_STRING
        
        # 步骤1: 使用配置的remember_student Cookie
        remember_cookie = COOKIE_STRING.strip()
        if not remember_cookie:
            return jsonify({
                'success': False,
                'message': 'Cookie未配置'
            }), 500
        
        # 步骤2: 检查是否已经包含s=部分
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
        
        # 获取OSS上传密钥
        oss_config = get_oss_key(cookies)
        
        if oss_config:
            return jsonify({
                'success': True,
                'data': oss_config
            })
        else:
            return jsonify({
                'success': False,
                'message': '获取上传密钥失败'
            }), 500
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

# API: 保存上传记录
@app.route('/api/save-record', methods=['POST'])
@login_required
def save_upload_record():
    try:
        data = request.get_json()
        
        # 验证必要参数
        if not all(key in data for key in ['name', 'file', 'size', 'type', 'original_filename']):
            return jsonify({
                'success': False,
                'message': f'参数不完整，缺少：{[key for key in ["name", "file", "size", "type", "original_filename"] if key not in data]}'
            }), 400
        
        # 尝试转换数据类型
        try:
            file_size = int(data['size']) if data['size'] else 0
        except (ValueError, TypeError):
            return jsonify({
                'success': False,
                'message': '文件大小格式错误'
            }), 400
        
        # 创建上传记录
        upload_record = UploadRecord(
            user_id=session['user_id'],
            filename=data['name'],
            original_filename=data['original_filename'],
            file_url=data['file'],
            file_size=file_size,
            file_type=data['type']
        )
        
        db.session.add(upload_record)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '记录保存成功',
            'data': {
                'record_id': upload_record.id
            }
        })
    except Exception as e:
        db.session.rollback()
        import traceback
        print(f"保存上传记录失败: {str(e)}")
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': f'保存记录失败: {str(e)}'
        }), 500

if __name__ == '__main__':
    app.run(debug=True, port=8080)
