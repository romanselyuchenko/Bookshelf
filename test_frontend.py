import pytest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import os
from pathlib import Path
import time
import tempfile
from PIL import Image
from selenium.common.exceptions import TimeoutException

@pytest.fixture
def driver():
    # Создаем временную директорию для загрузок
    download_dir = tempfile.mkdtemp()
    
    # Настройка опций Chrome
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_experimental_option('prefs', {
        'download.default_directory': download_dir,
        'download.prompt_for_download': False,
        'download.directory_upgrade': True,
        'safebrowsing.enabled': True
    })
    
    # Добавляем дополнительные настройки для загрузки в headless режиме
    chrome_options.add_experimental_option("excludeSwitches", ["enable-logging"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    
    driver = webdriver.Chrome(options=chrome_options)
    driver.command_executor._commands["send_command"] = ("POST", '/session/$sessionId/chromium/send_command')
    params = {'cmd': 'Page.setDownloadBehavior', 
              'params': {'behavior': 'allow', 'downloadPath': download_dir}}
    driver.execute("send_command", params)
    
    yield driver, download_dir
    
    # Очистка после теста
    driver.quit()
    for file in Path(download_dir).glob('*'):
        file.unlink()
    os.rmdir(download_dir)

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

# def test_initial_page_load(driver):
#     """Тест загрузки начальной страницы"""
#     driver, _ = driver
#     driver.get("http://localhost:8000")
#     assert "Твоя книжная полка" in driver.title
    
#     # Проверяем наличие основных элементов
#     assert driver.find_element(By.ID, "size-buttons").is_displayed()
#     assert driver.find_element(By.ID, "book-upload-section").is_displayed()
#     assert driver.find_element(By.ID, "generate-btn").is_displayed()

# def test_resolution_selection(driver):
#     """Тест выбора разрешения"""
#     driver, _ = driver
#     driver.get("http://localhost:8000")
    
#     resolution_btn = driver.find_element(By.ID, "size-btn-1920")
#     resolution_btn.click()
    
#     bg_section = driver.find_element(By.ID, "bg-upload-section")
#     assert bg_section.is_displayed()
#     assert "selected" in resolution_btn.get_attribute("class")

# def test_add_book_button(driver):
#     """Тест добавления новых полей для книг"""
#     driver, _ = driver
#     driver.get("http://localhost:8000")
    
#     initial_book_inputs = len(driver.find_elements(By.CLASS_NAME, "book-upload"))
#     add_book_btn = driver.find_element(By.ID, "add-book-btn")
#     add_book_btn.click()
    
#     new_book_inputs = len(driver.find_elements(By.CLASS_NAME, "book-upload"))
#     assert new_book_inputs == initial_book_inputs + 1

# def test_file_upload(driver, test_images):
#     """Тест загрузки файлов"""
#     driver, _ = driver
#     driver.get("http://localhost:8000")
    
#     driver.find_element(By.ID, "size-btn-1920").click()
    
#     bg_input = driver.find_element(By.ID, "bg-upload")
#     bg_input.send_keys(test_images["background"])
    
#     book_input = driver.find_element(By.CLASS_NAME, "book-upload")
#     book_input.send_keys(test_images["book"])
    
#     assert bg_input.get_attribute("value") != ""
#     assert book_input.get_attribute("value") != ""

def test_generate_button(driver, test_images):
    """Тест генерации с 1 книгой"""
    driver, download_dir = driver
    driver.get("http://localhost:8000")
    
    driver.find_element(By.ID, "size-btn-1920").click()
    
    bg_input = driver.find_element(By.ID, "bg-upload")
    bg_input.send_keys(test_images["background"])
    
    book_input = driver.find_element(By.CLASS_NAME, "book-upload")
    book_input.send_keys(test_images["book"])
    
    generate_btn = driver.find_element(By.ID, "generate-btn")
    generate_btn.click()
    
    # Проверяем, что директория существует
    assert Path(download_dir).exists(), f"Download directory {download_dir} does not exist"
    
    # Ждем появления файла в директории загрузок
    max_wait = 20  # Увеличили время ожидания до 20 секунд
    try:
        WebDriverWait(driver, max_wait).until(
            lambda x: any(Path(download_dir).glob('*'))
        )
    except TimeoutException:
        print(f"Download directory contents after timeout: {list(Path(download_dir).glob('*'))}")
        print(f"Download directory path: {download_dir}")
        raise
    
    # Даем небольшое время на завершение загрузки
    time.sleep(0.5)
    
    files = list(Path(download_dir).glob('*'))
    assert len(files) > 0, "Файл не был скачан"
    assert files[0].stat().st_size > 0, "Скачанный файл пуст"

def test_upload_too_small_background(driver, test_images):
    """Тест загрузки фона меньше минимально допустимого размера"""
    driver, _ = driver
    driver.get("http://localhost:8000")
    
    # Создаем фон меньше минимального размера (1087x611)
    current_dir = Path(__file__).parent
    small_bg_path = current_dir / "test_data" / "small_background.png"
    Image.new('RGB', (1087, 611), 'white').save(small_bg_path)
    
    # Выбираем разрешение 1280x720
    driver.find_element(By.ID, "size-btn-1280").click()
    
    # Загружаем маленький фон
    bg_input = driver.find_element(By.ID, "bg-upload")
    bg_input.send_keys(str(small_bg_path))
    
    # Проверяем, что кнопка генерации стала красной и неактивной
    generate_btn = driver.find_element(By.ID, "generate-btn")
    assert generate_btn.get_attribute("disabled")
    assert generate_btn.value_of_css_property("background-color") == "rgba(255, 68, 68, 1)"

def test_upload_too_large_background(driver, test_images):
    """Тест загрузки фона больше максимально допустимого размера"""
    driver, _ = driver
    driver.get("http://localhost:8000")
    
    # Создаем фон больше максимального размера (2945x1657)
    current_dir = Path(__file__).parent
    large_bg_path = current_dir / "test_data" / "large_background.png"
    Image.new('RGB', (2945, 1657), 'white').save(large_bg_path)
    
    # Выбираем разрешение 2560x1440
    driver.find_element(By.ID, "size-btn-2560").click()
    
    # Загружаем большой фон
    bg_input = driver.find_element(By.ID, "bg-upload")
    bg_input.send_keys(str(large_bg_path))
    
    # Проверяем, что кнопка генерации стала красной и неактивной
    generate_btn = driver.find_element(By.ID, "generate-btn")
    assert generate_btn.get_attribute("disabled")
    assert generate_btn.value_of_css_property("background-color") == "rgba(255, 68, 68, 1)"

def test_upload_wrong_aspect_ratio_book(driver, test_images):
    """Тест загрузки книги с неподходящим соотношением сторон"""
    driver, _ = driver
    driver.get("http://localhost:8000")
    
    # Создаем фон правильного размера
    current_dir = Path(__file__).parent
    background_path = current_dir / "test_data" / "background.png"
    Image.new('RGB', (1920, 1080), 'white').save(background_path)
    
    # Создаем книгу с неправильным соотношением сторон (слишком широкая)
    wrong_book_path = current_dir / "test_data" / "wrong_ratio_book.png"
    Image.new('RGB', (400, 300), 'blue').save(wrong_book_path)  # соотношение 4:3 вместо 2:3
    
    # Выбираем разрешение и загружаем фон
    driver.find_element(By.ID, "size-btn-1920").click()
    bg_input = driver.find_element(By.ID, "bg-upload")
    bg_input.send_keys(str(background_path))
    
    # Загружаем книгу с неправильным соотношением
    book_input = driver.find_element(By.CLASS_NAME, "book-upload")
    book_input.send_keys(str(wrong_book_path))
    
    # Даем время на обработку файла и появление сообщения
    time.sleep(0.5)
    
    # Проверяем, что появилось сообщение об ошибке
    error_message = driver.find_element(By.ID, "book-error-message")  # Изменили селектор
    assert "Неподходящее соотношение сторон книги" in error_message.text
    
    # Проверяем, что кнопка генерации стала красной и неактивной
    generate_btn = driver.find_element(By.ID, "generate-btn")
    assert generate_btn.get_attribute("disabled")
    assert generate_btn.value_of_css_property("background-color") == "rgba(255, 68, 68, 1)"

def test_max_book_upload_fields(driver):
    """Тест ограничения максимального количества полей для загрузки книг"""
    driver, _ = driver
    driver.get("http://localhost:8000")
    
    add_book_btn = driver.find_element(By.ID, "add-book-btn")
    
    # Изначально должно быть 1 поле
    initial_book_inputs = driver.find_elements(By.CLASS_NAME, "book-upload")
    assert len(initial_book_inputs) == 1
    
    # Добавляем поля до максимума (еще 7 раз, так как одно уже есть)
    for i in range(7):
        add_book_btn.click()
        
    # Проверяем, что теперь ровно 8 полей
    book_inputs = driver.find_elements(By.CLASS_NAME, "book-upload")
    assert len(book_inputs) == 8
    
    # Проверяем, что кнопка добавления стала неактивной и серой
    assert add_book_btn.get_attribute("disabled")
    assert add_book_btn.value_of_css_property("background-color") == "rgba(204, 204, 204, 1)"  # #cccccc
    
    # Пробуем нажать кнопку еще раз
    add_book_btn.click()
    
    # Проверяем, что количество полей не изменилось
    final_book_inputs = driver.find_elements(By.CLASS_NAME, "book-upload")
    assert len(final_book_inputs) == 8

def test_generate_with_max_books(driver, test_images):
    """Тест генерации с максимальным количеством книг (8)"""
    driver_instance, download_dir = driver
    driver_instance.get("http://localhost:8000")
    
    # Создаем фон
    current_dir = Path(__file__).parent
    background_path = current_dir / "test_data" / "background.png"
    Image.new('RGB', (1920, 1080), 'white').save(background_path)
    
    # Создаем книгу правильного размера
    book_path = current_dir / "test_data" / "book.png"
    Image.new('RGB', (240, 360), 'blue').save(book_path)
    
    # Выбираем разрешение и загружаем фон
    driver_instance.find_element(By.ID, "size-btn-1920").click()
    bg_input = driver_instance.find_element(By.ID, "bg-upload")
    bg_input.send_keys(str(background_path))
    
    # Добавляем поля для книг до максимума
    add_book_btn = driver_instance.find_element(By.ID, "add-book-btn")
    for _ in range(7):  # Добавляем еще 7 полей (одно уже есть)
        add_book_btn.click()
    
    # Загружаем книги во все поля
    book_inputs = driver_instance.find_elements(By.CLASS_NAME, "book-upload")
    for book_input in book_inputs:
        book_input.send_keys(str(book_path))
    
    # Нажимаем кнопку генерации
    generate_btn = driver_instance.find_element(By.ID, "generate-btn")
    assert not generate_btn.get_attribute("disabled")  # Кнопка должна быть активна
    assert generate_btn.value_of_css_property("background-color") == "rgba(76, 175, 80, 1)"  # Зеленый цвет
    generate_btn.click()
    
    # Ждем появления файла в директории загрузок
    max_wait = 20  # Увеличили время ожидания до 20 секунд
    try:
        WebDriverWait(driver_instance, max_wait).until(
            lambda x: any(Path(download_dir).glob('*'))
        )
    except TimeoutException:
        print(f"Download directory contents after timeout: {list(Path(download_dir).glob('*'))}")
        print(f"Download directory path: {download_dir}")
        raise
    
    # Даем небольшое время на завершение загрузки
    time.sleep(0.5)
    
    files = list(Path(download_dir).glob('*'))
    assert len(files) > 0
    assert files[0].stat().st_size > 0