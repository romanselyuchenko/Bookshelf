// Проверка размера фона
const bgErrorMessageDiv = document.createElement('div');
bgErrorMessageDiv.style.color = 'red';
bgErrorMessageDiv.style.marginTop = '10px';

const bgUploadSection = document.getElementById('bg-upload-section');
bgUploadSection.appendChild(bgErrorMessageDiv);

document.getElementById('bg-upload').addEventListener('change', function () {
  const file = this.files[0];
  if (file) {
    const img = new Image();
    const reader = new FileReader();

    reader.onload = (e) => {
      img.src = e.target.result;
      img.onload = () => {
        const selectedResolution = document.querySelector('.size-btn.selected')?.textContent || '1920x1080';
        const [expectedWidth, expectedHeight] = selectedResolution.split('x').map(Number);

        const widthTolerance = expectedWidth * 0.15;
        const heightTolerance = expectedHeight * 0.15;

        if (
          img.width < expectedWidth - widthTolerance ||
          img.width > expectedWidth + widthTolerance ||
          img.height < expectedHeight - heightTolerance ||
          img.height > expectedHeight + heightTolerance
        ) {
          bgErrorMessageDiv.textContent = `Добавьте изображение размером около ${expectedWidth}x${expectedHeight}.`;
        } else {
          bgErrorMessageDiv.textContent = '';
        }
      };
    };
    reader.readAsDataURL(file);
  }
});

const bookErrorMessageDiv = document.createElement('div');
bookErrorMessageDiv.style.color = 'red';
bookErrorMessageDiv.style.marginTop = '10px';
document.body.insertBefore(bookErrorMessageDiv, document.getElementById('generate-btn').nextSibling);

let bookCount = 1;

function validateBookSize(file, index) {
  return new Promise((resolve) => {
    const img = new Image();
    const reader = new FileReader();
    const BOOK_WIDTH = 240;
    const BOOK_HEIGHT = 360;
    const expectedAspectRatio = BOOK_WIDTH / BOOK_HEIGHT;

    reader.onload = (e) => {
      img.src = e.target.result;
      img.onload = () => {
        const width = img.width;
        const height = img.height;
        const actualAspectRatio = width / height;

        const aspectRatioTolerance = 0.15;
        const lowerBound = expectedAspectRatio * (1 - aspectRatioTolerance);
        const upperBound = expectedAspectRatio * (1 + aspectRatioTolerance);

        if (actualAspectRatio < lowerBound || actualAspectRatio > upperBound) {
          bookErrorMessageDiv.textContent = `Неподходящее соотношение сторон книги № ${index + 1}. Ожидается соотношение около ${BOOK_WIDTH}:${BOOK_HEIGHT}.`;
          resolve(false);
        } else {
          bookErrorMessageDiv.textContent = '';
          resolve(true);
        }
      };
    };
    reader.readAsDataURL(file);
  });
}

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

  const newInput = newBookField.querySelector('.book-upload');
  newInput.addEventListener('change', function() {
    if (this.files[0]) {
      validateBookSize(this.files[0], bookCount - 1);
    }
  });
});

document.querySelector('.book-upload').addEventListener('change', function() {
  if (this.files[0]) {
    validateBookSize(this.files[0], 0);
  }
});

async function validateAndUploadBooks() {
  const bgFile = document.getElementById('bg-upload').files[0];
  const bookFiles = document.querySelectorAll('.book-upload');

  if (!bgFile) {
    bookErrorMessageDiv.textContent = "Пожалуйста, загрузите фон.";
    return;
  }

  let validImages = true;
  bookErrorMessageDiv.textContent = '';

  for (let index = 0; index < bookFiles.length; index++) {
    const input = bookFiles[index];
    if (input.files[0]) {
      const isValid = await validateBookSize(input.files[0], index);
      if (!isValid) {
        validImages = false;
        break;
      }
    }
  }

  if (!validImages) return;

  // Создаем FormData для отправки файлов
  const formData = new FormData();
  formData.append('background', bgFile);
  
  // Добавляем книги
  bookFiles.forEach((input, index) => {
    if (input.files[0]) {
      formData.append(`book${index + 1}`, input.files[0]);
    }
  });

  // Добавляем выбранное разрешение
  const selectedResolution = document.querySelector('.size-btn.selected')?.textContent || '1920x1080';
  formData.append('resolution', selectedResolution);

  try {
    const response = await fetch('/upload/', {
      method: 'POST',
      body: formData
    });

    if (response.ok) {
      // Создаем ссылку для скачивания
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'bookshelf.png';
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } else {
      const error = await response.json();
      bookErrorMessageDiv.textContent = error.error || 'Произошла ошибка при генерации изображения';
    }
  } catch (error) {
    bookErrorMessageDiv.textContent = 'Ошибка при отправке данных на сервер';
    console.error('Error:', error);
  }
}

document.getElementById('generate-btn').addEventListener('click', validateAndUploadBooks);

document.querySelectorAll('.size-btn').forEach(button => {
  button.addEventListener('click', function() {
    // Удаляем класс selected у всех кнопок
    document.querySelectorAll('.size-btn').forEach(btn => btn.classList.remove('selected'));
    // Добавляем класс selected текущей кнопке
    this.classList.add('selected');
    
    // Показываем секцию загрузки фона
    const bgUploadSection = document.getElementById('bg-upload-section');
    bgUploadSection.style.display = 'block';
    
    // Очищаем сообщение об ошибке
    bgErrorMessageDiv.textContent = '';
    
    // Если уже есть загруженный файл фона, проверяем его размер заново
    const bgUpload = document.getElementById('bg-upload');
    if (bgUpload.files[0]) {
      bgUpload.dispatchEvent(new Event('change'));
    }
  });
});
