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
    
    # Инициализация драйвера с опциями
    driver = webdriver.Chrome(options=chrome_options)
    driver.implicitly_wait(10)
    
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

def test_initial_page_load(driver):
    """Тест загрузки начальной страницы"""
    driver, _ = driver  # распаковываем значения
    driver.get("http://localhost:8000")
    assert "Твоя книжная полка" in driver.title
    
    # Проверяем наличие основных элементов
    assert driver.find_element(By.ID, "size-buttons").is_displayed()
    assert driver.find_element(By.ID, "book-upload-section").is_displayed()
    assert driver.find_element(By.ID, "generate-btn").is_displayed()

def test_resolution_selection(driver):
    """Тест выбора разрешения"""
    driver, _ = driver  # распаковываем значения
    driver.get("http://localhost:8000")
    
    resolution_btn = driver.find_element(By.ID, "size-btn-1920")
    resolution_btn.click()
    
    bg_section = driver.find_element(By.ID, "bg-upload-section")
    assert bg_section.is_displayed()
    assert "selected" in resolution_btn.get_attribute("class")

def test_add_book_button(driver):
    """Тест добавления новых полей для книг"""
    driver, _ = driver  # распаковываем значения
    driver.get("http://localhost:8000")
    
    initial_book_inputs = len(driver.find_elements(By.CLASS_NAME, "book-upload"))
    add_book_btn = driver.find_element(By.ID, "add-book-btn")
    add_book_btn.click()
    
    new_book_inputs = len(driver.find_elements(By.CLASS_NAME, "book-upload"))
    assert new_book_inputs == initial_book_inputs + 1

def test_file_upload(driver, test_images):
    """Тест загрузки файлов"""
    driver, _ = driver  # распаковываем значения
    driver.get("http://localhost:8000")
    
    driver.find_element(By.ID, "size-btn-1920").click()
    
    bg_input = driver.find_element(By.ID, "bg-upload")
    bg_input.send_keys(test_images["background"])
    
    book_input = driver.find_element(By.CLASS_NAME, "book-upload")
    book_input.send_keys(test_images["book"])
    
    assert bg_input.get_attribute("value") != ""
    assert book_input.get_attribute("value") != ""

def test_generate_button(driver, test_images):
    """Тест кнопки генерации"""
    driver, download_dir = driver  # распаковываем значения
    driver.get("http://localhost:8000")
    
    driver.find_element(By.ID, "size-btn-1920").click()
    
    bg_input = driver.find_element(By.ID, "bg-upload")
    bg_input.send_keys(test_images["background"])
    
    book_input = driver.find_element(By.CLASS_NAME, "book-upload")
    book_input.send_keys(test_images["book"])
    
    generate_btn = driver.find_element(By.ID, "generate-btn")
    generate_btn.click()
    
    # Ждем появления файла в директории загрузок
    max_wait = 10
    downloaded = False
    start_time = time.time()
    while time.time() - start_time < max_wait:
        files = list(Path(download_dir).glob('*.png'))
        if files:
            downloaded = True
            break
        time.sleep(0.5)
    
    assert downloaded, "Файл не был скачан"
    
    downloaded_file = files[0]
    assert downloaded_file.stat().st_size > 0, "Скачанный файл пуст"
    
    # Проверяем изображение
    with Image.open(downloaded_file) as img:
        assert img.format == 'PNG', "Файл не является PNG изображением"
        assert img.size == (1920, 1080), "Неверные размеры изображения"