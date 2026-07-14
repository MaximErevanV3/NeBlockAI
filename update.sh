#!/bin/bash

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

DIR="/root/neblock-bot"
SERVICE="neblock-bot"

if [ "$EUID" -ne 0 ]; then 
    echo -e "${RED}❌ Запусти: sudo bash update.sh${NC}"
    exit 1
fi

echo -e "${GREEN}🔄 Обновление NeBlock AI...${NC}"

# Остановка бота
echo -e "${YELLOW}[1/3] Остановка бота...${NC}"
systemctl stop $SERVICE
echo -e "${GREEN}✓ Бот остановлен${NC}"

# Обновление кода
echo -e "${YELLOW}[2/3] Загрузка обновлений...${NC}"
cd "$DIR"
git pull
echo -e "${GREEN}✓ Код обновлён${NC}"

# Обновление зависимостей
echo -e "${YELLOW}[3/3] Обновление пакетов...${NC}"
pip3 install --break-system-packages --upgrade python-telegram-bot openai python-dotenv 2>/dev/null
echo -e "${GREEN}✓ Пакеты обновлены${NC}"

# Запуск
systemctl start $SERVICE
sleep 2

if systemctl is-active --quiet $SERVICE; then
    echo -e "${GREEN}✅ Бот обновлён и запущен!${NC}"
else
    echo -e "${RED}❌ Ошибка запуска${NC}"
    journalctl -u $SERVICE -n 10 --no-pager
fi
