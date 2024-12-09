console.log("Скрипт загружен");
let bookCount = 1;

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
    alert("Пожалуйста, загрузите фон.");
    return;
  }

  if (bookFiles.length === 0 || !bookFiles[0].files[0]) {
    alert("Пожалуйста, загрузите хотя бы одну книгу.");
    return;
  }

  const formData = new FormData();
  formData.append('background', bgFile);
  bookFiles.forEach((input, index) => {
    if (input.files[0]) {
      formData.append(`book${index + 1}`, input.files[0]);
    }
  });

  try {
    const response = await fetch('http://127.0.0.1:8000/upload/', {
      method: 'POST',
      body: formData,
    });
    if (!response.ok) throw new Error('Ошибка при генерации изображения');

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
    alert(error.message);
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
