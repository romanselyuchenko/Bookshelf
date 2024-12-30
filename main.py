from fastapi import FastAPI, File, UploadFile, Form
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from PIL import Image
import io
import os
from uuid import uuid4
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Добавляем middleware для отключения кеширования
@app.middleware("http")
async def add_no_cache_headers(request, call_next):
    response = await call_next(request)
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response

# Папка для сохранения временных файлов
OUTPUT_DIR = "generated"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Настройка статических файлов с отключенным кешированием
app.mount("/static", StaticFiles(directory="static", html=True), name="static")

# Размеры книги
BOOK_WIDTH = 240
BOOK_HEIGHT = 360

# Размер итогового изображения
CANVAS_WIDTH = 1920
CANVAS_HEIGHT = 1080


@app.post("/upload/")
async def upload_files(background: UploadFile = File(...), 
                       book1: UploadFile = File(...), 
                       book2: UploadFile = File(None), 
                       book3: UploadFile = File(None),
                       book4: UploadFile = File(None),
                       book5: UploadFile = File(None),
                       book6: UploadFile = File(None),
                       book7: UploadFile = File(None),
                       book8: UploadFile = File(None),
                       resolution: str = Form('1920x1080')):  # Значение по умолчанию
    # Определяем размеры на основе выбранного разрешения
    if resolution == '1280x720':
        canvas_width, canvas_height = 1280, 720
    elif resolution == '1600x900':
        canvas_width, canvas_height = 1600, 900
    elif resolution == '2560x1440':
        canvas_width, canvas_height = 2560, 1440
    else:  # По умолчанию 1920x1080
        canvas_width, canvas_height = 1920, 1080

    # Читаем фон
    if background is None:
        return {"error": "Фон не загружен"}

    background_image = Image.open(io.BytesIO(await background.read())).convert("RGBA")
    bg_width, bg_height = background_image.size

    # Проверка на допустимый размер с погрешностью 15%
    width_tolerance = canvas_width * 0.15
    height_tolerance = canvas_height * 0.15

    if not (canvas_width - width_tolerance <= bg_width <= canvas_width + width_tolerance) or \
       not (canvas_height - height_tolerance <= bg_height <= canvas_height + height_tolerance):
        return {"error": f"Размер фона должен быть около {canvas_width}x{canvas_height} пикселей с погрешностью 15%."}

    background_image = background_image.resize((canvas_width, canvas_height))

    # Список книг
    book_files = [book1, book2, book3, book4, book5, book6, book7, book8]
    books = []

    # Обрабатываем каждую загруженную книгу
    for book_file in book_files:
        if book_file is not None:
            book_image = Image.open(io.BytesIO(await book_file.read())).convert("RGBA")
            # Добавляем масштабирование книги до стандартного размера
            book_image = book_image.resize((BOOK_WIDTH, BOOK_HEIGHT))
            books.append(book_image)

    # Проверка на наличие хотя бы одной книги
    if not books:
        return {"error": "Добавьте хотя бы одну книгу"}

    # Размещение книг на полке
    result_image = background_image.copy()
    rows = 3  # Количество рядов
    cols = canvas_width // BOOK_WIDTH  # Максимальное число книг в ряду

    x_offset = canvas_width - BOOK_WIDTH  # Начинаем с правого края
    y_offset = canvas_height - BOOK_HEIGHT  # Начинаем с нижнего ряда

    for idx, book in enumerate(books):
        # Добавляем книгу на изображение
        result_image.paste(book, (x_offset, y_offset), book)

        # Смещаем по горизонтали
        x_offset -= BOOK_WIDTH  # Сдвигаем влево

        # Если ряд заполнен, переходим на следующий
        if x_offset < 0:
            x_offset = canvas_width - BOOK_WIDTH  # Снова начинаем с правого края
            y_offset -= BOOK_HEIGHT  # Переходим на следующий ряд

        # Проверяем, если ряды закончились
        if y_offset < 0:
            break

    # Сохраняем итоговое изображение
    output_path = os.path.join(OUTPUT_DIR, f"bookshelf_{uuid4().hex}.png")
    result_image.save(output_path)

    # Возвращаем изображение пользователю
    return FileResponse(output_path, media_type="image/png", filename="bookshelf.png")

@app.get("/")
async def read_root():
    return FileResponse("index.html")  # Возвращаем HTML-страницу
