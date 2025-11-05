import serial
import threading
import logging
from typing import Callable, Optional
from config import settings
from models import UARTStatus

logger = logging.getLogger(__name__)


class UARTManager:
    """Менеджер для работы с UART портом"""

    def __init__(self):
        self.serial_port: Optional[serial.Serial] = None
        self.is_open: bool = False
        self.read_thread: Optional[threading.Thread] = None
        self.running: bool = False
        self.data_callback: Optional[Callable[[bytes], None]] = None
        self._lock = threading.Lock()

    def connect(self) -> bool:
        """Открыть UART порт"""
        with self._lock:
            if self.is_open:
                logger.warning("⚠️ UART порт уже открыт")
                return True

            try:
                uart_config = settings.get_uart_config()
                self.serial_port = serial.Serial(**uart_config)

                self.is_open = True
                self.running = True

                # Запуск потока чтения
                self.read_thread = threading.Thread(
                    target=self._read_loop,
                    daemon=True,
                    name="UART-Reader"
                )
                self.read_thread.start()

                logger.info(
                    f"✅ UART порт открыт: {settings.uart_port} "
                    f"@ {settings.uart_baudrate} baud"
                )
                return True

            except serial.SerialException as e:
                logger.error(f"❌ Ошибка открытия UART порта: {e}")
                self.is_open = False
                return False
            except Exception as e:
                logger.error(f"❌ Неожиданная ошибка при открытии UART: {e}")
                self.is_open = False
                return False

    def disconnect(self):
        """Закрыть UART порт"""
        with self._lock:
            self.running = False

            if self.read_thread and self.read_thread.is_alive():
                logger.debug("Ожидание завершения потока чтения...")
                self.read_thread.join(timeout=2)

            if self.serial_port and self.serial_port.is_open:
                try:
                    self.serial_port.close()
                    logger.info("🔌 UART порт закрыт")
                except Exception as e:
                    logger.error(f"❌ Ошибка при закрытии UART: {e}")

            self.is_open = False
            self.serial_port = None

    def _read_loop(self):
        """Цикл чтения данных из UART"""
        logger.debug("Поток чтения UART запущен")

        while self.running and self.serial_port and self.serial_port.is_open:
            try:
                if self.serial_port.in_waiting > 0:
                    data = self.serial_port.read(self.serial_port.in_waiting)

                    if data:
                        logger.debug(f"📥 UART → WS: {data.hex()} ({len(data)} bytes)")

                        if self.data_callback:
                            try:
                                self.data_callback(data)
                            except Exception as e:
                                logger.error(f"❌ Ошибка в callback: {e}")

            except serial.SerialException as e:
                logger.error(f"❌ Ошибка чтения UART: {e}")
                self.is_open = False
                break
            except Exception as e:
                logger.error(f"❌ Неожиданная ошибка в цикле чтения: {e}")

        logger.debug("Поток чтения UART завершен")

    def write(self, data: bytes) -> bool:
        """Записать данные в UART"""
        if not self.serial_port or not self.serial_port.is_open:
            logger.warning("⚠️ UART порт не открыт")
            return False

        try:
            bytes_written = self.serial_port.write(data)
            self.serial_port.flush()
            logger.debug(f"📤 WS → UART: {data.hex()} ({bytes_written} bytes)")
            return True

        except serial.SerialTimeoutException:
            logger.error("❌ Таймаут записи в UART")
            return False
        except serial.SerialException as e:
            logger.error(f"❌ Ошибка записи в UART: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ Неожиданная ошибка записи: {e}")
            return False

    def set_data_callback(self, callback: Callable[[bytes], None]):
        """Установить callback для получения данных"""
        self.data_callback = callback

    def get_status(self) -> UARTStatus:
        """Получить статус UART"""
        return UARTStatus(
            connected=self.is_open,
            port=settings.uart_port,
            baudrate=settings.uart_baudrate,
            bytesize=settings.uart_bytesize,
            stopbits=settings.uart_stopbits,
            parity=settings.uart_parity
        )

    def is_connected(self) -> bool:
        """Проверить, подключен ли UART"""
        return self.is_open and self.serial_port is not None and self.serial_port.is_open