import asyncio
import logging
from fastapi import WebSocket, WebSocketDisconnect
from typing import Set
from models import InfoMessage

logger = logging.getLogger(__name__)


class WebSocketManager:
    """Менеджер для работы с WebSocket соединениями"""

    def __init__(self, uart_manager):
        self.active_connections: Set[WebSocket] = set()
        self.uart_manager = uart_manager
        self.uart_manager.set_data_callback(self.broadcast_uart_data)
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket):
        """Подключить WebSocket клиента"""
        await websocket.accept()

        async with self._lock:
            self.active_connections.add(websocket)

        client_host = websocket.client.host if websocket.client else "unknown"
        client_port = websocket.client.port if websocket.client else "unknown"
        logger.info(f"🔗 Новое WebSocket соединение: {client_host}:{client_port}")

        # Отправка приветственного сообщения
        info_message = InfoMessage(
            type="info",
            message="Connected to UART WebSocket Bridge",
            uartStatus=self.uart_manager.get_status()
        )

        await self.send_info(websocket, info_message)

    async def disconnect(self, websocket: WebSocket):
        """Отключить WebSocket клиента"""
        async with self._lock:
            self.active_connections.discard(websocket)

        client_host = websocket.client.host if websocket.client else "unknown"
        client_port = websocket.client.port if websocket.client else "unknown"
        logger.info(f"🔌 WebSocket отключен: {client_host}:{client_port}")

    async def send_personal_message(self, message: bytes, websocket: WebSocket):
        """Отправить бинарное сообщение конкретному клиенту"""
        try:
            await websocket.send_bytes(message)
        except Exception as e:
            logger.error(f"❌ Ошибка отправки сообщения: {e}")

    async def send_info(self, websocket: WebSocket, info: InfoMessage):
        """Отправить JSON информацию"""
        try:
            await websocket.send_text(info.model_dump_json())
        except Exception as e:
            logger.error(f"❌ Ошибка отправки JSON: {e}")

    async def broadcast(self, message: bytes):
        """Отправить сообщение всем подключенным клиентам"""
        disconnected = set()

        async with self._lock:
            connections = self.active_connections.copy()

        for connection in connections:
            try:
                await connection.send_bytes(message)
            except WebSocketDisconnect:
                logger.debug("Клиент отключился во время broadcast")
                disconnected.add(connection)
            except Exception as e:
                logger.error(f"❌ Ошибка broadcast: {e}")
                disconnected.add(connection)

        # Удаление отключенных клиентов
        if disconnected:
            async with self._lock:
                for connection in disconnected:
                    self.active_connections.discard(connection)

    def broadcast_uart_data(self, data: bytes):
        """Callback для трансляции данных из UART (вызывается из другого потока)"""
        try:
            # Создаем задачу в event loop
            asyncio.run_coroutine_threadsafe(
                self.broadcast(data),
                asyncio.get_event_loop()
            )
        except Exception as e:
            logger.error(f"❌ Ошибка создания задачи broadcast: {e}")

    def get_connections_count(self) -> int:
        """Получить количество активных соединений"""
        return len(self.active_connections)