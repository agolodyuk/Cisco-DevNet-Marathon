## Домашняя работа. DevNet Марафон. День 2. Nornir

Задача:
    Найти switch, port хоста по заданному MAC-адресу.
Вход:
    MAC адрес хоста в сети.
Выход:
    Switch, port за которым находится host с заданным MAC.

Основные допущения:
- за access портом всегда endpoint
- SVI это эндпоинт
- Формат MAC на входе - aaaa.bbbb.cccc

Запуск:
```
(nornir) user@host:~/path$ python3 day2.py --mac aaaa.bbbb.cccc
```