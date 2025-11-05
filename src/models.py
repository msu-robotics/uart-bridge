from pydantic import BaseModel, Field
from typing import Literal
from datetime import datetime


class UARTStatus(BaseModel):
    """Модель статуса UART"""
    connected: bool
    port: str
    baudrate: int
    bytesize: int
    stopbits: int
    parity: str


class SystemStatus(BaseModel):
    """Модель статуса системы"""
    uart: UARTStatus
    websocket: dict
    server: dict
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class SendDataRequest(BaseModel):
    """Модель запроса отправки данных в UART"""
    data: str = Field(..., description="Hex строка для отправки (например, '48656c6c6f')")

    class Config:
        json_schema_extra = {
            "example": {
                "data": "48656c6c6f"
            }
        }


class SendDataResponse(BaseModel):
    """Модель ответа на отправку данных"""
    status: Literal["success", "error"]
    bytes_sent: int = 0
    message: str = ""


class InfoMessage(BaseModel):
    """Модель информационного сообщения для WebSocket"""
    type: Literal["info", "error", "warning"]
    message: str
    uartStatus: UARTStatus | None = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ReconnectResponse(BaseModel):
    """Модель ответа на переподключение UART"""
    status: Literal["success", "error"]
    message: str
    uart_status: UARTStatus