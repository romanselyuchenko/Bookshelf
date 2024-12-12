from fastapi import FastAPI, File, UploadFile, Form
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from PIL import Image
import io
import os
from uuid import uuid4

app = FastAPI()

# Папка для сохранения временных файлов
OUTPUT_DIR = "generated"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Настройка статических файлов
app.mount("/static", StaticFiles(directory="static"), name="static")

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
                       book8: UploadFile = File(None)):
    # Читаем фон
    if background is None:
        return {"error": "Фон не загружен"}

    background_image = Image.open(io.BytesIO(await background.read())).convert("RGBA")
    background_image = background_image.resize((CANVAS_WIDTH, CANVAS_HEIGHT))

    # Список книг
    book_files = [book1, book2, book3, book4, book5, book6, book7, book8]
    books = []

    # Обрабатываем каждую загруженную книгу
    for book_file in book_files:
        if book_file is not None:
            book_image = Image.open(io.BytesIO(await book_file.read())).convert("RGBA")
            books.append(book_image)

    # Проверка на наличие хотя бы одной книги
    if not books:
        return {"error": "Добавьте хотя бы одну книгу"}

    # Размещение книг на полке
    result_image = background_image.copy()
    rows = 3  # Количество рядов
    cols = CANVAS_WIDTH // BOOK_WIDTH  # Максимальное число книг в ряду

    x_offset = CANVAS_WIDTH - BOOK_WIDTH  # Начинаем с правого края
    y_offset = CANVAS_HEIGHT - BOOK_HEIGHT  # Начинаем с нижнего ряда

    for idx, book in enumerate(books):
        # Добавляем книгу на изображение
        result_image.paste(book, (x_offset, y_offset), book)

        # Смещаем по горизонтали
        x_offset -= BOOK_WIDTH  # Сдвигаем влево

        # Если ряд заполнен, переходим на следующий
        if x_offset < 0:
            x_offset = CANVAS_WIDTH - BOOK_WIDTH  # Снова начинаем с правого края
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
