import asyncio
import hashlib
import html
import ipaddress
import json
import math
import random
import socket
from datetime import date, datetime, time
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import astrbot.api.message_components as Comp
from astrbot.api import AstrBotConfig, logger
from astrbot.api.event import AstrMessageEvent, filter
from astrbot.api.star import Context, Star, register

PLUGIN_NAME = "astrbot_plugin_jrys"
# 以下常量需与 metadata.yaml 保持一致,避免版本/作者信息脱节。
PLUGIN_AUTHOR = "fiatlux2333"
PLUGIN_DESC = "今日运势签到插件 - AstrBot HTML 渲染版"
PLUGIN_VERSION = "v1.3.2"
# 旧插件名（曾用 _fix 后缀），用于一次性迁移历史签到数据
LEGACY_PLUGIN_NAME = "astrbot_plugin_jrys_fix"
SEED_MOD = 1_000_000_001
CARD_WIDTH = 600
VIEWPORT_HEIGHT = 2160
RENDER_CACHE_VERSION = 3

# 字体文件 → 系统路径候选列表（按优先级，跨平台）
# Debian/Ubuntu: apt install fonts-noto-cjk fonts-noto-color-emoji fonts-wqy-zenhei
SYSTEM_FONT_PATHS = {
    "simhei.ttf": [
        # Windows
        r"C:\Windows\Fonts\simhei.ttf",
        r"C:\Windows\Fonts\simhei.ttc",
        # Linux - Noto Sans CJK (Debian/Ubuntu)
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/truetype/noto-cjk/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/noto-cjk/NotoSansCJK-Regular.ttc",
        # Linux - WenQuanYi (fallback)
        "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
        "/usr/share/fonts/wqy-zenhei/wqy-zenhei.ttc",
    ],
    "segoeuiemoji.ttf": [
        # Windows
        r"C:\Windows\Fonts\seguiemj.ttf",
        # Linux - Noto Color Emoji (Debian 13: apt install fonts-noto-color-emoji)
        "/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf",
        "/usr/share/fonts/noto-color-emoji/NotoColorEmoji.ttf",
    ],
}

DEFAULT_LEVELS = [
    {"level": 0, "levelExp": 0, "levelName": "不知名杂鱼", "levelColor": "#838383"},
    {"level": 1, "levelExp": 500, "levelName": "荒野漫步者", "levelColor": "#838383"},
    {"level": 2, "levelExp": 1000, "levelName": "拓荒者", "levelColor": "#838383"},
    {"level": 3, "levelExp": 1500, "levelName": "冒险家", "levelColor": "#838383"},
    {
        "level": 4,
        "levelExp": 2000,
        "levelName": "传说的冒险家",
        "levelColor": "#000000",
    },
    {"level": 5, "levelExp": 3000, "levelName": "隐秘收藏家", "levelColor": "#000000"},
    {"level": 6, "levelExp": 4000, "levelName": "言灵探索者", "levelColor": "#42bc05"},
    {"level": 7, "levelExp": 5000, "levelName": "水系魔法师", "levelColor": "#42bc05"},
    {"level": 8, "levelExp": 6000, "levelName": "水系魔导师", "levelColor": "#42bc05"},
    {"level": 9, "levelExp": 8000, "levelName": "藏书的魔女", "levelColor": "#2003da"},
    {
        "level": 10,
        "levelExp": 10000,
        "levelName": "人形图书馆",
        "levelColor": "#2003da",
    },
    {
        "level": 11,
        "levelExp": 15000,
        "levelName": "文明归档员",
        "levelColor": "#2003da",
    },
    {
        "level": 12,
        "levelExp": 20000,
        "levelName": "高塔思索者",
        "levelColor": "#03a4da",
    },
    {
        "level": 13,
        "levelExp": 25000,
        "levelName": "未知探索者",
        "levelColor": "#03a4da",
    },
    {
        "level": 14,
        "levelExp": 30000,
        "levelName": "背负真相之人",
        "levelColor": "#9d03da",
    },
    {"level": 15, "levelExp": 35000, "levelName": "守密人", "levelColor": "#9d03da"},
    {
        "level": 16,
        "levelExp": 40000,
        "levelName": "被缚的倒吊者",
        "levelColor": "#9d03da",
    },
    {
        "level": 17,
        "levelExp": 45000,
        "levelName": "崩毁世界之人",
        "levelColor": "#f10171",
    },
    {
        "level": 18,
        "levelExp": 50000,
        "levelName": "命运眷顾者",
        "levelColor": "#f10171",
    },
    {
        "level": 19,
        "levelExp": 100000,
        "levelName": "文明领航员",
        "levelColor": "#c9b86d",
    },
    {
        "level": 20,
        "levelExp": 1000000,
        "levelName": "天选之人",
        "levelColor": "#ffd000",
    },
]

DEFAULT_FORTUNES = [
    {"luck": 0, "desc": "走平坦的路但会摔倒的程度"},
    {"luck": 5, "desc": "吃泡面会没有调味包的程度"},
    {"luck": 15, "desc": "上厕所会忘记带纸的程度"},
    {"luck": 20, "desc": "上学/上班路上会堵车的程度"},
    {"luck": 25, "desc": "点外卖很晚才会送到的程度"},
    {"luck": 30, "desc": "点外卖会多给予赠品的程度"},
    {"luck": 35, "desc": "出门能捡到几枚硬币的程度"},
    {"luck": 40, "desc": "踩到香蕉皮不会滑倒的程度"},
    {"luck": 50, "desc": "玩滑梯能流畅滑到底的程度"},
    {"luck": 60, "desc": "晚上走森林不会迷路的程度"},
    {"luck": 70, "desc": "打游戏能够轻松过关的程度"},
    {"luck": 80, "desc": "抽卡能够大成功的程度"},
    {"luck": 95, "desc": "天选之人"},
]

DEFAULT_EVENTS = [
    {"name": "看直播", "good": "喜欢的内容开播啦", "bad": "喜欢的内容咕了一整天"},
    {"name": "打轴", "good": "一次性过", "bad": "谁说话这么难懂"},
    {"name": "剪辑", "good": "灵感爆发", "bad": "一团乱麻"},
    {"name": "校对", "good": "变成无情的审轴机器", "bad": "被闪轴闪瞎眼"},
    {"name": "背单词", "good": "这次六级肯定过", "bad": "背完50个忘了45个"},
    {"name": "做作业", "good": "做的每个都对", "bad": "做一个做错一个"},
    {"name": "锻炼身体", "good": "身体健康，更加精神", "bad": "容易用力过猛"},
    {"name": "烹饪", "good": "味道意外不错", "bad": "难道这就是仰望星空派"},
    {"name": "告白", "good": "其实我也喜欢你好久了", "bad": "对不起，你是一个好人"},
    {"name": "追新番", "good": "正好看到精彩回", "bad": "可能被剧透"},
    {"name": "音游", "good": "手感在线", "bad": "又双叒叕 LOST 了"},
    {"name": "向大佬请教", "good": "太棒了，学到许多", "bad": "太棒了，什么都没学到"},
    {"name": "早起", "good": "迎接第一缕阳光", "bad": "才4点，再睡一会"},
    {"name": "早睡", "good": "第二天精神饱满", "bad": "失眠数羊画圈圈"},
    {"name": "抽卡", "good": "单抽出货", "bad": "到井前一发出货"},
    {"name": "拼乐高", "good": "顺利完工", "bad": "发现少了一块零件"},
    {"name": "跳槽", "good": "新工作待遇大幅提升", "bad": "待遇还不如之前的"},
    {"name": "写开源库", "good": "代码写得又快又稳", "bad": "写完发现已有更好的轮子"},
    {"name": "写单元测试", "good": "将减少出错", "bad": "会降低你的开发效率"},
    {"name": "白天上线", "good": "今天白天上线是安全的", "bad": "可能导致灾难性后果"},
    {"name": "重构", "good": "代码质量得到提高", "bad": "很可能陷入泥潭"},
    {"name": "面试", "good": "面试官今天心情很好", "bad": "面试官不爽，会拿你出气"},
    {"name": "提交代码", "good": "遇到冲突的几率最低", "bad": "会遇到一大堆冲突"},
    {
        "name": "代码复审",
        "good": "发现重要问题的几率大大增加",
        "bad": "你什么问题都发现不了",
    },
    {"name": "晚上上线", "good": "晚上是精神最好的时候", "bad": "你白天已经筋疲力尽了"},
    {"name": "氪金", "good": "早买早享受", "bad": "第二天就 50% off"},
    {"name": "挑战高难", "good": "一上来就是新纪录", "bad": "先热手比较好"},
    {"name": "与群友水聊", "good": "话题不断", "bad": "容易聊到忘记正事"},
    {"name": "学习新技能", "good": "有会成为大神的资质", "bad": "可能会误入歧途"},
    {"name": "上课玩手机", "good": "会发现好玩的事情", "bad": "会被老师教训"},
    {"name": "出门带伞", "good": "今天下雨你信不信", "bad": "好运气都被遮住了"},
    {"name": "玩 Minecraft", "good": "建筑灵感爆发", "bad": "启动器可能闹脾气"},
    {"name": "上 Steam", "good": "愿望单迎来折扣", "bad": "钱包会被清空"},
    {"name": "修图", "good": "原片直出毫无压力", "bad": "Photoshop 未响应"},
    {"name": "赶稿", "good": "完美守住 deadline", "bad": "终究还是超期"},
    {"name": "摸鱼", "good": "短暂恢复精神", "bad": "被老板当场抓获"},
    {"name": "入手新游戏", "good": "你会玩的很开心", "bad": "这游戏明天就打折"},
    {"name": "出门", "good": "今天会是个好天气", "bad": "中途可能变天"},
]


def plugin_dir() -> Path:
    return Path(__file__).resolve().parent


def plugin_data_dir() -> Path:
    current = plugin_dir()
    if current.parent.name == "plugins" and current.parent.parent.name == "data":
        return current.parent.parent / PLUGIN_NAME
    return current / "data"


def stable_user_number(uid: str) -> int:
    uid = str(uid)
    if uid.isdigit():
        return int(uid)
    digest = hashlib.sha256(uid.encode("utf-8")).hexdigest()
    return int(digest[:16], 16)


def seeded_random(seed: int) -> float:
    value = math.sin(seed) * 10000
    return value - math.floor(value)


def today_midnight_timestamp() -> int:
    return int(datetime.combine(date.today(), time.min).timestamp())


def get_greeting(hour: int) -> str:
    if 0 <= hour < 5:
        return "晚安"
    if 5 <= hour < 9:
        return "早上好"
    if 9 <= hour < 11:
        return "上午好"
    if 11 <= hour < 14:
        return "中午好"
    if 14 <= hour < 18:
        return "下午好"
    if 18 <= hour < 20:
        return "傍晚好"
    return "晚上好"


def is_url(value: str) -> bool:
    try:
        return urlparse(value).scheme.lower() in {"http", "https"}
    except ValueError:
        return False


def escape(value: Any) -> str:
    return html.escape(str(value), quote=True)


def shorten(value: str, limit: int) -> str:
    value = value.strip()
    return value if len(value) <= limit else value[: limit - 1] + "..."


@register(
    PLUGIN_NAME,
    PLUGIN_AUTHOR,
    PLUGIN_DESC,
    PLUGIN_VERSION,
)
class JrysFix(Star):
    def __init__(self, context: Context, config: AstrBotConfig | None = None):
        super().__init__(context)
        self.config = config or {}
        self.sign_exp_min = self.config_int("sign_exp_min", 1)
        self.sign_exp_max = self.config_int("sign_exp_max", 100)
        self.sign_coin_min = self.config_int("sign_coin_min", 1)
        self.sign_coin_max = self.config_int("sign_coin_max", 100)
        self.currency = str(self.config.get("currency", "coin"))
        background_source = str(
            self.config.get("background_url", "assets/default_background.jpg")
        ).strip()
        self.background_url = (
            self._validate_http_url(
                background_source,
                "background_url",
                "assets/default_background.jpg",
            )
            if is_url(background_source)
            else background_source
        )
        self.enable_hitokoto = self.config_bool("enable_hitokoto", True)
        default_hitokoto_api = "https://v1.hitokoto.cn/?c=a&c=b&c=k"
        self.hitokoto_api = self._validate_http_url(
            str(self.config.get("hitokoto_api", default_hitokoto_api)).strip(),
            "hitokoto_api",
            default_hitokoto_api,
        )
        self.send_text_fallback = self.config_bool("send_text_fallback", True)
        self.browser_executable_path = str(
            self.config.get("browser_executable_path", "")
        ).strip()
        self.data_dir = plugin_data_dir()
        self.cache_dir = self.data_dir / "cache"
        self.data_file = self.data_dir / "jrys_data.json"
        self.user_data: dict[str, dict[str, Any]] = {}
        # 并发保护：签到读改写共享数据；浏览器实例复用
        self._data_lock = asyncio.Lock()
        self._browser_lock = asyncio.Lock()
        self._playwright = None
        self._browser = None

    def config_int(self, key: str, default: int) -> int:
        try:
            return int(self.config.get(key, default))
        except (TypeError, ValueError):
            logger.warning(f"Invalid config value for {key}, fallback to {default}.")
            return default

    def config_bool(self, key: str, default: bool) -> bool:
        value = self.config.get(key, default)
        if isinstance(value, bool):
            return value
        return str(value).lower() in {"1", "true", "yes", "on"}

    @staticmethod
    def _validate_http_url(url: str, key: str, default: str) -> str:
        """校验 http/https URL 并拒绝指向内网/回环地址,防止 SSRF。"""
        if not url:
            return default
        try:
            parsed = urlparse(url)
            host = parsed.hostname
            parsed.port
        except ValueError:
            logger.warning(f"URL {key} 格式无效,回退默认值。")
            return default
        if parsed.scheme.lower() not in {"http", "https"} or not host:
            logger.warning(f"配置 {key} 必须是 http/https URL,回退默认值。")
            return default
        if parsed.username is not None or parsed.password is not None:
            logger.warning(f"URL {key} 不允许包含用户凭据,回退默认值。")
            return default
        normalized_host = host.rstrip(".").lower()
        if normalized_host == "localhost" or normalized_host.endswith(
            (".localhost", ".local", ".internal", ".lan")
        ):
            logger.warning(f"URL {key} 指向本地主机 {host},已拒绝,回退默认值。")
            return default
        try:
            ip = ipaddress.ip_address(normalized_host)
            if not ip.is_global:
                logger.warning(f"URL {key} 指向非公网地址 {host},已拒绝,回退默认值。")
                return default
        except ValueError:
            pass
        return url

    async def _is_public_http_url(self, url: str) -> bool:
        """解析远程资源主机并确保所有结果均为公网地址。"""
        validated = self._validate_http_url(url, "render_resource", "")
        if not validated:
            return False
        parsed = urlparse(validated)
        host = parsed.hostname
        if not host:
            return False
        try:
            ipaddress.ip_address(host.rstrip("."))
            return True
        except ValueError:
            pass
        try:
            addresses = await asyncio.to_thread(
                socket.getaddrinfo,
                host,
                parsed.port or (443 if parsed.scheme.lower() == "https" else 80),
                type=socket.SOCK_STREAM,
            )
        except OSError as exc:
            logger.warning(f"远程图片域名 {host} 解析失败,已阻止请求：{exc}")
            return False
        resolved_ips = {item[4][0].split("%", 1)[0] for item in addresses}
        return bool(resolved_ips) and all(
            ipaddress.ip_address(address).is_global for address in resolved_ips
        )

    async def _route_render_request(self, route) -> None:
        """阻止渲染页面及重定向请求访问非公网 HTTP(S) 地址。"""
        request_url = route.request.url
        if is_url(request_url) and not await self._is_public_http_url(request_url):
            logger.warning(
                f"已阻止渲染器访问非公网主机：{urlparse(request_url).hostname}"
            )
            await route.abort()
            return
        await route.continue_()

    async def initialize(self):
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.cleanup_cache()
        self.migrate_legacy_data()
        await self.ensure_fonts()
        self.user_data = self.load_data()
        logger.info(f"{PLUGIN_NAME} initialized, loaded {len(self.user_data)} users.")

    async def terminate(self):
        await asyncio.to_thread(self.save_data)
        await self.close_browser()

    def cleanup_cache(self):
        """清理非当天的 HTML/PNG 渲染缓存，避免磁盘无限增长。"""
        today = date.today().isoformat()
        for path in self.cache_dir.glob("jrys_*"):
            if today not in path.name:
                try:
                    path.unlink()
                except OSError:
                    pass

    def migrate_legacy_data(self):
        """一次性迁移旧插件名（astrbot_plugin_jrys_fix）目录下的历史签到数据。"""
        if self.data_file.exists():
            return
        legacy_dir = self.data_dir.parent / LEGACY_PLUGIN_NAME
        legacy_file = legacy_dir / "jrys_data.json"
        if legacy_dir == self.data_dir or not legacy_file.exists():
            return
        try:
            self.data_dir.mkdir(parents=True, exist_ok=True)
            self.data_file.write_text(
                legacy_file.read_text(encoding="utf-8"), encoding="utf-8"
            )
            logger.info(f"已迁移旧签到数据：{legacy_file} → {self.data_file}")
        except Exception as exc:
            logger.error(f"迁移旧签到数据失败：{exc}")

    def load_data(self) -> dict[str, dict[str, Any]]:
        if not self.data_file.exists():
            return {}
        try:
            return json.loads(self.data_file.read_text(encoding="utf-8"))
        except Exception as exc:
            logger.error(f"Failed to load {self.data_file}: {exc}")
            return {}

    def save_data(self):
        self.data_dir.mkdir(parents=True, exist_ok=True)
        tmp_file = self.data_file.with_suffix(".tmp")
        tmp_file.write_text(
            json.dumps(self.user_data, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        tmp_file.replace(self.data_file)

    async def ensure_fonts(self):
        """
        检测中文字体是否可用，并在缺失时给出安装提示。
        Emoji 已改为内置 SVG 图片，不再依赖系统 emoji 字体。
        Debian / Ubuntu 用户请执行：
          apt install fonts-noto-cjk fonts-noto-color-emoji fonts-wqy-zenhei
        """
        for filename in SYSTEM_FONT_PATHS:
            resolved = self.resolve_font(filename)
            if resolved is None:
                if filename == "simhei.ttf":
                    logger.warning(
                        f"中文字体未找到（{filename}）。\n"
                        "Debian/Ubuntu 请执行：\n"
                        "  apt install fonts-noto-cjk fonts-wqy-zenhei\n"
                        "中文可能无法正常显示。"
                    )
                else:
                    logger.debug(
                        f"字体文件未找到：{filename}（emoji 已改用内置 SVG，可忽略此警告）"
                    )
            else:
                logger.info(f"字体已找到：{filename} → {resolved}")

    def resolve_font(self, filename: str) -> Path | None:
        """查找字体文件：cache > 系统路径 > assets。返回 Path 或 None。"""
        # 1) cache 目录（之前下载的）
        cached = self.cache_dir / filename
        if cached.exists():
            return cached
        # 2) 系统字体路径
        for sys_path in SYSTEM_FONT_PATHS.get(filename, []):
            p = Path(sys_path)
            if p.exists():
                return p
        # 3) 插件 assets 目录
        bundled = plugin_dir() / "assets" / filename
        if bundled.exists():
            return bundled
        return None

    def emoji_svg(self, codepoint: str) -> str:
        """返回 emoji SVG 的 <img> 标签，避免依赖系统 emoji 字体。"""
        return f'<img class="icon" src="{self.asset_uri(f"assets/emoji_{codepoint}.svg")}" alt="">'

    def font_uri(self, filename: str) -> str:
        """返回字体文件的 file:// URI，找不到则返回空字符串（CSS 会静默忽略）。"""
        path = self.resolve_font(filename)
        if path and path.exists():
            return path.resolve().as_uri()
        logger.debug(f"Font file {filename} not found, @font-face src will be empty.")
        return ""

    def resolve_local_path(self, value: str) -> Path:
        path = Path(value)
        if not path.is_absolute():
            path = plugin_dir() / value
        return path

    def asset_uri(self, relative: str) -> str:
        return (plugin_dir() / relative).resolve().as_uri()

    def image_source_to_uri(self, source: str) -> str:
        source = source.strip() or "assets/default_background.jpg"
        if is_url(source):
            return source
        path = self.resolve_local_path(source)
        if path.is_dir():
            images = [
                p
                for p in path.iterdir()
                if p.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp"}
            ]
            if images:
                path = random.choice(images)
        if not path.exists():
            path = plugin_dir() / "assets" / "default_background.jpg"
        return path.resolve().as_uri()

    def get_avatar_url(self, event: AstrMessageEvent) -> str:
        default_avatar = (
            (plugin_dir() / "assets" / "default_avatar.png").resolve().as_uri()
        )

        def safe_avatar(value: Any) -> str:
            return self._validate_http_url(str(value).strip(), "avatar_url", "")

        for method_name in ("get_sender_avatar", "get_sender_avatar_url"):
            method = getattr(event, method_name, None)
            if callable(method):
                try:
                    value = method()
                    if value:
                        avatar = safe_avatar(value)
                        if avatar:
                            return avatar
                except Exception:
                    pass
        message_obj = getattr(event, "message_obj", None)
        sender = getattr(message_obj, "sender", None)
        for attr in ("avatar", "avatar_url"):
            value = getattr(sender, attr, None)
            if value:
                avatar = safe_avatar(value)
                if avatar:
                    return avatar
        # 仅 QQ 系平台使用 q1.qlogo.cn 兜底,避免在其他平台拿到无关 QQ 用户的头像。
        sender_id = ""
        platform = ""
        try:
            platform = str(event.get_platform_name())
            sender_id = str(event.get_sender_id())
        except Exception:
            sender_id = ""
        if (
            platform in {"aiocqhttp", "qq_official", "qq_official_webhook"}
            and sender_id.isdigit()
        ):
            return f"https://q1.qlogo.cn/g?b=qq&nk={sender_id}&s=100"
        return default_avatar

    async def get_hitokoto(self) -> str:
        if not self.enable_hitokoto or not self.hitokoto_api:
            return "『 随机生成，请勿迷信。』"
        try:
            import aiohttp

            timeout = aiohttp.ClientTimeout(total=5)
            headers = {"User-Agent": "AstrBot-JRYS/1.0"}
            async with aiohttp.ClientSession(
                headers=headers, timeout=timeout
            ) as session:
                async with session.get(self.hitokoto_api) as resp:
                    payload = await resp.json(content_type=None)
            # 外部接口返回内容不可信，转义后再拼入 HTML，避免注入。
            text = escape(payload.get("hitokoto") or "随机生成，请勿迷信。")
            source = escape(payload.get("from") or "")
            who = escape(payload.get("from_who") or "")
            author = f"{who}《{source}》" if who and source else who or source
            return f"『{text}』<br>—— {author}" if author else f"『{text}』"
        except Exception as exc:
            logger.debug(f"Failed to fetch hitokoto: {exc}")
            return "『 随机生成，请勿迷信。』"

    def get_fortune(self, uid: str) -> int:
        user_number = stable_user_number(uid)
        seed = (user_number * today_midnight_timestamp()) % SEED_MOD
        return int(seeded_random(seed) * 100)

    def get_random_events(self, uid: str) -> list[dict[str, str]]:
        seed = self.get_fortune(uid)
        indexes = []
        seen_indexes = set()
        counter = 0
        while len(indexes) < 4:
            index = math.floor(seeded_random(seed + counter) * len(DEFAULT_EVENTS))
            if index not in seen_indexes:
                indexes.append(index)
                seen_indexes.add(index)
            counter += 1
        return [DEFAULT_EVENTS[index] for index in indexes]

    def random_with_luck(self, min_value: int, max_value: int, luck: int) -> int:
        low, high = sorted((min_value, max_value))
        mean = luck / 100
        std = 0.12
        a = random.random()
        b = random.random()
        while a == 0.0 or b == 0.0:
            a = random.random()
            b = random.random()
        value = math.cos(2 * math.pi * a) * math.sqrt(-2 * math.log(b))
        value = value * std + mean
        if value > 1:
            value = 2 - value
        elif value < 0:
            value = -value
        value = max(0, min(1, value))
        return round(value * (high - low) + low)

    def get_level_info(self, exp: int) -> tuple[dict[str, Any], int | None]:
        current = DEFAULT_LEVELS[0]
        next_exp: int | None = None
        for index, level in enumerate(DEFAULT_LEVELS):
            if exp >= level["levelExp"]:
                current = level
                next_exp = (
                    DEFAULT_LEVELS[index + 1]["levelExp"]
                    if index + 1 < len(DEFAULT_LEVELS)
                    else None
                )
            else:
                break
        return current, next_exp

    def get_fortune_desc(self, luck: int) -> str:
        desc = DEFAULT_FORTUNES[0]["desc"]
        for fortune in DEFAULT_FORTUNES:
            if luck >= fortune["luck"]:
                desc = fortune["desc"]
            else:
                break
        return desc

    async def signin_user(self, uid: str, username: str) -> dict[str, Any]:
        today = date.today().isoformat()
        async with self._data_lock:
            user = self.user_data.setdefault(
                uid,
                {
                    "name": username,
                    "last_signin": "",
                    "exp": 0,
                    "coin": 0,
                    "signin_count": 0,
                },
            )
            if user.get("last_signin") == today:
                return {"status": 1}
            luck = self.get_fortune(uid)
            exp_gain = self.random_with_luck(self.sign_exp_min, self.sign_exp_max, luck)
            coin_gain = self.random_with_luck(
                self.sign_coin_min, self.sign_coin_max, luck
            )
            user["name"] = username
            user["last_signin"] = today
            user["exp"] = int(user.get("exp", 0)) + exp_gain
            user["coin"] = int(user.get("coin", 0)) + coin_gain
            user["signin_count"] = int(user.get("signin_count", 0)) + 1
            await asyncio.to_thread(self.save_data)
            return {
                "status": 0,
                "exp_gain": exp_gain,
                "coin_gain": coin_gain,
                "total_exp": user["exp"],
                "total_coin": user["coin"],
                "signin_count": user["signin_count"],
            }

    def collect_view_model(
        self,
        event: AstrMessageEvent,
        uid: str,
        username: str,
        signin_result: dict[str, Any],
        hitokoto: str = "",
    ) -> dict[str, Any]:
        luck = self.get_fortune(uid)
        user = self.user_data.get(uid, {})
        total_exp = int(signin_result.get("total_exp", user.get("exp", 0)))
        total_coin = int(signin_result.get("total_coin", user.get("coin", 0)))
        signin_count = int(
            signin_result.get("signin_count", user.get("signin_count", 0))
        )
        level, next_exp = self.get_level_info(total_exp)
        if next_exp is None:
            exp_text = f"{total_exp}/???"
            progress = "100.000"
        else:
            exp_text = f"{total_exp}/{next_exp}"
            progress = f"{min(total_exp / next_exp * 100, 100):.3f}"
        events = self.get_random_events(uid)
        now = datetime.now()
        return {
            "uid": uid,
            "username": shorten(username, 13),
            "date": f"{now.month:02d}/{now.day:02d}",
            "greeting": get_greeting(now.hour),
            "signed_today": signin_result["status"] == 1,
            "exp_gain": int(signin_result.get("exp_gain", 0)),
            "coin_gain": int(signin_result.get("coin_gain", 0)),
            "total_exp": total_exp,
            "total_coin": total_coin,
            "signin_count": signin_count,
            "level": level,
            "exp_text": exp_text,
            "progress": progress,
            "luck": luck,
            "fortune_desc": self.get_fortune_desc(luck),
            "good_events": events[:2],
            "bad_events": events[2:],
            "hitokoto": hitokoto or "『 随机生成，请勿迷信。』",
            "background": self.image_source_to_uri(self.background_url),
            "avatar": self.get_avatar_url(event),
        }

    def build_html(self, view: dict[str, Any]) -> str:
        status = "今天已经签到过了哦" if view["signed_today"] else "签到成功！"
        emoji_jelly = f'<img class="icon" src="{self.asset_uri("assets/emoji_1fae7.svg")}" alt="">'
        emoji_coin = f'<img class="icon" src="{self.asset_uri("assets/emoji_1fa99.svg")}" alt="">'
        reward = (
            f"{emoji_jelly}+{view['exp_gain']} {emoji_coin}+{view['coin_gain']}"
            if not view["signed_today"]
            else f"累计 {escape(self.currency)} {view['total_coin']}"
        )
        gooddo = "<br>".join(
            f"{escape(item['name'])}——{escape(item['good'])}"
            for item in view["good_events"]
        )
        baddo = "<br>".join(
            f"{escape(item['name'])}——{escape(item['bad'])}"
            for item in view["bad_events"]
        )
        # hitokoto 已在 get_hitokoto() 中转义，此处直接插入（仅含受控的 <br>）
        hitokoto = view["hitokoto"]
        background = escape(view["background"])
        avatar = escape(view["avatar"])
        return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; img-src file: http: https:; style-src 'unsafe-inline'; font-src file:">
<title>运势签到</title>
<style>
@font-face {{ font-family: 'osans4'; src: url("{self.font_uri("osans4.subset.woff2")}") format("woff2"); }}
* {{ box-sizing: border-box; }}
html, body {{ margin: 0; padding: 0; background: transparent; }}
body {{ width: 600px; font-family: 'Noto Sans SC', osans4, 'WenQuanYi Zen Hei', 'Microsoft YaHei', Arial, sans-serif; }}
.container {{ width: 600px; background: #fff; overflow: hidden; }}
.hero {{ width: 600px; height: 389px; object-fit: cover; display: block; }}
.header {{ display: flex; flex-direction: row; justify-content: space-between; margin-left: 24px; margin-right: 40px; margin-top: -48px; position: relative; z-index: 2; }}
.avatar {{ width: 80px; height: 80px; object-fit: cover; border-radius: 10px; border: 3px solid #fff; }}
.dateInfo {{ height: 83px; width: 430px; border-radius: 10px; background: rgba(255,255,255,0.45); box-shadow: 0 0 5px #a7a7a7; backdrop-filter: blur(6px); -webkit-backdrop-filter: blur(6px); display: flex; flex-direction: row; justify-content: space-between; align-items: center; font-size: 60px; font-weight: 700; line-height: 1; }}
.dateInfo span {{ margin-left: 16px; margin-right: 16px; white-space: nowrap; }}
.dateInfo .date {{ color: #666; }}
.hitokoto {{ color: #838383; font-size: 16px; line-height: 1.45; text-align: center; padding-top: 18px; min-height: 72px; }}
.content {{ padding: 0 30px; }}
.signin {{ color: #838383; margin-top: 0; margin-bottom: 8px; font-size: 20px; font-weight: 600; }}
.icon {{ width: 1.2em; height: 1.2em; vertical-align: -0.2em; display: inline-block; }}
.levelInfo {{ display: flex; flex-direction: row; justify-content: space-between; font-size: 30px; font-weight: 800; line-height: 1.18; white-space: nowrap; align-items: baseline; color: #000; }}
.levelInfo .exp {{ color: #b4b1b1; }}
.level-bar {{ margin-top: 2px; display: flex; align-items: center; }}
.bar-container {{ width: 100%; background: #e0e0e0; border-radius: 5px; overflow: hidden; }}
.progress {{ width: {view["progress"]}%; background: #666; padding: 5px 0; border-radius: 5px 0 0 5px; height: 29px; }}
.fortune {{ display: flex; flex-direction: row; justify-content: space-between; align-items: center; margin-top: 10px; margin-right: 5px; }}
.fortune .luck {{ font-size: 36px; font-weight: 800; color: #000; }}
.fortune .desc {{ font-size: 28px; color: #838383; white-space: nowrap; font-weight: 600; }}
hr {{ border: 0; border-top: 1px solid #bcbcbc; margin: 10px 0 0; }}
.toDo {{ display: flex; flex-direction: row; margin-top: 18px; align-items: center; }}
.toDo p {{ margin: 0 0 0 20px; font-size: 20px; line-height: 1.28; font-weight: 600; }}
.goodText {{ color: #4b3732; text-shadow: 0 0 1px #ffbbbb; }}
.badText {{ color: #343a43; text-shadow: 0 0 1px #bcdbff; }}
.toDoBg {{ border-radius: 50%; width: 48px; height: 48px; min-width: 48px; display: flex; justify-content: center; align-items: center; }}
.toDoBg span {{ font-size: 32px; font-weight: 800; color: #fff; line-height: 1; }}
.credit {{ margin-top: 4px; text-align: center; color: #999; font-size: 12px; padding: 8px 10px 10px; }}
</style>
</head>
<body id="body">
  <div class="container">
    <img class="hero" src="{background}" alt="background">
    <div class="header">
      <img class="avatar" src="{avatar}" alt="avatar">
      <div class="dateInfo">
        <span>{escape(view["greeting"])}</span>
        <span class="date">{escape(view["date"])}</span>
      </div>
    </div>
    <div class="hitokoto">{hitokoto}</div>
    <div class="content">
      <div class="signin">{status} {reward}</div>
      <div class="levelInfo">
        <span style="color:{view["level"]["levelColor"]}">{escape(view["level"]["levelName"])}</span>
        <span class="exp">{escape(view["exp_text"])}</span>
      </div>
      <div class="level-bar"><div class="bar-container"><div class="progress"></div></div></div>
      <div class="fortune">
        <span class="luck">{self.emoji_svg("1f340")} {escape(view["luck"])}</span>
        <span class="desc">{self.emoji_svg("1f320")} {escape(view["fortune_desc"])}</span>
      </div>
      <hr>
      <div class="toDo"><div class="toDoBg" style="background-color:#D94A3F;"><span>宜</span></div><p class="goodText">{gooddo}</p></div>
      <div class="toDo"><div class="toDoBg" style="background-color:#000;"><span>忌</span></div><p class="badText">{baddo}</p></div>
    </div>
    <div class="credit">随机生成 请勿迷信 | AstrBot</div>
  </div>
</body>
</html>"""

    async def get_browser(self):
        """获取（并按需懒启动）复用的 Chromium 实例。"""
        try:
            from playwright.async_api import async_playwright
        except ImportError as exc:
            raise RuntimeError(
                "缺少 playwright 依赖，请确认 requirements.txt 已安装。"
            ) from exc

        async with self._browser_lock:
            if self._browser is not None and self._browser.is_connected():
                return self._browser
            if self._playwright is None:
                self._playwright = await async_playwright().start()
            launch_args: dict[str, Any] = {
                "headless": True,
                "args": ["--no-sandbox", "--disable-dev-shm-usage"],
            }
            if self.browser_executable_path:
                launch_args["executable_path"] = self.browser_executable_path
            self._browser = await self._playwright.chromium.launch(**launch_args)
            return self._browser

    async def close_browser(self):
        """关闭复用的浏览器与 playwright，供 terminate 或异常重置调用。"""
        async with self._browser_lock:
            if self._browser is not None:
                try:
                    await self._browser.close()
                except Exception:
                    pass
                self._browser = None
            if self._playwright is not None:
                try:
                    await self._playwright.stop()
                except Exception:
                    pass
                self._playwright = None

    async def render_card(self, view: dict[str, Any]) -> Path:
        html_text = self.build_html(view)
        digest_source = f"{RENDER_CACHE_VERSION}\0{html_text}"
        digest = hashlib.md5(digest_source.encode("utf-8")).hexdigest()[:10]
        today = date.today().isoformat()
        uid = view.get("uid", "anon")
        html_path = self.cache_dir / f"jrys_{today}_{uid}_{digest}.html"
        image_path = self.cache_dir / f"jrys_{today}_{uid}_{digest}.png"
        # 缓存命中:今日已渲染过相同内容的卡片,直接返回,避免重复启动浏览器。
        if image_path.exists():
            return image_path
        # 1% 概率清理非当天的旧缓存,避免长期运行磁盘膨胀。
        if random.random() < 0.01:
            try:
                await asyncio.to_thread(self.cleanup_cache)
            except Exception:
                pass
        html_path.write_text(html_text, encoding="utf-8")

        try:
            browser = await self.get_browser()
            page = await browser.new_page(
                viewport={"width": CARD_WIDTH, "height": VIEWPORT_HEIGHT},
                device_scale_factor=1,
            )
            try:
                await page.route("**/*", self._route_render_request)
                await page.goto(
                    html_path.resolve().as_uri(), wait_until="domcontentloaded"
                )

                # domcontentloaded 不会等待图片下载。必须等背景完整解码后再截图，
                # 否则慢速或渐进式 JPEG 可能只渲染一部分。
                hero = page.locator(".hero")
                decode_image = """async (image) => {
                    await image.decode();
                    if (!image.complete || image.naturalWidth === 0) {
                        throw new Error("image failed to load");
                    }
                }"""
                try:
                    await asyncio.wait_for(hero.evaluate(decode_image), timeout=15)
                except Exception as exc:
                    logger.warning(f"背景图加载失败，改用默认背景图：{exc}")
                    await hero.evaluate(
                        "(image, source) => { image.src = source; }",
                        self.asset_uri("assets/default_background.jpg"),
                    )
                    await asyncio.wait_for(hero.evaluate(decode_image), timeout=5)

                avatar = page.locator(".avatar")
                try:
                    await asyncio.wait_for(avatar.evaluate(decode_image), timeout=5)
                except Exception:
                    await avatar.evaluate(
                        "(image, source) => { image.src = source; }",
                        self.asset_uri("assets/default_avatar.png"),
                    )
                    await asyncio.wait_for(avatar.evaluate(decode_image), timeout=5)

                # 先写入唯一临时文件再原子替换，避免并发请求读到半写入 PNG。
                temp_image_path = image_path.with_name(
                    f".{image_path.stem}-{random.getrandbits(64):016x}.png"
                )
                try:
                    await page.locator("#body").screenshot(
                        path=str(temp_image_path), type="png"
                    )
                    temp_image_path.replace(image_path)
                finally:
                    temp_image_path.unlink(missing_ok=True)
            finally:
                await page.close()
        except Exception:
            # 浏览器可能已崩溃,重置以便下次重新启动
            await self.close_browser()
            raise
        return image_path

    def build_message(self, view: dict[str, Any]) -> str:
        status = (
            "今天已经签到过了哦。"
            if view["signed_today"]
            else f"签到成功！经验 +{view['exp_gain']}，{self.currency} +{view['coin_gain']}。"
        )
        good_text = "\n".join(
            f"{item['name']}：{item['good']}" for item in view["good_events"]
        )
        bad_text = "\n".join(
            f"{item['name']}：{item['bad']}" for item in view["bad_events"]
        )
        return f"""今日运势

{view["greeting"]} {view["username"]}！ {view["date"]}
{status}
等级：{view["level"]["levelName"]} ({view["exp_text"]})
今日运势：{view["luck"]}
运势描述：{view["fortune_desc"]}

宜：
{good_text}

忌：
{bad_text}

随机生成，请勿迷信"""

    @filter.command("jrys")
    async def jrys_command(self, event: AstrMessageEvent):
        """今日运势签到"""
        try:
            uid = str(event.get_sender_id())
            username = event.get_sender_name() or f"用户{uid[-4:]}"
            signin_result = await self.signin_user(uid, username)
            hitokoto = await self.get_hitokoto()
            view = await asyncio.to_thread(
                self.collect_view_model, event, uid, username, signin_result, hitokoto
            )
            try:
                image_path = await self.render_card(view)
                yield event.chain_result([Comp.Image.fromFileSystem(str(image_path))])
            except Exception as image_exc:
                logger.error(f"Failed to render jrys card: {image_exc}")
                if self.send_text_fallback:
                    yield event.plain_result(self.build_message(view))
                else:
                    yield event.plain_result(
                        "运势图片生成失败，请检查 Playwright/Chromium 或 browser_executable_path 配置。"
                    )
        except Exception as exc:
            logger.error(f"Failed to handle /jrys: {exc}")
            yield event.plain_result("签到失败，请稍后再试或联系管理员。")
        finally:
            event.stop_event()
