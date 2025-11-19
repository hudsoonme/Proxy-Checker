# Proxy Checker (HTTP/SOCKS5)

Простой и быстрый **валикачество-проверятель прокси** на Python

> Поддержка HTTP, HTTPS, SOCKS4, SOCKS5  
> Мультипоточность  
> Автосохранение рабочих/мёртвых

## Установка

> pip install requests pysocks

## Формат proxies.txt

> Примеры (можно смешивать типы)
1.2.3.4:8080
user:pass@5.6.7.8:1080
socks5://9.10.11.12:1080
socks5://user2:pass2@13.14.15.16:1080
http://17.18.19.20:3128

## Запуск

> python proxy_checker.py

## Результат:

working.txt — рабочие
dead.txt — мёртвые

