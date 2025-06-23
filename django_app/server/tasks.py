from celery import shared_task
import requests
from django.conf import settings


@shared_task
def send_quiz_task(chat_id, questions):
    TELEGRAM_API = settings.TELEGRAM_API
    results = []
    for quiz in questions:
        question = quiz['question']
        options = quiz['options']
        correct_option = quiz['correctOption']

        try:
            response = requests.post(f"{TELEGRAM_API}/sendPoll", json={
                "chat_id": chat_id,
                "question": question,
                "options": options,
                "is_anonymous": False,
                "type": "quiz",
                "correct_option_id": correct_option,
            })
            
            results.append({
                "question": question,
                "status": "success" if response.status_code == 200 else "error",
                "message": response.json() if response.status_code != 200 else ""
            })

        except Exception as e:
            results.append({
                "question": question,
                "status": "error",
                "message": str(e)
            })

    return results
