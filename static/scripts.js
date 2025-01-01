// В начале файла добавляем получение кнопки
const generateBtn = document.getElementById('generate-btn');

// Проверка размера фона
const bgErrorMessageDiv = document.createElement('div');
bgErrorMessageDiv.style.color = 'red';
bgErrorMessageDiv.style.marginTop = '10px';

const bgUploadSection = document.getElementById('bg-upload-section');
bgUploadSection.appendChild(bgErrorMessageDiv);

document.getElementById('bg-upload').addEventListener('change', function () {
  const file = this.files[0];
  const generateBtn = document.getElementById('generate-btn');
  
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
          generateBtn.style.backgroundColor = '#ff4444';
          generateBtn.disabled = true;
        } else {
          bgErrorMessageDiv.textContent = '';
          generateBtn.style.backgroundColor = '#4CAF50';
          generateBtn.disabled = false;
        }
      };
    };
    reader.readAsDataURL(file);
  }
});

// Создаем div для сообщений об ошибках книг
const bookErrorMessageDiv = document.createElement('div');
bookErrorMessageDiv.id = 'book-error-message';
bookErrorMessageDiv.style.color = 'red';
bookErrorMessageDiv.style.marginTop = '10px';
document.getElementById('book-upload-section').appendChild(bookErrorMessageDiv);

let bookCount = 1;
const MAX_BOOKS = 8;

function validateBookSize(file) {
  const img = new Image();
  const reader = new FileReader();
  
  reader.onload = (e) => {
    img.src = e.target.result;
    img.onload = () => {
      const aspectRatio = img.width / img.height;
      // Проверяем соотношение сторон (должно быть примерно 2:3)
      if (Math.abs(aspectRatio - (2/3)) > 0.1) {
        bookErrorMessageDiv.textContent = "Неподходящее соотношение сторон книги";
        generateBtn.style.backgroundColor = '#ff4444';
        generateBtn.disabled = true;
        return;
      }
      bookErrorMessageDiv.textContent = '';
      generateBtn.style.backgroundColor = '#4CAF50';
      generateBtn.disabled = false;
    };
  };
  reader.readAsDataURL(file);
}

document.getElementById('add-book-btn').addEventListener('click', function () {
  if (bookCount >= MAX_BOOKS) {
    return; // Не добавляем новые поля, если достигнут максимум
  }
  
  bookCount++;

  const bookUploadSection = document.getElementById('book-upload-section');
  const newBookField = document.createElement('div');
  newBookField.classList.add('upload-field');
  newBookField.innerHTML = `
    <label>Добавить книгу ${bookCount}:</label>
    <input type="file" accept="image/*" class="book-upload">
  `;
  bookUploadSection.appendChild(newBookField);

  // Если достигли максимума, делаем кнопку неактивной
  if (bookCount >= MAX_BOOKS) {
    this.disabled = true;
    this.style.backgroundColor = '#cccccc';
  }

  const newInput = newBookField.querySelector('.book-upload');
  newInput.addEventListener('change', function() {
    if (this.files[0]) {
      validateBookSize(this.files[0]);
    }
  });
});

document.querySelector('.book-upload').addEventListener('change', function() {
  if (this.files[0]) {
    validateBookSize(this.files[0]);
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
      const isValid = await validateBookSize(input.files[0]);
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
