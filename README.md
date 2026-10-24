# Лабораторная работа №6. Автоматизация тестирования веб-форм (Selenium WebDriver)

**Репозиторий:** https://github.com/wangsuisuis/lab6_automationlab6_automation

Автотесты поисковой формы на сайте **Яндекс** (`https://ya.ru`) с использованием
Selenium WebDriver, паттерна **Page Object Model**, параллельного запуска
(`pytest-xdist`) и отчётности **Allure**.

## Технологический стек

| Компонент | Версия / назначение |
|---|---|
| Python | 3.12 |
| Selenium WebDriver | 4.51.0 |
| pytest | 8.4.2 |
| pytest-xdist | 3.8.0 — параллельный запуск |
| allure-pytest | 2.16.2 — отчётность |
| Page Object Model | `pages/yandex_form_page.py` |

## Структура проекта

```
lab6_automation/
├── pages/
│   ├── __init__.py
│   └── yandex_form_page.py   # Page Object главной страницы ya.ru
├── tests/
│   ├── __init__.py
│   └── test_yandex_form.py   # тестовые сценарии
├── conftest.py               # фикстуры браузера, скриншоты при падении
├── pytest.ini                # маркеры, addopts, Allure
├── requirements.txt
└── README.md
```

## Установка

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows
pip install -r requirements.txt
```

Требуется установленный **Google Chrome** (драйвер Selenium Manager скачает
автоматически, `webdriver-manager` оставлен как резервный вариант).

## Запуск тестов

```bash
# обычный запуск
pytest tests/test_yandex_form.py -v

# параллельный запуск (2 потока)
pytest tests/test_yandex_form.py -n 2 -v

# только дымовые тесты
pytest -m smoke -v

# с формированием результатов Allure
pytest --alluredir=allure-results
```

## Allure-отчёт

```bash
# онлайн-просмотр
allure serve allure-results

# статический отчёт в папку allure-report
allure generate allure-results -o allure-report --clean
allure open allure-report
```

В отчёт прикладываются скриншоты каждого шага, а при падении теста —
скриншот, HTML-код страницы и URL.

## Реализованные проверки

| Тест | Что проверяет |
|---|---|
| `test_search_returns_results` | ввод запроса, отправка формы, выдача релевантных результатов (3 запроса, parametrize) |
| `test_suggest_display` | появление списка автодополнения при вводе |
| `test_search_input_clear` | очистка поля кнопкой-крестиком |
| `test_submit_navigates_to_search` | переход на `/search` с параметром `text` |

## Особенности запуска

* **Chrome запускается в видимом режиме.** В headless-режиме Яндекс показывает
  SmartCaptcha вместо выдачи, поэтому `--headless` выключен по умолчанию
  (включается флагом `pytest --headless`).
* Тесты закрывают промо-модалку «Установите Яндекс Браузер», которая
  перекрывает кнопку «Найти» (см. `YandexFormPage.dismiss_overlays`).
* Адрес сайта можно переопределить: `BASE_URL=https://ya.ru pytest`.
* У каждого xdist-воркера свой профиль Chrome (временная папка), поэтому
  параллельный запуск не конфликтует.

## Результаты

```
6 passed in 34.68s   # pytest -n 2 -v
```
