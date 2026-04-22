# VPS 自动运行脚本

自动执行定时任务并推送通知到手机。

## 功能

- ✅ 定时运行：每天 11:30 开始，每 6 小时执行一次（11:30, 17:30, 23:30）
- ✅ 推送通知：支持 Bark（iOS）、Server酱、Telegram
- ✅ GitHub Actions：云端自动执行
- ✅ 本地 Crontab：VPS 本地定时执行
- ✅ 开机自启：重启后自动运行

---

## 文件说明

| 文件 | 说明 |
|------|------|
| `vps每日自动运行.sh` | 主脚本，定时执行任务 |
| `add_github_secrets.sh` | 添加 GitHub Secrets 工具 |
| `.env` | 环境变量配置文件 |
| `.github/workflows/daily-run.yml` | GitHub Actions 工作流 |

---

## 快速开始

### 1. 配置环境变量

编辑 `.env` 文件：
```bash
USERNAME=hqlak47@gmail.com
PASSWORD=hqlak47@gmail.com
BARK_KEY=8kSTPbxDxoRtzezBT84nQj
BARK_SERVER=https://api.day.app
```

### 2. 安装定时任务（本地 VPS）

```bash
# 添加执行权限
chmod +x vps每日自动运行.sh

# 安装 Crontab 定时任务
./vps每日自动运行.sh install

# 或使用 Systemd（推荐，需要 sudo）
sudo ./vps每日自动运行.sh systemd
```

### 3. 配置 GitHub Actions

```bash
# 1. 创建 GitHub Token（需要 repo + workflow 权限）
#    访问：https://github.com/settings/tokens/new

# 2. 添加 Secrets
./add_github_secrets.sh <GITHUB_TOKEN> pixian5/iku --env-file .env

# 3. 推送到 GitHub
git add .
git commit -m "添加自动运行脚本"
git push
```

---

## 使用方法

### vps每日自动运行.sh

```bash
./vps每日自动运行.sh run       # 手动执行任务
./vps每日自动运行.sh install   # 安装 Crontab 定时任务
./vps每日自动运行.sh systemd   # 安装 Systemd 服务（需要 sudo）
./vps每日自动运行.sh status    # 查看状态和日志
./vps每日自动运行.sh uninstall # 卸载定时任务
./vps每日自动运行.sh help      # 显示帮助信息
```

### add_github_secrets.sh

```bash
# 添加单个 Secret
./add_github_secrets.sh <GITHUB_TOKEN> <REPO> <SECRET_NAME> <SECRET_VALUE>

# 示例
./add_github_secrets.sh ghp_xxxx pixian5/iku USERNAME myuser
./add_github_secrets.sh ghp_xxxx pixian5/iku PASSWORD mypass

# 批量添加（从 .env 文件）
./add_github_secrets.sh <GITHUB_TOKEN> <REPO> --env-file .env

# 示例
./add_github_secrets.sh ghp_xxxx pixian5/iku --env-file .env
```

---

## 定时任务时间

| 时间 (北京时间) | 说明 |
|------|------|
| **11:30** | 第一次运行 |
| **17:30** | +6小时 |
| **23:30** | +6小时 |

---

## 推送通知配置

### Bark（iOS）

1. App Store 下载 Bark
2. 打开 App 获取 Key
3. 配置 `.env`：
```bash
BARK_KEY=你的Key
BARK_SERVER=https://api.day.app
```

### Server酱

1. 访问 https://sct.ftqq.com 获取 SendKey
2. 编辑 `vps每日自动运行.sh`：
```bash
PUSH_TOKEN="你的SendKey"
PUSH_URL="https://sctapi.ftqq.com/${PUSH_TOKEN}.send"
```

### Telegram Bot

1. 创建 Bot 获取 Token
2. 获取 Chat ID
3. 编辑 `vps每日自动运行.sh`，取消注释 Telegram 部分：
```bash
TELEGRAM_BOT_TOKEN="你的BotToken"
TELEGRAM_CHAT_ID="你的ChatID"
```

---

## 添加自定义任务

编辑 `vps每日自动运行.sh` 的 `main_task()` 函数：

```bash
main_task() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] 开始执行任务..." >> $LOG_FILE

    # ========== 在这里添加你的实际任务 ==========
    python3 /home/x/fuwu/ikuuu/checkin.py
    ./some_script.sh
    # ===========================================

    echo "[$(date '+%Y-%m-%d %H:%M:%S')] 任务执行完成" >> $LOG_FILE
}
```

---

## 移植到其他 VPS

### 方法一：复制文件

```bash
# 复制到新 VPS
scp vps每日自动运行.sh add_github_secrets.sh .env user@新VPS:/path/to/project/

# 在新 VPS 上安装
ssh user@新VPS
cd /path/to/project/
chmod +x vps每日自动运行.sh add_github_secrets.sh
./vps每日自动运行.sh install
```

### 方法二：Git Clone

```bash
git clone https://github.com/pixian5/iku.git
cd ikuu
chmod +x vps每日自动运行.sh add_github_secrets.sh
./vps每日自动运行.sh install
```

---

## GitHub Token 权限

创建 Token 时需要勾选：

- ✅ `repo`（全部子选项）
- ✅ `workflow`

访问：https://github.com/settings/tokens/new

---

## 常见问题

### Q: 如何查看日志？

```bash
./vps每日自动运行.sh status
# 或
tail -f /var/log/vps_daily_run.log
```

### Q: 如何测试推送？

```bash
curl "https://api.day.app/你的BARK_KEY/测试/推送成功"
```

### Q: 如何手动触发 GitHub Actions？

访问：https://github.com/pixian5/iku/actions

点击 **VPS Daily Run** → **Run workflow** → **Run workflow**

---

## License

MIT
