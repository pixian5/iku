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

## 完整脚本

### vps每日自动运行.sh

```bash
#!/bin/bash
# VPS每日自动运行脚本
# 功能：自启动、每天11:30开始、每隔6小时运行一次、推送通知
# 每天运行时间点：11:30, 17:30, 23:30（共3次）

# ==================== 配置区域 ====================
SCRIPT_NAME="vps每日自动运行"
SCRIPT_PATH="/home/x/fuwu/ikuuu/vps每日自动运行.sh"
LOG_FILE="/var/log/vps_daily_run.log"

# 登录凭据
USERNAME="hqlak47@gmail.com"
PASSWORD="hqlak47@gmail.com"

# 推送配置（请根据实际情况修改）
PUSH_TOKEN="YOUR_PUSH_TOKEN"  # 如：Server酱、Bark、Telegram等
PUSH_URL="https://sctapi.ftqq.com/${PUSH_TOKEN}.send"

# ==================== 主任务函数 ====================
main_task() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] 开始执行任务..." >> $LOG_FILE

    # ========== 在这里添加你的实际任务 ==========
    # 示例任务：
    # python3 /home/x/fuwu/ikuuu/checkin.py
    # ./some_script.sh
    # ===========================================

    echo "[$(date '+%Y-%m-%d %H:%M:%S')] 任务执行完成" >> $LOG_FILE
}

# ==================== 推送通知函数 ====================
send_push() {
    local title="$1"
    local content="$2"

    # Server酱推送示例
    if [[ "$PUSH_TOKEN" != "YOUR_PUSH_TOKEN" ]]; then
        curl -s -X POST "$PUSH_URL" \
            -d "title=${title}" \
            -d "desp=${content}" >> $LOG_FILE 2>&1
    fi

    # Telegram Bot 推送示例（取消注释启用）
    # TELEGRAM_BOT_TOKEN="YOUR_BOT_TOKEN"
    # TELEGRAM_CHAT_ID="YOUR_CHAT_ID"
    # curl -s -X POST "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage" \
    #     -d "chat_id=${TELEGRAM_CHAT_ID}" \
    #     -d "text=${title}%0A${content}" >> $LOG_FILE 2>&1

    # Bark推送示例（iOS）
    # BARK_KEY="YOUR_BARK_KEY"
    # curl -s "https://api.day.app/${BARK_KEY}/${title}/${content}" >> $LOG_FILE 2>&1
}

# ==================== 定时任务安装函数 ====================
setup_cron() {
    echo "正在配置定时任务..."

    # 备份现有crontab
    crontab -l > /tmp/cron_backup 2>/dev/null

    # 检查是否已存在该脚本的定时任务
    if grep -q "$SCRIPT_PATH" /tmp/cron_backup 2>/dev/null; then
        echo "定时任务已存在，跳过安装"
        return
    fi

    # 添加定时任务：
    # 1. 每天11:30第一次运行
    # 2. 之后每隔6小时：11:30, 17:30, 23:30
    # 3. 开机自启动（通过@reboot）

    cat >> /tmp/cron_backup << 'EOF'

# VPS每日自动运行任务（11:30开始，每6小时一次）
30 11 * * * /home/x/fuwu/ikuuu/vps每日自动运行.sh run >> /var/log/vps_daily_run.log 2>&1
30 17 * * * /home/x/fuwu/ikuuu/vps每日自动运行.sh run >> /var/log/vps_daily_run.log 2>&1
30 23 * * * /home/x/fuwu/ikuuu/vps每日自动运行.sh run >> /var/log/vps_daily_run.log 2>&1
@reboot sleep 60 && /home/x/fuwu/ikuuu/vps每日自动运行.sh run >> /var/log/vps_daily_run.log 2>&1
EOF

    # 应用新的crontab
    crontab /tmp/cron_backup
    rm /tmp/cron_backup

    echo "定时任务配置完成！"
    echo "当前定时任务列表："
    crontab -l | grep -A5 "VPS每日"
}

# ==================== systemd服务安装函数 ====================
setup_systemd() {
    echo "正在配置systemd服务..."

    cat > /etc/systemd/system/vps-daily-run.service << 'EOF'
[Unit]
Description=VPS每日自动运行服务
After=network.target

[Service]
Type=simple
ExecStart=/home/x/fuwu/ikuuu/vps每日自动运行.sh run
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

    # 创建定时器（每天11:30）
    cat > /etc/systemd/system/vps-daily-run.timer << 'EOF'
[Unit]
Description=VPS每日自动运行定时器（每天11:30）

[Timer]
OnCalendar=*-*-* 11:30:00
Persistent=true

[Install]
WantedBy=timers.target
EOF

    # 创建定时器（11:30开始，每6小时：11:30, 17:30, 23:30）
    cat > /etc/systemd/system/vps-daily-run-6h.timer << 'EOF'
[Unit]
Description=VPS每日自动运行定时器（每6小时）

[Timer]
OnCalendar=*-*-* 11:30:00
OnCalendar=*-*-* 17:30:00
OnCalendar=*-*-* 23:30:00
Persistent=true

[Install]
WantedBy=timers.target
EOF

    systemctl daemon-reload
    systemctl enable vps-daily-run.service
    systemctl enable vps-daily-run.timer
    systemctl enable vps-daily-run-6h.timer
    systemctl start vps-daily-run.timer
    systemctl start vps-daily-run-6h.timer

    echo "systemd服务配置完成！"
}

# ==================== 帮助信息 ====================
show_help() {
    echo "用法: $0 [命令]"
    echo ""
    echo "命令:"
    echo "  run       - 执行主任务"
    echo "  install   - 安装定时任务（crontab方式）"
    echo "  systemd   - 安装systemd服务（推荐）"
    echo "  uninstall - 卸载定时任务"
    echo "  status    - 查看状态"
    echo "  help      - 显示帮助信息"
    echo ""
    echo "定时任务说明:"
    echo "  - 每天 11:30 第一次运行"
    echo "  - 之后每隔 6 小时运行 (11:30, 17:30, 23:30)"
    echo "  - 每天共 3 次"
    echo "  - 开机自动启动（延迟60秒）"
}

# ==================== 卸载函数 ====================
uninstall() {
    echo "正在卸载定时任务..."

    # 删除crontab中的任务
    crontab -l | grep -v "$SCRIPT_PATH" | crontab -

    # 删除systemd服务
    systemctl disable vps-daily-run.service 2>/dev/null
    systemctl disable vps-daily-run.timer 2>/dev/null
    systemctl disable vps-daily-run-6h.timer 2>/dev/null
    systemctl stop vps-daily-run.timer 2>/dev/null
    systemctl stop vps-daily-run-6h.timer 2>/dev/null
    rm -f /etc/systemd/system/vps-daily-run.service
    rm -f /etc/systemd/system/vps-daily-run.timer
    rm -f /etc/systemd/system/vps-daily-run-6h.timer
    systemctl daemon-reload

    echo "卸载完成！"
}

# ==================== 状态查看函数 ====================
show_status() {
    echo "===== VPS每日自动运行状态 ====="
    echo ""
    echo "--- Crontab任务 ---"
    crontab -l 2>/dev/null | grep -A5 "VPS每日" || echo "无crontab任务"
    echo ""
    echo "--- Systemd服务状态 ---"
    systemctl status vps-daily-run.service 2>/dev/null || echo "systemd服务未安装"
    echo ""
    echo "--- 最近日志 ---"
    tail -20 $LOG_FILE 2>/dev/null || echo "暂无日志"
}

# ==================== 主入口 ====================
case "$1" in
    run)
        main_task
        send_push "VPS任务完成" "任务已于 $(date '+%Y-%m-%d %H:%M:%S') 执行完成"
        ;;
    install)
        setup_cron
        ;;
    systemd)
        setup_systemd
        ;;
    uninstall)
        uninstall
        ;;
    status)
        show_status
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        show_help
        ;;
esac
```

### add_github_secrets.sh

```bash
#!/bin/bash
# GitHub Secrets 添加工具
# 用于自动添加环境变量到 GitHub 仓库
# 用法: ./add_github_secrets.sh <GITHUB_TOKEN> <REPO> <SECRET_NAME> <SECRET_VALUE>

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 检查参数
if [ "$#" -lt 4 ]; then
    echo -e "${YELLOW}用法:${NC}"
    echo "  $0 <GITHUB_TOKEN> <REPO> <SECRET_NAME> <SECRET_VALUE>"
    echo ""
    echo -e "${YELLOW}示例:${NC}"
    echo "  $0 ghp_xxxx pixian5/iku USERNAME myuser"
    echo "  $0 ghp_xxxx pixian5/iku PASSWORD mypass"
    echo ""
    echo -e "${YELLOW}批量添加（从.env文件）:${NC}"
    echo "  $0 ghp_xxxx pixian5/iku --env-file .env"
    echo ""
    echo -e "${YELLOW}Token权限要求:${NC}"
    echo "  需要 repo 和 workflow 权限"
    exit 1
fi

TOKEN="$1"
REPO="$2"

# 检查加密工具
setup_crypto_env() {
    if [ ! -d /tmp/crypto_env ]; then
        echo -e "${YELLOW}正在安装加密工具...${NC}"
        python3 -m venv /tmp/crypto_env
        source /tmp/crypto_env/bin/activate
        pip install pynacl requests -q
        deactivate
    fi
}

# 获取仓库公钥
get_public_key() {
    local response
    response=$(curl -s -H "Authorization: token $TOKEN" \
        -H "Accept: application/vnd.github.v3+json" \
        "https://api.github.com/repos/$REPO/actions/secrets/public-key")

    KEY_ID=$(echo "$response" | python3 -c "import sys,json; print(json.load(sys.stdin)['key_id'])")
    PUBLIC_KEY=$(echo "$response" | python3 -c "import sys,json; print(json.load(sys.stdin)['key'])")

    if [ -z "$KEY_ID" ] || [ -z "$PUBLIC_KEY" ]; then
        echo -e "${RED}错误: 无法获取仓库公钥，请检查Token权限和仓库名${NC}"
        exit 1
    fi
}

# 添加单个Secret
add_secret() {
    local name="$1"
    local value="$2"

    local result
    result=$(/tmp/crypto_env/bin/python3 << EOF
import base64
import requests
from nacl import encoding, public

PUBLIC_KEY = "$PUBLIC_KEY"
KEY_ID = "$KEY_ID"
TOKEN = "$TOKEN"
REPO = "$REPO"
SECRET_NAME = "$name"
SECRET_VALUE = "$value"

def encrypt_secret(public_key_b64, secret_value):
    public_key_bytes = base64.b64decode(public_key_b64)
    public_key = public.PublicKey(public_key_bytes)
    sealed_box = public.SealedBox(public_key)
    encrypted = sealed_box.encrypt(secret_value.encode("utf-8"))
    return base64.b64encode(encrypted).decode("utf-8")

encrypted_value = encrypt_secret(PUBLIC_KEY, SECRET_VALUE)
url = f"https://api.github.com/repos/{REPO}/actions/secrets/{SECRET_NAME}"
headers = {
    "Authorization": f"token {TOKEN}",
    "Accept": "application/vnd.github.v3+json"
}
data = {
    "encrypted_value": encrypted_value,
    "key_id": KEY_ID
}
response = requests.put(url, headers=headers, json=data)
print(response.status_code)
EOF
)

    if [ "$result" = "201" ] || [ "$result" = "204" ]; then
        echo -e "${GREEN}✅ $name 添加成功${NC}"
        return 0
    else
        echo -e "${RED}❌ $name 添加失败 (HTTP $result)${NC}"
        return 1
    fi
}

# 从.env文件批量添加
add_from_env_file() {
    local env_file="$1"

    if [ ! -f "$env_file" ]; then
        echo -e "${RED}错误: 文件 $env_file 不存在${NC}"
        exit 1
    fi

    echo -e "${YELLOW}从 $env_file 批量添加 Secrets...${NC}"
    echo ""

    while IFS='=' read -r name value || [ -n "$name" ]; do
        # 跳过空行和注释
        [ -z "$name" ] && continue
        [[ "$name" =~ ^# ]] && continue

        # 去除前后空格
        name=$(echo "$name" | xargs)
        value=$(echo "$value" | xargs)

        [ -z "$name" ] && continue

        add_secret "$name" "$value"
    done < "$env_file"
}

# 列出现有Secrets
list_secrets() {
    echo -e "${YELLOW}现有 Secrets:${NC}"
    curl -s -H "Authorization: token $TOKEN" \
        -H "Accept: application/vnd.github.v3+json" \
        "https://api.github.com/repos/$REPO/actions/secrets" | \
        python3 -c "import sys,json; d=json.load(sys.stdin); [print(f'  - {s[\"name\"]}') for s in d.get('secrets',[])]"
}

# 主流程
main() {
    setup_crypto_env
    get_public_key

    # 批量模式
    if [ "$3" = "--env-file" ]; then
        add_from_env_file "$4"
        echo ""
        list_secrets
        exit 0
    fi

    # 单个添加模式
    local SECRET_NAME="$3"
    local SECRET_VALUE="$4"

    echo -e "${YELLOW}添加 Secret 到 $REPO...${NC}"
    add_secret "$SECRET_NAME" "$SECRET_VALUE"
    echo ""
    list_secrets
}

main
```

---

## License

MIT
