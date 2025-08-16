from flask import Blueprint, render_template, request, jsonify
from app import socketio
from app.game_logic.game_manager import GameManager

bp = Blueprint('game', __name__, url_prefix='/game')

def get_rooms_data():
    """获取房间数据的辅助函数"""
    game_manager = GameManager()
    games = game_manager.get_all_games()
    
    rooms = []
    for room_id, game_state in games.items():
        rooms.append({
            'id': room_id,
            'name': f'房间 {room_id}',
            'players': len(game_state['players']),
            'max_players': 2,
            'status': game_state['game_phase']
        })
    
    # 如果没有房间，创建一些测试房间
    if not rooms:
        # 创建测试房间
        test_room1 = game_manager.create_game('test1')
        test_room2 = game_manager.create_game('test2')
        rooms = [
            {'id': 'test1', 'name': '测试房间1', 'players': 0, 'max_players': 2, 'status': 'waiting'},
            {'id': 'test2', 'name': '测试房间2', 'players': 0, 'max_players': 2, 'status': 'waiting'}
        ]
    
    return rooms

@bp.route('/room/<room_id>')
def game_room(room_id):
    """游戏房间页面"""
    return render_template('game_room.html', room_id=room_id)

@bp.route('/api/rooms', methods=['GET'])
def get_rooms():
    """获取房间列表"""
    rooms = get_rooms_data()
    print(f"返回房间列表: {rooms}")  # 调试信息
    return jsonify(rooms)

@bp.route('/api/rooms', methods=['POST'])
def create_room():
    """创建新房间"""
    data = request.get_json()
    room_name = data.get('name', '新房间')
    
    # 生成房间ID
    import uuid
    room_id = str(uuid.uuid4())[:8]
    
    # 创建游戏状态
    game_manager = GameManager()
    game_manager.create_game(room_id)
    
    new_room = {
        'id': room_id,
        'name': room_name,
        'players': 0,
        'max_players': 2,
        'status': 'waiting'
    }
    
    print(f"创建新房间: {new_room}")  # 调试信息
    return jsonify(new_room), 201

# SocketIO游戏事件
@socketio.on('join_room')
def handle_join_room(data):
    """加入房间"""
    room_id = data.get('room_id')
    player_name = data.get('player_name')
    player_id = request.sid  # 使用Socket.IO的session ID作为玩家ID
    
    print(f'玩家 {player_name} (ID: {player_id}) 尝试加入房间 {room_id}')
    
    # 加入Socket.IO房间
    from flask_socketio import join_room
    join_room(room_id)
    
    # 添加到游戏状态
    game_manager = GameManager()
    success = game_manager.add_player_to_game(room_id, player_id, player_name)
    
    if success:
        # 获取更新后的游戏状态
        game_state = game_manager.get_game_state(room_id)
        print(f'玩家加入成功，房间状态: {game_state}')
        
        # 向房间内所有玩家广播更新
        socketio.emit('player_joined', {
            'player_name': player_name,
            'room_id': room_id,
            'game_state': game_state
        }, room=room_id)
        
        # 向所有客户端广播房间列表更新
        updated_rooms = get_rooms_data()
        print(f"广播房间列表更新: {updated_rooms}")
        socketio.emit('rooms_updated', {
            'rooms': updated_rooms
        })
    else:
        print(f'玩家加入失败: 房间已满或加入失败')
        socketio.emit('error', {
            'message': '房间已满或加入失败'
        })

@socketio.on('leave_room')
def handle_leave_room(data):
    """离开房间"""
    room_id = data.get('room_id')
    player_name = data.get('player_name')
    player_id = request.sid
    
    print(f'玩家 {player_name} 离开房间 {room_id}')
    
    # 从游戏状态中移除
    game_manager = GameManager()
    game_manager.remove_player_from_game(room_id, player_id)
    
    # 离开Socket.IO房间
    from flask_socketio import leave_room
    leave_room(room_id)
    
    # 获取更新后的游戏状态
    game_state = game_manager.get_game_state(room_id)
    if game_state:
        socketio.emit('player_left', {
            'player_name': player_name,
            'room_id': room_id,
            'game_state': game_state
        }, room=room_id)
    else:
        socketio.emit('room_closed', {
            'room_id': room_id,
            'message': '房间已关闭'
        }, room=room_id)
    
    # 向所有客户端广播房间列表更新
    updated_rooms = get_rooms_data()
    print(f"玩家离开后广播房间列表更新: {updated_rooms}")
    socketio.emit('rooms_updated', {
        'rooms': updated_rooms
    })

@socketio.on('start_game')
def handle_start_game(data):
    """开始游戏"""
    room_id = data.get('room_id')
    player_id = request.sid
    
    game_manager = GameManager()
    success = game_manager.start_game(room_id)
    
    if success:
        game_state = game_manager.get_game_state(room_id)
        socketio.emit('game_started', {
            'room_id': room_id,
            'game_state': game_state
        }, room=room_id)
    else:
        socketio.emit('error', {
            'message': '无法开始游戏，需要2名玩家'
        })

@socketio.on('use_card')
def handle_use_card(data):
    """使用卡牌"""
    room_id = data.get('room_id')
    card_index = data.get('card_index')
    target_id = data.get('target_id')
    player_id = request.sid
    
    game_manager = GameManager()
    success = game_manager.use_card(room_id, player_id, card_index, target_id)
    
    if success:
        game_state = game_manager.get_game_state(room_id)
        socketio.emit('card_used', {
            'room_id': room_id,
            'player_id': player_id,
            'card_index': card_index,
            'target_id': target_id,
            'game_state': game_state
        }, room=room_id)
        
        # 检查游戏是否结束
        game = game_manager.get_game(room_id)
        if game:
            winner = game.check_game_over()
            if winner:
                socketio.emit('game_over', {
                    'room_id': room_id,
                    'winner_id': winner,
                    'winner_name': game.players[winner]['name']
                }, room=room_id)
    else:
        socketio.emit('error', {
            'message': '无法使用卡牌'
        })

@socketio.on('end_turn')
def handle_end_turn(data):
    """结束回合"""
    room_id = data.get('room_id')
    player_id = request.sid
    
    game_manager = GameManager()
    success = game_manager.end_turn(room_id, player_id)
    
    if success:
        game_state = game_manager.get_game_state(room_id)
        socketio.emit('turn_ended', {
            'room_id': room_id,
            'next_player': game_state['current_turn'],
            'game_state': game_state
        }, room=room_id)
    else:
        socketio.emit('error', {
            'message': '无法结束回合'
        })

@socketio.on('draw_card')
def handle_draw_card(data):
    """抽牌"""
    room_id = data.get('room_id')
    player_id = request.sid
    
    game_manager = GameManager()
    card = game_manager.draw_card(room_id, player_id)
    
    if card:
        game_state = game_manager.get_game_state(room_id)
        socketio.emit('card_drawn', {
            'room_id': room_id,
            'player_id': player_id,
            'card': card.to_dict(),
            'game_state': game_state
        }, room=room_id)
    else:
        socketio.emit('error', {
            'message': '无法抽牌'
        })

@socketio.on('resolve_attack')
def handle_resolve_attack(data):
    """结算攻击"""
    room_id = data.get('room_id')
    
    game_manager = GameManager()
    success = game_manager.resolve_attack(room_id)
    
    if success:
        game_state = game_manager.get_game_state(room_id)
        socketio.emit('attack_resolved', {
            'room_id': room_id,
            'game_state': game_state
        }, room=room_id)
        
        # 检查游戏是否结束
        game = game_manager.get_game(room_id)
        if game:
            winner = game.check_game_over()
            if winner:
                socketio.emit('game_over', {
                    'room_id': room_id,
                    'winner_id': winner,
                    'winner_name': game.players[winner]['name']
                }, room=room_id)
    else:
        socketio.emit('error', {
            'message': '无法结算攻击'
        })

@socketio.on('get_game_state')
def handle_get_game_state(data):
    """获取游戏状态"""
    room_id = data.get('room_id')
    
    game_manager = GameManager()
    game_state = game_manager.get_game_state(room_id)
    
    if game_state:
        socketio.emit('game_state_update', {
            'room_id': room_id,
            'game_state': game_state
        })
    else:
        socketio.emit('error', {
            'message': '游戏不存在'
        })
