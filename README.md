# Система сбора логов

## Сборка и запуск

### Требования
- Docker
- Docker Compose

### Инструкция по сборке

> Проект log-collector подключается с помощью git submodule. Описание проекта log-collector доступно в его репозитории: https://github.com/arsnazarenko/log-collector
```bash
git clone --recurse-submodules https://github.com/arsnazarenko/abds-course-work.git && cd abds-course-work
make init
make up
...
make stop
```

### Доступные сервисы

| Сервис | Адрес | Логин | Пароль |
|--------|-------|-------|--------|
| RabbitMQ Management (rmq1) | http://localhost:15672 | guest | guest |
| RabbitMQ Management (rmq2) | http://localhost:15673 | guest | guest |
| RabbitMQ Management (rmq3) | http://localhost:15674 | guest | guest |
| ClickHouse (ch1) HTTP | http://localhost:8123 | default | default |
| ClickHouse (ch2) HTTP | http://localhost:8124 | default | default |
| ClickHouse (ch3) HTTP | http://localhost:8125 | default | default |
| Collector API | http://localhost:8080 | - | - |
| Prometheus | http://localhost:9090 | - | - |
| Grafana | http://localhost:3000 | admin | admin |
| Superset | http://localhost:8088 | admin | admin |
| Airflow Web UI | http://localhost:8081 | airflow | airflow |

### Полезные команды

```bash
make stop              # Остановка всех сервисов
make kill-generator    # Остановка генератора логов
make upload-json-samples    # Загрузка JSON примеров
make upload-clf-samples     # Загрузка CLF примеров
make upload-syslog-samples  # Загрузка Syslog примеров
```

> После остановки всех сервисов необходимо удалить из ./volumes данные контейнеров. Может потребоваться sudo
