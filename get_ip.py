#!/usr/bin/env python3
"""
Скрипт для определения IP адреса компьютера в локальной сети
"""
import socket

def get_local_ip():
    """Получить локальный IP адрес компьютера"""
    try:
        # Создаем временное соединение для определения IP
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # Не отправляем данные, просто определяем интерфейс
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        try:
            # Альтернативный способ
            hostname = socket.gethostname()
            ip = socket.gethostbyname(hostname)
            return ip
        except Exception:
            return "127.0.0.1"

if __name__ == "__main__":
    ip = get_local_ip()
    print(f"Ваш IP адрес в локальной сети: {ip}")
    print(f"\nДля подключения мобильного приложения используйте:")
    print(f"  http://{ip}:8000")
    print(f"\nИли установите переменную окружения:")
    print(f"  export BACKEND_URL=http://{ip}:8000")



