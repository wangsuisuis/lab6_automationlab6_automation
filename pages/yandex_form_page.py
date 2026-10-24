# -*- coding: utf-8 -*-
"""Page Object Model для поисковой формы на главной странице Яндекс.

Класс инкапсулирует:
  * локаторы элементов страницы;
  * методы взаимодействия с элементами;
  * бизнес-логику страницы (полный сценарий поиска).
"""

import time

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException,
    ElementClickInterceptedException,
)


class YandexFormPage:
    """Главная страница ya.ru с поисковой строкой."""

    # ---- Локаторы элементов формы -------------------------------------
    SEARCH_INPUT = (By.ID, "text")
    SUGGEST_POPUP = (By.CSS_SELECTOR, ".mini-suggest__popup-content")
    SUGGEST_ITEMS = (By.CSS_SELECTOR, ".mini-suggest__popup-content .mini-suggest__item")
    SEARCH_BUTTON = (By.CSS_SELECTOR, "button[type='submit'].search3__button")
    CLEAR_BUTTON = (By.CSS_SELECTOR, ".mini-suggest__input-clear")
    # Результаты поиска (серп)
    SEARCH_RESULTS = (By.CSS_SELECTOR, "#search-result .serp-item")
    RESULT_TITLES = (By.CSS_SELECTOR, ".OrganicTitle-Link")
    CAPTCHA_FORM = (By.CSS_SELECTOR, "form[action*='showcaptcha'], .SmartCaptcha")
    # Модальные окна и промо-баннеры, перекрывающие форму
    OVERLAY_CLOSE_BUTTONS = (
        By.CSS_SELECTOR,
        "button.DistributionButtonClose, .Modal_visible button[aria-label='Закрыть'], "
        ".Modal_visible .Modal-Close",
    )
    VISIBLE_MODAL = (By.CSS_SELECTOR, ".Modal_visible")

    def __init__(self, driver, base_url: str = "https://ya.ru"):
        self.driver = driver
        self.base_url = base_url
        self.wait = WebDriverWait(driver, 15)

    # ---- Действия ------------------------------------------------------
    def dismiss_overlays(self, timeout: float = 5.0) -> "YandexFormPage":
        """Закрыть промо-модалки Яндекса, перекрывающие форму поиска.

        На зарубежных IP Яндекс показывает модальное окно «Установите
        Яндекс Браузер», из-за которого обычный click() перехватывается.
        """
        end = time.time() + timeout
        while time.time() < end:
            try:
                buttons = [
                    b for b in self.driver.find_elements(*self.OVERLAY_CLOSE_BUTTONS)
                    if b.is_displayed()
                ]
                if not buttons:
                    break
                try:
                    buttons[0].click()
                except Exception:
                    self.driver.execute_script("arguments[0].click();", buttons[0])
                time.sleep(0.3)
            except Exception:
                # страница перерисовывается — пробуем ещё раз
                time.sleep(0.3)

        # Если модалка осталась (например, анимация), убираем её из DOM
        try:
            for modal in self.driver.find_elements(*self.VISIBLE_MODAL):
                if modal.is_displayed():
                    self.driver.execute_script("arguments[0].remove();", modal)
        except Exception:
            pass
        return self

    def open_page(self) -> "YandexFormPage":
        """Открыть главную страницу поисковика."""
        self.driver.get(self.base_url)
        self.wait.until(EC.visibility_of_element_located(self.SEARCH_INPUT))
        self.dismiss_overlays()
        return self

    def enter_search_text(self, text: str) -> "YandexFormPage":
        """Ввести текст в поисковую строку."""
        search_input = self.wait.until(EC.element_to_be_clickable(self.SEARCH_INPUT))
        search_input.clear()
        search_input.send_keys(text)
        return self

    def clear_search_input(self) -> "YandexFormPage":
        """Очистить поле через кнопку-крестик на форме."""
        button = self.wait.until(EC.element_to_be_clickable(self.CLEAR_BUTTON))
        try:
            button.click()
        except ElementClickInterceptedException:
            # промо-модалка может появиться с задержкой — закрываем и повторяем
            self.dismiss_overlays()
            button = self.wait.until(EC.element_to_be_clickable(self.CLEAR_BUTTON))
            self.driver.execute_script("arguments[0].click();", button)
        return self

    def get_search_input_value(self) -> str:
        """Текущее значение поля поиска."""
        return self.driver.find_element(*self.SEARCH_INPUT).get_attribute("value")

    def wait_for_suggest(self) -> "YandexFormPage":
        """Дождаться появления списка подсказок."""
        self.wait.until(EC.visibility_of_element_located(self.SUGGEST_POPUP))
        return self

    def get_suggestions(self) -> list:
        """Тексты подсказок автодополнения."""
        try:
            items = self.wait.until(EC.presence_of_all_elements_located(self.SUGGEST_ITEMS))
        except TimeoutException:
            return []
        return [item.text.strip() for item in items if item.text.strip()]

    def submit_search(self) -> "YandexFormPage":
        """Нажать кнопку «Найти» (с обходом перекрывающих баннеров)."""
        button = self.wait.until(EC.element_to_be_clickable(self.SEARCH_BUTTON))
        try:
            button.click()
        except ElementClickInterceptedException:
            self.dismiss_overlays()
            button = self.wait.until(EC.element_to_be_clickable(self.SEARCH_BUTTON))
            try:
                button.click()
            except ElementClickInterceptedException:
                # Резервный вариант: отправка формы клавишей Enter
                self.driver.find_element(*self.SEARCH_INPUT).send_keys(Keys.ENTER)
        return self

    def wait_for_search_results(self) -> "YandexFormPage":
        """Дождаться загрузки страницы выдачи."""
        # Яндекс открывает и /search/?text=..., и /search?text=... — проверяем подстроку
        self.wait.until(lambda drv: "/search" in drv.current_url)
        self.wait.until(EC.presence_of_element_located(self.SEARCH_RESULTS))
        self.dismiss_overlays()
        return self

    def get_results_count(self) -> int:
        """Количество найденных результатов на странице."""
        return len(self.driver.find_elements(*self.SEARCH_RESULTS))

    def get_result_titles(self, limit: int = 5) -> list:
        """Заголовки первых результатов поиска."""
        titles = self.driver.find_elements(*self.RESULT_TITLES)
        return [t.text.strip() for t in titles[:limit] if t.text.strip()]

    def get_page_title(self) -> str:
        return self.driver.title

    def is_captcha_shown(self) -> bool:
        """Проверка, что Яндекс показал SmartCaptcha вместо выдачи."""
        if "showcaptcha" in self.driver.current_url:
            return True
        return len(self.driver.find_elements(*self.CAPTCHA_FORM)) > 0

    # ---- Бизнес-сценарий ----------------------------------------------
    def perform_search(self, query: str) -> "YandexFormPage":
        """Полный цикл: ввод запроса, ожидание подсказок, отправка, выдача."""
        (self.enter_search_text(query)
             .wait_for_suggest()
             .submit_search()
             .wait_for_search_results())
        return self
