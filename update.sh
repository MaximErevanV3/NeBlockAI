#!/bin/bash

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
NC='\033[0m'

SERVICE="neblock-bot"
DIR="/root/neblock-bot"

if [ "$EUID" -ne 0 ]; then 
    echo -e "${RED}Запусти: sudo bash update.sh${NC}"
    exit 1
fi

echo -e "${CYAN}"
echo "╔══════════════════════════════════╗"
echo "║   🧠 NeBlock AI V2 Updater      ║"
echo "╚══════════════════════════════════╝"
echo -e "${NC}"

# Остановка
echo -e "${YELLOW}[1/3] Остановка бота...${NC}"
systemctl stop $SERVICE 2>/dev/null
sleep 1
echo -e "${GREEN}✓ Бот остановлен${NC}"

# Обновление из GitHub
echo -e "${YELLOW}[2/3] Загрузка обновлений V2...${NC}"
if [ -d "$DIR" ]; then
    cd "$DIR"
    git fetch --all 2>/dev/null
    git reset --hard origin/main 2>/dev/null
    echo -e "${GREEN}✓ Код обновлён до V2${NC}"
else
    echo -e "${RED}❌ Директория не найдена. Установи бота через install.sh${NC}"
    exit 1
fi

# Права на файлы
chmod +x "$DIR"/*.sh 2>/dev/null

# Запуск
echo -e "${YELLOW}[3/3] Запуск бота...${NC}"
systemctl start $SERVICE
sleep 2

if systemctl is-active --quiet $SERVICE; then
    echo -e "${GREEN}✅ NeBlock AI V2 обновлён и работает!${NC}"
else
    echo -e "${RED}❌ Ошибка запуска! Смотри логи:${NC}"
    journalctl -u $SERVICE -n 15 --no-pager
fi

echo ""
echo -e "${CYAN}Команды:${NC}"
echo -e "  Статус:    ${GREEN}systemctl status $SERVICE${NC}"
echo -e "  Логи:      ${GREEN}journalctl -u $SERVICE -f${NC}"
echo -e "  Перезапуск: ${GREEN}systemctl restart $SERVICE${NC}"
