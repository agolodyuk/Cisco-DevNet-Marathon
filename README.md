# Cisco-DevNet-Marathon
Cisco DevNet Marathon 27.04-30.04.2020

Домашняя работа. DevNet Марафон. День 1. 

##### Топология тестовой сети:
как таковой нет, т.к. скрипт писал-тестировал на боевом железе. 
Для проверки - поправьте инвентаризационный файл под свой стенд - test_tb.yaml и установите PyATS.
По офф. мануалу Cisco это делается парой команд.

##### Используемая версия pyats:
```
You are currently running pyATS version: 19.12
Python: 3.6.9 [64bit]

  Package              Version
  -------------------- -------
  pyats                19.12
  pyats.aereport       19.12
  pyats.aetest         19.12
  pyats.async          19.12
  pyats.connections    19.12
  pyats.datastructures 19.12
  pyats.easypy         19.12
  pyats.kleenex        19.12
  pyats.log            19.12
  pyats.reporter       19.12
  pyats.results        19.12
  pyats.tcl            19.12
  pyats.topology       19.12
  pyats.utils          19.12
```

##### Запуск:

```
(pyats) user@host:~/path$ python3 devnet_day1.py --ntp A.B.C.D 
```