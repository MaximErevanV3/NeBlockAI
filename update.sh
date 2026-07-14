#!/bin/bash

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

DIR="/root/neblock-bot"
SERVICE="neblock-bot"

if [ "$EUID" -ne 0 ]; then 
    echo -e "${RED}Запусти: sudo bash update.sh${NC}"
    exit 1
fi

echo -e "${GREEN}Обновление NeBlock AI...${NC}"

# Остановка
echo -e "${YELLOW}[1/4] Остановка бота...${NC}"
systemctl stop $SERVICE
echo -e "${GREEN}Бот остановлен${NC}"

# Обновление кода
echo -e "${YELLOW}[2/4] Загрузка с GitHub...${NC}"
cd "$DIR"
git pull
echo -e "${GREEN}Код обновлён${NC}"

# Зависимости
echo -e "${YELLOW}[3/4] Обновление пакетов...${NC}"
pip3 install --break-system-packages --upgrade python-telegram-bot openai 2>/dev/null
echo -e "${GREEN}Пакеты обновлены${NC}"

# Запуск
echo -e "${YELLOW}[4/4] Запуск бота...${NC}"
systemctl start $SERVICE
sleep 2

if systemctl is-active --quiet $SERVICE; then
    echo -e "${GREEN}Бот обновлён и работает!${NC}"
else
    echo -e "${RED}Ошибка запуска${NC}"
    journalctl -u $SERVICE -n 10 --no-pager
fi
