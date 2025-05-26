document.addEventListener('DOMContentLoaded', function() {
    document.querySelectorAll('.check-code').forEach(button => {
        button.addEventListener('click', async function() {
            const taskId = this.getAttribute('data-task-id');
            const codeEditor = document.getElementById(`codeEditor${taskId}`);
            const output = document.getElementById(`output${taskId}`);
            const successAlert = document.getElementById(`successAlert${taskId}`);
            const dangerAlert = document.getElementById(`dangerAlert${taskId}`);

            // Добавляем вывод результата
            const wrappedCode = `${userCode}\nconsole.log(result);`;
            
            // UI состояния
            this.disabled = true;
            const originalText = this.innerHTML;
            this.innerHTML = '<span class="spinner-border spinner-border-sm"></span> Проверка...';
            output.innerHTML = '';
            
            try {
                const response = await fetch('/api/check-js-solution', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({
                        user_id: document.getElementById('idUser').value,
                        lesson_id: document.getElementById('idLesson').value,
                        task_id: taskId,
                        code: wrappedCode
                    })
                });

                const data = await response.json();
                
                if (data.is_correct) {
                    output.innerHTML = `
                        <div class="text-success">✓ Верное решение!</div>
                        <div class="text-muted">Результат: ${data.user_result}</div>
                    `;
                    successAlert.classList.remove('d-none');
                    dangerAlert.classList.add('d-none');
                } else {
                    output.innerHTML = `
                        <div class="text-danger">✗ Неверное решение</div>
                        <div class="text-muted">Ваш результат: ${data.user_result || 'нет'}</div>
                        <div class="text-muted">Ожидаемый: ${data.expected_result}</div>
                    `;
                    dangerAlert.classList.remove('d-none');
                    successAlert.classList.add('d-none');
                }
            } catch (error) {
                output.innerHTML = '<div class="text-danger">Ошибка соединения</div>';
                console.error('Error:', error);
            } finally {
                this.disabled = false;
                this.innerHTML = originalText;
            }
        });
    });
});