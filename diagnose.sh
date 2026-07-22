#!/bin/bash

# ═══════════════════════════════════════════
# 🩺 NeBlock AI - Диагностика
# ═══════════════════════════════════════════

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
NC='\033[0m'

SERVICE="neblock-bot"
DIR="/root/neblock-bot"

echo -e "${CYAN}🔍 Диагностика NeBlock AI${NC}"
echo ""

# Проверка статуса
echo -e "${YELLOW}Статус сервиса:${NC}"
systemctl status $SERVICE --no-pager -l 2>/dev/null || echo "Сервис не найден"
echo ""

# Последние ошибки
echo -e "${YELLOW}Последние ошибки:${NC}"
journalctl -u $SERVICE -n 10 --no-pager 2>/dev/null || echo "Логов нет"
echo ""

# Проверка файла
echo -e "${YELLOW}Проверка bot.py:${NC}"
if [ -f "$DIR/bot.py" ]; then
    echo -e "${GREEN}✓ Файл bot.py существует${NC}"
    python3 -m py_compile "$DIR/bot.py" 2>&1 && echo -e "${GREEN}✓ Синтаксис OK${NC}" || echo -e "${RED}❌ Ошибка синтаксиса${NC}"
else
    echo -e "${RED}❌ Файл bot.py не найден в $DIR${NC}"
fi
echo ""

# Проверка интернета
echo -e "${YELLOW}Проверка интернета:${NC}"
ping -c 1 api.telegram.org > /dev/null 2>&1 && echo -e "${GREEN}✓ Telegram API доступен${NC}" || echo -e "${RED}❌ Telegram API недоступен${NC}"
ping -c 1 api.cloud.yandex.net > /dev/null 2>&1 && echo -e "${GREEN}✓ Yandex Cloud доступен${NC}" || echo -e "${RED}❌ Yandex Cloud недоступен${NC}"
echo ""

# Исправление
echo -e "${YELLOW}Попытка исправления:${NC}"
systemctl stop $SERVICE 2>/dev/null
cd "$DIR" 2>/dev/null && git pull 2>/dev/null
pip3 install --break-system-packages --upgrade python-telegram-bot openai 2>/dev/null || pip3 install --upgrade python-telegram-bot openai 2>/dev/null
systemctl start $SERVICE 2>/dev/null
sleep 3
systemctl is-active --quiet $SERVICE && echo -e "${GREEN}✅ Бот запущен!${NC}" || echo -e "${RED}❌ Всё ещё ошибка${NC}"
