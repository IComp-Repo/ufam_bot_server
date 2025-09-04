from celery import shared_task
import requests
from django.utils import timezone
from project.settings.base import TELEGRAM_API
from .models import Quiz, QuizQuestion, QuizOption, QuizMessage

@shared_task
def send_quiz_task(quiz_id, chat_id, questions):
    """
    Envia perguntas de um Quiz para o Telegram e salva no banco.
    :param quiz_id: ID do Quiz já criado na view
    :param chat_id: chat_id do grupo
    :param questions: lista [{question, options, correct_option_id}, ...]
    """
    results = []
    try:
        quiz = Quiz.objects.get(id=quiz_id)
    except Quiz.DoesNotExist:
        return [{"status": "error", "message": f"Quiz {quiz_id} não encontrado"}]

    for idx, q in enumerate(questions):
        question_text = q["question"]
        options = q["options"]
        correct_idx = q.get("correct_option_id") or q.get("correctOption")

        try:
            resp = requests.post(f"{TELEGRAM_API}/sendPoll", json={
                "chat_id": chat_id,
                "question": question_text,
                "options": options,
                "is_anonymous": False,
                "type": "quiz",
                "correct_option_id": correct_idx,
            }, timeout=20)

            if resp.status_code != 200:
                results.append({
                    "index": idx,
                    "question": question_text,
                    "status": "error",
                    "error": resp.text,
                })
                continue

            data = resp.json().get("result", {})
            message_id = data.get("message_id")
            poll_obj = data.get("poll") or {}
            telegram_poll_id = poll_obj.get("id")

            # cria a pergunta no banco
            qq = QuizQuestion.objects.create(
                quiz=quiz,
                text=question_text,
                correct_option_index=correct_idx,
                telegram_poll_id=telegram_poll_id
            )

            # cria opções
            for o_idx, opt_text in enumerate(options):
                QuizOption.objects.create(question=qq, option_index=o_idx, text=opt_text)

            # cria mensagem vinculada
            if message_id:
                QuizMessage.objects.create(
                    question=qq,
                    chat_id=str(chat_id),
                    message_id=message_id,
                    sent_at=timezone.now()
                )

            results.append({
                "index": idx,
                "question": question_text,
                "status": "success",
                "question_id": qq.id,
            })

        except Exception as e:
            results.append({
                "index": idx,
                "question": question_text,
                "status": "error",
                "error": str(e),
            })

    return results
