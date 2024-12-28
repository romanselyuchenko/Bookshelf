import pytest
from fastapi.testclient import TestClient
from main import app
from PIL import Image
import io

client = TestClient(app)

@pytest.fixture
def sample_background():
    # Создаем тестовое изображение фона 1920x1080
    img = Image.new('RGBA', (1920, 1080), 'white')
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='PNG')
    img_byte_arr.seek(0)
    return img_byte_arr

@pytest.fixture
def sample_book():
    # Создаем тестовое изображение книги
    img = Image.new('RGBA', (240, 360), 'blue')
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='PNG')
    img_byte_arr.seek(0)
    return img_byte_arr

def test_read_root():
    """Тест доступности главной страницы"""
    response = client.get("/")
    assert response.status_code == 200

def test_no_cache_headers():
    """Тест заголовков кэширования"""
    response = client.get("/")
    assert response.headers["Cache-Control"] == "no-cache, no-store, must-revalidate"
    assert response.headers["Pragma"] == "no-cache"
    assert response.headers["Expires"] == "0"

def test_upload_success(sample_background, sample_book):
    """Тест успешной загрузки файлов"""
    files = {
        "background": ("background.png", sample_background, "image/png"),
        "book1": ("book1.png", sample_book, "image/png")
    }
    response = client.post("/upload/", files=files, data={"resolution": "1920x1080"})
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"

def test_upload_no_background(sample_book):
    """Тест загрузки без фона"""
    files = {
        "book1": ("book1.png", sample_book, "image/png")
    }
    response = client.post("/upload/", files=files, data={"resolution": "1920x1080"})
    assert response.status_code == 422  # FastAPI возвращает 422 для отсутствующих обязательных полей

def test_upload_no_books(sample_background):
    """Тест загрузки без книг"""
    files = {
        "background": ("background.png", sample_background, "image/png")
    }
    response = client.post("/upload/", files=files, data={"resolution": "1920x1080"})
    assert response.status_code == 422  # Изменили ожидаемый код

def test_different_resolutions(sample_book):
    """Тест поддержки разных разрешений"""
    resolutions = ['1280x720', '1600x900', '1920x1080', '2560x1440']
    
    for res in resolutions:
        width, height = map(int, res.split('x'))
        # Создаем фон соответствующего размера
        background = io.BytesIO()
        Image.new('RGBA', (width, height), 'white').save(background, format='PNG')
        background.seek(0)
        
        files = {
            "background": ("background.png", background, "image/png"),
            "book1": ("book1.png", sample_book, "image/png")
        }
        response = client.post("/upload/", files=files, data={"resolution": res})
        assert response.status_code == 200

def test_min_background_size(sample_book):
    """Тест минимального допустимого размера фона с погрешностью 15%"""
    # Для разрешения 1280x720
    # Минимальный размер с учетом погрешности 15%: 1088x612
    min_width = int(1280 * 0.85)  # 1088
    min_height = int(720 * 0.85)   # 612
    
    background = io.BytesIO()
    Image.new('RGBA', (min_width, min_height), 'white').save(background, format='PNG')
    background.seek(0)
    
    files = {
        "background": ("background.png", background, "image/png"),
        "book1": ("book1.png", sample_book, "image/png")
    }
    response = client.post("/upload/", files=files, data={"resolution": "1280x720"})
    assert response.status_code == 200

def test_max_background_size(sample_book):
    """Тест максимального допустимого размера фона с погрешностью 15%"""
    # Для разрешения 2560x1440
    # Максимальный размер с учетом погрешности 15%: 2944x1656
    max_width = int(2560 * 1.15)   # 2944
    max_height = int(1440 * 1.15)   # 1656
    
    background = io.BytesIO()
    Image.new('RGBA', (max_width, max_height), 'white').save(background, format='PNG')
    background.seek(0)
    
    files = {
        "background": ("background.png", background, "image/png"),
        "book1": ("book1.png", sample_book, "image/png")
    }
    response = client.post("/upload/", files=files, data={"resolution": "2560x1440"})
    assert response.status_code == 200

def test_min_book_size(sample_background):
    """Тест минимального допустимого размера книги (100x150)"""
    book = io.BytesIO()
    Image.new('RGBA', (100, 150), 'blue').save(book, format='PNG')
    book.seek(0)
    
    files = {
        "background": ("background.png", sample_background, "image/png"),
        "book1": ("book1.png", book, "image/png")
    }
    response = client.post("/upload/", files=files, data={"resolution": "1920x1080"})
    assert response.status_code == 200

def test_max_book_size(sample_background):
    """Тест максимального допустимого размера книги (400x600)"""
    book = io.BytesIO()
    Image.new('RGBA', (400, 600), 'blue').save(book, format='PNG')
    book.seek(0)
    
    files = {
        "background": ("background.png", sample_background, "image/png"),
        "book1": ("book1.png", book, "image/png")
    }
    response = client.post("/upload/", files=files, data={"resolution": "1920x1080"})
    assert response.status_code == 200

def test_narrowest_book_ratio(sample_background):
    """Тест самого узкого допустимого соотношения сторон книги (1:2)"""
    book = io.BytesIO()
    Image.new('RGBA', (150, 300), 'blue').save(book, format='PNG')
    book.seek(0)
    
    files = {
        "background": ("background.png", sample_background, "image/png"),
        "book1": ("book1.png", book, "image/png")
    }
    response = client.post("/upload/", files=files, data={"resolution": "1920x1080"})
    assert response.status_code == 200

def test_widest_book_ratio(sample_background):
    """Тест самого широкого допустимого соотношения сторон книги (1:1)"""
    book = io.BytesIO()
    Image.new('RGBA', (200, 200), 'blue').save(book, format='PNG')
    book.seek(0)
    
    files = {
        "background": ("background.png", sample_background, "image/png"),
        "book1": ("book1.png", book, "image/png")
    }
    response = client.post("/upload/", files=files, data={"resolution": "1920x1080"})
    assert response.status_code == 200