# Financial Analyzer Integration

## Обзор

Финансовый анализатор успешно интегрирован в FinvizPro! Теперь приложение включает мощные инструменты для анализа финансовой отчетности.

## Новые Функции

### 1. **PDF Parser** (`pdf-parser.html`)
- Загрузка и парсинг финансовых отчетов (10-K, Annual Reports, IFRS statements)
- Извлечение текста и таблиц из PDF
- Поддержка OCR для сканированных документов
- Метаданные документа

### 2. **GAAP/IFRS Classifier** (`gaap-classifier.html`)
- Автоматическое определение стандарта отчетности
- Многоуровневая система детекции
- Уровень уверенности классификации
- Детальные доказательства и индикаторы

### 3. **Financial Extractor** (`financial-extractor.html`)
- Извлечение Income Statement (Отчет о прибылях и убытках)
- Извлечение Balance Sheet (Баланс)
- Извлечение Cash Flow Statement (Отчет о движении денежных средств)
- Интерактивные графики с Plotly
- Табличное представление данных

### 4. **Model Builder** (`model-builder.html`)
- Построение интегрированной 3-statement модели
- Валидация всех связей между отчетами
- Проверка балансировки модели
- Ключевые финансовые метрики

### 5. **Forecast Engine** (`forecast-engine.html`)
- Генерация многолетних прогнозов (1-10 лет)
- Настраиваемые предположения (assumptions)
- Сценарный анализ (Base/Bull/Bear)
- Driver-based моделирование
- Интерактивные графики прогнозов

### 6. **Report Generator** (`report-generator.html`)
- Генерация профессиональных PDF отчетов
- Полный анализ с графиками и таблицами
- Executive Summary
- Исторические данные и прогнозы
- Финансовые коэффициенты и KPI

## API Endpoints

Все новые endpoints доступны по адресу `/api/analyzer/`:

```
POST /api/analyzer/upload          - Загрузка PDF файла
POST /api/analyzer/parse            - Парсинг PDF
POST /api/analyzer/classify         - Классификация GAAP/IFRS
POST /api/analyzer/extract          - Извлечение финансовых данных
POST /api/analyzer/model            - Построение модели
POST /api/analyzer/forecast         - Генерация прогноза
POST /api/analyzer/report           - Генерация PDF отчета
GET  /api/analyzer/download/<file>  - Скачивание отчета
GET  /api/analyzer/status           - Статус анализатора
GET  /api/analyzer/demo/sample-data - Демо данные
```

## Структура Файлов

```
finviz python/
├── backend/
│   ├── app.py                      # Основной Flask app (обновлен)
│   ├── financial_analyzer_api.py   # API endpoints для анализатора
│   ├── finanalyzer/                # Модули финансового анализатора
│   │   ├── core/                   # Основные модули
│   │   │   ├── pdf_parser.py
│   │   │   ├── gaap_ifrs_classifier.py
│   │   │   ├── financial_extractor.py
│   │   │   ├── model_engine.py
│   │   │   ├── forecast_engine.py
│   │   │   └── report_generator.py
│   │   └── models/                 # Модели данных
│   │       └── schemas.py
│   ├── uploads/                    # Загруженные PDF файлы
│   ├── output/                     # Сгенерированные отчеты
│   └── requirements.txt            # Обновленные зависимости
│
└── frontend/
    ├── index.html                  # Главная страница (обновлена)
    ├── pdf-parser.html             # Страница парсера PDF
    ├── gaap-classifier.html        # Страница классификатора
    ├── financial-extractor.html    # Страница экстрактора
    ├── model-builder.html          # Страница построения модели
    ├── forecast-engine.html        # Страница прогнозирования
    ├── report-generator.html       # Страница генерации отчетов
    ├── analyzer-styles.css         # Стили для анализатора
    ├── style.css                   # Основные стили
    └── config.js                   # Конфигурация API
```

## Установка и Запуск

### 1. Установка зависимостей

```bash
cd backend
pip install -r requirements.txt
```

**Важно:** Для полной функциональности требуется установка Tesseract OCR:
- **Windows**: Скачайте с https://github.com/UB-Mannheim/tesseract/wiki
- **macOS**: `brew install tesseract`
- **Linux**: `sudo apt-get install tesseract-ocr`

### 2. Запуск приложения

```bash
# Из корневой директории проекта
start_finvizpro.bat
```

Или вручную:

```bash
# Backend
cd backend
python app.py

# Frontend будет доступен на http://localhost:5000
```

### 3. Использование

1. Откройте браузер и перейдите на `http://localhost:5000`
2. В навигации выберите "Financial Analyzer"
3. Загрузите PDF финансового отчета
4. Следуйте по шагам:
   - PDF Parser → GAAP/IFRS Classifier → Financial Extractor → Model Builder → Forecast Engine → Report Generator

## Workflow Анализа

```
1. PDF Parser
   ↓ (загрузка и парсинг PDF)
2. GAAP/IFRS Classifier
   ↓ (определение стандарта)
3. Financial Extractor
   ↓ (извлечение данных)
4. Model Builder
   ↓ (построение модели)
5. Forecast Engine
   ↓ (прогнозирование)
6. Report Generator
   ↓ (генерация PDF отчета)
```

## Технологии

### Backend
- **Flask** - Web framework
- **pdfplumber** - PDF parsing
- **pytesseract** - OCR
- **reportlab** - PDF generation
- **pandas** - Data processing
- **matplotlib/plotly** - Visualizations
- **pydantic** - Data validation

### Frontend
- **HTML5/CSS3/JavaScript** - Core technologies
- **Plotly.js** - Interactive charts
- **Modern CSS** - Gradients, animations, glassmorphism

## Особенности Дизайна

- 🎨 **Премиум дизайн** с градиентами и анимациями
- 📱 **Responsive** - адаптивный для всех устройств
- 🌙 **Dark mode ready** - поддержка темной темы
- ⚡ **Быстрый и интуитивный** интерфейс
- 📊 **Интерактивные графики** с Plotly

## Примеры Использования

### Загрузка и анализ отчета

```javascript
// 1. Загрузка файла
const formData = new FormData();
formData.append('file', pdfFile);

const uploadResponse = await fetch('/api/analyzer/upload', {
    method: 'POST',
    body: formData
});

// 2. Парсинг
const parseResponse = await fetch('/api/analyzer/parse', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ filename: 'report.pdf' })
});

// 3. Классификация
const classifyResponse = await fetch('/api/analyzer/classify', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ filename: 'report.pdf' })
});
```

### Генерация прогноза

```javascript
const forecastResponse = await fetch('/api/analyzer/forecast', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
        filename: 'report.pdf',
        years: 5,
        scenario: 'base',
        assumptions: {
            revenue_growth_rate: 0.08,
            gross_margin: 0.42,
            operating_margin: 0.22,
            tax_rate: 0.21
        }
    })
});
```

## Troubleshooting

### Проблема: Модули finanalyzer не найдены

**Решение:** Убедитесь, что вы скопировали папку `src` из finanalyzer в `backend/finanalyzer`:

```bash
xcopy /E /I /Y "путь\к\finanalyzer\src" "backend\finanalyzer"
```

### Проблема: OCR не работает

**Решение:** Установите Tesseract OCR и добавьте его в PATH.

### Проблема: PDF не парсится

**Решение:** 
1. Проверьте, что PDF не защищен паролем
2. Убедитесь, что PDF содержит текст (не только изображения)
3. Для сканированных документов требуется Tesseract OCR

## Будущие Улучшения

- [ ] Web scraping для SEC EDGAR
- [ ] AI-powered extraction с GPT-4
- [ ] Поддержка Excel экспорта
- [ ] Batch processing нескольких файлов
- [ ] Сохранение истории анализов
- [ ] Сравнение компаний
- [ ] Industry benchmarking

## Лицензия

MIT License

## Авторы

- FinvizPro Team
- Financial Analyzer Integration

---

**Готово к использованию!** 🚀

Для вопросов и предложений создавайте issues в репозитории.
