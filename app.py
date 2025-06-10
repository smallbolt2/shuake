from flask import Flask, render_template, request, jsonify
import json
import threading
import time
from datetime import datetime
import os
from mooc.user import User
from flask_socketio import SocketIO, emit
import logging
from logging.handlers import QueueHandler
import queue

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

# 全局变量
users = {}
user_threads = {}
log_queue = queue.Queue()

# 自定义日志处理器
class WebSocketLogHandler(logging.Handler):
    def emit(self, record):
        try:
            msg = self.format(record)
            socketio.emit('log_message', {
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'message': msg
            })
        except Exception:
            self.handleError(record)

# 设置日志处理器
def setup_logging():
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    
    # 禁用Werkzeug的访问日志
    logging.getLogger('werkzeug').setLevel(logging.WARNING)
    
    # 控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    root_logger.addHandler(console_handler)
    
    # WebSocket处理器
    ws_handler = WebSocketLogHandler()
    ws_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    root_logger.addHandler(ws_handler)

# 在应用启动时设置日志
setup_logging()

def load_config():
    """加载配置文件"""
    try:
        with open('config.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return {"users": [], "global": {"limit": 3}}

def save_config(config):
    """保存配置文件"""
    with open('sample.config.json', 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=2)

@app.route('/')
def index():
    """主页"""
    return render_template('index.html')

@app.route('/api/status')
def get_status():
    """获取系统状态"""
    status = {
        'running_users': len([u for u in users.values() if u.running]),
        'total_users': len(users),
        'users': []
    }
    
    for username, user in users.items():
        user_status = user.get_status()
        status['users'].append({
            'username': username,
            'status': user_status['status'],
            'course': user_status['course'],
            'video': user_status['video'],
            'running': user_status['running']
        })
    
    return jsonify(status)

@app.route('/api/logs')
def get_logs():
    """获取日志（简化版本）"""
    logs = []
    for username, user in users.items():
        if hasattr(user, 'logger') and user.logger:
            # 这里可以添加获取用户日志的逻辑
            logs.append({
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'username': username,
                'message': user.current_status
            })
    return jsonify({'logs': logs})

@app.route('/api/start', methods=['POST'])
def start_user():
    """启动用户"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': '请求数据为空'})
        
        username = data.get('username')
        if not username:
            return jsonify({'success': False, 'message': '用户名不能为空'})
        
        if username in user_threads and user_threads[username].is_alive():
            return jsonify({'success': False, 'message': '用户已在运行中'})
        
        # 从配置文件获取用户信息
        config = load_config()
        user_config = None
        for user in config['users']:
            if user['username'] == username:
                user_config = user
                break
        
        if not user_config:
            return jsonify({'success': False, 'message': '用户配置不存在'})
        
        # 创建用户实例，使用全局limit参数
        user = User(
            base_url=user_config['base_url'],
            school_id=user_config['school_id'],
            username=user_config['username'],
            password=user_config['password'],
            study_limit=config['global']['limit']  # 使用全局limit参数
        )
        
        users[username] = user
        
        # 启动用户线程
        def run_user():
            try:
                user.run()
            except Exception as e:
                user.update_status(f"运行出错: {str(e)}")
        
        thread = threading.Thread(target=run_user, daemon=True)
        thread.start()
        user_threads[username] = thread
        
        return jsonify({'success': True, 'message': f'用户 {username} 已启动'})
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'启动失败: {str(e)}'})

@app.route('/api/stop', methods=['POST'])
def stop_user():
    """停止用户"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': '请求数据为空'})
        
        username = data.get('username')
        if not username or username not in users:
            return jsonify({'success': False, 'message': '用户不存在'})
        
        user = users[username]
        user.stop()
        
        # 等待线程结束
        if username in user_threads:
            user_threads[username].join(timeout=5)
            del user_threads[username]
        
        return jsonify({'success': True, 'message': f'用户 {username} 已停止'})
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'停止失败: {str(e)}'})

@app.route('/api/stop_all', methods=['POST'])
def stop_all():
    """停止所有用户"""
    try:
        for username, user in users.items():
            user.stop()
        
        # 等待所有线程结束
        for thread in user_threads.values():
            thread.join(timeout=5)
        
        user_threads.clear()
        
        return jsonify({'success': True, 'message': '所有用户已停止'})
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'停止失败: {str(e)}'})

@app.route('/api/users')
def get_users():
    """获取用户列表"""
    config = load_config()
    return jsonify(config['users'])

if __name__ == '__main__':
    socketio.run(app, debug=True, host='0.0.0.0', port=5000) 
