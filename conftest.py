# -*- coding: utf-8 -*-
"""Общая конфигурация pytest: фикстуры браузера и отчётность Allure."""

import os
import shutil
import tempfile

import allure
import pytest
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


def pytest_addoption(parser):
    parser.addoption(
        "--headless",
        action="store_true",
        default=False,
        help="Запустить Chrome без окна (headless). Яндекс в этом режиме часто "
             "показывает SmartCaptcha, поэтому по умолчанию браузер видимый.",
    )


def pytest_configure(config):
    config.addinivalue_line("markers", "smoke: дымовые проверки")
    config.addinivalue_line("markers", "ui: тесты пользовательского интерфейса")


def _chrome_options(pytestconfig, profile_dir: str) -> Options:
    options = Options()
    # Постоянный профиль делает сессию «живой» и снижает риск капчи
    options.add_argument(f"--user-data-dir={profile_dir}")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--lang=ru-RU")
    options.add_argument("--no-first-run")
    options.add_argument("--no-default-browser-check")
    options.add_argument("--disable-gpu")
    # Окно второго воркера оказывается «позади» — Chrome душит фоновые вкладки
    options.add_argument("--disable-backgrounding-occluded-windows")
    options.add_argument("--disable-renderer-backgrounding")
    options.add_argument("--disable-background-timer-throttling")
    # Скрываем признаки автоматизации
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)

    headless = pytestconfig.getoption("--headless") or os.getenv("HEADLESS", "0") == "1"
    if headless:
        options.add_argument("--headless=new")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
    return options


@pytest.fixture(scope="session")
def browser(pytestconfig):
    """Экземпляр Chrome на всю тестовую сессию (свой профиль у каждого xdist-воркера)."""
    worker = os.environ.get("PYTEST_XDIST_WORKER", "master")
    profile_dir = os.path.join(tempfile.gettempdir(), f"lr6_chrome_profile_{worker}")

    driver = webdriver.Chrome(options=_chrome_options(pytestconfig, profile_dir))
    # Убираем navigator.webdriver — иначе Яндекс отдаёт капчу
    driver.execute_cdp_cmd(
        "Page.addScriptToEvaluateOnNewDocument",
        {"source": "Object.defineProperty(navigator,'webdriver',{get:()=>undefined})"},
    )
    driver.set_window_size(1920, 1080)
    driver.set_page_load_timeout(60)

    yield driver

    driver.quit()
    shutil.rmtree(profile_dir, ignore_errors=True)


@pytest.fixture(scope="session")
def base_url() -> str:
    """Адрес тестируемого сайта (можно переопределить переменной окружения BASE_URL)."""
    return os.getenv("BASE_URL", "https://ya.ru")


@pytest.fixture
def form_page(browser, base_url):
    """Открытая главная страница с поисковой формой."""
    from pages.yandex_form_page import YandexFormPage

    return YandexFormPage(browser, base_url).open_page()


def attach_screenshot(driver, name: str) -> None:
    """Приложить скриншот текущего состояния страницы к Allure-отчёту."""
    try:
        allure.attach(
            driver.get_screenshot_as_png(),
            name=name,
            attachment_type=allure.attachment_type.PNG,
        )
    except Exception:  # браузер уже закрыт — не роняем тест
        pass


def pytest_sessionfinish(session, exitstatus):
    """Дополнительное окружение и категории дефектов для Allure-отчёта."""
    if hasattr(session.config, "workerinput"):  # xdist-воркер, пишет только master
        return
    import json
    import platform
    import selenium

    results_dir = session.config.getoption("--alluredir", None) or "allure-results"
    os.makedirs(results_dir, exist_ok=True)

    env = {
        "Browser": "Google Chrome (visible)",
        "Base.URL": os.getenv("BASE_URL", "https://ya.ru"),
        "Python": platform.python_version(),
        "Selenium": selenium.__version__,
        "Platform": f"{platform.system()} {platform.release()}",
        "Headless": "yes" if session.config.getoption("--headless") else "no",
    }
    with open(os.path.join(results_dir, "environment.properties"), "w", encoding="utf-8") as fh:
        for key, value in env.items():
            fh.write(f"{key}={value}\n")

    categories = [
        {
            "name": "Падения тестов",
            "matchedStatuses": ["failed", "broken"],
        },
        {
            "name": "Проблемы окружения (капча, сеть)",
            "matchedStatuses": ["broken"],
            "messageRegex": ".*(SmartCaptcha|TimeoutException|WebDriverException).*",
        },
    ]
    with open(os.path.join(results_dir, "categories.json"), "w", encoding="utf-8") as fh:
        json.dump(categories, fh, ensure_ascii=False, indent=2)


@pytest.hookimpl(hookwrapper=True, tryfirst=True)
def pytest_runtest_makereport(item, call):
    """Скриншот, HTML-код страницы и URL при падении теста."""
    outcome = yield
    report = outcome.get_result()
    if report.failed and report.when in ("setup", "call"):
        driver = item.funcargs.get("browser")
        if driver is not None:
            try:
                allure.attach(
                    driver.get_screenshot_as_png(),
                    name=f"FAILED_{item.name}",
                    attachment_type=allure.attachment_type.PNG,
                )
                allure.attach(
                    driver.page_source[:200_000],
                    name="page_source",
                    attachment_type=allure.attachment_type.HTML,
                )
                allure.attach(
                    driver.current_url,
                    name="url",
                    attachment_type=allure.attachment_type.TEXT,
                )
            except Exception:
                pass
