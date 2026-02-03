# AI Image Hub

Автоматизована платформа для генерації та редагування зображень з використанням ChatGPT та Nanobanano Pro.

## Можливості

- **Генерація зображень**: Створення нових зображень з текстового опису (будь-якою мовою)
- **Редагування зображень**: Модифікація існуючих зображень на основі текстових інструкцій
- **Інтелектуальні промпти**: ChatGPT автоматично перетворює простий опис на професійний промпт
- **Повне логування**: Всі операції записуються в базу даних

## Архітектура

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Streamlit     │────▶│    FastAPI      │────▶│   PostgreSQL    │
│   Frontend      │     │    Backend      │     │    Database     │
└─────────────────┘     └────────┬────────┘     └─────────────────┘
                                 │
                    ┌────────────┴────────────┐
                    │                         │
              ┌─────▼─────┐            ┌──────▼──────┐
              │  ChatGPT  │            │  Nanobanano │
              │    API    │            │   Pro API   │
              └───────────┘            └─────────────┘
```

## Швидкий старт з Docker

### 1. Клонування та налаштування

```bash
git clone https://github.com/your-repo/nanobanano.git
cd nanobanano

# Копіюємо приклад конфігурації
cp .env.example .env
```

### 2. Редагуємо `.env` файл

```env
OPENAI_API_KEY=your_openai_api_key
NANOBANANO_API_KEY=your_nanobanano_api_key
API_SECRET_TOKEN=your_secure_token_here
```

### 3. Запуск

```bash
docker-compose up -d
```

### 4. Доступ до сервісів

- **Frontend (Streamlit)**: http://localhost:8501
- **Backend API (FastAPI)**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

## Локальна розробка

### Вимоги

- Python 3.11+
- PostgreSQL 15+

### Встановлення

```bash
# Створення віртуального середовища
python -m venv venv
source venv/bin/activate  # Linux/Mac
# або: venv\Scripts\activate  # Windows

# Встановлення залежностей
pip install -r requirements.txt

# Налаштування змінних оточення
cp .env.example .env
# Редагуйте .env файл
```

### Запуск Backend

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Запуск Frontend

```bash
streamlit run frontend/app.py
```

## API Документація

### Автентифікація

Всі запити (крім `/health`) потребують заголовок `X-API-Token`.

### Ендпоінти

#### POST `/api/v1/generate`
Генерація нового зображення.

```json
{
  "description": "Котик грає на піаніно",
  "width": 1024,
  "height": 1024,
  "style": "photorealistic"
}
```

#### POST `/api/v1/edit`
Редагування існуючого зображення.

```json
{
  "image_url": "https://example.com/image.jpg",
  "edit_description": "Змінити фон на зоряне небо",
  "strength": 0.7
}
```

#### GET `/api/v1/history`
Отримання історії транзакцій.

#### GET `/api/v1/transaction/{id}`
Деталі конкретної транзакції.

## Структура проекту

```
nanobanano/
├── app/
│   ├── api/
│   │   ├── __init__.py
│   │   └── routes.py          # API ендпоінти
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py          # Конфігурація
│   │   ├── database.py        # Підключення до БД
│   │   └── security.py        # Автентифікація
│   ├── models/
│   │   ├── __init__.py
│   │   └── transaction.py     # Моделі БД
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── requests.py        # Схеми запитів
│   │   └── responses.py       # Схеми відповідей
│   ├── services/
│   │   ├── __init__.py
│   │   ├── chatgpt_service.py # Інтеграція з ChatGPT
│   │   └── nanobanano_service.py # Інтеграція з Nanobanano
│   ├── __init__.py
│   └── main.py                # Точка входу FastAPI
├── frontend/
│   └── app.py                 # Streamlit frontend
├── docker-compose.yml
├── Dockerfile
├── Dockerfile.frontend
├── requirements.txt
├── .env.example
└── README.md
```

## Ліцензія

MIT License
