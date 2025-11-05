from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
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
    http_host: str = Field(default="0.0.0.0")
    http_port: int = Field(default=8000, ge=1, le=65535)

    # UART настройки
    uart_port: str = Field(default="/dev/ttyUSB0")
    uart_baudrate: int = Field(default=115200)
    uart_bytesize: int = Field(default=8)
    uart_stopbits: int = Field(default=1)
    uart_parity: str = Field(default='N')
    uart_timeout: float = Field(default=1.0, ge=0)
    uart_write_timeout: float = Field(default=1.0, ge=0)

    # WebSocket настройки
    ws_ping_interval: int = Field(default=30, ge=1)
    ws_max_size: int = Field(default=104857600, ge=1024)
    ws_ping_timeout: int = Field(default=10, ge=1)

    # Логирование
    log_level: str = Field(default="INFO")

    @field_validator('uart_port')
    @classmethod
    def validate_uart_port(cls, v: str) -> str:
        if not v:
            raise ValueError("UART порт не может быть пустым")
        return v

    @field_validator('uart_bytesize')
    @classmethod
    def validate_bytesize(cls, v: int) -> int:
        if v not in [5, 6, 7, 8]:
            raise ValueError(f"uart_bytesize должен быть 5, 6, 7 или 8")
        return v

    @field_validator('uart_stopbits')
    @classmethod
    def validate_stopbits(cls, v: int) -> int:
        if v not in [1, 2]:
            raise ValueError(f"uart_stopbits должен быть 1 или 2")
        return v

    @field_validator('uart_parity')
    @classmethod
    def validate_parity(cls, v: str) -> str:
        v = v.upper()
        if v not in ['N', 'E', 'O', 'M', 'S']:
            raise ValueError(f"uart_parity должен быть N, E, O, M или S")
        return v

    @field_validator('log_level')
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        v = v.upper()
        if v not in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
            raise ValueError(f"Неверный уровень логирования")
        return v

    def get_uart_config(self) -> dict:
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
        return getattr(logging, self.log_level.upper())


settings = Settings()


def configure_logging():
    logging.basicConfig(
        level=settings.get_logging_level(),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
