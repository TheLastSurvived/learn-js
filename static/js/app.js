document.addEventListener('DOMContentLoaded', function() {
    document.querySelectorAll('.check-code').forEach(button => {
        button.addEventListener('click', async function() {
            const taskId = this.getAttribute('data-task-id');
            const idLesson = document.getElementById('idLesson').value;
            const idTask = document.getElementById('idtask').value;
            const idUser = document.getElementById('idUser').value;
            const codeEditor = document.getElementById(`codeEditor${taskId}`);
            const output = document.getElementById(`output${taskId}`);
            const outputContainer = document.getElementById(`outputContainer${taskId}`);
            const successAlert = document.getElementById(`successAlert${taskId}`);
            const dangerAlert = document.getElementById(`dangerAlert${taskId}`);
            const loadingSpinner = document.getElementById('loadingSpinner');
        
            try {
                // Показываем спиннер загрузки
                loadingSpinner.classList.remove('d-none');
                outputContainer.classList.add('d-none');
                successAlert.classList.add('d-none');
                dangerAlert.classList.add('d-none');

                // Получаем данные задания
                const response = await fetch(`/api/task/${taskId}`);
                if (!response.ok) throw new Error('Network response was not ok');
                const taskData = await response.json();

                // Подготовка контекста
                const context = {};
                
                // Выполняем эталонное решение
                try {
                    const solutionFunc = new Function(taskData.solution + '; return result;');
                    const expectedResult = solutionFunc.call(context);
                    
                    // Выполняем пользовательский код
                    try {
                        const userFunc = new Function(codeEditor.value + '; return result;');
                        const userResult = userFunc.call(context);
                        
                        // Сравниваем результаты
                        const isCorrect = JSON.stringify(userResult) === JSON.stringify(expectedResult);
                        
                        // Показываем результаты
                        outputContainer.classList.remove('d-none');
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
                        const saveResponse = await fetch(`/api/save-solution`, {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({
                                user_id: idUser,
                                lesson_id: idLesson,
                                task_id: taskId,
                                code: codeEditor.value,
                                is_correct: isCorrect
                            })
                        });
                        
                        if (!saveResponse.ok) {
                            throw new Error('Ошибка при сохранении решения');
                        }
                        
                    } catch (userError) {
                        outputContainer.classList.remove('d-none');
                        output.innerHTML = `<div class="text-danger">Ошибка в вашем коде: ${userError.message}</div>`;
                    }
                    
                } catch (solutionError) {
                    outputContainer.classList.remove('d-none');
                    output.innerHTML = `<div class="text-danger">Ошибка в эталонном решении: ${solutionError.message}</div>`;
                }
                
            } catch (error) {
                console.error('Error:', error);
                outputContainer.classList.remove('d-none');
                output.innerHTML = `<div class="text-danger">Ошибка: ${error.message}</div>`;
            } finally {
                loadingSpinner.classList.add('d-none');
                successAlert.scrollIntoView({ behavior: 'smooth' });
            }
        });
    });
});