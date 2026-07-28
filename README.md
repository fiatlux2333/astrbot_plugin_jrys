# 今日运势签到 (astrbot_plugin_jrys)

✨ 基于 AstrBot 的一个插件 ✨

为你的群聊提供精美的 HTML 渲染运势签到卡片，包含签到奖励、等级成长、每日宜忌与一言。

> **今日运势，与你同行。**

## 📖 介绍

这是一个从 [koishi-plugin-jrys-fix](https://github.com/CatKoishi/koishi-plugin-jrys-fix) 移植到 AstrBot 的今日运势签到插件。插件使用 Playwright 渲染 HTML 并截图生成精美的签到卡片图片，包含等级成长、经验/货币奖励、每日宜忌事项与随机一言。

<img width="600" height="888" alt="33e555bf305febe0b9a66e8b4eb8f783" src="https://github.com/user-attachments/assets/f0beba58-3725-4b5e-8ad9-0e6a1d7faf9e" />


## 💿 安装

### 通过 AstrBot 插件市场安装（推荐）

1. 在 AstrBot WebUI 中打开插件市场
2. 搜索 `astrbot_plugin_jrys` 或 `今日运势签到`
3. 点击安装

### 手动安装

1. 下载插件 zip 或在 AstrBot 插件目录下克隆仓库：

```
cd AstrBot/data/plugins
git clone https://github.com/fiatlux2333/astrbot_plugin_jrys
```

2. 安装依赖（AstrBot 会自动根据 `requirements.txt` 安装 Python 包）：

```
pip install -r requirements.txt
```

3. 安装中文字体（**Linux / Docker 服务器必需**，否则图片中文会显示为方框）：

```bash
# Debian / Ubuntu / Docker
apt-get install -y fonts-noto-cjk fonts-noto-color-emoji fonts-wqy-zenhei

# RHEL / CentOS
yum install -y google-noto-cjk-fonts

# Alpine
apk add font-noto-cjk
```

> macOS / Windows 系统自带中文字体，无需此步。

4. 确认 Playwright 浏览器可用：

```
playwright install chromium
```

如果 Playwright 默认浏览器不可用，请在插件配置中填写 `browser_executable_path`，例如 `/usr/bin/chromium`。

5. 在 AstrBot WebUI 的插件管理中启用插件

> ⚠️ **图片渲染功能依赖 Playwright 的 Chromium 浏览器**，若浏览器不可用，插件会自动降级为纯文本输出（需在配置中启用 `send_text_fallback`）。

## ⚙️ 配置

在 AstrBot WebUI 的插件配置页面进行配置：

| 配置项 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `background_url` | str | `assets/default_background.jpg` | 签到卡片公网图片 URL、本地图片路径或本地图片目录（随机选图）；内网、回环及本地域名会被拒绝 |
| `browser_executable_path` | str | `""` | Chromium/Chrome 可执行文件路径，留空则使用 Playwright 自带浏览器 |
| `enable_hitokoto` | bool | `true` | 是否启用随机一言（来自 hitokoto.cn） |
| `hitokoto_api` | str | `https://v1.hitokoto.cn/?c=a&c=b&c=k` | 一言 API 地址 |
| `send_text_fallback` | bool | `true` | 图片生成失败时是否发送纯文本回退消息 |
| `sign_exp_min` | int | `1` | 签到获得经验最小值 |
| `sign_exp_max` | int | `100` | 签到获得经验最大值 |
| `sign_coin_min` | int | `1` | 签到获得货币最小值 |
| `sign_coin_max` | int | `100` | 签到获得货币最大值 |
| `currency` | str | `coin` | 插件内货币名称（显示在签到卡片和消息中） |

## 🎁 使用

```
/jrys           签到并查看今日运势卡片
```

首次使用会注册用户，之后每天可以签到一次。签到成功会获得随机经验和货币奖励，并有概率触发特殊运势事件。

签到卡片包含以下内容：

- 用户信息（头像、昵称）
- 签到状态与奖励（经验 + 货币）
- 当前等级与进度条（21 级，不同等级有不同颜色）
- 今日运势值（0~95）与运势描述
- 每日宜忌事项（宜做 / 忌做）
- 随机一言

## 📋 依赖

- `playwright>=1.45.0` - 浏览器自动化，用于 HTML 转图片
- `aiohttp>=3.8.0` - 异步获取随机一言（AstrBot 已内置，通常无需单独安装）

安装 Playwright 浏览器：

```
playwright install chromium
```

## 🖋 字体说明

本插件渲染签到卡片时使用以下方案保证 emoji 和中文字体正确显示：

- **Emoji**：使用内置的 [Twemoji](https://github.com/twitter/twemoji) 官方 SVG 图片（🫧🪙🍀🌠），完全不依赖系统 emoji 字体
- **中文**：优先通过 Google Fonts CDN 加载 `Noto Sans SC`，回退到系统字体

> Linux / Docker 服务器若未安装中文字体，图片中的中文会显示为方框（□）。请在安装阶段完成字体安装，或在有外网访问的环境下让 Google Fonts CDN 自动加载。

## ⚠️ 注意事项

1. **Playwright 浏览器**：图片渲染依赖 Chromium，若 `playwright install chromium` 后仍有问题，请在配置中填写 `browser_executable_path`
2. **一言 API**：默认使用 `https://v1.hitokoto.cn/`，若网络无法访问可在配置中更换为其他一言 API 或关闭 `enable_hitokoto`
3. **数据持久化**：用户数据存放在 `AstrBot/data/astrbot_plugin_jrys/jrys_data.json`，请勿手动编辑
4. **等级配置**：等级名称、经验阈值和颜色在 `main.py` 的 `DEFAULT_LEVELS` 中定义，可根据需要修改
5. **运势配置**：运势描述、宜忌事件在 `main.py` 的 `DEFAULT_FORTUNES` 和 `DEFAULT_EVENTS` 中定义，可根据需要修改

## 🛠️ 技术实现

- 使用 **Playwright** 渲染 HTML 并截图生成签到卡片图片
- 使用 **hitokoto.cn API** 获取随机一言
- 使用本地 **JSON 文件**持久化用户数据（经验、货币、签到记录）
- 使用 **种子随机算法**（基于用户 ID + 日期）保证每日运势确定性且不可预测
- Emoji 使用内置 Twemoji SVG 图片，跨平台零字体依赖

## 📝 功能特性

- 🎴 **精美签到卡片** - Playwright HTML 渲染，高保真还原 Koishi 原版样式
- 📈 **等级成长系统** - 21 级等级体系，不同等级有不同颜色标识
- 🔋  **签到奖励** - 随机经验和货币奖励，支持自定义奖励范围
- 🍀 **每日运势** - 0~95 共 13 档运势值，附带趣味运势描述
- ✅ **每日宜忌** - 基于 seed 随机生成今日宜做和忌做事项
- 💬 **随机一言** - 集成 hitokoto.cn，卡片底部展示随机句子
- 🖼️ **自定义背景** - 支持公网 URL、本地图片或本地图片目录（随机选图）
- 🔄 **纯文本回退** - 图片生成失败时自动降级为纯文本消息

## 📄 许可证

本项目基于 [MIT License](./LICENSE) 开源,继承自原项目 [koishi-plugin-jrys-fix](https://github.com/CatKoishi/koishi-plugin-jrys-fix) 的许可证。

## ❤ 致谢

- [koishi-plugin-jrys-fix](https://github.com/CatKoishi/koishi-plugin-jrys-fix) - 原始项目，由 [NyaKoishi](https://github.com/CatKoishi) 开发
- [AstrBot](https://github.com/AstrBotDevs/AstrBot) - 优秀的机器人框架
- [Playwright](https://playwright.dev/) - 浏览器自动化方案
- [Twemoji](https://github.com/twitter/twemoji) - Twitter 开源 emoji 图标集

## 📮 反馈与建议

如有问题或建议，欢迎提交 Issue 或 Pull Request！
