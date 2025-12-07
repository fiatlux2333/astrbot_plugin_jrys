import json
import os
import random
import math
from datetime import datetime, date
from typing import Dict, List, Any
from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star, register
from astrbot.api import logger

@register("jrys_fix", "Miku", "今日运势签到插件", "1.0.0")
class JrysFix(Star):
    def __init__(self, context: Context):
        super().__init__(context)
        self.data_file = "jrys_data.json"
        self.user_data = self.load_data()
        
        # 默认配置
        self.config = {
            "img_url": "https://api.example.com/random-image",
            "sign_exp_min": 1,
            "sign_exp_max": 100,
            "sign_coin_min": 1,
            "sign_coin_max": 100,
            "currency": "coin"
        }
        
        # 等级信息
        self.level_info = [
            {"level": 0, "levelExp": 0, "levelName": "不知名杂鱼", "levelColor": "#838383"},
            {"level": 1, "levelExp": 500, "levelName": "荒野漫步者", "levelColor": "#838383"},
            {"level": 2, "levelExp": 1000, "levelName": "拓荒者", "levelColor": "#838383"},
            {"level": 3, "levelExp": 1500, "levelName": "冒险家", "levelColor": "#838383"},
            {"level": 4, "levelExp": 2000, "levelName": "传说的冒险家", "levelColor": "#000000"},
            {"level": 5, "levelExp": 3000, "levelName": "隐秘收藏家", "levelColor": "#000000"},
            {"level": 6, "levelExp": 4000, "levelName": "言灵探索者", "levelColor": "#42bc05"},
            {"level": 7, "levelExp": 5000, "levelName": "水系魔法师", "levelColor": "#42bc05"},
            {"level": 8, "levelExp": 6000, "levelName": "水系魔导师", "levelColor": "#42bc05"},
            {"level": 9, "levelExp": 8000, "levelName": "藏书的魔女", "levelColor": "#2003da"},
            {"level": 10, "levelExp": 10000, "levelName": "人形图书馆", "levelColor": "#2003da"}
        ]
        
        # 运势描述
        self.fortune_info = [
            {"luck": 0, "desc": "走平坦的路但会摔倒的程度"},
            {"luck": 5, "desc": "吃泡面会没有调味包的程度"},
            {"luck": 15, "desc": "上厕所会忘记带纸的程度"},
            {"luck": 20, "desc": "上学/上班路上会堵车的程度"},
            {"luck": 25, "desc": "点外卖很晚才会送到的程度"},
            {"luck": 30, "desc": "点外卖会多给予赠品的程度"},
            {"luck": 35, "desc": "出门能捡到几枚硬币的程度"},
            {"luck": 40, "desc": "踩到香蕉皮不会滑倒的程度"},
            {"luck": 50, "desc": "玩滑梯能够流畅滑到底的程度"},
            {"luck": 60, "desc": "晚上走森林不会迷路的程度"},
            {"luck": 70, "desc": "打游戏能够轻松过关的程度"},
            {"luck": 80, "desc": "抽卡能够大成功的程度"},
            {"luck": 95, "desc": "天选之人"}
        ]
        
        # 黄历事件
        self.events = [
            {"name": "网购", "good": "买到超值好物", "bad": "会被坑"},
            {"name": "学习", "good": "效率倍增", "bad": "一看就困"},
            {"name": "运动", "good": "身轻如燕", "bad": "容易受伤"},
            {"name": "聚会", "good": "遇到贵人", "bad": "尴尬冷场"},
            {"name": "投资", "good": "收益丰厚", "bad": "血本无归"},
            {"name": "表白", "good": "一击即中", "bad": "当场去世"},
            {"name": "熬夜", "good": "灵感爆发", "bad": "猝死边缘"},
            {"name": "吃辣", "good": "神清气爽", "bad": "菊花残"}
        ]
    
    def load_data(self) -> Dict:
        """加载用户数据"""
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return {}
        return {}
    
    def save_data(self):
        """保存用户数据"""
        with open(self.data_file, 'w', encoding='utf-8') as f:
            json.dump(self.user_data, f, ensure_ascii=False, indent=2)
    
    def seeded_random(self, seed: int) -> float:
        """基于种子的随机数生成"""
        x = math.sin(seed) * 10000
        return x - math.floor(x)
    
    def get_fortune(self, uid: str) -> int:
        """获取今日运势值"""
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        seed = (int(uid) * int(today.timestamp())) % 1000000001
        return int(self.seeded_random(seed) * 100)
    
    def get_random_events(self, uid: str) -> List[Dict]:
        """获取随机黄历事件"""
        seed = self.get_fortune(uid)
        random.seed(seed)
        return random.sample(self.events, min(4, len(self.events)))
    
    def get_level_info(self, exp: int) -> Dict:
        """获取等级信息"""
        level_data = self.level_info[0]
        next_exp = "???"
        
        for i, level in enumerate(self.level_info):
            if exp >= level["levelExp"]:
                level_data = level
                if i + 1 < len(self.level_info):
                    next_exp = self.level_info[i + 1]["levelExp"]
            else:
                break
        
        return {"levelInfo": level_data, "nextExp": next_exp}
    
    def get_fortune_desc(self, luck: int) -> str:
        """获取运势描述"""
        desc = self.fortune_info[0]["desc"]
        for fortune in self.fortune_info:
            if luck >= fortune["luck"]:
                desc = fortune["desc"]
            else:
                break
        return desc
    
    def get_greeting(self, hour: int) -> str:
        """获取问候语"""
        if 0 <= hour < 5:
            return "晚安"
        elif 5 <= hour < 9:
            return "早上好"
        elif 9 <= hour < 11:
            return "上午好"
        elif 11 <= hour < 14:
            return "中午好"
        elif 14 <= hour < 18:
            return "下午好"
        elif 18 <= hour < 20:
            return "傍晚好"
        else:
            return "晚上好"
    
    def random_with_luck(self, min_val: int, max_val: int, luck: int) -> int:
        """基于运势的随机数生成"""
        mean = luck / 100
        std = 0.12
        
        # Box-Muller变换生成正态分布
        a = random.random()
        b = random.random()
        while a == 0.0 or b == 0.0:
            a = random.random()
            b = random.random()
        
        rand = math.cos(2 * math.pi * a) * math.sqrt(-2 * math.log(b))
        rand = rand * std + mean
        
        # 折叠到[0,1]范围
        if rand > 1:
            rand = 2 - rand
        elif rand < 0:
            rand = -rand
        
        # 确保在范围内
        rand = max(0, min(1, rand))
        
        return round(rand * (max_val - min_val) + min_val)
    
    async def signin_user(self, uid: str, username: str) -> Dict:
        """签到功能"""
        today = date.today().isoformat()
        
        if uid not in self.user_data:
            self.user_data[uid] = {
                "name": username,
                "last_signin": "",
                "exp": 0,
                "signin_count": 0
            }
        
        user = self.user_data[uid]
        
        if user["last_signin"] == today:
            return {"status": 1}  # 已签到
        
        # 执行签到
        luck = self.get_fortune(uid)
        exp_gain = self.random_with_luck(self.config["sign_exp_min"], self.config["sign_exp_max"], luck)
        coin_gain = self.random_with_luck(self.config["sign_coin_min"], self.config["sign_coin_max"], luck)
        
        user["name"] = username
        user["last_signin"] = today
        user["exp"] += exp_gain
        user["signin_count"] += 1
        
        self.save_data()
        
        return {
            "status": 0,
            "exp_gain": exp_gain,
            "coin_gain": coin_gain,
            "total_exp": user["exp"],
            "signin_count": user["signin_count"]
        }
    
    @filter.command("jrys")
    async def jrys_command(self, event: AstrMessageEvent):
        """今日运势签到"""
        uid = str(event.get_sender_id())
        username = event.get_sender_name() or str(uid)
        
        # 执行签到
        signin_result = await self.signin_user(uid, username)
        
        if signin_result["status"] == 1:
            yield event.plain_result("今天已经签到过了哦~")
            return
        
        # 获取运势和相关信息
        luck = self.get_fortune(uid)
        fortune_desc = self.get_fortune_desc(luck)
        level_info = self.get_level_info(signin_result["total_exp"])
        events = self.get_random_events(uid)
        greeting = self.get_greeting(datetime.now().hour)
        
        # 构建消息
        now = datetime.now()
        date_str = f"{now.month:02d}/{now.day:02d}"
        
        # 计算等级进度
        if isinstance(level_info["nextExp"], int):
            progress = (signin_result["total_exp"] / level_info["nextExp"] * 100)
            progress_str = f"{progress:.1f}%"
            exp_str = f"{signin_result['total_exp']}/{level_info['nextExp']}"
        else:
            progress_str = "100%"
            exp_str = f"{signin_result['total_exp']}/MAX"
        
        # 选择宜忌事件
        good_events = events[:2] if len(events) >= 2 else events
        bad_events = events[2:4] if len(events) >= 4 else events[:2]
        
        good_str = "\n".join([f"{e['name']}——{e['good']}" for e in good_events])
        bad_str = "\n".join([f"{e['name']}——{e['bad']}" for e in bad_events])
        
        message_text = f"""🌟 今日运势 🌟

{greeting} {username}！ {date_str}

✅ 签到成功！
🫧 经验 +{signin_result['exp_gain']}
🪙 {self.config['currency']} +{signin_result['coin_gain']}

📊 等级信息：
{level_info['levelInfo']['levelName']} ({exp_str})
进度：{progress_str}

🍀 今日运势：{luck}
🌠 运势描述：{fortune_desc}

━━━━━━━━━━━━━━━━

✅ 宜：
{good_str}

❌ 忌：
{bad_str}

━━━━━━━━━━━━━━━━
随机生成 请勿迷信"""
        
        yield event.plain_result(message_text)
=======
=======
>>>>>>> 29dad5c9f062ec2119c5047059b51b98155b536b
from astrbot.api.event import filter, AstrMessageEvent, MessageEventResult
from astrbot.api.star import Context, Star, register
from astrbot.api import logger

@register("helloworld", "YourName", "一个简单的 Hello World 插件", "1.0.0")
class MyPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)

    async def initialize(self):
        """可选择实现异步的插件初始化方法，当实例化该插件类之后会自动调用该方法。"""

    # 注册指令的装饰器。指令名为 helloworld。注册成功后，发送 `/helloworld` 就会触发这个指令，并回复 `你好, {user_name}!`
    @filter.command("helloworld")
    async def helloworld(self, event: AstrMessageEvent):
        """这是一个 hello world 指令""" # 这是 handler 的描述，将会被解析方便用户了解插件内容。建议填写。
        user_name = event.get_sender_name()
        message_str = event.message_str # 用户发的纯文本消息字符串
        message_chain = event.get_messages() # 用户所发的消息的消息链 # from astrbot.api.message_components import *
        logger.info(message_chain)
        yield event.plain_result(f"Hello, {user_name}, 你发了 {message_str}!") # 发送一条纯文本消息

    async def terminate(self):
        """可选择实现异步的插件销毁方法，当插件被卸载/停用时会调用。"""

