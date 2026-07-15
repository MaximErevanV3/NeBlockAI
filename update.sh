#!/bin/bash

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

SERVICE="neblock-bot"
DIR="/root/neblock-bot"

if [ "$EUID" -ne 0 ]; then 
    echo -e "${RED}Запусти: sudo bash update.sh${NC}"
    exit 1
fi

echo -e "${GREEN}🔄 Обновление NeBlock AI...${NC}"

# Остановка
echo -e "${YELLOW}[1/3] Остановка бота...${NC}"
systemctl stop $SERVICE 2>/dev/null
echo -e "${GREEN}✓ Бот остановлен${NC}"

# Скачивание
echo -e "${YELLOW}[2/3] Загрузка обновлений с GitHub...${NC}"
if [ -d "$DIR" ]; then
    cd "$DIR"
    git fetch --all
    git reset --hard origin/main
    echo -e "${GREEN}✓ Код обновлён${NC}"
else
    git clone https://github.com/MaximErevanV3/NeBlockAI.git "$DIR"
    cd "$DIR"
    echo -e "${GREEN}✓ Репозиторий склонирован${NC}"
fi

# Запуск
echo -e "${YELLOW}[3/3] Запуск бота...${NC}"
systemctl start $SERVICE
sleep 2

if systemctl is-active --quiet $SERVICE; then
    echo -e "${GREEN}✅ Бот обновлён и работает!${NC}"
else
    echo -e "${RED}❌ Ошибка запуска!${NC}"
    echo -e "${YELLOW}Логи:${NC}"
    journalctl -u $SERVICE -n 15 --no-pager
fi
