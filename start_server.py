#!/usr/bin/env python3
"""
Скрипт запуска бэкенд-сервера с автоматическим определением IP
"""
import subprocess
import sys
import socket
import os

def get_local_ip():
    """Получить локальный IP адрес компьютера"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        try:
            hostname = socket.gethostname()
            return socket.gethostbyname(hostname)
        except Exception:
            return "127.0.0.1"

def main():
    local_ip = get_local_ip()
    port = 8000
    
    print("=" * 70)
    print("🚀 Запуск GymGenius AI Backend Server")
    print("=" * 70)
    print(f"📡 IP адрес в сети: {local_ip}")
    print(f"🌐 Порт: {port}")
    print(f"🔗 URL для подключения: http://{local_ip}:{port}")
    print("=" * 70)
    print("\n💡 Информация:")
    print(f"   - Сервер будет доступен на всех устройствах в вашей сети")
    print(f"   - Локальный доступ: http://localhost:{port}")
    print(f"   - Доступ из сети: http://{local_ip}:{port}")
    print("\n⚠️  Важно:")
    print("   1. Убедитесь, что файрвол разрешает подключения на порт 8000")
    print("   2. Все устройства должны быть в одной Wi-Fi сети")
    print("   3. В мобильном приложении используйте IP: " + local_ip)
    print("=" * 70)
    print("\n")
    
    # Запускаем сервер
    try:
        import uvicorn
        uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False)
    except ImportError:
        print("❌ Ошибка: uvicorn не установлен")
        print("Установите зависимости: pip install -r requirements.txt")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n\n👋 Сервер остановлен")
    except Exception as e:
        print(f"\n❌ Ошибка запуска: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()



