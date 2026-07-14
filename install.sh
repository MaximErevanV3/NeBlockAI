#!/bin/bash

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

REPO_URL="https://github.com/MaximErevanV3/NeBlockAI.git"
INSTALL_DIR="/root/neblock-bot"
SERVICE_NAME="neblock-bot"

echo -e "${GREEN}🧠 Neblock AI Installer${NC}"
echo ""

# Проверка root
if [[ $EUID -ne 0 ]]; then
    echo -e "${RED}Запусти от root: sudo bash install.sh${NC}"
    exit 1
fi

# 1. Обновление
echo -e "${YELLOW}[1/6] Обновление системы...${NC}"
apt update -y && apt upgrade -y
echo -e "${GREEN}Готово${NC}"

# 2. Зависимости
echo -e "${YELLOW}[2/6] Установка пакетов...${NC}"
apt install python3 python3-pip git curl -y
echo -e "${GREEN}Готово${NC}"

# 3. Клонирование
echo -e "${YELLOW}[3/6] Загрузка бота с GitHub...${NC}"
if [ -d "$INSTALL_DIR" ]; then
    cd "$INSTALL_DIR"
    git pull
else
    git clone "$REPO_URL" "$INSTALL_DIR"
    cd "$INSTALL_DIR"
fi
echo -e "${GREEN}Готово${NC}"

# 4. Python пакеты
echo -e "${YELLOW}[4/6] Установка Python пакетов...${NC}"
pip3 install python-telegram-bot openai python-dotenv
echo -e "${GREEN}Готово${NC}"

# 5. Конфиг
echo -e "${YELLOW}[5/6] Настройка конфига...${NC}"
cd "$INSTALL_DIR"
if [ -f ".env.example" ]; then
    cp .env.example .env
    echo -e "${GREEN}Конфиг создан${NC}"
else
    cat > .env << 'EOF'
TELEGRAM_TOKEN=8700124191:AAE6qSSouLjlDxPWwoFObJORMbDotsby9co
YANDEX_API_KEY=AQVNy7Dm-dvQRzejHvH0383oHTZhhW2fda95I558
PROMPT_ID=fvt621uiq1fftiu5qomu
EOF
    echo -e "${YELLOW}Создан шаблон .env${NC}"
fi

# 6. Сервис
echo -e "${YELLOW}[6/6] Создание сервиса...${NC}"
cat > "/etc/systemd/system/${SERVICE_NAME}.service" << EOF
[Unit]
Description=Neblock AI Bot
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=$INSTALL_DIR
ExecStart=/usr/bin/python3 $INSTALL_DIR/bot.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable "$SERVICE_NAME"
systemctl start "$SERVICE_NAME"
sleep 2

if systemctl is-active --quiet "$SERVICE_NAME"; then
    echo -e "${GREEN}✅ Бот запущен!${NC}"
else
    echo -e "${RED}❌ Ошибка запуска${NC}"
    journalctl -u "$SERVICE_NAME" -n 10 --no-pager
fi

echo ""
echo -e "${CYAN}Команды:${NC}"
echo -e "  status: ${GREEN}systemctl status $SERVICE_NAME${NC}"
echo -e "  logs:  ${GREEN}journalctl -u $SERVICE_NAME -f${NC}"
echo -e "  restart: ${GREEN}systemctl restart $SERVICE_NAME${NC}"
echo ""
echo -e "${GREEN}Готово! Бот работает 24/7 🚀${NC}"
