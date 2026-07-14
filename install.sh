#!/bin/bash

# ═══════════════════════════════════════════
#     🧠 Neblock AI - Universal Installer
#     Deepseek V4 Flash Telegram Bot
# ═══════════════════════════════════════════

set -e

# Цвета
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
WHITE='\033[1;37m'
BOLD='\033[1m'
NC='\033[0m'

# Конфигурация
REPO_URL="https://github.com/MaximErevanV3/NeBlockAI.git"
INSTALL_DIR="/root/neblock-bot"
SERVICE_NAME="neblock-bot"

# Баннер
banner() {
    clear
    echo -e "${PURPLE}${BOLD}"
    echo "╔══════════════════════════════════════════════╗"
    echo "║                                              ║"
    echo "║         🧠 Neblock AI Installer              ║"
    echo "║         Deepseek V4 Flash Bot               ║"
    echo "║         Universal VPS Setup                 ║"
    echo "║                                              ║"
    echo "╚══════════════════════════════════════════════╝"
    echo -e "${NC}"
}

# Прогресс с анимацией
spinner() {
    local pid=$1
    local delay=0.1
    local spinstr='⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏'
    while [ "$(ps a | awk '{print $1}' | grep $pid)" ]; do
        local temp=${spinstr#?}
        printf " [${CYAN}%c${NC}] " "$spinstr"
        local spinstr=$temp${spinstr%"$temp"}
        sleep $delay
        printf "\b\b\b\b\b\b"
    done
    printf "    \b\b\b\b"
}

# Функция для шагов
step() {
    echo -e "\n${YELLOW}${BOLD}[$1/8]${NC} ${WHITE}$2${NC}"
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
}

# Функция успеха
ok() {
    echo -e "  ${GREEN}✅ $1${NC}"
}

# Функция ошибки
error() {
    echo -e "  ${RED}❌ $1${NC}"
    exit 1
}

# Функция инфо
info() {
    echo -e "  ${BLUE}ℹ️  $1${NC}"
}

# Проверка root
check_root() {
    if [[ $EUID -ne 0 ]]; then
        echo -e "${RED}❌ Запусти от root пользователя!${NC}"
        echo -e "${YELLOW}  sudo bash install.sh${NC}"
        exit 1
    fi
}

# Шаг 1
step1() {
    step "1" "Обновление пакетов системы"
    apt update -y > /dev/null 2>&1 &
    spinner $!
    ok "Репозитории обновлены"
    
    apt upgrade -y > /dev/null 2>&1 &
    spinner $!
    ok "Пакеты обновлены"
}

# Шаг 2
step2() {
    step "2" "Установка необходимых пакетов"
    
    PACKAGES="python3 python3-pip python3-venv git curl wget ufw htop"
    
    for pkg in $PACKAGES; do
        printf "  Установка %-20s" "$pkg..."
        apt install $pkg -y > /dev/null 2>&1 &
        spinner $!
        echo -e "${GREEN}✓${NC}"
    done
    
    ok "Все пакеты установлены"
}

# Шаг 3
step3() {
    step "3" "Клонирование репозитория с GitHub"
    
    if [ -d "$INSTALL_DIR" ]; then
        info "Директория существует, обновляю..."
        cd "$INSTALL_DIR"
        git pull origin main > /dev/null 2>&1 &
        spinner $!
        ok "Репозиторий обновлён"
    else
        info "Клонирую репозиторий..."
        git clone "$REPO_URL" "$INSTALL_DIR" > /dev/null 2>&1 &
        spinner $!
        ok "Репозиторий склонирован"
    fi
    
    cd "$INSTALL_DIR"
    ok "Рабочая директория: $INSTALL_DIR"
}

# Шаг 4
step4() {
    step "4" "Установка Python зависимостей"
    
    cd "$INSTALL_DIR"
    
    info "Обновляю pip..."
    python3 -m pip install --upgrade pip > /dev/null 2>&1 &
    spinner $!
    ok "Pip обновлён"
    
    if [ -f "requirements.txt" ]; then
        info "Устанавливаю из requirements.txt..."
        pip3 install -r requirements.txt > /dev/null 2>&1 &
        spinner $!
        ok "Зависимости из requirements.txt установлены"
    else
        info "requirements.txt не найден, устанавливаю стандартные..."
        pip3 install python-telegram-bot openai python-dotenv > /dev/null 2>&1 &
        spinner $!
        ok "Стандартные зависимости установлены"
    fi
}

# Шаг 5
step5() {
    step "5" "Настройка конфигурации"
    
    cd "$INSTALL_DIR"
    
    if [ ! -f ".env" ]; then
        info "Создаю .env файл..."
        cat > .env << 'EOF'
TELEGRAM_TOKEN=8700124191:AAE6qSSouLjlDxPWwoFObJORMbDotsby9co
YANDEX_API_KEY=AQVNy7Dm-dvQRzejHvH0383oHTZhhW2fda95I558
PROMPT_ID=fvt621uiq1fftiu5qomu
EOF
        ok ".env файл создан с шаблоном"
        info "Отредактируй если нужно: nano $INSTALL_DIR/.env"
    else
        ok ".env файл уже существует"
    fi
    
    # Проверяем токен
    if grep -q "your_token_here" ".env" 2>/dev/null; then
        info "⚠️  Не забудь заменить токен в .env файле!"
    fi
}

# Шаг 6
step6() {
    step "6" "Проверка синтаксиса Python"
    
    cd "$INSTALL_DIR"
    
    # Ищем Python файл
    BOT_FILE=$(ls *.py 2>/dev/null | head -1)
    
    if [ -z "$BOT_FILE" ]; then
        error "Python файл не найден в $INSTALL_DIR"
    fi
    
    info "Найден файл: $BOT_FILE"
    
    # Проверка синтаксиса
    python3 -m py_compile "$BOT_FILE" 2>/dev/null && {
        ok "Синтаксис Python корректен"
    } || {
        error "Ошибка в синтаксисе Python файла"
    }
    
    # Быстрый тестовый запуск
    info "Тестовый запуск на 3 секунды..."
    timeout 5 python3 "$BOT_FILE" > /tmp/neblock-test.log 2>&1 &
    TEST_PID=$!
    sleep 3
    
    if kill -0 $TEST_PID 2>/dev/null; then
        kill $TEST_PID 2>/dev/null
        ok "Бот запускается без ошибок"
    else
        info "⚠️  Бот завершился (проверь .env)"
    fi
}

# Шаг 7
step7() {
    step "7" "Создание systemd сервиса"
    
    cd "$INSTALL_DIR"
    BOT_FILE=$(ls *.py 2>/dev/null | head -1)
    
    cat > "/etc/systemd/system/${SERVICE_NAME}.service" << EOF
[Unit]
Description=Neblock AI Telegram Bot (Deepseek V4 Flash)
Documentation=https://github.com/MaximErevanV3/NeBlockAI
After=network.target network-online.target
Wants=network-online.target

[Service]
Type=simple
User=root
Group=root
WorkingDirectory=$INSTALL_DIR
EnvironmentFile=$INSTALL_DIR/.env
ExecStart=/usr/bin/python3 $INSTALL_DIR/$BOT_FILE
ExecReload=/bin/kill -HUP \$MAINPID
Restart=always
RestartSec=10
KillMode=mixed
KillSignal=SIGTERM
TimeoutStopSec=30

# Оптимизация
LimitNOFILE=65536
LimitNPROC=4096
MemoryMax=512M
CPUQuota=50%

# Логирование
StandardOutput=journal
StandardError=journal
SyslogIdentifier=$SERVICE_NAME

# Безопасность
NoNewPrivileges=yes
PrivateTmp=yes
ProtectSystem=strict
ProtectHome=yes
ReadWritePaths=$INSTALL_DIR

[Install]
WantedBy=multi-user.target
EOF
    
    systemctl daemon-reload &
    spinner $!
    ok "Конфигурация systemd создана"
    
    systemctl enable "$SERVICE_NAME" > /dev/null 2>&1 &
    spinner $!
    ok "Автозапуск включен"
}

# Шаг 8
step8() {
    step "8" "Запуск и проверка бота"
    
    info "Запускаю сервис..."
    systemctl start "$SERVICE_NAME" &
    spinner $!
    
    sleep 2
    
    if systemctl is-active --quiet "$SERVICE_NAME"; then
        ok "Бот успешно запущен и работает!"
    else
        error "Бот не запустился. Проверь логи: journalctl -u $SERVICE_NAME -n 30"
    fi
}

# Показать итоговую информацию
show_summary() {
    IP=$(curl -s ifconfig.me 2>/dev/null || echo "неизвестен")
    UPTIME=$(uptime -p)
    
    echo ""
    echo -e "${PURPLE}${BOLD}"
    echo "╔══════════════════════════════════════════════╗"
    echo "║                                              ║"
    echo "║         🎉 Установка завершена!              ║"
    echo "║         Neblock AI готов к работе            ║"
    echo "║                                              ║"
    echo "╚══════════════════════════════════════════════╝"
    echo -e "${NC}"
    
    echo -e "${WHITE}${BOLD}📊 Информация:${NC}"
    echo -e "  ${CYAN}🌐 IP сервера:${NC}     ${WHITE}$IP${NC}"
    echo -e "  ${CYAN}📁 Директория:${NC}     ${WHITE}$INSTALL_DIR${NC}"
    echo -e "  ${CYAN}🤖 Статус:${NC}         ${GREEN}$(systemctl is-active $SERVICE_NAME)${NC}"
    echo -e "  ${CYAN}⏱️  Аптайм сервера:${NC} ${WHITE}$UPTIME${NC}"
    echo ""
    
    echo -e "${WHITE}${BOLD}📋 Полезные команды:${NC}"
    echo ""
    echo -e "  ${YELLOW}Статус бота:${NC}"
    echo -e "    ${GREEN}systemctl status $SERVICE_NAME${NC}"
    echo ""
    echo -e "  ${YELLOW}Логи в реальном времени:${NC}"
    echo -e "    ${GREEN}journalctl -u $SERVICE_NAME -f${NC}"
    echo ""
    echo -e "  ${YELLOW}Логи за сегодня:${NC}"
    echo -e "    ${GREEN}journalctl -u $SERVICE_NAME --since today${NC}"
    echo ""
    echo -e "  ${YELLOW}Перезапустить бота:${NC}"
    echo -e "    ${GREEN}systemctl restart $SERVICE_NAME${NC}"
    echo ""
    echo -e "  ${YELLOW}Остановить бота:${NC}"
    echo -e "    ${GREEN}systemctl stop $SERVICE_NAME${NC}"
    echo ""
    echo -e "  ${YELLOW}Редактировать конфиг:${NC}"
    echo -e "    ${GREEN}nano $INSTALL_DIR/.env${NC}"
    echo ""
    echo -e "  ${YELLOW}Обновить бота с GitHub:${NC}"
    echo -e "    ${GREEN}cd $INSTALL_DIR && git pull && systemctl restart $SERVICE_NAME${NC}"
    echo ""
    
    echo -e "${PURPLE}${BOLD}Бот работает 24/7! 🚀${NC}"
}

# Главная функция
main() {
    banner
    check_root
    
    echo -e "${BLUE}${BOLD}🚀 Начинаю установку Neblock AI на VPS...${NC}"
    echo -e "${CYAN}   Время начала: $(date '+%Y-%m-%d %H:%M:%S')${NC}"
    echo ""
    
    # Подсчёт времени
    START_TIME=$(date +%s)
    
    step1
    step2
    step3
    step4
    step5
    step6
    step7
    step8
    
    END_TIME=$(date +%s)
    TOTAL_TIME=$((END_TIME - START_TIME))
    
    show_summary
    
    echo -e "${WHITE}⏱️  Время установки: ${TOTAL_TIME} секунд${NC}"
    echo -e "${GREEN}${BOLD}✅ Всё готово! Твой бот в Telegram уже работает!${NC}"
    echo ""
}

# Обработка ошибок
trap 'echo -e "\n${RED}❌ Установка прервана!${NC}"; exit 1' INT TERM

# Запуск
main
