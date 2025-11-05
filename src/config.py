from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Literal
import logging


class Settings(BaseSettings):
    """Конфигурация приложения с использованием Pydantic Settings"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    # HTTP Server настройки
    http_host: str = Field(
        default="0.0.0.0",
        description="HTTP сервер хост"
    )
    http_port: int = Field(
        default=8000,
        ge=1,
        le=65535,
        description="HTTP сервер порт"
    )

    # UART настройки
    uart_port: str = Field(
        default="/dev/ttyUSB0",
        description="UART порт (например, /dev/ttyUSB0 или COM3)"
    )
    uart_baudrate: int = Field(
        default=115200,
        description="Скорость передачи данных (бит/с)"
    )
    uart_bytesize: Literal[5, 6, 7, 8] = Field(
        default=8,
        description="Размер байта данных"
    )
    uart_stopbits: Literal[1, 2] = Field(
        default=1,
        description="Количество стоп-битов"
    )
    uart_parity: Literal['N', 'E', 'O', 'M', 'S'] = Field(
        default='N',
        description="Четность (N=None, E=Even, O=Odd, M=Mark, S=Space)"
    )
    uart_timeout: float = Field(
        default=1.0,
        ge=0,
        description="Таймаут чтения (секунды)"
    )
    uart_write_timeout: float = Field(
        default=1.0,
        ge=0,
        description="Таймаут записи (секунды)"
    )

    # WebSocket настройки
    ws_ping_interval: int = Field(
        default=30,
        ge=1,
        description="Интервал ping для WebSocket (секунды)"
    )
    ws_max_size: int = Field(
        default=104857600,  # 100 MB
        ge=1024,
        description="Максимальный размер сообщения WebSocket (байты)"
    )
    ws_ping_timeout: int = Field(
        default=10,
        ge=1,
        description="Таймаут ожидания pong (секунды)"
    )

    # Логирование
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="INFO",
        description="Уровень логирования"
    )

    @field_validator('uart_port')
    @classmethod
    def validate_uart_port(cls, v: str) -> str:
        """Валидация UART порта"""
        if not v:
            raise ValueError("UART порт не может быть пустым")
        return v

    @field_validator('uart_baudrate')
    @classmethod
    def validate_baudrate(cls, v: int) -> int:
        """Валидация скорости передачи"""
        valid_baudrates = [
            300, 600, 1200, 2400, 4800, 9600, 14400, 19200,
            28800, 38400, 57600, 115200, 230400, 460800, 921600
        ]
        if v not in valid_baudrates:
            logging.warning(
                f"Нестандартная скорость передачи: {v}. "
                f"Рекомендуемые значения: {valid_baudrates}"
            )
        return v

    def get_uart_config(self) -> dict:
        """Получить конфигурацию UART в виде словаря"""
        return {
            "port": self.uart_port,
            "baudrate": self.uart_baudrate,
            "bytesize": self.uart_bytesize,
            "stopbits": self.uart_stopbits,
            "parity": self.uart_parity,
            "timeout": self.uart_timeout,
            "write_timeout": self.uart_write_timeout
        }

    def get_logging_level(self) -> int:
        """Получить уровень логирования"""
        return getattr(logging, self.log_level)


# Создание глобального экземпляра настроек
settings = Settings()


def configure_logging():
    """Настройка логирования"""
    logging.basicConfig(
        level=settings.get_logging_level(),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )