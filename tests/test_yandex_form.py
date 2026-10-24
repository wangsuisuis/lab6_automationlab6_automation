# -*- coding: utf-8 -*-
"""Автотесты поисковой формы Яндекс (Selenium WebDriver + Page Object Model)."""

import allure
import pytest

from conftest import attach_screenshot


@allure.epic("UI-автоматизация")
@allure.feature("Поисковая форма Яндекс")
class TestYandexSearchForm:
    """Проверки заполнения и отправки формы поиска на ya.ru."""

    @allure.story("Поиск и выдача результатов")
    @allure.title("Поиск по запросу «{query}» возвращает релевантную выдачу")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.ui
    @pytest.mark.smoke
    @pytest.mark.parametrize(
        "query,expected_text",
        [
            ("Selenium WebDriver", "Selenium"),
            ("Python pytest", "pytest"),
            ("автоматизация тестирования", "тестирование"),
        ],
        ids=["selenium", "pytest", "testing"],
    )
    def test_search_returns_results(self, form_page, query, expected_text):
        with allure.step(f"Ввести запрос: «{query}»"):
            form_page.enter_search_text(query)
            assert form_page.get_search_input_value() == query, \
                "Текст не попал в поисковую строку"
            attach_screenshot(form_page.driver, f"Ввод запроса «{query}»")

        with allure.step("Отправить форму поиска"):
            form_page.submit_search()

        with allure.step("Дождаться страницы результатов поиска"):
            form_page.wait_for_search_results()
            assert not form_page.is_captcha_shown(), \
                "Яндекс показал SmartCaptcha вместо результатов поиска"
            attach_screenshot(form_page.driver, "Страница результатов поиска")

        with allure.step("Проверить, что выдача соответствует запросу"):
            count = form_page.get_results_count()
            titles = form_page.get_result_titles(limit=10)
            page_title = form_page.get_page_title()

            with allure.step(f"Найдено результатов: {count}"):
                assert count > 0, "Результаты поиска не отобразились"
            with allure.step(f"Заголовок страницы: {page_title}"):
                assert query.lower() in page_title.lower(), \
                    f"Запрос «{query}» не отражён в заголовке страницы: «{page_title}»"

            joined = " ".join(titles).lower()
            assert expected_text.lower() in joined, (
                f"Ожидаемый текст «{expected_text}» не найден в заголовках "
                f"первых результатов: {titles}"
            )

    @allure.story("Автодополнение")
    @allure.title("При вводе запроса отображается список подсказок")
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.ui
    @pytest.mark.smoke
    def test_suggest_display(self, form_page):
        with allure.step("Ввести запрос «автоматизация тестирования»"):
            form_page.enter_search_text("автоматизация тестирования")
            attach_screenshot(form_page.driver, "Ввод запроса для подсказок")

        with allure.step("Проверить, что блок подсказок появился"):
            form_page.wait_for_suggest()
            suggestions = form_page.get_suggestions()
            attach_screenshot(form_page.driver, "Список подсказок")

        with allure.step(f"Подсказок в списке: {len(suggestions)}"):
            assert suggestions, "Список подсказок пуст или не отобразился"

    @allure.story("Очистка формы")
    @allure.title("Кнопка очистки удаляет введённый текст")
    @allure.severity(allure.severity_level.MINOR)
    @pytest.mark.ui
    def test_search_input_clear(self, form_page):
        with allure.step("Ввести текст в поисковую строку"):
            form_page.enter_search_text("текст для очистки")
            assert form_page.get_search_input_value() == "текст для очистки"

        with allure.step("Нажать кнопку очистки поля"):
            form_page.clear_search_input()

        with allure.step("Проверить, что поле пустое"):
            value = form_page.get_search_input_value()
            attach_screenshot(form_page.driver, "Поле после очистки")
            assert value == "", f"Поле не очищено, значение: «{value}»"

    @allure.story("Отправка формы")
    @allure.title("Отправка формы переводит на страницу поиска с текстом запроса")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.ui
    @pytest.mark.regression
    def test_submit_navigates_to_search(self, form_page):
        query = "Page Object Model"

        with allure.step(f"Ввести запрос «{query}» и отправить форму"):
            form_page.enter_search_text(query).submit_search()

        with allure.step("Проверить URL страницы поиска"):
            form_page.wait_for_search_results()
            url = form_page.driver.current_url
            assert "/search" in url, f"Открылась не страница поиска: {url}"
            assert "text=" in url.lower(), f"В URL нет параметра запроса: {url}"
            attach_screenshot(form_page.driver, "URL страницы поиска")
