from typing import Dict, List, Any, Optional
from .card import Card, CardType
import random
import uuid

class GameState:
    """游戏状态管理器"""
    
    def __init__(self, room_id: str):
        self.room_id = room_id
        self.players = {}  # 玩家信息
        self.current_turn = None  # 当前回合玩家
        self.game_phase = "waiting"  # 游戏阶段: waiting, playing, finished
        self.deck = []  # 牌堆
        self.discard_pile = []  # 弃牌堆
        self.game_log = []  # 游戏日志
        self.pending_attack = None  # 待处理的攻击
        self.attack_target = None  # 攻击目标
        self.waiting_for_dodge = False  # 是否等待闪避
        self.turn_card_usage = {}  # 回合使用记录：{player_id: {card_name: count}}
        
    def add_player(self, player_id: str, player_name: str) -> bool:
        """添加玩家到游戏"""
        if len(self.players) >= 2:  # 限制2人游戏
            return False
            
        self.players[player_id] = {
            'id': player_id,
            'name': player_name,
            'san': 4,  # 初始san值
            'max_san': 4,  # 最大san值
            'hand_cards': [],  # 手牌
            'equipment': [],  # 装备
            'status': [],  # 状态效果
            'homework_used_this_turn': False  # 本回合是否已使用作业牌
        }
        
        # 初始化回合使用记录
        self.turn_card_usage[player_id] = {}
        
        # 记录日志
        self.game_log.append({
            'type': 'player_joined',
            'player': player_name,
            'message': f'{player_name} 加入了游戏'
        })
        
        return True
    
    def remove_player(self, player_id: str) -> bool:
        """移除玩家"""
        if player_id in self.players:
            player_name = self.players[player_id]['name']
            del self.players[player_id]
            
            # 清理回合使用记录
            if player_id in self.turn_card_usage:
                del self.turn_card_usage[player_id]
            
            self.game_log.append({
                'type': 'player_left',
                'player': player_name,
                'message': f'{player_name} 离开了游戏'
            })
            
            # 如果游戏正在进行，结束游戏
            if self.game_phase == "playing":
                self.end_game()
            
            return True
        return False
    
    def start_game(self) -> bool:
        """开始游戏"""
        if len(self.players) != 2:
            return False
            
        # 清理所有玩家的手牌和状态
        for player_id in self.players:
            self.players[player_id]['hand_cards'] = []
            self.players[player_id]['homework_used_this_turn'] = False
            self.players[player_id]['san'] = 4  # 重置san值
            self.turn_card_usage[player_id] = {}  # 清理回合使用记录
            
        # 清理游戏状态
        self.deck = []
        self.discard_pile = []
        self.game_log = []
        self.pending_attack = None
        self.attack_target = None
        self.waiting_for_dodge = False
            
        self.game_phase = "playing"
        self.initialize_deck()
        self.deal_initial_cards()
        self.current_turn = list(self.players.keys())[0]  # 第一个玩家开始
        
        # 第一个玩家在游戏开始时抽两张牌
        self.draw_card(self.current_turn)
        self.draw_card(self.current_turn)
        
        self.game_log.append({
            'type': 'game_started',
            'message': '游戏开始！'
        })
        
        return True
    
    def initialize_deck(self):
        """初始化牌堆"""
        self.deck = []
        
        # 添加作业牌
        homework_cards = [
            ("一套卷子", "对目标造成1点伤害"),
            ("线性代数", "其他所有敌对玩家需要弃掉一张'一套卷子'，否则对其造成1点作业伤害"),
            ("清算时刻", "指定一个目标对其造成N点作业伤害，N=本回合使用过的'一套卷子'的数量"),
        ]
        
        for name, desc in homework_cards:
            if name == "一套卷子":
                count = 3  # 一套卷子3张
            elif name == "线性代数":
                count = 2  # 线性代数2张
            elif name == "清算时刻":
                count = 1  # 清算时刻1张
            else:
                count = 2  # 默认2张
            
            for _ in range(count):
                if name == "一套卷子":
                    from .card import HomeworkCard
                    card = HomeworkCard(
                        card_id=str(uuid.uuid4()),
                        name=name,
                        description=desc
                    )
                elif name == "线性代数":
                    from .card import LinearAlgebraCard
                    card = LinearAlgebraCard(card_id=str(uuid.uuid4()))
                elif name == "清算时刻":
                    from .card import SettlementCard
                    card = SettlementCard(card_id=str(uuid.uuid4()))
                else:
                    from .card import HomeworkCard
                    card = HomeworkCard(
                        card_id=str(uuid.uuid4()),
                        name=name,
                        description=desc
                    )
                self.deck.append(card)
        
        # 添加体术牌
        physical_cards = [
            ("运动", "恢复1点san值"),
            ("休息", "恢复1点san值"),
            ("冥想", "恢复1点san值"),
            ("挠痒", "指定一名玩家，弃掉他的一张手牌"),
            ("泰山压顶", "指定一个目标对其造成N点伤害，N=(当前的san值/2)"),
        ]
        
        # 添加驳回牌
        dodge_cards = [
            ("驳回", "闪避一次攻击"),
        ]
        
        for name, desc in physical_cards:
            if name in ["运动", "休息", "冥想"]:
                count = 2  # 基础体术牌2张
            elif name == "挠痒":
                count = 1  # 挠痒1张
            elif name == "泰山压顶":
                count = 1  # 泰山压顶1张
            else:
                count = 2  # 默认2张
            
            for _ in range(count):
                if name in ["运动", "休息", "冥想"]:
                    from .card import PhysicalCard
                    card = PhysicalCard(
                        card_id=str(uuid.uuid4()),
                        name=name,
                        description=desc
                    )
                elif name == "挠痒":
                    from .card import ScratchCard
                    card = ScratchCard(card_id=str(uuid.uuid4()))
                elif name == "泰山压顶":
                    from .card import TaishanCard
                    card = TaishanCard(card_id=str(uuid.uuid4()))
                else:
                    from .card import PhysicalCard
                    card = PhysicalCard(
                        card_id=str(uuid.uuid4()),
                        name=name,
                        description=desc
                    )
                self.deck.append(card)
        
        # 添加驳回牌
        for name, desc in dodge_cards:
            for _ in range(4):  # 驳回牌4张
                from .card import DodgeCard
                card = DodgeCard(
                    card_id=str(uuid.uuid4()),
                    name=name,
                    description=desc
                )
                self.deck.append(card)
        
        # 洗牌
        random.shuffle(self.deck)
    
    def deal_initial_cards(self):
        """发初始手牌"""
        for player_id in self.players:
            # 每个玩家发4张牌
            for _ in range(4):
                if self.deck:
                    card = self.deck.pop()
                    print(f"DEBUG: 发牌给 {self.players[player_id]['name']}, 卡牌类型: {type(card)}, 卡牌名称: {card.name}")
                    self.players[player_id]['hand_cards'].append(card)
    
    def draw_card(self, player_id: str) -> Optional[Card]:
        """玩家抽牌"""
        if player_id not in self.players:
            return None
            
        if not self.deck:
            # 如果牌堆空了，重新洗牌
            self.reshuffle_discard_pile()
            
        if self.deck:
            card = self.deck.pop()
            print(f"DEBUG: {self.players[player_id]['name']} 抽牌, 卡牌类型: {type(card)}, 卡牌名称: {card.name}")
            self.players[player_id]['hand_cards'].append(card)
            
            self.game_log.append({
                'type': 'card_drawn',
                'player': self.players[player_id]['name'],
                'message': f'{self.players[player_id]["name"]} 抽了一张牌'
            })
            
            return card
        return None
    
    def reshuffle_discard_pile(self):
        """重新洗牌弃牌堆"""
        if self.discard_pile:
            # 直接使用弃牌堆的卡牌对象，而不是复制
            self.deck = self.discard_pile
            self.discard_pile = []
            random.shuffle(self.deck)
            
            self.game_log.append({
                'type': 'deck_reshuffled',
                'message': '牌堆重新洗牌'
            })
    
    def use_card(self, player_id: str, card_index: int, target_id: Optional[str] = None) -> bool:
        """使用卡牌"""
        if player_id not in self.players:
            return False
            
        player = self.players[player_id]
        if card_index >= len(player['hand_cards']):
            return False
            
        card = player['hand_cards'][card_index]
        
        # 确保card是卡牌对象而不是字典
        if isinstance(card, dict):
            print(f"错误：手牌中存储的是字典而不是卡牌对象")
            return False
        
        # 记录卡牌使用
        self.record_card_usage(player_id, card.name)
        
        # 检查作业牌使用限制
        if card.card_type == CardType.HOMEWORK:
            if card.name == "一套卷子":
                # 一套卷子每回合只能使用一次
                if self.get_card_usage_count(player_id, "一套卷子") > 1:
                    print(f"错误：{player['name']} 本回合已经使用过一套卷子")
                    return False
            elif card.name == "线性代数":
                # 线性代数不受使用次数限制
                pass
            elif card.name == "清算时刻":
                # 清算时刻不受使用次数限制
                pass
            else:
                # 其他作业牌不受限制
                pass
        
        # 处理驳回牌（闪）
        if card.name == "驳回":
            if not self.waiting_for_dodge or player_id != self.attack_target:
                print(f"错误：{player['name']} 不能在此刻使用驳回牌")
                return False
            
            # 检查是否可以用驳回牌闪避当前攻击
            if self.pending_attack and self.pending_attack['card'].name == "线性代数":
                print(f"错误：{player['name']} 不能用驳回牌闪避线性代数")
                return False
            
            # 使用驳回牌闪避攻击
            self.waiting_for_dodge = False
            self.pending_attack = None
            self.attack_target = None
            
            # 移除手牌，加入弃牌堆
            player['hand_cards'].pop(card_index)
            self.discard_pile.append(card)
            
            # 添加游戏日志
            self.game_log.append({
                'type': 'card_used',
                'player': player['name'],
                'card': card.name,
                'message': f'{player["name"]} 使用了 {card.name} 闪避了攻击'
            })
            
            return True
        
        # 处理一套卷子抵消线性代数
        if card.name == "一套卷子" and self.waiting_for_dodge and player_id == self.attack_target:
            if self.pending_attack and self.pending_attack['card'].name == "线性代数":
                # 使用一套卷子抵消线性代数
                self.waiting_for_dodge = False
                self.pending_attack = None
                self.attack_target = None
                
                # 移除手牌，加入弃牌堆
                player['hand_cards'].pop(card_index)
                self.discard_pile.append(card)
                
                # 添加游戏日志
                self.game_log.append({
                    'type': 'card_used',
                    'player': player['name'],
                    'card': card.name,
                    'message': f'{player["name"]} 使用了一套卷子抵消了线性代数的攻击'
                })
                
                return True
        
        # 检查是否在自己的回合（对于主动使用的卡牌）
        if self.current_turn != player_id:
            print(f"错误：{player['name']} 不是当前回合玩家，不能使用卡牌")
            return False
        
        # 处理特殊卡牌（需要等待闪避的作业牌）
        if card.name in ["线性代数", "清算时刻"]:
            if target_id and target_id in self.players:
                # 设置待处理的攻击
                self.pending_attack = {
                    'attacker': player_id,
                    'target': target_id,
                    'card': card
                }
                self.attack_target = target_id
                self.waiting_for_dodge = True
                
                # 移除手牌，加入弃牌堆
                player['hand_cards'].pop(card_index)
                self.discard_pile.append(card)
                
                # 添加游戏日志
                target_name = self.players[target_id]['name']
                self.game_log.append({
                    'type': 'card_used',
                    'player': player['name'],
                    'card': card.name,
                    'target': target_name,
                    'message': f'{player["name"]} 对 {target_name} 使用了 {card.name}，等待闪避'
                })
                
                return True
        
        # 处理立即生效的特殊卡牌
        if card.name in ["泰山压顶"]:
            if target_id and target_id in self.players:
                # 设置待处理的攻击
                self.pending_attack = {
                    'attacker': player_id,
                    'target': target_id,
                    'card': card
                }
                self.attack_target = target_id
                self.waiting_for_dodge = True
                
                # 移除手牌，加入弃牌堆
                player['hand_cards'].pop(card_index)
                self.discard_pile.append(card)
                
                # 添加游戏日志
                target_name = self.players[target_id]['name']
                self.game_log.append({
                    'type': 'card_used',
                    'player': player['name'],
                    'card': card.name,
                    'target': target_name,
                    'message': f'{player["name"]} 对 {target_name} 使用了 {card.name}，等待闪避'
                })
                
                return True
        
        # 处理普通作业牌攻击
        if card.card_type == CardType.HOMEWORK:
            if target_id and target_id in self.players:
                # 设置待处理的攻击
                self.pending_attack = {
                    'attacker': player_id,
                    'target': target_id,
                    'card': card
                }
                self.attack_target = target_id
                self.waiting_for_dodge = True
                
                # 移除手牌，加入弃牌堆
                player['hand_cards'].pop(card_index)
                self.discard_pile.append(card)
                
                # 添加游戏日志
                target_name = self.players[target_id]['name']
                self.game_log.append({
                    'type': 'card_used',
                    'player': player['name'],
                    'card': card.name,
                    'target': target_name,
                    'message': f'{player["name"]} 对 {target_name} 使用了 {card.name}，等待闪避'
                })
                
                return True
        
        # 处理普通体术牌（恢复）
        if card.card_type == CardType.PHYSICAL and card.name not in ["驳回", "挠痒", "泰山压顶"]:
            if target_id and target_id in self.players:
                # 体术牌恢复san值
                target = target_id if target_id else player_id
                current_san = self.players[target]['san']
                max_san = self.players[target]['max_san']
                self.players[target]['san'] = min(max_san, current_san + 1)
                print(f"体术牌效果：{player['name']} 为 {self.players[target]['name']} 恢复1点san值，当前san值：{self.players[target]['san']}")
            
            # 移除手牌，加入弃牌堆
            player['hand_cards'].pop(card_index)
            self.discard_pile.append(card)
            
            # 添加游戏日志
            target_name = self.players[target_id]['name'] if target_id and target_id in self.players else '自己'
            self.game_log.append({
                'type': 'card_used',
                'player': player['name'],
                'card': card.name,
                'target': target_name,
                'message': f'{player["name"]} 使用了 {card.name}'
            })
            
            return True
        
        # 处理挠痒卡牌
        if card.name == "挠痒":
            if target_id and target_id in self.players:
                # 挠痒效果：直接弃掉目标玩家的第一张手牌
                target_hand = self.players[target_id]['hand_cards']
                if target_hand:
                    discarded_card = target_hand.pop(0)
                    effect_msg = f'弃掉了 {self.players[target_id]["name"]} 的一张手牌'
                else:
                    effect_msg = f'{self.players[target_id]["name"]} 没有手牌可弃'
                
                # 移除手牌，加入弃牌堆
                player['hand_cards'].pop(card_index)
                self.discard_pile.append(card)
                
                # 添加游戏日志
                target_name = self.players[target_id]['name']
                self.game_log.append({
                    'type': 'card_used',
                    'player': player['name'],
                    'target': target_name,
                    'card': card.name,
                    'effect': effect_msg,
                    'message': f'{player["name"]} 对 {target_name} 使用了 {card.name}，{effect_msg}'
                })
                
                return True
        
        return False
    
    def resolve_attack(self) -> bool:
        """结算攻击（当没有闪避时）"""
        if not self.pending_attack:
            return False
        
        attacker_id = self.pending_attack['attacker']
        target_id = self.pending_attack['target']
        card = self.pending_attack['card']
        
        # 处理线性代数卡牌
        if card.name == "线性代数":
            # 获取所有敌对玩家（除了攻击者）
            enemies = [pid for pid in self.players.keys() if pid != attacker_id]
            
            for enemy_id in enemies:
                enemy_hand = self.players[enemy_id]['hand_cards']
                # 检查是否有"一套卷子"
                has_yitaojuanzi = any(card_obj.name == '一套卷子' for card_obj in enemy_hand)
                
                if has_yitaojuanzi:
                    # 如果有"一套卷子"，需要弃掉一张
                    # 找到第一张"一套卷子"并移除
                    for i, card_obj in enumerate(enemy_hand):
                        if card_obj.name == '一套卷子':
                            enemy_hand.pop(i)
                            break
                    
                    effect_msg = f"{self.players[enemy_id]['name']} 弃掉了一张'一套卷子'"
                else:
                    # 没有"一套卷子"，直接造成伤害
                    old_san = self.players[enemy_id]['san']
                    self.players[enemy_id]['san'] = max(0, self.players[enemy_id]['san'] - 1)
                    new_san = self.players[enemy_id]['san']
                    print(f"DEBUG: 线性代数对 {self.players[enemy_id]['name']} 造成伤害: {old_san} -> {new_san}")
                    effect_msg = f"{self.players[enemy_id]['name']} 没有'一套卷子'，受到1点伤害，san值从{old_san}降至{new_san}"
                
                # 记录游戏日志
                self.game_log.append({
                    'type': 'attack_resolved',
                    'player': self.players[attacker_id]['name'],
                    'target': self.players[enemy_id]['name'],
                    'card': card.name,
                    'effect': effect_msg,
                    'message': effect_msg
                })
        # 处理清算时刻卡牌
        elif card.name == "清算时刻":
            # 计算本回合使用过的"一套卷子"数量
            yitaojuanzi_count = self.get_card_usage_count(attacker_id, '一套卷子')
            
            # 造成伤害
            damage = yitaojuanzi_count
            self.players[target_id]['san'] = max(0, self.players[target_id]['san'] - damage)
            
            # 记录游戏日志
            self.game_log.append({
                'type': 'card_used',
                'player': self.players[attacker_id]['name'],
                'target': self.players[target_id]['name'],
                'card': card.name,
                'effect': f'对 {self.players[target_id]["name"]} 造成 {damage} 点伤害（本回合使用了 {yitaojuanzi_count} 张一套卷子）'
            })
        # 处理泰山压顶卡牌
        elif card.name == "泰山压顶":
            # 泰山压顶效果：造成N点伤害，N=(攻击者当前san值/2)
            attacker_san = self.players[attacker_id]['san']
            damage = max(1, attacker_san // 2)  # 至少造成1点伤害
            self.players[target_id]['san'] = max(0, self.players[target_id]['san'] - damage)
            
            # 记录游戏日志
            self.game_log.append({
                'type': 'attack_resolved',
                'player': self.players[attacker_id]['name'],
                'target': self.players[target_id]['name'],
                'card': card.name,
                'message': f'{self.players[attacker_id]["name"]} 的 {card.name} 对 {self.players[target_id]["name"]} 造成了 {damage} 点伤害（基于攻击者san值 {attacker_san}）'
            })
        else:
            # 普通攻击牌造成1点伤害
            self.players[target_id]['san'] = max(0, self.players[target_id]['san'] - 1)
            print(f"攻击结算：{self.players[attacker_id]['name']} 对 {self.players[target_id]['name']} 造成1点伤害，剩余san值：{self.players[target_id]['san']}")
            
            # 添加游戏日志
            self.game_log.append({
                'type': 'attack_resolved',
                'player': self.players[attacker_id]['name'],
                'target': self.players[target_id]['name'],
                'card': card.name,
                'message': f'{self.players[attacker_id]["name"]} 的 {card.name} 对 {self.players[target_id]["name"]} 造成了1点伤害'
            })
        
        # 清除待处理的攻击
        self.pending_attack = None
        self.attack_target = None
        self.waiting_for_dodge = False
        
        # 检查游戏是否结束
        self.check_game_over()
        
        return True
    
    def end_turn(self, player_id: str):
        """结束回合"""
        if self.current_turn != player_id:
            return False
        
        # 如果有待处理的攻击，结算攻击
        if self.pending_attack:
            self.resolve_attack()
            
        # 重置当前玩家的作业牌使用标记
        self.players[player_id]['homework_used_this_turn'] = False
        
        # 清除当前玩家的回合使用记录
        self.clear_turn_usage(player_id)
            
        # 切换到下一个玩家
        player_ids = list(self.players.keys())
        current_index = player_ids.index(player_id)
        next_index = (current_index + 1) % len(player_ids)
        self.current_turn = player_ids[next_index]
        
        # 重置下一个玩家的作业牌使用标记
        self.players[self.current_turn]['homework_used_this_turn'] = False
        
        # 新回合开始，抽两张牌
        print(f"DEBUG: {self.players[self.current_turn]['name']} 开始抽牌，当前手牌数量: {len(self.players[self.current_turn]['hand_cards'])}")
        self.draw_card(self.current_turn)
        print(f"DEBUG: 抽第一张牌后，手牌数量: {len(self.players[self.current_turn]['hand_cards'])}")
        self.draw_card(self.current_turn)
        print(f"DEBUG: 抽第二张牌后，手牌数量: {len(self.players[self.current_turn]['hand_cards'])}")
        
        self.game_log.append({
            'type': 'turn_ended',
            'player': self.players[player_id]['name'],
            'next_player': self.players[self.current_turn]['name'],
            'message': f'{self.players[player_id]["name"]} 的回合结束，轮到 {self.players[self.current_turn]["name"]}'
        })
        
        return True
    
    def check_game_over(self) -> Optional[str]:
        """检查游戏是否结束，返回获胜者ID"""
        alive_players = []
        for player_id, player in self.players.items():
            if player['san'] > 0:
                alive_players.append(player_id)
        
        if len(alive_players) <= 1:
            self.game_phase = "finished"
            winner_id = alive_players[0] if alive_players else None
            
            # 添加游戏结束日志
            if winner_id:
                winner_name = self.players[winner_id]['name']
                self.game_log.append({
                    'type': 'game_over',
                    'winner': winner_name,
                    'message': f'游戏结束！{winner_name} 获胜！'
                })
            else:
                self.game_log.append({
                    'type': 'game_over',
                    'message': '游戏结束！平局！'
                })
            
            return winner_id
        
        return None
    
    def end_game(self):
        """结束游戏"""
        self.game_phase = "finished"
        self.game_log.append({
            'type': 'game_ended',
            'message': '游戏结束'
        })
    
    def record_card_usage(self, player_id: str, card_name: str):
        """记录卡牌使用"""
        if player_id not in self.turn_card_usage:
            self.turn_card_usage[player_id] = {}
        
        if card_name not in self.turn_card_usage[player_id]:
            self.turn_card_usage[player_id][card_name] = 0
        
        self.turn_card_usage[player_id][card_name] += 1
    
    def get_card_usage_count(self, player_id: str, card_name: str) -> int:
        """获取指定卡牌的使用次数"""
        if player_id in self.turn_card_usage and card_name in self.turn_card_usage[player_id]:
            return self.turn_card_usage[player_id][card_name]
        return 0
    
    def clear_turn_usage(self, player_id: str):
        """清除指定玩家的回合使用记录"""
        if player_id in self.turn_card_usage:
            self.turn_card_usage[player_id] = {}
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        # 处理pending_attack的序列化
        pending_attack_dict = None
        if self.pending_attack:
            pending_attack_dict = {
                'attacker': self.pending_attack['attacker'],
                'target': self.pending_attack['target'],
                'card': self.pending_attack['card'].to_dict() if hasattr(self.pending_attack['card'], 'to_dict') else self.pending_attack['card'],
                'type': self.pending_attack.get('type')
            }
        
        return {
            'room_id': self.room_id,
            'players': {
                pid: {
                    'id': p['id'],
                    'name': p['name'],
                    'san': p['san'],
                    'max_san': p['max_san'],
                    'hand_cards': [card.to_dict() for card in p['hand_cards']],
                    'equipment': p['equipment'],
                    'status': p['status'],
                    'homework_used_this_turn': p['homework_used_this_turn']
                }
                for pid, p in self.players.items()
            },
            'current_turn': self.current_turn,
            'game_phase': self.game_phase,
            'deck_count': len(self.deck),
            'discard_count': len(self.discard_pile),
            'game_log': self.game_log[-10:],  # 只返回最近10条日志
            'waiting_for_dodge': self.waiting_for_dodge,
            'attack_target': self.attack_target,
            'turn_card_usage': self.turn_card_usage,  # 添加回合使用记录
            'pending_attack': pending_attack_dict  # 添加待处理攻击信息
        }
