from flask import Blueprint, render_template, request, jsonify
from app import socketio

bp = Blueprint('main', __name__)

@bp.route('/')
def index():
    """首页"""
    return render_template('index.html')

@bp.route('/game')
def game():
    """游戏页面"""
    return render_template('game.html')

@bp.route('/api/status')
def status():
    """API状态检查"""
    return jsonify({
        'status': 'ok',
        'message': '希望杀游戏服务器运行正常'
    })

# SocketIO事件处理
@socketio.on('connect')
def handle_connect():
    """客户端连接事件"""
    print('客户端已连接')
    socketio.emit('message', {'data': '欢迎来到希望杀！'})

@socketio.on('disconnect')
def handle_disconnect():
    """客户端断开连接事件"""
    print('客户端已断开连接')
