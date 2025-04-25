document.addEventListener('DOMContentLoaded', function() {
    const idLesson = document.getElementById('idLesson');
    const idUser = document.getElementById('idUser');
    const runBtn = document.getElementById('runCode');
    const checkBtn = document.getElementById('checkCode');
    const codeEditor = document.getElementById('codeEditor');
    const output = document.getElementById('output');
    const successAlert = document.getElementById('successAlert');
    const dangerAlert = document.getElementById('dangerAlert');

    if (runBtn) {
        runBtn.addEventListener('click', function() {
            try {
                // Очищаем предыдущий вывод
                output.innerHTML = '';
                
                // Захватываем console.log
                const originalLog = console.log;
                console.log = function() {
                    for (let i = 0; i < arguments.length; i++) {
                        output.innerHTML += '<div>' + arguments[i] + '</div>';
                    }
                    originalLog.apply(console, arguments);
                };
                
                // Выполняем код
                new Function(codeEditor.value)();
                
                // Восстанавливаем console.log
                console.log = originalLog;
            } catch (e) {
                output.innerHTML = '<div class="text-danger">Ошибка: ' + e.message + '</div>';
            }
        });
    }
    
    if (checkBtn) {
        checkBtn.addEventListener('click', async function() {
            try {


                const normalizeCode = (code) => {
                    return code
                        .replace(/\s+/g, ' ')       // Заменяем все пробельные символы на один пробел
                        .replace(/\/\/.*$/gm, '')  // Удаляем однострочные комментарии
                        .trim();
                };

                // Получаем данные с сервера (правильное решение)
                const response = await fetch(`http://127.0.0.1:5000/api/lesson/${idLesson.value}`);
                if (!response.ok) {
                    throw new Error('Network response was not ok');
                }
                const data = await response.json();
                
                // Сравниваем решения
                const isCorrect = normalizeCode(data.solution) === normalizeCode(codeEditor.value);
                
                // Показываем соответствующее уведомление
                if (isCorrect) {
                    dangerAlert.classList.add('d-none');
                    successAlert.classList.remove('d-none');
                    successAlert.classList.add('fade-in');
                } else {
                    successAlert.classList.add('d-none');
                    dangerAlert.classList.remove('d-none');
                    dangerAlert.classList.add('fade-in');
                }
                
                // Отправляем решение пользователя на сервер для сохранения
                const saveResponse = await fetch('http://127.0.0.1:5000/api/save-solution', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        user_id: idUser.value, // Должен быть определен где-то в вашем коде
                        lesson_id: idLesson.value, // Или динамически определять текущий урок
                        code: codeEditor.value,
                        is_correct: isCorrect
                    })
                });
                
                if (!saveResponse.ok) {
                    console.error('Failed to save solution');
                }
                
            } catch (error) {
                console.error('Error:', error);
            }
            
            // Прокрутка к сообщению
            successAlert.scrollIntoView({ behavior: 'smooth' });
        });
    }
});


