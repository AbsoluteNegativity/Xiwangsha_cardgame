from app import create_app, socketio

app = create_app()

if __name__ == '__main__':
    print("启动希望杀游戏服务器...")
    print("访问地址: http://localhost:5000")
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
