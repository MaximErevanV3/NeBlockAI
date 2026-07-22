#!/bin/bash

# ═══════════════════════════════════════════
# 🔄 NeBlock AI - Обновление
# ═══════════════════════════════════════════

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
NC='\033[0m'

DIR="/root/neblock-bot"
SERVICE="neblock-bot"

if [ "$EUID" -ne 0 ]; then 
    echo -e "${RED}Запусти: sudo bash update.sh${NC}"
    exit 1
fi

echo -e "${CYAN}"
echo "╔══════════════════════════════════════╗"
echo "║     🔄 NeBlock AI - Обновление      ║"
echo "╚══════════════════════════════════════╝"
echo -e "${NC}"

# 1. Остановка
echo -e "${YELLOW}[1/4] Остановка бота...${NC}"
systemctl stop $SERVICE
sleep 2
echo -e "${GREEN}✓ Бот остановлен${NC}"

# 2. Обновление кода
echo -e "${YELLOW}[2/4] Загрузка обновлений...${NC}"
if [ -d "$DIR" ]; then
    cd "$DIR"
    git fetch --all
    git reset --hard origin/main
    echo -e "${GREEN}✓ Код обновлён${NC}"
else
    echo -e "${RED}❌ Директория не найдена. Запусти install.sh${NC}"
    exit 1
fi

# 3. Обновление пакетов
echo -e "${YELLOW}[3/4] Обновление зависимостей...${NC}"
pip3 install --break-system-packages --upgrade python-telegram-bot openai python-dotenv 2>/dev/null || pip3 install --upgrade python-telegram-bot openai python-dotenv
echo -e "${GREEN}✓ Зависимости обновлены${NC}"

# 4. Проверка синтаксиса и запуск
echo -e "${YELLOW}[4/4] Проверка и запуск...${NC}"
python3 -m py_compile "$DIR/bot.py" 2>/dev/null
if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Ошибка синтаксиса в bot.py!${NC}"
    python3 -m py_compile "$DIR/bot.py"
    exit 1
fi
echo -e "${GREEN}✓ Синтаксис OK${NC}"

# Обновляем сервис (на случай изменений)
cat > /etc/systemd/system/${SERVICE}.service << EOF
[Unit]
Description=NeBlock AI Telegram Bot
After=network.target
Wants=network-online.target

[Service]
Type=simple
User=root
WorkingDirectory=$DIR
ExecStart=/usr/bin/python3 $DIR/bot.py
Restart=always
RestartSec=5
StartLimitInterval=0
StartLimitBurst=0
KillMode=process
TimeoutStopSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl start $SERVICE
sleep 3

if systemctl is-active --quiet $SERVICE; then
    echo -e "${GREEN}✅ Бот обновлён и работает!${NC}"
else
    echo -e "${RED}❌ Ошибка запуска! Логи:${NC}"
    journalctl -u $SERVICE -n 20 --no-pager
fi

echo ""
echo -e "${CYAN}Логи: ${GREEN}journalctl -u $SERVICE -f${NC}"
