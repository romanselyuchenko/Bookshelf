console.log("Скрипт загружен");
let bookCount = 1;

// Создаем элемент для отображения сообщений об ошибках
const errorMessageDiv = document.createElement('div');
errorMessageDiv.style.color = 'red'; // Устанавливаем цвет текста
errorMessageDiv.style.marginTop = '10px'; // Отступ сверху
document.body.insertBefore(errorMessageDiv, document.getElementById('generate-btn').nextSibling);

// Функция добавления полей для книг
document.getElementById('add-book-btn').addEventListener('click', function () {
  bookCount++;

  const bookUploadSection = document.getElementById('book-upload-section');
  const newBookField = document.createElement('div');
  newBookField.classList.add('upload-field');
  newBookField.innerHTML = `
    <label>Добавить книгу ${bookCount}:</label>
    <input type="file" accept="image/*" class="book-upload">
  `;
  bookUploadSection.appendChild(newBookField);
});

// Функция генерации изображения (отправка данных на сервер)
document.getElementById('generate-btn').addEventListener('click', async function () {
  const bgFile = document.getElementById('bg-upload').files[0];
  const bookFiles = document.querySelectorAll('.book-upload');

  if (!bgFile) {
    errorMessageDiv.textContent = "Пожалуйста, загрузите фон.";
    return;
  }

  const formData = new FormData();
  formData.append('background', bgFile);
  let validImages = true; // Флаг для проверки валидности изображений
  errorMessageDiv.textContent = ''; // Сбрасываем сообщение об ошибке

  const BOOK_WIDTH = 240; // Задайте ваши размеры
  const BOOK_HEIGHT = 360;
  const expectedAspectRatio = BOOK_WIDTH / BOOK_HEIGHT;

  for (let index = 0; index < bookFiles.length; index++) {
    const input = bookFiles[index];
    if (input.files[0]) {
      const file = input.files[0];
      const img = new Image();
      const reader = new FileReader();

      reader.onload = (e) => {
        img.src = e.target.result;
        img.onload = () => {
          // Проверка соотношения сторон изображения
          const width = img.width;
          const height = img.height;
          const actualAspectRatio = width / height;

          // Допустимое отклонение соотношения сторон (например, ±10%)
          const aspectRatioTolerance = 0.15; // Вы можете изменить это значение на ваше усмотрение
          const lowerBound = expectedAspectRatio * (1 - aspectRatioTolerance);
          const upperBound = expectedAspectRatio * (1 + aspectRatioTolerance);

          if (actualAspectRatio < lowerBound || actualAspectRatio > upperBound) {
            errorMessageDiv.textContent = `Неподходящее соотношение сторон книги № ${index + 1}. Ожидается соотношение около ${BOOK_WIDTH}:${BOOK_HEIGHT}.`;
            validImages = false; // Установите флаг в false
          } else {
            // Изменение размера изображения перед добавлением в FormData
            const canvas = document.createElement('canvas');
            canvas.width = BOOK_WIDTH;
            canvas.height = BOOK_HEIGHT;
            const ctx = canvas.getContext('2d');
            ctx.drawImage(img, 0, 0, BOOK_WIDTH, BOOK_HEIGHT);
            canvas.toBlob((blob) => {
              formData.append(`book${index + 1}`, blob); // Добавляем измененное изображение в FormData
            }, 'image/png');
          }
        };
      };

      reader.readAsDataURL(file);
    }
  }

  // Ждем, пока все изображения будут проверены
  await new Promise(resolve => setTimeout(resolve, 1000));

  if (!validImages) {
    return; // Если есть недопустимые изображения, не отправляем форму
  }

  // Отправка формы, если все изображения валидны
  try {
    const response = await fetch('http://127.0.0.1:8000/upload/', {
      method: 'POST',
      body: formData,
    });
    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.error);
    }

    const blob = await response.blob();
    const url = URL.createObjectURL(blob);

    const linkContainer = document.getElementById('download-link-container');
    linkContainer.innerHTML = '';
    const link = document.createElement('a');
    link.href = url;
    link.download = 'bookshelf.png';
    link.textContent = 'Скачать сгенерированное изображение';
    linkContainer.appendChild(link);
  } catch (error) {
    errorMessageDiv.textContent = error.message; // Выводим сообщение об ошибке на странице
  }
});

// Функция для отображения поля загрузки фона
document.addEventListener('DOMContentLoaded', function () {
  console.log("Скрипт загружен");

  document.querySelectorAll('.size-btn').forEach(button => {
    button.addEventListener('click', function () {
      const resolution = this.textContent;
      const bgUploadSection = document.getElementById('bg-upload-section');
      const bgResolution = document.getElementById('bg-resolution');
      
      bgResolution.textContent = resolution;
      bgUploadSection.style.display = 'block';
    });
  });
});
