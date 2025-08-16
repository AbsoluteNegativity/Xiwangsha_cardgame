from typing import Dict, Optional
from .game_state import GameState
import uuid

class GameManager:
    """游戏管理器 - 单例模式"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(GameManager, cls).__new__(cls)
            cls._instance.games = {}  # 存储所有游戏房间
        return cls._instance
    
    def create_game(self, room_id: str) -> GameState:
        """创建新游戏"""
        if room_id in self.games:
            return self.games[room_id]
            
        game_state = GameState(room_id)
        self.games[room_id] = game_state
        return game_state
    
    def get_game(self, room_id: str) -> Optional[GameState]:
        """获取游戏状态"""
        return self.games.get(room_id)
    
    def remove_game(self, room_id: str) -> bool:
        """移除游戏"""
        if room_id in self.games:
            del self.games[room_id]
            return True
        return False
    
    def add_player_to_game(self, room_id: str, player_id: str, player_name: str) -> bool:
        """添加玩家到游戏"""
        game = self.get_game(room_id)
        if not game:
            game = self.create_game(room_id)
        
        return game.add_player(player_id, player_name)
    
    def remove_player_from_game(self, room_id: str, player_id: str) -> bool:
        """从游戏中移除玩家"""
        game = self.get_game(room_id)
        if not game:
            return False
        
        success = game.remove_player(player_id)
        
        # 如果没有玩家了，删除游戏
        if not game.players:
            self.remove_game(room_id)
        
        return success
    
    def start_game(self, room_id: str) -> bool:
        """开始游戏"""
        game = self.get_game(room_id)
        if not game:
            return False
        
        return game.start_game()
    
    def use_card(self, room_id: str, player_id: str, card_index: int, target_id: Optional[str] = None) -> bool:
        """使用卡牌"""
        game = self.get_game(room_id)
        if not game:
            return False
        
        return game.use_card(player_id, card_index, target_id)
    
    def end_turn(self, room_id: str, player_id: str) -> bool:
        """结束回合"""
        game = self.get_game(room_id)
        if not game:
            return False
        
        return game.end_turn(player_id)
    
    def draw_card(self, room_id: str, player_id: str):
        """抽牌"""
        game = self.get_game(room_id)
        if not game:
            return None
        
        return game.draw_card(player_id)
    
    def resolve_attack(self, room_id: str) -> bool:
        """结算攻击"""
        game = self.get_game(room_id)
        if not game:
            return False
        
        return game.resolve_attack()
    
    def get_game_state(self, room_id: str) -> Optional[dict]:
        """获取游戏状态"""
        game = self.get_game(room_id)
        if not game:
            return None
        
        return game.to_dict()
    
    def get_all_games(self) -> Dict[str, dict]:
        """获取所有游戏状态"""
        return {
            room_id: game.to_dict() 
            for room_id, game in self.games.items()
        }
