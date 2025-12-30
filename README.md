# Geo Points API

Backend-приложение на Django DRF для работы с географическими точками на карте. Предоставляет REST API для создания точек, обмена сообщениями и поиска контента в заданном радиусе от указанных координат.

## 📋 Функциональность

- ✅ Создание географических точек (GeoJSON Point формат)
- ✅ Создание сообщений к точкам
- ✅ Поиск точек в заданном радиусе
- ✅ Поиск сообщений в заданном радиусе
- ✅ Аутентификация для всех эндпоинтов (Basic Auth + Session Auth)

## 🛠 Технический стек

- **Poetry** 
- **black / flake8**
- **coverage** для измерения покрытия
- **Django TestCase** для тестирования
- **httpie** - для запросов (вместо curl) 

- **Python 3.10+**
- **Django 5.0**
- **Django REST Framework 3.15**
- **SQLite** (в production рекомендуется PostgreSQL + PostGIS)
- **django-geojson** для хранения географических координат
- **Haversine formula** для расчёта расстояний

## 🚀 Быстрый старт

1. Клонируем и настраиваем окружение

```shell
git clone git@github.com:xelpixness/redcollar-geo-points-api.git
cd redcollar-geo-points-api/

# Создадим виртуальное окружение и установим зависимости
python3 -m venv .venv
source .venv/bin/activate  # для Windows: .venv\Scripts\activate
pip install poetry
poetry install --no-root
```

2. Настроим базу данных

```shell
python manage.py migrate

# Создадим пару юзеров для тестирования (суперюзеры для простоты)
python manage.py createsuperuser   # admin  / pass123 
python manage.py createsuperuser   # walker / pass123
```

3. Запуск тестов с покрытием 

```shell
coverage run --source='geo_api' manage.py test geo_api
coverage html  # для просмотра отчёта в браузере 
coverage report
```

```shell
Name                                 Stmts   Miss  Cover
--------------------------------------------------------
geo_api/__init__.py                      0      0   100%
geo_api/admin.py                         1      0   100%
geo_api/apps.py                          4      0   100%
geo_api/migrations/0001_initial.py       8      0   100%
geo_api/migrations/__init__.py           0      0   100%
geo_api/models.py                       19      0   100%
geo_api/serializers.py                  36      0   100%
geo_api/tests.py                       298      0   100%
geo_api/urls.py                          3      0   100%
geo_api/utils.py                        13      0   100%
geo_api/views.py                        87      4    95%
--------------------------------------------------------
TOTAL                                  469      4    99%
```

## 🍋‍🟩 Примеры API запросов 

✨ вместо `curl` будем использовать `httpie`

Запускаем сервер: 

```shell
python manage.py runserver
```

### 🌍 Точки

🔴 Пробуем добавить точку без аутентификации: 

```shell
http POST http://127.0.0.1:8000/api/points/ \
  name="Test Point" \
  coordinates:='{"type": "Point", "coordinates": [0, 0]}'
```

```json
HTTP/1.1 403 Forbidden
// ...
{
    "detail": "Authentication credentials were not provided."
}
```

🟢 Добавляем первую точку: 

```shell
http -a admin:pass123 POST http://127.0.0.1:8000/api/points/ \
  name="Кремль" \
  description="Московский Кремль" \
  coordinates:='{"type": "Point", "coordinates": [37.6173, 55.7517]}'
```

```json
HTTP/1.1 201 Created
// ...
{
    "coordinates": {
        "coordinates": [
            37.6173,
            55.7517
        ],
        "type": "Point"
    },
    "created_at": "2025-12-30T04:17:11.544016Z",
    "created_by": 1,
    "description": "Московский Кремль",
    "id": 1,
    "name": "Кремль",
    "updated_at": "2025-12-30T04:17:11.544058Z"
}
```

🟢 Добавляем ещё две точки:

```shell
# Санкт-Петербург (~700км от Москвы)
http -a admin:pass123 POST http://127.0.0.1:8000/api/points/ \
  name="Зимний дворец" \
  description="Эрмитаж. Музей в Санкт-Петербурге" \
  coordinates:='{"type": "Point", "coordinates": [30.3141, 59.9398]}'

# Зеленоград (~45 км от Москвы)
http -a walker:pass123 POST http://127.0.0.1:8000/api/points/ \
  name="Зеленоград" \
  description="Город-спутник Москвы" \
  coordinates:='{"type": "Point", "coordinates": [37.1818, 55.9825]}'
```

```json
// ответы аналогичные! ✨
```

🔴 Пробуем создать точку с невалидной долготой: 

```shell
http -a admin:pass123 POST http://127.0.0.1:8000/api/points/ \
  name="Invalid Point" \
  coordinates:='{"type": "Point", "coordinates": [200, 50]}'
```

```json
HTTP/1.1 400 Bad Request
// ...
{
    "coordinates": [
        "Longitude must be between -180 and 180 degrees"
    ]
}
```

🔴 Или с отсутствующим полем `type` в GeoJSON: 

```shell
http -a admin:pass123 POST http://127.0.0.1:8000/api/points/ \
  name="Missing Type" \
  coordinates:='{"coordinates": [0, 0]}'
```

```json
HTTP/1.1 400 Bad Request
// ...
{
    "coordinates": [
        "Missing 'type' field in GeoJSON"
    ]
}
```

### 🌍 Сообщения 

🔴 Пробуем создать сообщение для точки без аутентификации: 

```shell
http POST http://127.0.0.1:8000/api/points/messages/ \
  point=1 \
  text="Привет из Москвы!"
```

```
HTTP/1.1 403 Forbidden
// ...
{
    "detail": "Authentication credentials were not provided."
}
```

🟢 Создаём сообщение для первой точки:

```shell
http -a admin:pass123 POST http://127.0.0.1:8000/api/points/messages/ \
  point=1 \
  text="Привет из Москвы!"
```

```json
HTTP/1.1 201 Created
// ...

{
    "created_at": "2025-12-30T04:44:10.421492Z",
    "id": 1,
    "point": 1,
    "text": "Привет из Москвы!",
    "user": 1
}
```


🟢 Аналогично создаём сообщения для 2 и 3 точки: 

```shell
http -a admin:pass123 POST http://127.0.0.1:8000/api/points/messages/ \
  point=2 \
  text="Красивый Эрмитаж! Обязательно к посещению."


http -a walker:pass123 POST http://127.0.0.1:8000/api/points/messages/ \
  point=3 \
  text="Зеленоград - самый зелёный город Подмосковья!"


http -a admin:pass123 POST http://127.0.0.1:8000/api/points/messages/ \
  point=3 \
  text="Мечтаю съездить в Зеленоград!"
```

```shell
# ответы аналогичные! ✨
```

🔴 Пробуем создать сообщение для несуществующей точки: 

```
http -a admin:pass123 POST http://127.0.0.1:8000/api/points/messages/ \
  point=999 \
  text="Bad point"
```

```json
HTTP/1.1 400 Bad Request
// ...
{
    "point": [
        "Point does not exist. Please provide a valid point ID."
    ]
}
```

### 🌍 Поиск точек в радиусе

🔴 Поиск без аутентификации:

```shell
http GET "http://127.0.0.1:8000/api/points/search/?latitude=55.7558&longitude=37.6173&radius=10"
```

```json
HTTP/1.1 403 Forbidden
// ...
{
    "detail": "Authentication credentials were not provided."
}
```

🔴 Поиск без передачи радиуса: 

```shell
http -a admin:pass123 GET "http://127.0.0.1:8000/api/points/search/?latitude=55.7558&longitude=37.6173"
```

```json
HTTP/1.1 400 Bad Request
// ...
{
    "error": "Missing required parameters",
    "example": "/api/points/search/?latitude=55.7558&longitude=37.6173&radius=10",
    "required": [
        "latitude",
        "longitude",
        "radius (km)"
    ]
}
```

🟢 Поиск точек в 5км от Москвы: 

```shell
http -a admin:pass123 GET "http://127.0.0.1:8000/api/points/search/?latitude=55.7558&longitude=37.6173&radius=5"
```

```json
HTTP/1.1 200 OK
// ...
{
    "points": [
        {
            "coordinates": {
                "coordinates": [
                    37.6173,
                    55.7517
                ],
                "type": "Point"
            },
            "created_by": "admin",
            "description": "Московский Кремль",
            "distance_km": 0.46,
            "id": 1,
            "name": "Кремль"
        }
    ],
    "points_found": 1,
    "radius_km": 5.0,
    "search_center": {
        "latitude": 55.7558,
        "longitude": 37.6173
    }
}
```

🟢 Поиск точек в 1000 км от Москвы: 

```shell
http -a admin:pass123 GET "http://127.0.0.1:8000/api/points/search/?latitude=55.7558&longitude=37.6173&radius=1000"
```

```json
HTTP/1.1 200 OK
// ...
{
    "points": [
        {
            "coordinates": {
                "coordinates": [
                    37.6173,
                    55.7517
                ],
                "type": "Point"
            },
            "created_by": "admin",
            "description": "Московский Кремль",
            "distance_km": 0.46,
            "id": 1,
            "name": "Кремль"
        },
        {
            "coordinates": {
                "coordinates": [
                    30.3141,
                    59.9398
                ],
                "type": "Point"
            },
            "created_by": "admin",
            "description": "Эрмитаж. Музей в Санкт-Петербурге",
            "distance_km": 634.29,
            "id": 2,
            "name": "Зимний дворец"
        },
        {
            "coordinates": {
                "coordinates": [
                    37.1818,
                    55.9825
                ],
                "type": "Point"
            },
            "created_by": "walker",
            "description": "Город-спутник Москвы",
            "distance_km": 37.06,
            "id": 3,
            "name": "Зеленоград"
        }
    ],
    "points_found": 3,
    "radius_km": 1000.0,
    "search_center": {
        "latitude": 55.7558,
        "longitude": 37.6173
    }
}
```

### 🌍 Поиск сообщений в радиусе

🔴 Поиск без аутентификации:

```shell
http GET "http://127.0.0.1:8000/api/points/messages/search/?latitude=55.7558&longitude=37.6173&radius=5"
```

```json
HTTP/1.1 403 Forbidden
// ...
{
    "detail": "Authentication credentials were not provided."
}

```

🔴 Поиск без одно параметра (широты):

```shell
http -a admin:pass123 GET "http://127.0.0.1:8000/api/points/messages/search/?longitude=37.6173&radius=5"
```

```json
HTTP/1.1 400 Bad Request
// ...
{
    "error": "Missing required parameters",
    "example": "/api/points/messages/search/?latitude=55.7558&longitude=37.6173&radius=10",
    "required": [
        "latitude",
        "longitude",
        "radius (km)"
    ]
}
```

🟢 Поиск сообщений в 5км от Москвы: 

```shell
http -a admin:pass123 GET "http://127.0.0.1:8000/api/points/messages/search/?latitude=55.7558&longitude=37.6173&radius=5"
```

```json
HTTP/1.1 200 OK
// ...
{
    "messages": [
        {
            "created_at": "2025-12-30T04:44:10.421492Z",
            "distance_km": 0.46,
            "id": 1,
            "point": {
                "coordinates": {
                    "coordinates": [
                        37.6173,
                        55.7517
                    ],
                    "type": "Point"
                },
                "id": 1,
                "name": "Кремль"
            },
            "text": "Привет из Москвы!",
            "user": {
                "id": 1,
                "username": "admin"
            }
        }
    ],
    "messages_found": 1,
    "radius_km": 5.0,
    "search_center": {
        "latitude": 55.7558,
        "longitude": 37.6173
    }
}
```

🟢 Поиск сообщений в 1000км от Москвы: 

```shell
http -a admin:pass123 GET "http://127.0.0.1:8000/api/points/messages/search/?latitude=55.7558&longitude=37.6173&radius=1000"
```

```json
{
    "messages": [
        {
            "created_at": "2025-12-30T04:44:10.421492Z",
            "distance_km": 0.46,
            "id": 1,
            "point": {
                "coordinates": {
                    "coordinates": [
                        37.6173,
                        55.7517
                    ],
                    "type": "Point"
                },
                "id": 1,
                "name": "Кремль"
            },
            "text": "Привет из Москвы!",
            "user": {
                "id": 1,
                "username": "admin"
            }
        },
        {
            "created_at": "2025-12-30T05:13:03.497115Z",
            "distance_km": 634.29,
            "id": 2,
            "point": {
                "coordinates": {
                    "coordinates": [
                        30.3141,
                        59.9398
                    ],
                    "type": "Point"
                },
                "id": 2,
                "name": "Зимний дворец"
            },
            "text": "Красивый Эрмитаж! Обязательно к посещению.",
            "user": {
                "id": 1,
                "username": "admin"
            }
        },
        {
            "created_at": "2025-12-30T05:13:12.785990Z",
            "distance_km": 37.06,
            "id": 3,
            "point": {
                "coordinates": {
                    "coordinates": [
                        37.1818,
                        55.9825
                    ],
                    "type": "Point"
                },
                "id": 3,
                "name": "Зеленоград"
            },
            "text": "Зеленоград - самый зелёный город Подмосковья!",
            "user": {
                "id": 2,
                "username": "walker"
            }
        },
        {
            "created_at": "2025-12-30T05:13:26.013471Z",
            "distance_km": 37.06,
            "id": 4,
            "point": {
                "coordinates": {
                    "coordinates": [
                        37.1818,
                        55.9825
                    ],
                    "type": "Point"
                },
                "id": 3,
                "name": "Зеленоград"
            },
            "text": "Мечтаю съездить в Зеленоград!",
            "user": {
                "id": 1,
                "username": "admin"
            }
        }
    ],
    "messages_found": 4,
    "radius_km": 1000.0,
    "search_center": {
        "latitude": 55.7558,
        "longitude": 37.6173
    }
}
```

## Спасибо за внимание! ✨
