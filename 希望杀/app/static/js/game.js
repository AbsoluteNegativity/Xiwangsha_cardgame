// 游戏大厅页面功能

// 加载房间列表
function loadRooms() {
    const roomsList = document.getElementById('rooms-list');
    roomsList.innerHTML = '<p>正在加载房间列表...</p>';
    
    fetch('/game/api/rooms')
        .then(response => response.json())
        .then(rooms => {
            if (rooms.length === 0) {
                roomsList.innerHTML = '<p>暂无房间，请创建一个新房间</p>';
                return;
            }
            
            roomsList.innerHTML = rooms.map(room => `
                <div class="room-item">
                    <div class="room-info">
                        <h3>${room.name}</h3>
                        <p>玩家: ${room.players}/${room.max_players}</p>
                    </div>
                    <button onclick="joinRoom('${room.id}')" class="btn btn-primary" 
                            ${room.players >= room.max_players ? 'disabled' : ''}>
                        ${room.players >= room.max_players ? '房间已满' : '加入房间'}
                    </button>
                </div>
            `).join('');
        })
        .catch(error => {
            roomsList.innerHTML = '<p>加载房间列表失败</p>';
            console.error('Error:', error);
        });
}

// 创建房间
function createRoom() {
    const roomName = document.getElementById('room-name').value.trim();
    if (!roomName) {
        showMessage('请输入房间名称', 'error');
        return;
    }
    
    fetch('/game/api/rooms', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ name: roomName })
    })
    .then(response => response.json())
    .then(room => {
        showMessage(`房间 "${room.name}" 创建成功！`, 'success');
        document.getElementById('room-name').value = '';
        loadRooms(); // 重新加载房间列表
    })
    .catch(error => {
        showMessage('创建房间失败', 'error');
        console.error('Error:', error);
    });
}

// 加入房间
function joinRoom(roomId) {
    const playerName = prompt('请输入您的玩家名称:');
    if (!playerName) {
        return;
    }
    
    // 跳转到游戏房间页面
    window.location.href = `/game/room/${roomId}?player=${encodeURIComponent(playerName)}`;
}

// 刷新房间列表
function refreshRooms() {
    loadRooms();
    showMessage('房间列表已刷新', 'success');
}

// 显示消息
function showMessage(message, type = 'success') {
    const messageElement = document.getElementById('message');
    messageElement.textContent = message;
    messageElement.className = `message ${type}`;
    
    // 3秒后自动隐藏消息
    setTimeout(() => {
        messageElement.textContent = '';
        messageElement.className = 'message';
    }, 3000);
}

// 页面加载完成后自动加载房间列表
document.addEventListener('DOMContentLoaded', function() {
    console.log('游戏大厅页面已加载');
    loadRooms();
    
    // 初始化Socket.IO连接以接收房间更新
    const socket = io();
    
    socket.on('connect', function() {
        console.log('已连接到服务器');
    });
    
    socket.on('rooms_updated', function(data) {
        console.log('房间列表更新:', data);
        updateRoomsList(data.rooms);
    });
});

// 更新房间列表显示
function updateRoomsList(rooms) {
    const roomsList = document.getElementById('rooms-list');
    
    if (rooms.length === 0) {
        roomsList.innerHTML = '<p>暂无房间，请创建一个新房间</p>';
        return;
    }
    
    roomsList.innerHTML = rooms.map(room => `
        <div class="room-item">
            <div class="room-info">
                <h3>${room.name}</h3>
                <p>玩家: ${room.players}/${room.max_players}</p>
            </div>
            <button onclick="joinRoom('${room.id}')" class="btn btn-primary" 
                    ${room.players >= room.max_players ? 'disabled' : ''}>
                ${room.players >= room.max_players ? '房间已满' : '加入房间'}
            </button>
        </div>
    `).join('');
}
