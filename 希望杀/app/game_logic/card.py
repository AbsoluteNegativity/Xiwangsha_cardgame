from enum import Enum
from typing import List, Dict, Any, Optional

class CardType(Enum):
    """卡牌类型枚举"""
    HOMEWORK = "作业牌"      # 作业牌
    PHYSICAL = "体术牌"      # 体术牌
    EVENT = "事件牌"         # 事件牌
    EQUIPMENT = "装备牌"     # 装备牌
    STATUS = "状态牌"        # 状态牌
    TIME = "时间牌"          # 时间牌
    MAGIC = "魔法牌"         # 魔法牌

class Card:
    """卡牌基础类"""
    
    def __init__(self, 
                 card_id: str,
                 name: str, 
                 card_type: CardType,
                 description: str,
                 cost: int = 0,
                 effect: Optional[str] = None):
        """
        初始化卡牌
        
        Args:
            card_id: 卡牌唯一ID
            name: 卡牌名称
            card_type: 卡牌类型
            description: 卡牌描述
            cost: 使用费用
            effect: 卡牌效果描述
        """
        self.card_id = card_id
        self.name = name
        self.card_type = card_type
        self.description = description
        self.cost = cost
        self.effect = effect
        
    def use(self, game_state: Dict[str, Any], player_id: str, target_id: Optional[str] = None) -> Dict[str, Any]:
        """
        使用卡牌
        
        Args:
            game_state: 游戏状态
            player_id: 使用卡牌的玩家ID
            target_id: 目标玩家ID（可选）
            
        Returns:
            更新后的游戏状态
        """
        # 基础实现，子类需要重写
        return game_state
    
    def can_use(self, game_state: Dict[str, Any], player_id: str) -> bool:
        """
        检查卡牌是否可以使用
        
        Args:
            game_state: 游戏状态
            player_id: 玩家ID
            
        Returns:
            是否可以使用
        """
        # 基础实现，子类需要重写
        return True
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'card_id': self.card_id,
            'name': self.name,
            'card_type': self.card_type.value,
            'description': self.description,
            'cost': self.cost,
            'effect': self.effect
        }

class HomeworkCard(Card):
    """作业牌类"""
    
    def __init__(self, card_id: str, name: str, description: str, damage: int = 1):
        super().__init__(card_id, name, CardType.HOMEWORK, description, cost=0)
        self.damage = damage
    
    def use(self, game_state: Dict[str, Any], player_id: str, target_id: Optional[str] = None) -> Dict[str, Any]:
        """使用作业牌对目标造成伤害"""
        if target_id and target_id in game_state['players']:
            # 减少目标玩家的san值
            game_state['players'][target_id]['san'] = max(0, game_state['players'][target_id]['san'] - self.damage)
            
            # 记录游戏日志
            if 'game_log' not in game_state:
                game_state['game_log'] = []
            game_state['game_log'].append({
                'type': 'card_used',
                'player': game_state['players'][player_id]['name'],
                'target': game_state['players'][target_id]['name'],
                'card': self.name,
                'effect': f'对 {game_state["players"][target_id]["name"]} 造成 {self.damage} 点伤害'
            })
        
        return game_state

class PhysicalCard(Card):
    """体术牌类"""
    
    def __init__(self, card_id: str, name: str, description: str, heal: int = 1):
        super().__init__(card_id, name, CardType.PHYSICAL, description, cost=0)
        self.heal = heal
    
    def use(self, game_state: Dict[str, Any], player_id: str, target_id: Optional[str] = None) -> Dict[str, Any]:
        """使用体术牌恢复san值"""
        target = target_id if target_id else player_id
        
        if target in game_state['players']:
            # 恢复目标玩家的san值
            current_san = game_state['players'][target]['san']
            max_san = game_state['players'][target]['max_san']
            game_state['players'][target]['san'] = min(max_san, current_san + self.heal)
            
            # 记录游戏日志
            if 'game_log' not in game_state:
                game_state['game_log'] = []
            game_state['game_log'].append({
                'type': 'card_used',
                'player': game_state['players'][player_id]['name'],
                'target': game_state['players'][target]['name'],
                'card': self.name,
                'effect': f'为 {game_state["players"][target]["name"]} 恢复 {self.heal} 点san值'
            })
        
        return game_state

class DodgeCard(Card):
    """驳回牌类（闪）"""
    
    def __init__(self, card_id: str, name: str, description: str):
        super().__init__(card_id, name, CardType.PHYSICAL, description, cost=0)
    
    def use(self, game_state: Dict[str, Any], player_id: str, target_id: Optional[str] = None) -> Dict[str, Any]:
        """使用驳回牌闪避攻击"""
        # 驳回牌的效果在游戏状态中处理
        if 'game_log' not in game_state:
            game_state['game_log'] = []
        game_state['game_log'].append({
            'type': 'card_used',
            'player': game_state['players'][player_id]['name'],
            'card': self.name,
            'effect': f'{game_state["players"][player_id]["name"]} 使用了 {self.name} 闪避了攻击'
        })
        
        return game_state

# ==================== 新增卡牌类 ====================

class LinearAlgebraCard(HomeworkCard):
    """线性代数牌 - 其他所有敌对玩家需要弃掉一张"一套卷子"，否则对其造成1点作业伤害"""
    
    def __init__(self, card_id: str):
        super().__init__(card_id, "线性代数", "其他所有敌对玩家需要弃掉一张'一套卷子'，否则对其造成1点作业伤害", damage=1)
    
    def use(self, game_state: Dict[str, Any], player_id: str, target_id: Optional[str] = None) -> Dict[str, Any]:
        """使用线性代数牌"""
        # 获取所有敌对玩家（除了自己）
        enemies = [pid for pid in game_state['players'].keys() if pid != player_id]
        
        for enemy_id in enemies:
            enemy_hand = game_state['players'][enemy_id]['hand_cards']
            # 检查是否有"一套卷子"
            has_yitaojuanzi = any(card['name'] == '一套卷子' for card in enemy_hand)
            
            if has_yitaojuanzi:
                # 如果有"一套卷子"，需要弃掉一张
                # 找到第一张"一套卷子"并移除
                for i, card in enumerate(enemy_hand):
                    if card['name'] == '一套卷子':
                        enemy_hand.pop(i)
                        break
                
                effect_msg = f"{game_state['players'][enemy_id]['name']} 弃掉了一张'一套卷子'"
            else:
                # 没有"一套卷子"，直接造成伤害
                game_state['players'][enemy_id]['san'] = max(0, game_state['players'][enemy_id]['san'] - 1)
                effect_msg = f"{game_state['players'][enemy_id]['name']} 没有'一套卷子'，受到1点伤害"
            
            # 记录游戏日志
            if 'game_log' not in game_state:
                game_state['game_log'] = []
            game_state['game_log'].append({
                'type': 'card_used',
                'player': game_state['players'][player_id]['name'],
                'target': game_state['players'][enemy_id]['name'],
                'card': self.name,
                'effect': effect_msg
            })
        
        return game_state

class ScratchCard(PhysicalCard):
    """挠痒牌 - 指定一名玩家，弃掉他的一张手牌"""
    
    def __init__(self, card_id: str):
        super().__init__(card_id, "挠痒", "指定一名玩家，弃掉他的一张手牌", heal=0)
    
    def use(self, game_state: Dict[str, Any], player_id: str, target_id: Optional[str] = None) -> Dict[str, Any]:
        """使用挠痒牌"""
        if target_id and target_id in game_state['players']:
            target_hand = game_state['players'][target_id]['hand_cards']
            
            if target_hand:
                # 弃掉第一张手牌（简化处理，实际游戏中应该让玩家选择）
                discarded_card = target_hand.pop(0)
                
                # 记录游戏日志
                if 'game_log' not in game_state:
                    game_state['game_log'] = []
                game_state['game_log'].append({
                    'type': 'card_used',
                    'player': game_state['players'][player_id]['name'],
                    'target': game_state['players'][target_id]['name'],
                    'card': self.name,
                    'effect': f'弃掉了 {game_state["players"][target_id]["name"]} 的一张手牌'
                })
            else:
                # 没有手牌可弃
                if 'game_log' not in game_state:
                    game_state['game_log'] = []
                game_state['game_log'].append({
                    'type': 'card_used',
                    'player': game_state['players'][player_id]['name'],
                    'target': game_state['players'][target_id]['name'],
                    'card': self.name,
                    'effect': f'{game_state["players"][target_id]["name"]} 没有手牌可弃'
                })
        
        return game_state

class SettlementCard(HomeworkCard):
    """清算时刻牌 - 指定一个目标对其造成N点作业伤害，N=本回合使用过的"一套卷子"的数量"""
    
    def __init__(self, card_id: str):
        super().__init__(card_id, "清算时刻", "指定一个目标对其造成N点作业伤害，N=本回合使用过的'一套卷子'的数量", damage=0)
    
    def use(self, game_state: Dict[str, Any], player_id: str, target_id: Optional[str] = None) -> Dict[str, Any]:
        """使用清算时刻牌"""
        if target_id and target_id in game_state['players']:
            # 计算本回合使用过的"一套卷子"数量
            yitaojuanzi_count = 0
            if 'turn_card_usage' in game_state and player_id in game_state['turn_card_usage']:
                yitaojuanzi_count = game_state['turn_card_usage'][player_id].get('一套卷子', 0)
            
            # 造成伤害
            damage = yitaojuanzi_count
            game_state['players'][target_id]['san'] = max(0, game_state['players'][target_id]['san'] - damage)
            
            # 记录游戏日志
            if 'game_log' not in game_state:
                game_state['game_log'] = []
            game_state['game_log'].append({
                'type': 'card_used',
                'player': game_state['players'][player_id]['name'],
                'target': game_state['players'][target_id]['name'],
                'card': self.name,
                'effect': f'对 {game_state["players"][target_id]["name"]} 造成 {damage} 点伤害（本回合使用了 {yitaojuanzi_count} 张一套卷子）'
            })
        
        return game_state

class TaishanCard(PhysicalCard):
    """泰山压顶牌 - 指定一个目标对其造成N点伤害，N=(当前的san值/2)"""
    
    def __init__(self, card_id: str):
        super().__init__(card_id, "泰山压顶", "指定一个目标对其造成N点伤害，N=(当前的san值/2)", heal=0)
    
    def use(self, game_state: Dict[str, Any], player_id: str, target_id: Optional[str] = None) -> Dict[str, Any]:
        """使用泰山压顶牌"""
        if target_id and target_id in game_state['players']:
            # 计算伤害：当前san值的一半
            current_san = game_state['players'][player_id]['san']
            damage = current_san // 2
            
            # 造成伤害
            game_state['players'][target_id]['san'] = max(0, game_state['players'][target_id]['san'] - damage)
            
            # 记录游戏日志
            if 'game_log' not in game_state:
                game_state['game_log'] = []
            game_state['game_log'].append({
                'type': 'card_used',
                'player': game_state['players'][player_id]['name'],
                'target': game_state['players'][target_id]['name'],
                'card': self.name,
                'effect': f'对 {game_state["players"][target_id]["name"]} 造成 {damage} 点伤害（当前san值: {current_san}）'
            })
        
        return game_state

# ==================== 预留扩展空间 ====================

class EventCard(Card):
    """事件牌类 - 预留扩展空间"""
    
    def __init__(self, card_id: str, name: str, description: str):
        super().__init__(card_id, name, CardType.EVENT, description, cost=0)
    
    def use(self, game_state: Dict[str, Any], player_id: str, target_id: Optional[str] = None) -> Dict[str, Any]:
        """使用事件牌"""
        # 预留实现
        return game_state

class EquipmentCard(Card):
    """装备牌类 - 预留扩展空间"""
    
    def __init__(self, card_id: str, name: str, description: str):
        super().__init__(card_id, name, CardType.EQUIPMENT, description, cost=0)
    
    def use(self, game_state: Dict[str, Any], player_id: str, target_id: Optional[str] = None) -> Dict[str, Any]:
        """使用装备牌"""
        # 预留实现
        return game_state

class StatusCard(Card):
    """状态牌类 - 预留扩展空间"""
    
    def __init__(self, card_id: str, name: str, description: str, duration: int = 1):
        super().__init__(card_id, name, CardType.STATUS, description, cost=0)
        self.duration = duration
    
    def use(self, game_state: Dict[str, Any], player_id: str, target_id: Optional[str] = None) -> Dict[str, Any]:
        """使用状态牌"""
        # 预留实现
        return game_state

class TimeCard(Card):
    """时间牌类 - 预留扩展空间"""
    
    def __init__(self, card_id: str, name: str, description: str):
        super().__init__(card_id, name, CardType.TIME, description, cost=0)
    
    def use(self, game_state: Dict[str, Any], player_id: str, target_id: Optional[str] = None) -> Dict[str, Any]:
        """使用时间牌"""
        # 预留实现
        return game_state

class MagicCard(Card):
    """魔法牌类 - 预留扩展空间"""
    
    def __init__(self, card_id: str, name: str, description: str, magic_type: str = "咏唱"):
        super().__init__(card_id, name, CardType.MAGIC, description, cost=0)
        self.magic_type = magic_type  # "咏唱" 或 "反制"
    
    def use(self, game_state: Dict[str, Any], player_id: str, target_id: Optional[str] = None) -> Dict[str, Any]:
        """使用魔法牌"""
        # 预留实现
        return game_state
