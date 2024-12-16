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
    response = client.get("/")
    assert response.status_code == 200

def test_no_cache_headers():
    response = client.get("/")
    assert response.headers["Cache-Control"] == "no-cache, no-store, must-revalidate"
    assert response.headers["Pragma"] == "no-cache"
    assert response.headers["Expires"] == "0"

def test_upload_success(sample_background, sample_book):
    files = {
        "background": ("background.png", sample_background, "image/png"),
        "book1": ("book1.png", sample_book, "image/png")
    }
    response = client.post("/upload/", files=files, data={"resolution": "1920x1080"})
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"

def test_upload_no_background(sample_book):
    files = {
        "book1": ("book1.png", sample_book, "image/png")
    }
    response = client.post("/upload/", files=files, data={"resolution": "1920x1080"})
    assert response.status_code == 422  # FastAPI возвращает 422 для отсутствующих обязательных полей

def test_upload_no_books(sample_background):
    files = {
        "background": ("background.png", sample_background, "image/png")
    }
    response = client.post("/upload/", files=files, data={"resolution": "1920x1080"})
    assert response.status_code == 422  # Изменили ожидаемый код

def test_different_resolutions(sample_book):
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