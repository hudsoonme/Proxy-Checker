# proxy_checker.py
import requests
import threading
import queue
import time
import sys
from typing import List, Tuple
from concurrent.futures import ThreadPoolExecutor

# -------------------------------
# НАСТРОЙКИ
# -------------------------------
PROXY_FILE = "proxies.txt"          # Файл со списком прокси (формат: ip:port или user:pass@ip:port)
WORKING_FILE = "working.txt"        # Куда сохранять рабочие
DEAD_FILE = "dead.txt"              # Куда сохранять мёртвые
THREADS = 100                       # Количество потоков
TIMEOUT = 7                         # Таймаут в секундах
TEST_URL = "http://httpbin.org/ip"  # Тестовый URL (возвращает IP)

# -------------------------------
# Глобальные переменные
# -------------------------------
lock = threading.Lock()
working_count = 0
dead_count = 0
total_count = 0

# -------------------------------
# Функция проверки одного прокси
# -------------------------------
def check_proxy(proxy: str) -> Tuple[bool, str]:
    proxy = proxy.strip()
    if not proxy:
        return False, "empty"

    # Определяем тип прокси
    proxy_type = "http"
    if proxy.startswith("socks5://") or "socks5" in proxy.lower():
        proxy_type = "socks5"
        proxy = proxy.replace("socks5://", "").replace("socks4://", "")
    elif proxy.startswith("socks4://"):
        proxy_type = "socks4"
        proxy = proxy.replace("socks4://", "")
    elif proxy.startswith("http://") or proxy.startswith("https://"):
        proxy = proxy.split("://", 1)[1]

    # Формируем словарь прокси
    if "@" in proxy:
        auth, host_port = proxy.split("@", 1)
        user, password = auth.split(":", 1)
        proxies = {
            "http": f"{proxy_type}://{user}:{password}@{host_port}",
            "https": f"{proxy_type}://{user}:{password}@{host_port}",
        }
    else:
        proxies = {
            "http": f"{proxy_type}://{proxy}",
            "https": f"{proxy_type}://{proxy}",
        }

    try:
        response = requests.get(
            TEST_URL,
            proxies=proxies,
            timeout=TIMEOUT,
            verify=False,
            headers={"User-Agent": "Mozilla/5.0"}
        )
        if response.status_code == 200:
            ip = response.json().get("origin", "")
            return True, ip
        else:
            return False, f"status {response.status_code}"
    except Exception as e:
        error = str(e).lower()
        if "proxy" in error or "timeout" in error or "refused" in error:
            return False, "timeout/refused"
        return False, "error"

# -------------------------------
# Сохранение результата
# -------------------------------
def save_result(proxy: str, is_working: bool, info: str):
    global working_count, dead_count
    with lock:
        if is_working:
            with open(WORKING_FILE, "a", encoding="utf-8") as f:
                f.write(proxy + "\n")
            working_count += 1
            print(f"[+] РАБОЧИЙ: {proxy} → {info}")
        else:
            with open(DEAD_FILE, "a", encoding="utf-8") as f:
                f.write(proxy + "\n")
            dead_count += 1
            print(f"[-] МЁРТВЫЙ: {proxy} ({info})")

# -------------------------------
# Основная функция
# -------------------------------
def main():
    global total_count

    print(f"Запуск проверки прокси из: {PROXY_FILE}")
    print(f"Потоков: {THREADS} | Таймаут: {TIMEOUT}с\n")

    # Читаем прокси
    if not os.path.exists(PROXY_FILE):
        print(f"Файл {PROXY_FILE} не найден!")
        sys.exit(1)

    with open(PROXY_FILE, "r", encoding="utf-8") as f:
        proxies = [line.strip() for line in f if line.strip() and not line.startswith("#")]

    total_count = len(proxies)
    print(f"Загружено прокси: {total_count}\n")

    # Очищаем файлы
    open(WORKING_FILE, "w").close()
    open(DEAD_FILE, "w").close()

    start_time = time.time()

    # Запускаем проверку
    with ThreadPoolExecutor(max_workers=THREADS) as executor:
        futures = []
        for proxy in proxies:
            future = executor.submit(lambda p=proxy: save_result(p, *check_proxy(p)))
            futures.append(future)

        # Ждём завершения
        for future in futures:
            future.result()

    elapsed = time.time() - start_time
    print("\n" + "="*60)
    print(f"ГОТОВО за {elapsed:.1f} сек")
    print(f"Всего: {total_count}")
    print(f"Рабочих: {working_count} → {WORKING_FILE}")
    print(f"Мёртвых: {dead_count} → {DEAD_FILE}")
    print("="*60)

# -------------------------------
# Запуск
# -------------------------------
if __name__ == "__main__":
    try:
        import os
        requests.packages.urllib3.disable_warnings()
        main()
    except KeyboardInterrupt:
        print("\nОстановлено пользователем.")
