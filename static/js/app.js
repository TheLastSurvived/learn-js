const currentUrl = window.location.host ;


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
                // Получаем данные урока
                const response = await fetch(`https://${currentUrl}/api/lesson/${idLesson.value}`);
                if (!response.ok) throw new Error('Network response was not ok');
                const lessonData = await response.json();
                
                // Подготовка контекста
                const context = {};
                
                // Выполняем эталонное решение
                try {
                    const solutionFunc = new Function(lessonData.solution + '; return result;');
                    const expectedResult = solutionFunc.call(context);
                    
                    // Выполняем пользовательский код
                    try {
                        
                        const userFunc = new Function(codeEditor.value + '; return result;');
                        const userResult = userFunc.call(context);
                        
                        // Сравниваем результаты
                        const isCorrect = JSON.stringify(userResult) === JSON.stringify(expectedResult);
                        
                        // Показываем результаты
                        if (isCorrect) {
                            dangerAlert.classList.add('d-none');
                            successAlert.classList.remove('d-none');
                            output.innerHTML = `
                                <div class="text-success">Ваш результат: ${JSON.stringify(userResult)}</div>
                                <div class="text-success">Ожидаемый результат: ${JSON.stringify(expectedResult)}</div>
                            `;
                        } else {
                            successAlert.classList.add('d-none');
                            dangerAlert.classList.remove('d-none');
                            output.innerHTML = `
                                <div class="text-danger">Ваш результат: ${JSON.stringify(userResult)}</div>
                                <div class="text-danger">Ожидаемый результат: ${JSON.stringify(expectedResult)}</div>
                            `;
                        }
                        
                        // Сохраняем решение
                        const saveResponse = await fetch(`https://${currentUrl}/api/save-solution`, {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({
                                user_id: idUser.value,
                                lesson_id: idLesson.value,
                                code: codeEditor.value,
                                is_correct: isCorrect
                            })
                        });
                        
                    } catch (userError) {
                        output.innerHTML = `<div class="text-danger">Ошибка в вашем коде: ${userError.message}</div>`;
                    }
                    
                } catch (solutionError) {
                    output.innerHTML = `<div class="text-danger">Ошибка в эталонном решении: ${solutionError.message}</div>`;
                }
                
            } catch (error) {
                console.error('Error:', error);
                output.innerHTML = `<div class="text-danger">Ошибка: ${error.message}</div>`;
            }
            
            successAlert.scrollIntoView({ behavior: 'smooth' });
        });
    }
});


