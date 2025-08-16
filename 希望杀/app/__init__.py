from flask import Flask
from flask_socketio import SocketIO
from flask_cors import CORS
import os

# 创建SocketIO实例
socketio = SocketIO()

def create_app():
    """创建并配置Flask应用"""
    app = Flask(__name__, 
                template_folder='../templates',
                static_folder='static')
    
    # 配置应用
    app.config['SECRET_KEY'] = 'your-secret-key-here'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///xiwangsha.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # 启用CORS跨域支持
    CORS(app)
    
    # 初始化SocketIO
    socketio.init_app(app, cors_allowed_origins="*")
    
    # 注册蓝图
    from app.routes import main, game
    app.register_blueprint(main.bp)
    app.register_blueprint(game.bp)
    
    return app
