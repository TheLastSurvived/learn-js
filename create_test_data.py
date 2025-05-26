from app import app, db
from app import Test, TestQuestion

with app.app_context():
    # Тест по основам JavaScript
    js_basics = Test(
        title="Основы JavaScript",
        description="Проверьте свои знания базового синтаксиса JavaScript"
    )
    db.session.add(js_basics)
    
    questions = [
        {
            "question": "Какой оператор используется для присваивания значения?",
            "options": {"a": "=", "b": "==", "c": ":=", "d": "==="},
            "correct": "a"
        },
        {
            "question": "Что выведет код: console.log(typeof null)?",
            "options": {"a": "null", "b": "undefined", "c": "object", "d": "string"},
            "correct": "c",
            "code_snippet": "console.log(typeof null);"
        },
        # Добавьте больше вопросов
    ]
    
    for q in questions:
        question = TestQuestion(
            test=js_basics,
            question=q["question"],
            options=q["options"],
            correct_answer=q["correct"],
            code_snippet=q.get("code_snippet", None)
        )
        db.session.add(question)
    
    db.session.commit()