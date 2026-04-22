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
    crontab -l | grep -A3 "VPS每日"
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
    crontab -l 2>/dev/null | grep -A3 "VPS每日" || echo "无crontab任务"
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
