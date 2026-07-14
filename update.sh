#!/bin/bash

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

DIR="/root/neblock-bot"
SERVICE="neblock-bot"

if [ "$EUID" -ne 0 ]; then 
    echo -e "${RED}Запусти: sudo bash update.sh${NC}"
    exit 1
fi

echo -e "${GREEN}Обновление NeBlock AI${NC}"

echo -e "${YELLOW}Останавливаю бота...${NC}"
systemctl stop $SERVICE
sleep 1

echo -e "${YELLOW}Скачиваю обновления...${NC}"
cd $DIR
git pull origin main

echo -e "${YELLOW}Запускаю бота...${NC}"
systemctl start $SERVICE
sleep 2

if systemctl is-active --quiet $SERVICE; then
    echo -e "${GREEN}Бот обновлён и работает!${NC}"
else
    echo -e "${RED}Ошибка! Логи:${NC}"
    journalctl -u $SERVICE -n 10 --no-pager
fi
