import pytest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import os
from pathlib import Path
import time

@pytest.fixture
def driver():
    # Инициализация драйвера
    driver = webdriver.Chrome()  # или Firefox()
    driver.implicitly_wait(10)
    yield driver
    driver.quit()

@pytest.fixture
def test_images():
    # Создаем тестовые изображения во временной директории
    current_dir = Path(__file__).parent
    background_path = current_dir / "test_data" / "background.png"
    book_path = current_dir / "test_data" / "book.png"
    
    # Убедимся, что директория существует
    os.makedirs(current_dir / "test_data", exist_ok=True)
    
    # Создаем тестовые изображения, если их нет
    if not background_path.exists():
        from PIL import Image
        # Создаем фон 1920x1080
        Image.new('RGB', (1920, 1080), 'white').save(background_path)
        # Создаем книгу 240x360
        Image.new('RGB', (240, 360), 'blue').save(book_path)
    
    return {"background": str(background_path), "book": str(book_path)}

def test_initial_page_load(driver):
    """Тест загрузки начальной страницы"""
    driver.get("http://localhost:8000")
    assert "Твоя книжная полка" in driver.title
    
    # Проверяем наличие основных элементов
    assert driver.find_element(By.ID, "size-buttons").is_displayed()
    assert driver.find_element(By.ID, "book-upload-section").is_displayed()
    assert driver.find_element(By.ID, "generate-btn").is_displayed()

def test_resolution_selection(driver):
    """Тест выбора разрешения"""
    driver.get("http://localhost:8000")
    
    # Нажимаем на кнопку разрешения 1920x1080
    resolution_btn = driver.find_element(By.ID, "size-btn-1920")
    resolution_btn.click()
    
    # Проверяем, что секция загрузки фона стала видимой
    bg_section = driver.find_element(By.ID, "bg-upload-section")
    assert bg_section.is_displayed()
    
    # Проверяем, что кнопка получила класс selected
    assert "selected" in resolution_btn.get_attribute("class")

def test_add_book_button(driver):
    """Тест добавления новых полей для книг"""
    driver.get("http://localhost:8000")
    
    initial_book_inputs = len(driver.find_elements(By.CLASS_NAME, "book-upload"))
    
    # Нажимаем кнопку добавления книги
    add_book_btn = driver.find_element(By.ID, "add-book-btn")
    add_book_btn.click()
    
    # Проверяем, что появилось новое поле
    new_book_inputs = len(driver.find_elements(By.CLASS_NAME, "book-upload"))
    assert new_book_inputs == initial_book_inputs + 1

def test_file_upload(driver, test_images):
    """Тест загрузки файлов"""
    driver.get("http://localhost:8000")
    
    # Выбираем разрешение
    driver.find_element(By.ID, "size-btn-1920").click()
    
    # Загружаем фон
    bg_input = driver.find_element(By.ID, "bg-upload")
    bg_input.send_keys(test_images["background"])
    
    # Загружаем книгу
    book_input = driver.find_element(By.CLASS_NAME, "book-upload")
    book_input.send_keys(test_images["book"])
    
    # Проверяем, что файлы были загружены
    assert bg_input.get_attribute("value") != ""
    assert book_input.get_attribute("value") != ""

def test_generate_button(driver, test_images):
    """Тест кнопки генерации"""
    driver.get("http://localhost:8000")
    
    # Подготавливаем и загружаем файлы
    driver.find_element(By.ID, "size-btn-1920").click()
    
    bg_input = driver.find_element(By.ID, "bg-upload")
    bg_input.send_keys(test_images["background"])
    
    book_input = driver.find_element(By.CLASS_NAME, "book-upload")
    book_input.send_keys(test_images["book"])
    
    # Нажимаем кнопку генерации
    generate_btn = driver.find_element(By.ID, "generate-btn")
    generate_btn.click()
    
    # Даем время на обработку запроса
    time.sleep(2)  # Можно заменить на более элегантное ожидание
    
    # Проверяем, что нет сообщений об ошибках
    error_messages = driver.find_elements(By.CSS_SELECTOR, 'div[style*="color: red"]')
    visible_errors = [e for e in error_messages if e.is_displayed() and e.text]
    assert len(visible_errors) == 0