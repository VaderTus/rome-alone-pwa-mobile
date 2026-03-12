import tkinter as tk
from tkinter import messagebox, filedialog
import random
import datetime

# --- 数据模型 ---
class GameState:
    def __init__(self):
        self.reset()
    def reset(self):
        # 基础资源
        self.resources = {"Industry": 1, "Culture": 1, "Military": 1}
        self.regions = 1
        
        # 建筑状态 (Key 对应英文逻辑名)
        self.buildings = {
            "Sculpture": False,   # 凯旋雕塑
            "Aqueduct": False,    # 帝国引水道
            "Fortress": False,    # 军团要塞
            "GoldMine": False,    # 帝国金矿
            "Amphitheater": False # 圆形竞技场
        }
        
        # 纪念物进度 (Key 对应英文逻辑名)
        self.monuments_progress = {
            "Pantheon": 0, "Colosseum": 0, "Forum": 0,
            "Mausoleum": 0, "Arch": 0, "Market": 0
        }
        
        self.invasions_faced = 0
        self.game_over = False
        self.log = []
        # 已征服的城市计数（每种类型最多3个）
        self.cities = {"Industry": 0, "Culture": 0}
        self.init_deck()
        self.hand = []
        self.discard_pile = []

    def modify_resource(self, res_type, amount):
        # --- 被动技能触发逻辑 (新) ---
        if amount > 0:
            if res_type == "Industry" and self.buildings["GoldMine"]:
                amount += 2
                self.add_log("帝国金矿生效：工业+2")
            elif res_type == "Culture" and self.buildings["Amphitheater"]:
                amount += 2
                self.add_log("圆形竞技场生效：文化+2")
            elif res_type == "Military" and self.buildings["Fortress"]:
                amount += 2
                self.add_log("军团要塞生效：军事+2")
        
        self.resources[res_type] += amount
        self.resources[res_type] = max(0, min(9, self.resources[res_type]))

    def init_deck(self):
            # 按照新牌表构建 21 张牌的牌库
            self.deck = [
                # --- 建筑 ---
                {"name": "凯旋雕塑", "top": {"Industry": 1, "Military": 1, "Culture": 1}, "bottom": "Build_Sculpture", "cost": {"Industry": 2, "Culture": 1}, "desc": "Cost: 2 Industry, 1 Culture. Effect: 2 GP"},
                {"name": "帝国引水道", "top": {"Industry": 1, "Military": 1, "Culture": 1}, "bottom": "Build_Aqueduct", "cost": {"Industry": 2, "Culture": 1}, "desc": "Cost: 2 Industry, 1 Culture. Effect: 2 GP"},
                {"name": "军团要塞", "top": {"Military": 2, "Culture": 1}, "bottom": "Build_Fortress", "cost": {"Industry": 2, "Military": 1}, "desc": "Cost: 2 Industry, 1 Military. Effect: +2 Mil when gaining Mil"},
                {"name": "帝国金矿", "top": {"Industry": 3}, "bottom": "Build_GoldMine", "cost": {"Industry": 3}, "desc": "Cost: 3 Industry. Effect: +2 Ind when gaining Ind"},
                {"name": "圆形竞技场", "top": {"Industry": 1, "Culture": 2}, "bottom": "Build_Amphitheater", "cost": {"Industry": 2, "Culture": 1}, "desc": "Cost: 2 Industry, 1 Culture. Effect: +2 Cul when gaining Cul"},
                
                # --- 行动：征服与征收 ---
                {"name": "军团征服敕令1", "top": {"Industry": 2}, "bottom": "Conquest", "desc": "Pay Military=Regions. +1 Region"},
                {"name": "军团征服敕令2", "top": {"Industry": 1, "Culture": 1}, "bottom": "Conquest", "desc": "Pay Military=Regions. +1 Region"},
                {"name": "行省贡赋征召令1", "top": {"Industry": 2}, "bottom": "Tribute_Cul", "desc": "Gain Culture = Regions"},
                {"name": "行省贡赋征召令2", "top": {"Industry": 1, "Culture": 1}, "bottom": "Tribute_Ind", "desc": "Gain Industry = Regions"},
                
                # --- 纪念物 (奇观) ---
                {"name": "万神庙1", "top": {"Industry": 1, "Culture": 1}, "bottom": "Mon_Pantheon", "cost": {"Culture": 3}, "desc": "Cost: 3 Culture. Effect: (Needs 2)"},
                {"name": "万神庙2", "top": {"Culture": 2}, "bottom": "Mon_Pantheon", "cost": {"Industry": 1, "Culture": 2}, "desc": "Cost: 1 Industry, 2 Culture. Effect: (Needs 2)"},
                {"name": "罗马斗兽场1", "top": {"Industry": 1, "Military": 1}, "bottom": "Mon_Colosseum", "cost": {"Culture": 3}, "desc": "Cost: 3 Culture. Effect: (Needs 2)"},
                {"name": "罗马斗兽场2", "top": {"Military": 2}, "bottom": "Mon_Colosseum", "cost": {"Industry": 2, "Military": 1}, "desc": "Cost: 2 Industry, 1 Military. Effect: (Needs 2)"},
                {"name": "帝国广场1", "top": {"Industry": 1, "Culture": 1}, "bottom": "Mon_Forum", "cost": {"Culture": 3}, "desc": "Cost: 3 Culture. Effect: (Needs 2)"},
                {"name": "帝国广场2", "top": {"Culture": 2}, "bottom": "Mon_Forum", "cost": {"Industry": 3}, "desc": "Cost: 3 Industry. Effect: (Needs 2)"},
                {"name": "哈德良陵寝1", "top": {"Industry": 2}, "bottom": "Mon_Mausoleum", "cost": {"Industry": 2, "Military": 1}, "desc": "Cost: 2 Industry, 1 Military. Effect: (Needs 2)"},
                {"name": "哈德良陵寝2", "top": {"Industry": 1, "Military": 1}, "bottom": "Mon_Mausoleum", "cost": {"Culture": 3}, "desc": "Cost: 3 Culture. Effect: (Needs 2)"},
                {"name": "凯旋门1", "top": {"Culture": 1, "Military": 1}, "bottom": "Mon_Arch", "cost": {"Culture": 3}, "desc": "Cost: 3 Culture. Effect: (Needs 2)"},
                {"name": "凯旋门2", "top": {"Military": 2}, "bottom": "Mon_Arch", "cost": {"Industry": 2, "Military": 1}, "desc": "Cost: 2 Industry, 1 Military. Effect: (Needs 2)"},
                {"name": "图拉真市场1", "top": {"Industry": 2}, "bottom": "Mon_Market", "cost": {"Industry": 2, "Culture": 1}, "desc": "Cost: 2 Industry, 1 Culture. Effect: (Needs 2)"},
                {"name": "图拉真市场2", "top": {"Industry": 1, "Military": 1}, "bottom": "Mon_Market", "cost": {"Culture": 3}, "desc": "Cost: 3 Culture. Effect: (Needs 2)"}
            ]
            random.shuffle(self.deck)

    def add_log(self, msg):
        self.log.append(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] {msg}")

    def draw_cards(self):
        self.hand = []
        draw_count = min(3, len(self.deck))
        for _ in range(draw_count):
            self.hand.append(self.deck.pop())
        self.add_log(f"Drew {draw_count} cards. ({len(self.deck)} cards remaining)")
    
    def remove_card_from_deck(self, card_name):
        """从卡组中移除指定名称的所有卡牌"""
        original_count = len(self.hand)
        self.hand = [card for card in self.hand if card["name"] != card_name]
        removed_count = original_count - len(self.hand)
        if removed_count > 0:
            self.add_log(f"Removed {removed_count} copy of '{card_name}' from deck.")

    def check_invasion(self):
        if len(self.deck) == 0:
            self.invasions_faced += 1
            return True
        return False

# --- GUI 视图与控制器 ---
class RomeAloneGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Rome Alone: Rome in a Day")
        self.root.geometry("1000x700")
        self.game = GameState()
        
        self.setup_ui()
        self.start_turn()

    def setup_ui(self):
        # 顶部：资源和状态
        self.top_frame = tk.Frame(self.root, bd=2, relief=tk.GROOVE)
        self.top_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.res_labels = {}
        for res in ["Industry", "Culture", "Military"]:
            lbl = tk.Label(self.top_frame, text=f"{res}: 1/9", font=("Arial", 14, "bold"))
            lbl.pack(side=tk.LEFT, padx=15)
            self.res_labels[res] = lbl
            
        self.region_lbl = tk.Label(self.top_frame, text="Regions: 1", font=("Arial", 14, "bold"), fg="blue")
        self.region_lbl.pack(side=tk.LEFT, padx=15)
        
        self.invasion_lbl = tk.Label(self.top_frame, text="Invasions: 0/3", font=("Arial", 14, "bold"), fg="red")
        self.invasion_lbl.pack(side=tk.LEFT, padx=15)
        
        self.deck_lbl = tk.Label(self.top_frame, text="Deck: 21", font=("Arial", 14, "bold"), fg="green")
        self.deck_lbl.pack(side=tk.LEFT, padx=15)
        
        # 中部左侧：手牌区
        self.mid_frame = tk.Frame(self.root)
        self.mid_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.hand_frame = tk.LabelFrame(self.mid_frame, text="Your Hand (Choose 1 action)", font=("Arial", 12))
        self.hand_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # 中部右侧：建筑与奇观状态
        self.status_frame = tk.LabelFrame(self.mid_frame, text="Empire Status", font=("Arial", 12), width=300)
        self.status_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=10)
        
        self.bld_var = tk.StringVar()
        tk.Label(self.status_frame, textvariable=self.bld_var, justify=tk.LEFT, font=("Arial", 11)).pack(anchor="nw", padx=5, pady=5)
        
        # 底部：日志区
        self.log_frame = tk.Frame(self.root)
        self.log_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.log_box = tk.Listbox(self.log_frame, height=8, width=100)
        self.log_box.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        export_btn = tk.Button(self.log_frame, text="Export Log", command=self.export_log)
        export_btn.pack(side=tk.RIGHT, padx=5)

    def update_ui(self):
        for res, lbl in self.res_labels.items():
            lbl.config(text=f"{res}: {self.game.resources[res]}/9")
        self.region_lbl.config(text=f"Regions: {self.game.regions}")
        self.invasion_lbl.config(text=f"Invasions: {self.game.invasions_faced}/3")
        self.deck_lbl.config(text=f"Deck: {len(self.game.deck)}")
        
        # 更新状态区文本
        status_text = "--- Buildings ---\n"
        for b, built in self.game.buildings.items():
            status_text += f"{b}: {'[BUILT]' if built else '[ ]'}\n"
        status_text += "\n--- Monuments ---\n"
        for m, prog in self.game.monuments_progress.items():
            status_text += f"{m}: {prog}/2 cubes\n"
        self.bld_var.set(status_text)
        
        # 更新日志
        self.log_box.delete(0, tk.END)
        for msg in self.game.log[-8:]:
            self.log_box.insert(tk.END, msg)

    def start_turn(self):
        if self.game.game_over: return
        self.game.draw_cards()
        self.render_hand()
        self.update_ui()

    def render_hand(self):
        for widget in self.hand_frame.winfo_children():
            widget.destroy()
            
        for i, card in enumerate(self.game.hand):
            card_f = tk.Frame(self.hand_frame, bd=2, relief=tk.RAISED, width=200, height=300)
            card_f.pack(side=tk.LEFT, padx=10, pady=10, fill=tk.Y)
            card_f.pack_propagate(False)
            
            tk.Label(card_f, text=card["name"], font=("Arial", 12, "bold"), bg="lightgrey").pack(fill=tk.X)
            
            # 顶部动作
            top_text = "Gain:\n" + "\n".join([f"+{v} {k}" for k,v in card["top"].items()])
            tk.Button(card_f, text=top_text, height=4, bg="#e0f7fa", 
                      command=lambda c=card: self.play_card(c, "top")).pack(fill=tk.X, pady=5)
            
            tk.Label(card_f, text="--- OR ---").pack()
            
            # 底部动作
            tk.Button(card_f, text=f"Action:\n{card['desc']}", height=6, bg="#fff9c4", wraplength=180,
                      command=lambda c=card: self.play_card(c, "bottom")).pack(fill=tk.X, pady=5)

    def get_effective_military(self):
        mil = self.game.resources["Military"]
        return mil

    def consume_military(self, amount):
        if self.game.resources["Military"] >= amount:
            self.game.modify_resource("Military", -amount)

    def play_card(self, card, choice):
        success = True
        
        if choice == "top":
            for k, v in card["top"].items():
                self.game.modify_resource(k, v)
            self.game.add_log(f"Played {card['name']} for Top Resources.")
            
        elif choice == "bottom":
            action = card["bottom"]
            # 征服
            if action == "Conquest":
                cost = self.game.regions
                if self.get_effective_military() >= cost:
                    self.consume_military(cost)
                    # 成功征服：先增加区域
                    self.game.regions += 1

                    # 每种城市最多 3 个
                    max_each = 3

                    ind_avail = self.game.cities["Industry"] < max_each
                    cul_avail = self.game.cities["Culture"] < max_each

                    # 两种都满时仅增加区域
                    if not ind_avail and not cul_avail:
                        messagebox.showinfo("Conquest", "All city slots are full.")
                        self.game.add_log(f"Conquest: Region gained. Cities full.")
                        return
                    else:
                        # 如果只有一种可用，直接分配
                        chosen = None
                        if ind_avail and not cul_avail:
                            chosen = "Industry"
                        elif cul_avail and not ind_avail:
                            chosen = "Culture"
                        else:
                            # 两种都可用，询问玩家选择（Yes->Industry, No->Culture）
                            ans = messagebox.askyesno("Conquest", "Conquer an Industry city? (Yes=Industry, No=Culture)")
                            chosen = "Industry" if ans else "Culture"

                        # 再次检查选择的槽是否未满（以防并发或边界）
                        if chosen:
                            if self.game.cities[chosen] >= max_each:
                                # 如果选中类型已满且另一个类型可用，则改为另一个
                                other = "Culture" if chosen == "Industry" else "Industry"
                                if self.game.cities[other] < max_each:
                                    chosen = other
                                else:
                                    # 两者都满（安全兜底）
                                    messagebox.showinfo("Conquest", "All city slots are full. Region gained only.")
                                    self.game.add_log(f"Conquest: Region gained. Cities full.")
                                    chosen = None

                        if chosen:
                            # 增加城市计数并给予相应资源 +1
                            self.game.cities[chosen] += 1
                            self.game.modify_resource(chosen, 1)
                            self.game.add_log(f"Conquered a {chosen} city. {chosen} resource +1. ({self.game.cities[chosen]}/{max_each})")

                    self.game.add_log(f"Conquest Successful! Regions: {self.game.regions}")
                else:
                    messagebox.showerror("Error", "Not enough Military for Conquest!")
                    success = False
            # 征收 - 文化
            elif action == "Tribute_Cul":
                gain = self.game.regions
                self.game.modify_resource("Culture", gain)
                self.game.add_log(f"Tribute Collected: +{gain} Culture")
            # 征收 - 工业
            elif action == "Tribute_Ind":
                gain = self.game.regions
                self.game.modify_resource("Industry", gain)
                self.game.add_log(f"Tribute Collected: +{gain} Industry")
            # 建筑 - 凯旋雕塑
            elif action == "Build_Sculpture":
                if self.game.resources["Industry"] >= 2 and self.game.resources["Culture"] >= 1:
                    self.game.modify_resource("Industry", -2)
                    self.game.modify_resource("Culture", -1)
                    self.game.buildings["Sculpture"] = True
                    self.game.add_log("Built 凯旋雕塑 - +2 GP")
                    self.game.remove_card_from_deck("凯旋雕塑")
                else: success = False
            # 建筑 - 帝国引水道
            elif action == "Build_Aqueduct":
                if self.game.resources["Industry"] >= 2 and self.game.resources["Culture"] >= 1:
                    self.game.modify_resource("Industry", -2)
                    self.game.modify_resource("Culture", -1)
                    self.game.buildings["Aqueduct"] = True
                    self.game.add_log("Built 帝国引水道 - +2 GP")
                    self.game.remove_card_from_deck("帝国引水道")
                else: success = False
            # 建筑 - 军团要塞
            elif action == "Build_Fortress":
                if self.game.resources["Industry"] >= 2 and self.get_effective_military() >= 1:
                    self.game.modify_resource("Industry", -2)
                    self.consume_military(1)
                    self.game.buildings["Fortress"] = True
                    self.game.add_log("Built 军团要塞 - +2 Military when gaining Military")
                    self.game.remove_card_from_deck("军团要塞")
                else: success = False
            # 建筑 - 帝国金矿
            elif action == "Build_GoldMine":
                if self.game.resources["Industry"] >= 3:
                    self.game.modify_resource("Industry", -3)
                    self.game.buildings["GoldMine"] = True
                    self.game.add_log("Built 帝国金矿 - +2 Industry when gaining Industry")
                    self.game.remove_card_from_deck("帝国金矿")
                else: success = False
            # 建筑 - 圆形竞技场
            elif action == "Build_Amphitheater":
                if self.game.resources["Industry"] >= 2 and self.game.resources["Culture"] >= 1:
                    self.game.modify_resource("Industry", -2)
                    self.game.modify_resource("Culture", -1)
                    self.game.buildings["Amphitheater"] = True
                    self.game.add_log("Built 圆形竞技场 - +2 Culture when gaining Culture")
                    self.game.remove_card_from_deck("圆形竞技场")
                else: success = False
            # 纪念物 - 万神庙
            elif action == "Mon_Pantheon":
                if self.game.monuments_progress["Pantheon"] >= 2:
                    messagebox.showinfo("提示", "已经建成该纪念物")
                    return
                # 检查消耗资源是否足够
                if "cost" in card:
                    cost = card["cost"]
                    enough = all(self.game.resources.get(res, 0) >= amount for res, amount in cost.items())
                    if enough:
                        for res, amount in cost.items():
                            self.game.modify_resource(res, -amount)
                        self.game.monuments_progress["Pantheon"] += 1
                        self.game.add_log(f"Added cube to 万神庙: {self.game.monuments_progress['Pantheon']}/2")
                    else:
                        success = False
                else:
                    success = False
            # 纪念物 - 罗马斗兽场
            elif action == "Mon_Colosseum":
                if self.game.monuments_progress["Colosseum"] >= 2:
                    messagebox.showinfo("提示", "已经建成该纪念物")
                    return
                # 检查消耗资源是否足够
                if "cost" in card:
                    cost = card["cost"]
                    enough = all(self.game.resources.get(res, 0) >= amount for res, amount in cost.items())
                    if enough:
                        for res, amount in cost.items():
                            self.game.modify_resource(res, -amount)
                        self.game.monuments_progress["Colosseum"] += 1
                        self.game.add_log(f"Added cube to 罗马斗兽场: {self.game.monuments_progress['Colosseum']}/2")
                    else:
                        success = False
                else:
                    success = False
            # 纪念物 - 帝国广场
            elif action == "Mon_Forum":
                if self.game.monuments_progress["Forum"] >= 2:
                    messagebox.showinfo("提示", "已经建成该纪念物")
                    return
                # 检查消耗资源是否足够
                if "cost" in card:
                    cost = card["cost"]
                    enough = all(self.game.resources.get(res, 0) >= amount for res, amount in cost.items())
                    if enough:
                        for res, amount in cost.items():
                            self.game.modify_resource(res, -amount)
                        self.game.monuments_progress["Forum"] += 1
                        self.game.add_log(f"Added cube to 帝国广场: {self.game.monuments_progress['Forum']}/2")
                    else:
                        success = False
                else:
                    success = False
            # 纪念物 - 哈德良陵寝
            elif action == "Mon_Mausoleum":
                if self.game.monuments_progress["Mausoleum"] >= 2:
                    messagebox.showinfo("提示", "已经建成该纪念物")
                    return
                # 检查消耗资源是否足够
                if "cost" in card:
                    cost = card["cost"]
                    enough = all(self.game.resources.get(res, 0) >= amount for res, amount in cost.items())
                    if enough:
                        for res, amount in cost.items():
                            self.game.modify_resource(res, -amount)
                        self.game.monuments_progress["Mausoleum"] += 1
                        self.game.add_log(f"Added cube to 哈德良陵寝: {self.game.monuments_progress['Mausoleum']}/2")
                    else:
                        success = False
                else:
                    success = False
            # 纪念物 - 凯旋门
            elif action == "Mon_Arch":
                if self.game.monuments_progress["Arch"] >= 2:
                    messagebox.showinfo("提示", "已经建成该纪念物")
                    return
                # 检查消耗资源是否足够
                if "cost" in card:
                    cost = card["cost"]
                    enough = all(self.game.resources.get(res, 0) >= amount for res, amount in cost.items())
                    if enough:
                        for res, amount in cost.items():
                            self.game.modify_resource(res, -amount)
                        self.game.monuments_progress["Arch"] += 1
                        self.game.add_log(f"Added cube to 凯旋门: {self.game.monuments_progress['Arch']}/2")
                    else:
                        success = False
                else:
                    success = False
            # 纪念物 - 图拉真市场
            elif action == "Mon_Market":
                if self.game.monuments_progress["Market"] >= 2:
                    messagebox.showinfo("提示", "已经建成该纪念物")
                    return
                # 检查消耗资源是否足够
                if "cost" in card:
                    cost = card["cost"]
                    enough = all(self.game.resources.get(res, 0) >= amount for res, amount in cost.items())
                    if enough:
                        for res, amount in cost.items():
                            self.game.modify_resource(res, -amount)
                        self.game.monuments_progress["Market"] += 1
                        self.game.add_log(f"Added cube to 图拉真市场: {self.game.monuments_progress['Market']}/2")
                    else:
                        success = False
                else:
                    success = False

            if not success:
                if action not in ["Conquest"]:
                    messagebox.showerror("Error", "Not enough resources!")
                return
                
        # 丢弃手牌及处理回合结束
        self.game.discard_pile.extend(self.game.hand)
        self.game.hand = []
        
        if self.game.check_invasion():
            self.handle_invasion()
        else:
            self.start_turn()

    def handle_invasion(self):
        inv_num = self.game.invasions_faced
        self.game.add_log(f"*** BARBARIAN INVASION {inv_num} ***")
        
        if self.game.monuments_progress["Colosseum"] >= 2:
            self.game.add_log("Colosseum ignores the invasion!")
            messagebox.showinfo("Invasion", "Your Colosseum protected the Empire!")
        else:
            # 入侵强度递增：需 2, 3, 4 军事力量，否则失去 1, 1, 2 个区域
            costs = {1: (2, 1), 2: (3, 1), 3: (4, 2)}
            mil_cost, reg_loss = costs.get(inv_num, (4, 2))
            
            if self.get_effective_military() >= mil_cost:
                ans = messagebox.askyesno("Invasion", f"Pay {mil_cost} Military to stop the horde?\n(If No, lose {reg_loss} Regions)")
                if ans:
                    self.consume_military(mil_cost)
                    self.game.add_log(f"Defended invasion for {mil_cost} Military.")
                else:
                    self.lose_regions(reg_loss)
            else:
                messagebox.showwarning("Invasion", f"Not enough military! You lose {reg_loss} Regions.")
                self.lose_regions(reg_loss)
                
        if self.game.game_over:
            return
            
        if self.game.invasions_faced >= 3:
            self.calculate_score()
        else:
            self.game.deck = self.game.discard_pile
            random.shuffle(self.game.deck)
            self.game.discard_pile = []
            self.game.add_log("Discard pile shuffled into new deck.")
            self.start_turn()

    def lose_regions(self, amount):
        # 失去的单位优先从已征服的城市中选择（玩家选择类型）
        to_lose = amount
        max_each = 3

        while to_lose > 0:
            total_cities = self.game.cities.get("Industry", 0) + self.game.cities.get("Culture", 0)
            if total_cities > 0:
                # 玩家可以逐一选择要失去的城市类型
                ind_cnt = self.game.cities.get("Industry", 0)
                cul_cnt = self.game.cities.get("Culture", 0)

                if ind_cnt > 0 and cul_cnt > 0:
                    ans = messagebox.askyesno("Lose City", f"Lose an Industry city? Yes=Industry (Remaining I:{ind_cnt}, C:{cul_cnt})\nNo=Culture")
                    chosen = "Industry" if ans else "Culture"
                elif ind_cnt > 0:
                    chosen = "Industry"
                    messagebox.showinfo("Lose City", f"You must lose an Industry city. (Remaining I:{ind_cnt})")
                elif cul_cnt > 0:
                    chosen = "Culture"
                    messagebox.showinfo("Lose City", f"You must lose a Culture city. (Remaining C:{cul_cnt})")
                else:
                    chosen = None

                if chosen and self.game.cities.get(chosen, 0) > 0:
                    self.game.cities[chosen] -= 1
                    self.game.regions -= 1
                    to_lose -= 1
                    self.game.add_log(f"Lost one {chosen} city due to invasion. Regions now {self.game.regions}")
                else:
                    # 没有城市可供失去，直接失去区域
                    self.game.regions -= to_lose
                    self.game.add_log(f"Lost {to_lose} regions (no cities left). Current: {self.game.regions}")
                    to_lose = 0
            else:
                # 没有城市，直接失去剩余区域
                self.game.regions -= to_lose
                self.game.add_log(f"Lost {to_lose} regions. Current: {self.game.regions}")
                to_lose = 0

        if self.game.regions <= 0:
            self.game.game_over = True
            messagebox.showerror("Defeat", "Rome has fallen to the barbarians! You lost the game.")
        self.update_ui()

    def calculate_score(self):
        self.game.game_over = True
        score = self.game.regions # 每个区域1分
        
        if self.game.buildings["Sculpture"]: score += 2
        if self.game.buildings["Aqueduct"]: score += 2
        
        if self.game.monuments_progress["Pantheon"] >= 2: score += 4
        if self.game.monuments_progress["Colosseum"] >= 2:
            score += sum(1 for b in self.game.buildings.values() if b)
        if self.game.monuments_progress["Arch"] >= 2:
            score += self.game.regions
        if self.game.monuments_progress["Forum"] >= 2: score += 2
        if self.game.monuments_progress["Market"] >= 2: score += 2
        if self.game.monuments_progress["Mausoleum"] >= 2:
            score += min(self.game.resources.values())
            
        rank = "NERO"
        if score >= 16: rank = "AUGUSTUS"
        elif score >= 14: rank = "JULIUS CAESAR"
        elif score >= 12: rank = "MARCUS AURELIUS"
        elif score >= 10: rank = "TIBERIUS"
        
        msg = f"Game Over!\nTotal Glory Points: {score}\nYou are known as: {rank}"
        self.game.add_log(msg.replace("\n", " "))
        self.update_ui()
        messagebox.showinfo("Victory", msg)

    def export_log(self):
        file_path = filedialog.asksaveasfilename(defaultextension=".txt", title="Save Game Log")
        if file_path:
            with open(file_path, "w") as f:
                f.write("\n".join(self.game.log))
            messagebox.showinfo("Export", "Log exported successfully.")

if __name__ == "__main__":
    root = tk.Tk()
    app = RomeAloneGUI(root)
    root.mainloop()