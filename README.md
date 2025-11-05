# UART WebSocket Bridge API

![Python](https://img.shields.io/badge/python-3.11+-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)
![License](https://img.shields.io/badge/license-MIT-blue.svg)

**UART WebSocket Bridge API** - это высокопроизводительное решение для двусторонней трансляции данных между WebSocket соединениями и UART портом в реальном времени.

## 📋 Содержание

- [Возможности](#-возможности)
- [Архитектура](#-архитектура)
- [Установка](#-установка)
- [Конфигурация](#-конфигурация)
- [Запуск](#-запуск)
- [API Endpoints](#-api-endpoints)
- [WebSocket Protocol](#-websocket-protocol)
- [Примеры использования](#-примеры-использования)
- [Docker](#-docker)
- [Troubleshooting](#-troubleshooting)
- [Contributing](#-contributing)
- [License](#-license)

## 🚀 Возможности

- ✅ **Двусторонняя трансляция** - данные передаются в обе стороны между WebSocket и UART
- ✅ **Множественные клиенты** - поддержка нескольких одновременных WebSocket соединений
- ✅ **Валидация конфигурации** - использование Pydantic для проверки настроек
- ✅ **REST API** - управление UART и получение статуса через HTTP
- ✅ **Логирование** - детальное логирование всех операций
- ✅ **Автоматическая документация** - Swagger UI и ReDoc
- ✅ **CORS поддержка** - возможность использования из браузера
- ✅ **Health checks** - мониторинг состояния системы
- ✅ **Потокобезопасность** - корректная работа с UART в многопоточной среде

## 🏗 Архитектура

```
┌─────────────────┐
│  WebSocket      │
│  Clients        │
└────────┬────────┘
         │
         ▼
┌─────────────────┐       ┌─────────────────┐
│   FastAPI       │◄─────►│   UART          │
│   WebSocket     │       │   Manager       │
│   Manager       │       │                 │
└─────────────────┘       └────────┬────────┘
         │                         │
         ▼                         ▼
┌─────────────────┐       ┌─────────────────┐
│   Broadcast     │       │   Serial Port   │
│   to all WS     │       │   /dev/ttyUSB0  │
└─────────────────┘       └─────────────────┘
```

### Компоненты:

- **FastAPI** - асинхронный веб-фреймворк
- **WebSocket Manager** - управление WebSocket соединениями
- **UART Manager** - управление serial портом и потоками чтения
- **Pydantic Settings** - валидация и управление конфигурацией
- **PySerial** - взаимодействие с UART портом

## 📦 Установка

### Требования

- Python 3.11+
- pip или poetry
- Доступ к UART порту (права на `/dev/ttyUSB*` или COM порт)

### Установка зависимостей

```bash
# Клонирование репозитория
git clone https://github.com/yourusername/uart-websocket-bridge.git
cd uart-websocket-bridge

# Создание виртуального окружения
python -m venv venv

# Активация виртуального окружения
# Linux/Mac:
source venv/bin/activate
# Windows:
venv\Scripts\activate

# Установка зависимостей
pip install -r requirements.txt
```

### Права доступа к UART (Linux)

```bash
# Добавление пользователя в группу dialout
sudo usermod -a -G dialout $USER

# Перелогиниться или выполнить
newgrp dialout

# Проверка доступных портов
ls -l /dev/ttyUSB* /dev/ttyACM*
```

## ⚙️ Конфигурация

Создайте файл `.env` в корне проекта:

```env
# HTTP сервер
HTTP_HOST=0.0.0.0
HTTP_PORT=8000

# UART конфигурация
UART_PORT=/dev/ttyUSB0          # Linux: /dev/ttyUSB0, Windows: COM3
UART_BAUDRATE=115200
UART_BYTESIZE=8
UART_STOPBITS=1
UART_PARITY=N                   # N=None, E=Even, O=Odd, M=Mark, S=Space
UART_TIMEOUT=1.0
UART_WRITE_TIMEOUT=1.0

# WebSocket
WS_PING_INTERVAL=30
WS_MAX_SIZE=104857600           # 100 MB
WS_PING_TIMEOUT=10

# Логирование
LOG_LEVEL=INFO                  # DEBUG, INFO, WARNING, ERROR, CRITICAL
```

### Параметры UART

| Параметр | Описание | Возможные значения |
|----------|----------|-------------------|
| `UART_PORT` | Путь к устройству | `/dev/ttyUSB0`, `COM3` |
| `UART_BAUDRATE` | Скорость передачи | 9600, 115200, 921600 и др. |
| `UART_BYTESIZE` | Размер байта | 5, 6, 7, 8 |
| `UART_STOPBITS` | Стоп-биты | 1, 2 |
| `UART_PARITY` | Четность | N, E, O, M, S |

### Стандартные baudrate значения:
- 300, 600, 1200, 2400, 4800, 9600
- 14400, 19200, 28800, 38400, 57600
- 115200, 230400, 460800, 921600

## 🚀 Запуск

### Стандартный запуск

```bash
python main.py
```

### Запуск через Uvicorn с автоперезагрузкой

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### Запуск в production режиме

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Проверка запуска

```bash
curl http://localhost:8000/health
```

Ожидаемый ответ:
```json
{
  "status": "healthy",
  "uart_connected": true,
  "websocket_connections": 0
}
```

## 📡 API Endpoints

### REST API

| Метод | Endpoint | Описание |
|-------|----------|----------|
| `GET` | `/` | Информация об API |
| `GET` | `/api/status` | Полный статус системы |
| `GET` | `/api/uart/info` | Информация о UART |
| `POST` | `/api/uart/reconnect` | Переподключить UART |
| `POST` | `/api/uart/send` | Отправить данные в UART |
| `GET` | `/api/config` | Текущая конфигурация |
| `GET` | `/health` | Health check |
| `GET` | `/docs` | Swagger UI документация |
| `GET` | `/redoc` | ReDoc документация |

### WebSocket

| Endpoint | Протокол | Описание |
|----------|----------|----------|
| `/ws` | WebSocket | Двусторонняя трансляция с UART |

## 🔌 WebSocket Protocol

### Подключение

```javascript
const ws = new WebSocket('ws://localhost:8000/ws');
```

### Формат сообщений

#### От сервера к клиенту

**Информационные сообщения** (JSON):
```json
{
  "type": "info",
  "message": "Connected to UART WebSocket Bridge",
  "uartStatus": {
    "connected": true,
    "port": "/dev/ttyUSB0",
    "baudrate": 115200,
    "bytesize": 8,
    "stopbits": 1,
    "parity": "N"
  },
  "timestamp": "2024-01-20T12:00:00.000Z"
}
```

**Данные из UART** (Binary):
- Формат: бинарные данные (ArrayBuffer/Blob)
- Данные отправляются как есть без изменений

#### От клиента к серверу

**Отправка данных в UART** (Binary):
```javascript
// Отправка бинарных данных
const data = new Uint8Array([0x48, 0x65, 0x6C, 0x6C, 0x6F]); // "Hello"
ws.send(data.buffer);
```

### Типы сообщений

| Тип | Формат | Направление | Описание |
|-----|--------|-------------|----------|
| `info` | JSON | Server → Client | Информационное сообщение |
| `error` | JSON | Server → Client | Сообщение об ошибке |
| `warning` | JSON | Server → Client | Предупреждение |
| Binary | Bytes | Bidirectional | Данные UART |

## 💡 Примеры использования

### Python Client

```python
import asyncio
import websockets
import json


async def uart_client():
    uri = "ws://localhost:8000/ws"
    
    async with websockets.connect(uri) as websocket:
        print("✅ Connected")
        
        # Отправка hex данных
        data = bytes.fromhex("48656c6c6f")  # "Hello"
        await websocket.send(data)
        print(f"📤 Sent: {data.hex()}")
        
        # Прием данных
        async for message in websocket:
            if isinstance(message, bytes):
                print(f"📥 Received: {message.hex()}")
            else:
                info = json.loads(message)
                print(f"ℹ️ Info: {info['message']}")


asyncio.run(uart_client())
```

### JavaScript Client (Browser)

```html
<!DOCTYPE html>
<html>
<head>
    <title>UART WebSocket Client</title>
</head>
<body>
    <h1>UART WebSocket Bridge</h1>
    
    <div>
        <button onclick="connect()">Connect</button>
        <button onclick="disconnect()">Disconnect</button>
    </div>
    
    <div>
        <input type="text" id="hexInput" placeholder="Hex (e.g., 48656c6c6f)">
        <button onclick="sendHex()">Send</button>
    </div>
    
    <div>
        <h3>Log:</h3>
        <pre id="log" style="background: #f0f0f0; padding: 10px;"></pre>
    </div>

    <script>
        let ws = null;

        function connect() {
            ws = new WebSocket('ws://localhost:8000/ws');
            
            ws.onopen = () => {
                log('✅ Connected');
            };
            
            ws.onmessage = async (event) => {
                if (event.data instanceof Blob) {
                    const buffer = await event.data.arrayBuffer();
                    const hex = Array.from(new Uint8Array(buffer))
                        .map(b => b.toString(16).padStart(2, '0'))
                        .join(' ');
                    log(`📥 UART: ${hex}`);
                } else {
                    const data = JSON.parse(event.data);
                    log(`ℹ️ ${data.message}`);
                }
            };
            
            ws.onerror = (error) => {
                log(`❌ Error: ${error}`);
            };
            
            ws.onclose = () => {
                log('🔌 Disconnected');
            };
        }

        function disconnect() {
            if (ws) {
                ws.close();
                ws = null;
            }
        }

        function sendHex() {
            const input = document.getElementById('hexInput').value;
            
            try {
                const bytes = new Uint8Array(
                    input.match(/.{1,2}/g).map(byte => parseInt(byte, 16))
                );
                
                if (ws && ws.readyState === WebSocket.OPEN) {
                    ws.send(bytes.buffer);
                    log(`📤 Sent: ${input}`);
                } else {
                    log('❌ Not connected');
                }
            } catch (e) {
                log(`❌ Invalid hex: ${e.message}`);
            }
        }

        function log(message) {
            const logDiv = document.getElementById('log');
            const timestamp = new Date().toISOString();
            logDiv.textContent += `[${timestamp}] ${message}\n`;
            logDiv.scrollTop = logDiv.scrollHeight;
        }
    </script>
</body>
</html>
```

### cURL примеры

```bash
# Получить статус
curl http://localhost:8000/api/status

# Получить информацию о UART
curl http://localhost:8000/api/uart/info

# Отправить данные в UART через HTTP
curl -X POST http://localhost:8000/api/uart/send \
  -H "Content-Type: application/json" \
  -d '{"data": "48656c6c6f"}'

# Переподключить UART
curl -X POST http://localhost:8000/api/uart/reconnect

# Health check
curl http://localhost:8000/health
```

### Node.js Client

```javascript
const WebSocket = require('ws');

const ws = new WebSocket('ws://localhost:8000/ws');

ws.on('open', () => {
    console.log('✅ Connected');
    
    // Отправка hex данных
    const data = Buffer.from('48656c6c6f', 'hex');
    ws.send(data);
    console.log(`📤 Sent: ${data.toString('hex')}`);
});

ws.on('message', (data) => {
    if (Buffer.isBuffer(data)) {
        console.log(`📥 UART: ${data.toString('hex')}`);
    } else {
        const info = JSON.parse(data);
        console.log(`ℹ️ ${info.message}`);
    }
});

ws.on('error', (error) => {
    console.error('❌ Error:', error);
});

ws.on('close', () => {
    console.log('🔌 Disconnected');
});
```

## 🐳 Docker

### docker-compose.yml

```yaml
version: '3.8'

services:
  uart-bridge:
    build: .
    container_name: uart-websocket-bridge
    ports:
      - "8000:8000"
    devices:
      - "/dev/ttyUSB0:/dev/ttyUSB0"  # Пробросить UART устройство
    environment:
      - HTTP_HOST=0.0.0.0
      - HTTP_PORT=8000
      - UART_PORT=/dev/ttyUSB0
      - UART_BAUDRATE=115200
      - LOG_LEVEL=INFO
    restart: unless-stopped
    privileged: true  # Необходимо для доступа к устройствам
```

### Запуск через Docker

```bash
# Сборка образа
docker build -t uart-websocket-bridge .

# Запуск контейнера
docker run -d \
  --name uart-bridge \
  --device=/dev/ttyUSB0 \
  -p 8000:8000 \
  -e UART_PORT=/dev/ttyUSB0 \
  -e UART_BAUDRATE=115200 \
  uart-websocket-bridge

# Через docker-compose
docker-compose up -d

# Просмотр логов
docker logs -f uart-bridge
```

## 🔧 Troubleshooting

### UART порт не открывается

**Проблема**: `Permission denied` при доступе к `/dev/ttyUSB0`

**Решение**:
```bash
# Проверить права
ls -l /dev/ttyUSB0

# Добавить пользователя в группу
sudo usermod -a -G dialout $USER

# Перелогиниться или
newgrp dialout
```

### Порт уже используется

**Проблема**: `UART port already in use`

**Решение**:
```bash
# Найти процесс использующий порт
lsof /dev/ttyUSB0

# Или
fuser /dev/ttyUSB0

# Убить процесс
sudo kill -9 <PID>
```

### WebSocket соединение разрывается

**Проблема**: WebSocket соединение нестабильно

**Решение**:
- Проверить `WS_PING_INTERVAL` в `.env`
- Увеличить `WS_PING_TIMEOUT`
- Проверить firewall настройки
- Проверить прокси сервер (если используется)

### Данные не передаются

**Проблема**: Данные не доходят до UART

**Решение**:
```bash
# Проверить статус UART
curl http://localhost:8000/api/uart/info

# Проверить логи
# В коде установить LOG_LEVEL=DEBUG

# Проверить UART с помощью minicom
minicom -D /dev/ttyUSB0 -b 115200
```

### Неверный baudrate

**Проблема**: Неверная скорость передачи

**Решение**:
- Проверить настройки устройства
- Попробовать стандартные значения: 9600, 115200
- Использовать команду `stty` для проверки:
```bash
stty -F /dev/ttyUSB0
```

## 📊 Мониторинг

### Prometheus метрики (расширение)

Можно добавить prometheus-fastapi-instrumentator:

```bash
pip install prometheus-fastapi-instrumentator
```

```python
from prometheus_fastapi_instrumentator import Instrumentator

# В main.py
Instrumentator().instrument(app).expose(app)
```

### Логирование

Логи можно направить в файл:

```python
# В config.py
import logging.handlers

handler = logging.handlers.RotatingFileHandler(
    'uart_bridge.log',
    maxBytes=10485760,  # 10MB
    backupCount=5
)
logging.basicConfig(handlers=[handler])
```

## 🧪 Тестирование

```bash
# Установка pytest
pip install pytest pytest-asyncio httpx

# Запуск тестов
pytest tests/

# С покрытием
pytest --cov=. tests/
```

## 🤝 Contributing

Мы приветствуем вклад в проект!

1. Fork репозитория
2. Создайте feature branch (`git checkout -b feature/amazing-feature`)
3. Commit изменения (`git commit -m 'Add amazing feature'`)
4. Push в branch (`git push origin feature/amazing-feature`)
5. Откройте Pull Request

### Стиль кода

- Используйте `black` для форматирования
- Следуйте PEP 8
- Добавляйте type hints
- Пишите docstrings

```bash
# Форматирование кода
black .

# Проверка линтером
flake8 .

# Type checking
mypy .
```

## 📝 License

Этот проект распространяется под лицензией MIT. См. файл `LICENSE` для деталей.

## 🙏 Благодарности

- [FastAPI](https://fastapi.tiangolo.com/) - современный веб-фреймворк
- [Pydantic](https://pydantic-docs.helpmanual.io/) - валидация данных
- [PySerial](https://pythonhosted.org/pyserial/) - работа с serial портами
- [Uvicorn](https://www.uvicorn.org/) - ASGI сервер

---

**Made with ❤️ using Python & FastAPI**