#!/bin/bash

# Цвета
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Конфиг
REPO="https://github.com/MaximErevanV3/NeBlockAI.git"
DIR="/root/neblock-bot"
SERVICE="neblock-bot"

# Проверка root
if [ "$EUID" -ne 0 ]; then 
    echo -e "${RED}❌ Запусти: sudo bash install.sh${NC}"
    exit 1
fi

clear
echo -e "${GREEN}"
echo "╔══════════════════════════════╗"
echo "║   🧠 Neblock AI Installer   ║"
echo "╚══════════════════════════════╝"
echo -e "${NC}"

# Шаг 1: Система
echo -e "${YELLOW}[1/5] Система...${NC}"
apt update -y > /dev/null 2>&1
apt install python3 python3-pip git curl -y > /dev/null 2>&1
echo -e "${GREEN}✓ Готово${NC}"

# Шаг 2: Клонирование
echo -e "${YELLOW}[2/5] Загрузка бота...${NC}"
if [ -d "$DIR" ]; then
    cd "$DIR"
    git pull > /dev/null 2>&1
else
    git clone "$REPO" "$DIR" > /dev/null 2>&1
fi
cd "$DIR"
echo -e "${GREEN}✓ Готово${NC}"

# Шаг 3: Зависимости
echo -e "${YELLOW}[3/5] Зависимости Python...${NC}"
pip3 install --break-system-packages python-telegram-bot openai python-dotenv > /dev/null 2>&1
echo -e "${GREEN}✓ Готово${NC}"

# Шаг 4: Конфиг
echo -e "${YELLOW}[4/5] Конфигурация...${NC}"
if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        cp .env.example .env
    else
        cat > .env << 'EOF'
TELEGRAM_TOKEN=8700124191:AAE6qSSouLjlDxPWwoFObJORMbDotsby9co
YANDEX_API_KEY=AQVNy7Dm-dvQRzejHvH0383oHTZhhW2fda95I558
PROMPT_ID=fvt621uiq1fftiu5qomu
EOF
    fi
fi
echo -e "${GREEN}✓ Готово${NC}"

# Шаг 5: Сервис и запуск
echo -e "${YELLOW}[5/5] Запуск бота...${NC}"

# Останавливаем старый если есть
systemctl stop $SERVICE 2>/dev/null

cat > /etc/systemd/system/${SERVICE}.service << EOF
[Unit]
Description=Neblock AI Telegram Bot
After=network.target
[Service]
Type=simple
WorkingDirectory=$DIR
ExecStart=/usr/bin/python3 $DIR/bot.py
Restart=always
RestartSec=5
[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable $SERVICE > /dev/null 2>&1
systemctl start $SERVICE

sleep 2

if systemctl is-active --quiet $SERVICE; then
    echo -e "${GREEN}✓ Бот запущен${NC}"
else
    echo -e "${RED}✗ Ошибка запуска${NC}"
    echo ""
    echo -e "${YELLOW}Логи:${NC}"
    journalctl -u $SERVICE -n 10 --no-pager
    exit 1
fi

# Финал
echo ""
echo -e "${GREEN}╔══════════════════════════════╗${NC}"
echo -e "${GREEN}║     ✅ Установка завершена   ║${NC}"
echo -e "${GREEN}╚══════════════════════════════╝${NC}"
echo ""
echo -e "📋 Команды:"
echo -e "  Статус:    ${YELLOW}systemctl status $SERVICE${NC}"
echo -e "  Логи:      ${YELLOW}journalctl -u $SERVICE -f${NC}"
echo -e "  Перезапуск: ${YELLOW}systemctl restart $SERVICE${NC}"
echo -e "  Конфиг:    ${YELLOW}nano $DIR/.env${NC}"
echo ""
echo -e "${GREEN}🚀 Бот работает 24/7!${NC}"
