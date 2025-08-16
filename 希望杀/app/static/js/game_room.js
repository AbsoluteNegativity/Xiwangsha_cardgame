// 游戏房间页面功能

let socket;
let roomId;
let playerName;
let selectedCardIndex = -1;
let currentPlayerId = null;

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', function() {
    // 从URL获取房间ID和玩家名称
    const urlParams = new URLSearchParams(window.location.search);
    roomId = window.location.pathname.split('/').pop();
    playerName = urlParams.get('player') || '匿名玩家';
    
    console.log(`进入房间 ${roomId}, 玩家: ${playerName}`);
    
    // 初始化Socket.IO连接
    initSocket();
});

// 初始化Socket.IO连接
function initSocket() {
    socket = io();
    
    socket.on('connect', function() {
        console.log('已连接到服务器');
        showMessage('已连接到游戏服务器', 'success');
        
        // 保存当前玩家的Socket ID
        currentPlayerId = socket.id;
        
        // 连接成功后立即加入房间
        joinRoom();
    });
    
    socket.on('disconnect', function() {
        console.log('与服务器断开连接');
        showMessage('与服务器断开连接', 'error');
    });
    
    socket.on('message', function(data) {
        console.log('收到消息:', data);
        showMessage(data.data, 'success');
    });
    
    socket.on('player_joined', function(data) {
        console.log('玩家加入:', data);
        showMessage(`${data.player_name} 加入了房间`, 'success');
        if (data.game_state) {
            updateGameState(data.game_state);
        }
    });
    
    socket.on('player_left', function(data) {
        console.log('玩家离开:', data);
        showMessage(`${data.player_name} 离开了房间`, 'error');
        if (data.game_state) {
            updateGameState(data.game_state);
        }
    });
    
    socket.on('game_started', function(data) {
        console.log('游戏开始:', data);
        showMessage('游戏开始！', 'success');
        if (data.game_state) {
            updateGameState(data.game_state);
        }
        updateGameControls();
    });
    
    socket.on('card_used', function(data) {
        console.log('卡牌使用:', data);
        if (data.game_state) {
            updateGameState(data.game_state);
        }
    });
    
    socket.on('turn_ended', function(data) {
        console.log('回合结束:', data);
        showMessage(`轮到 ${data.next_player} 的回合`, 'success');
        if (data.game_state) {
            updateGameState(data.game_state);
        }
    });
    
    socket.on('game_over', function(data) {
        console.log('游戏结束:', data);
        showMessage(`游戏结束！获胜者: ${data.winner_name}`, 'success');
        updateGameControls();
    });
    
    socket.on('error', function(data) {
        console.log('错误:', data);
        showMessage(data.message, 'error');
    });
    
    socket.on('attack_resolved', function(data) {
        console.log('攻击结算:', data);
        showMessage('攻击已结算', 'success');
        if (data.game_state) {
            updateGameState(data.game_state);
        }
    });
}

// 加入房间
function joinRoom() {
    if (socket && socket.connected) {
        socket.emit('join_room', {
            room_id: roomId,
            player_name: playerName
        });
        showMessage(`正在加入房间 ${roomId}...`, 'success');
    }
}

// 离开房间
function leaveRoom() {
    if (socket && socket.connected) {
        socket.emit('leave_room', {
            room_id: roomId,
            player_name: playerName
        });
    }
    window.location.href = '/game';
}

// 开始游戏
function startGame() {
    if (socket && socket.connected) {
        socket.emit('start_game', {
            room_id: roomId
        });
        showMessage('正在开始游戏...', 'success');
    }
}

// 更新游戏状态
function updateGameState(gameState) {
    console.log('更新游戏状态:', gameState);
    
    // 更新玩家列表
    const playersDiv = document.getElementById('players');
    const players = Object.values(gameState.players);
    
    console.log('玩家列表:', players);
    
    if (players.length === 0) {
        playersDiv.innerHTML = '<p>暂无玩家</p>';
    } else {
        playersDiv.innerHTML = players.map(player => `
            <div class="player-info" data-player-id="${player.id}">
                <h4>${player.name}</h4>
                <p>San值: ${player.san}/${player.max_san}</p>
                <p>手牌数量: ${player.hand_cards.length}</p>
                ${gameState.current_turn === player.id ? '<span class="current-turn">当前回合</span>' : ''}
            </div>
        `).join('');
    }
    
    // 更新游戏阶段
    const statusElement = document.querySelector('.game-room p:nth-child(3)');
    if (statusElement) {
        statusElement.textContent = `状态: ${gameState.game_phase === 'waiting' ? '等待玩家加入...' : 
                                   gameState.game_phase === 'playing' ? '游戏进行中' : '游戏结束'}`;
    }
    
    // 更新手牌显示
    updateHandCards(gameState);
    
    // 更新游戏控制按钮
    updateGameControls(gameState);
    
    // 显示游戏日志
    if (gameState.game_log && gameState.game_log.length > 0) {
        const logDiv = document.getElementById('game-log');
        if (logDiv) {
            logDiv.innerHTML = gameState.game_log.map(log => `
                <div class="log-entry">${log.message || log.effect || '系统消息'}</div>
            `).join('');
        }
    }
}

// 更新游戏控制
function updateGameControls(gameState = null) {
    const startButton = document.querySelector('button[onclick="startGame()"]');
    const endTurnButton = document.querySelector('button[onclick="endTurn()"]');
    
    if (gameState) {
        const isMyTurn = gameState.current_turn === socket.id;
        const isPlaying = gameState.game_phase === 'playing';
        
        if (startButton) {
            startButton.disabled = isPlaying || Object.keys(gameState.players).length < 2;
            startButton.textContent = isPlaying ? '游戏进行中' : 
                                    Object.keys(gameState.players).length < 2 ? '需要2名玩家' : '开始游戏';
        }
        
        if (endTurnButton) {
            endTurnButton.style.display = isPlaying && isMyTurn ? 'inline-block' : 'none';
        }
    }
}

// 结束回合
function endTurn() {
    if (socket && socket.connected) {
        socket.emit('end_turn', {
            room_id: roomId
        });
        showMessage('回合结束', 'success');
    }
}

// 更新手牌显示
function updateHandCards(gameState) {
    const handCardsDiv = document.querySelector('.hand-cards');
    const cardsContainer = document.getElementById('hand-cards');
    
    // 找到当前玩家的手牌
    const currentPlayer = Object.values(gameState.players).find(player => player.id === currentPlayerId);
    
    if (gameState.game_phase === 'playing' && currentPlayer) {
        handCardsDiv.style.display = 'block';
        
        if (currentPlayer.hand_cards.length === 0) {
            cardsContainer.innerHTML = '<p>暂无手牌</p>';
        } else {
            cardsContainer.innerHTML = currentPlayer.hand_cards.map((card, index) => {
                // 检查是否可以点击这张卡牌
                let canClick = true;
                let clickAction = `selectCard(${index})`;
                
                // 检查是否在自己的回合
                const isMyTurn = gameState.current_turn === currentPlayerId;
                
                // 如果是驳回牌，检查是否在等待闪避状态
                if (card.name === '驳回') {
                    if (gameState.waiting_for_dodge && gameState.attack_target === currentPlayerId) {
                        // 检查是否可以用驳回牌闪避当前攻击
                        // 线性代数不能用驳回牌闪避
                        if (gameState.pending_attack && gameState.pending_attack.card && gameState.pending_attack.card.name === '线性代数') {
                            canClick = false;
                        } else {
                            clickAction = `useDodgeCard(${index})`;
                        }
                    } else {
                        // 不能使用驳回牌
                        canClick = false;
                    }
                }
                
                // 检查一套卷子是否可以用来抵消线性代数
                if (card.name === '一套卷子' && gameState.waiting_for_dodge && gameState.attack_target === currentPlayerId) {
                    if (gameState.pending_attack && gameState.pending_attack.card && gameState.pending_attack.card.name === '线性代数') {
                        // 一套卷子可以用来抵消线性代数
                        clickAction = `useYitaojuanziCard(${index})`;
                    }
                }
                
                // 检查一套卷子的使用限制
                if (card.name === '一套卷子') {
                    const currentPlayer = Object.values(gameState.players).find(player => player.id === currentPlayerId);
                    if (currentPlayer && gameState.turn_card_usage && gameState.turn_card_usage[currentPlayerId]) {
                        const usageCount = gameState.turn_card_usage[currentPlayerId]['一套卷子'] || 0;
                        if (usageCount >= 1) {
                            canClick = false;
                        }
                    }
                }
                
                // 检查体术牌是否只能在当前回合使用
                if (card.card_type === '体术牌' && card.name !== '驳回') {
                    if (!isMyTurn) {
                        canClick = false;
                    }
                }
                
                return `
                    <div class="card ${selectedCardIndex === index ? 'selected' : ''} ${!canClick ? 'disabled' : ''}" 
                         onclick="${canClick ? clickAction : ''}">
                        <div class="card-name">${card.name}</div>
                        <div class="card-type">${card.card_type}</div>
                        <div class="card-description">${card.description}</div>
                        ${!canClick ? '<div class="card-disabled">不可用</div>' : ''}
                    </div>
                `;
            }).join('');
            
            // 如果在等待闪避状态，添加相应的按钮
            if (gameState.waiting_for_dodge && gameState.attack_target === currentPlayerId) {
                let buttonText = '不闪避';
                let buttonAction = 'skipDodge()';
                
                // 根据攻击类型显示不同的按钮文本
                if (gameState.pending_attack && gameState.pending_attack.card) {
                    if (gameState.pending_attack.card.name === '线性代数') {
                        buttonText = '不弃掉一套卷子';
                    }
                }
                
                cardsContainer.innerHTML += `
                    <div class="no-dodge-button">
                        <button onclick="${buttonAction}" class="btn btn-secondary">${buttonText}</button>
                    </div>
                `;
            }
        }
    } else {
        handCardsDiv.style.display = 'none';
    }
}

// 选择卡牌
function selectCard(cardIndex) {
    selectedCardIndex = cardIndex;
    
    // 更新卡牌选中状态
    const cards = document.querySelectorAll('.card');
    cards.forEach((card, index) => {
        if (index === cardIndex) {
            card.classList.add('selected');
        } else {
            card.classList.remove('selected');
        }
    });
    
    // 显示目标选择界面
    showTargetSelection();
}

// 显示目标选择界面
function showTargetSelection() {
    const targetSelection = document.getElementById('target-selection');
    const targetSelect = document.getElementById('target-player');
    const cardUsage = document.querySelector('.card-usage');
    
    // 获取所有玩家作为目标（包括自己）
    const playerElements = document.querySelectorAll('.player-info');
    const targetPlayers = [];
    
    playerElements.forEach(playerElement => {
        const playerName = playerElement.querySelector('h4').textContent;
        const playerId = playerElement.getAttribute('data-player-id');
        if (playerId) {
            targetPlayers.push({ name: playerName, id: playerId });
        }
    });
    
    targetSelect.innerHTML = targetPlayers.map(player => 
        `<option value="${player.id}">${player.name}</option>`
    ).join('');
    
    targetSelection.style.display = 'block';
    cardUsage.style.display = 'block';
}

// 确认使用卡牌
function confirmUseCard() {
    if (selectedCardIndex === -1) {
        showMessage('请先选择要使用的卡牌', 'error');
        return;
    }
    
    const targetSelect = document.getElementById('target-player');
    const targetId = targetSelect.value;
    
    if (targetId) {
        useCard(selectedCardIndex, targetId);
        cancelUseCard();
    } else {
        showMessage('请选择目标玩家', 'error');
    }
}

// 取消使用卡牌
function cancelUseCard() {
    selectedCardIndex = -1;
    
    // 清除卡牌选中状态
    const cards = document.querySelectorAll('.card');
    cards.forEach(card => card.classList.remove('selected'));
    
    // 隐藏目标选择界面
    document.getElementById('target-selection').style.display = 'none';
    document.querySelector('.card-usage').style.display = 'none';
}

// 使用驳回牌
function useDodgeCard(cardIndex) {
    if (socket && socket.connected) {
        socket.emit('use_card', {
            room_id: roomId,
            card_index: cardIndex,
            target_id: null
        });
        showMessage('使用驳回牌闪避攻击', 'success');
    }
}

// 使用一套卷子抵消线性代数
function useYitaojuanziCard(cardIndex) {
    if (socket && socket.connected) {
        socket.emit('use_card', {
            room_id: roomId,
            card_index: cardIndex,
            target_id: null
        });
        showMessage('使用一套卷子抵消线性代数攻击', 'success');
    }
}

// 不闪避
function skipDodge() {
    if (socket && socket.connected) {
        socket.emit('resolve_attack', {
            room_id: roomId
        });
        showMessage('选择不闪避，攻击将结算', 'info');
    }
}

// 使用卡牌
function useCard(cardIndex, targetId = null) {
    if (socket && socket.connected) {
        socket.emit('use_card', {
            room_id: roomId,
            card_index: cardIndex,
            target_id: targetId
        });
    }
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