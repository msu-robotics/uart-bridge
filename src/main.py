import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from config import settings, configure_logging
from uart_manager import UARTManager
from websocket_handler import WebSocketManager
from models import (
    SystemStatus,
    SendDataRequest,
    SendDataResponse,
    ReconnectResponse,
    InfoMessage
)

# Настройка логирования
configure_logging()
logger = logging.getLogger(__name__)

# Инициализация менеджеров
uart_manager = UARTManager()
ws_manager = WebSocketManager(uart_manager)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Управление жизненным циклом приложения"""
    # Startup
    logger.info("🚀 Запуск UART WebSocket Bridge")
    logger.info(f"📝 Конфигурация: {settings.model_dump()}")
    uart_manager.connect()

    yield

    # Shutdown
    logger.info("🛑 Остановка UART WebSocket Bridge")
    uart_manager.disconnect()


# Создание приложения
app = FastAPI(
    title="UART WebSocket Bridge API",
    description="API для двусторонней трансляции данных между WebSocket и UART",
    version="1.0.0",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", tags=["Info"])
async def root():
    """Главная страница API"""
    return {
        "name": "UART WebSocket Bridge API",
        "version": "1.0.0",
        "description": "Двусторонняя трансляция данных между WebSocket и UART",
        "endpoints": {
            "websocket": "/ws",
            "status": "/api/status",
            "uart_info": "/api/uart/info",
            "uart_reconnect": "/api/uart/reconnect",
            "uart_send": "/api/uart/send",
            "config": "/api/config",
            "docs": "/docs",
            "redoc": "/redoc"
        }
    }


@app.get("/api/status", response_model=SystemStatus, tags=["Status"])
async def get_status():
    """Получить полный статус системы"""
    return SystemStatus(
        uart=uart_manager.get_status(),
        websocket={
            "active_connections": ws_manager.get_connections_count(),
            "ping_interval": settings.ws_ping_interval,
            "max_message_size": settings.ws_max_size
        },
        server={
            "host": settings.http_host,
            "port": settings.http_port,
            "log_level": settings.log_level
        }
    )


@app.get("/api/uart/info", tags=["UART"])
async def get_uart_info():
    """Получить подробную информацию о UART"""
    status = uart_manager.get_status()
    return {
        **status.model_dump(),
        "timeout": settings.uart_timeout,
        "write_timeout": settings.uart_write_timeout
    }


@app.post("/api/uart/reconnect", response_model=ReconnectResponse, tags=["UART"])
async def reconnect_uart():
    """Переподключить UART порт"""
    logger.info("🔄 Попытка переподключения UART...")

    uart_manager.disconnect()
    success = uart_manager.connect()

    uart_status = uart_manager.get_status()

    if success:
        return ReconnectResponse(
            status="success",
            message="UART успешно переподключен",
            uart_status=uart_status
        )
    else:
        return ReconnectResponse(
            status="error",
            message="Не удалось переподключить UART",
            uart_status=uart_status
        )


@app.post("/api/uart/send", response_model=SendDataResponse, tags=["UART"])
async def send_to_uart(request: SendDataRequest):
    """
    Отправить данные в UART через HTTP

    - **data**: Hex строка (например, "48656c6c6f" для "Hello")
    """
    try:
        # Преобразование hex строки в байты
        bytes_data = bytes.fromhex(request.data)

        # Отправка в UART
        success = uart_manager.write(bytes_data)

        if success:
            return SendDataResponse(
                status="success",
                bytes_sent=len(bytes_data),
                message=f"Отправлено {len(bytes_data)} байт в UART"
            )
        else:
            return SendDataResponse(
                status="error",
                bytes_sent=0,
                message="UART порт не доступен"
            )

    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=f"Неверный hex формат: {str(e)}"
        )
    except Exception as e:
        logger.error(f"❌ Ошибка отправки данных: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Внутренняя ошибка: {str(e)}"
        )


@app.get("/api/config", tags=["Config"])
async def get_config():
    """Получить текущую конфигурацию (без чувствительных данных)"""
    return {
        "http": {
            "host": settings.http_host,
            "port": settings.http_port
        },
        "uart": settings.get_uart_config(),
        "websocket": {
            "ping_interval": settings.ws_ping_interval,
            "max_size": settings.ws_max_size,
            "ping_timeout": settings.ws_ping_timeout
        },
        "logging": {
            "level": settings.log_level
        }
    }


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint для двусторонней связи с UART

    - Принимает бинарные данные от клиента и отправляет в UART
    - Транслирует данные из UART всем подключенным клиентам
    - Отправляет JSON сообщения для информации и статуса
    """
    await ws_manager.connect(websocket)

    try:
        while True:
            # Получение данных от WebSocket клиента
            data = await websocket.receive_bytes()

            logger.debug(f"📨 Получено от WS: {data.hex()} ({len(data)} bytes)")

            # Отправка данных в UART
            if not uart_manager.write(data):
                # Уведомление клиента об ошибке
                error_msg = InfoMessage(
                    type="error",
                    message="Не удалось отправить данные в UART",
                    uartStatus=uart_manager.get_status()
                )
                await ws_manager.send_info(websocket, error_msg)

    except WebSocketDisconnect:
        await ws_manager.disconnect(websocket)
        logger.info("🔌 Клиент нормально отключился")
    except Exception as e:
        logger.error(f"❌ Ошибка WebSocket: {e}")
        await ws_manager.disconnect(websocket)


@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint"""
    uart_connected = uart_manager.is_connected()

    return {
        "status": "healthy" if uart_connected else "degraded",
        "uart_connected": uart_connected,
        "websocket_connections": ws_manager.get_connections_count()
    }


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.http_host,
        port=settings.http_port,
        reload=False,
        log_level=settings.log_level.lower()
    )