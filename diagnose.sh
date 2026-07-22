#!/bin/bash

# ═══════════════════════════════════════════
# 🩺 NeBlock AI - Диагностика и ремонт
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

# 1. Статус сервиса
echo -e "${YELLOW}1. Статус сервиса:${NC}"
if systemctl is-active --quiet $SERVICE; then
    echo -e "${GREEN}✓ Сервис активен${NC}"
else
    echo -e "${RED}✗ Сервис не активен${NC}"
fi
echo ""

# 2. Последние ошибки
echo -e "${YELLOW}2. Последние логи:${NC}"
journalctl -u $SERVICE -n 15 --no-pager 2>/dev/null || echo "Логов нет"
echo ""

# 3. Проверка файла
echo -e "${YELLOW}3. Проверка bot.py:${NC}"
if [ -f "$DIR/bot.py" ]; then
    echo -e "${GREEN}✓ Файл существует${NC}"
    python3 -c "import py_compile; py_compile.compile('$DIR/bot.py', doraise=True)" 2>&1 && echo -e "${GREEN}✓ Синтаксис OK${NC}" || echo -e "${RED}❌ Ошибка синтаксиса${NC}"
else
    echo -e "${RED}❌ Файл не найден${NC}"
fi
echo ""

# 4. Проверка интернета
echo -e "${YELLOW}4. Проверка соединения:${NC}"
curl -s -o /dev/null -w "%{http_code}" https://api.telegram.org/bot$TELEGRAM_TOKEN/getMe 2>/dev/null | grep -q "200" && echo -e "${GREEN}✓ Telegram API OK${NC}" || echo -e "${RED}✗ Telegram API недоступен${NC}"
echo ""

# 5. Автоматическое исправление
echo -e "${YELLOW}5. Автоисправление:${NC}"
systemctl stop $SERVICE 2>/dev/null

# Обновление кода
if [ -d "$DIR" ]; then
    cd "$DIR"
    git pull 2>/dev/null && echo -e "${GREEN}✓ Код обновлён${NC}" || echo -e "${YELLOW}⚠ Не удалось обновить код${NC}"
fi

# Обновление пакетов
pip3 install --break-system-packages --upgrade python-telegram-bot openai python-dotenv 2>/dev/null || pip3 install --upgrade python-telegram-bot openai python-dotenv 2>/dev/null
echo -e "${GREEN}✓ Пакеты обновлены${NC}"

# Обновление сервиса
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
    echo -e "${GREEN}✅ Бот запущен и работает!${NC}"
else
    echo -e "${RED}❌ Всё ещё ошибка. Логи:${NC}"
    journalctl -u $SERVICE -n 20 --no-pager
fi
