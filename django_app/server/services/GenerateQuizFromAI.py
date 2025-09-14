import json
from groq import Groq, GroqError
from project.settings.base import GROQ_API_KEY
from ..exceptions import APIKeyNotConfiguredError, APICommunicationError
from pydantic import BaseModel, Field
from typing import List

class QuizQuestionSchema(BaseModel):
    """Define a estrutura de uma única questão do quiz."""
    question: str = Field(..., description="O texto da pergunta do quiz.")
    options: List[str] = Field(
        ...,
        description="Uma lista contendo exatamente 5 opções de resposta.",
        min_length=5,
        max_length=5
    )
    correctOption: int = Field(
        ...,
        description="O índice (0, 1, 2, 3 ou 4) da opção correta na lista de opções."
    )

class QuizSchema(BaseModel):
    """Define a estrutura do quiz completo, contendo uma lista de questões."""
    questions: List[QuizQuestionSchema] = Field(
        ...,
        description="A lista de questões para o quiz."
    )

def generate_quiz_with_groq(user_prompt: str, num_questions: int) -> dict:
    """
    Gera um quiz utilizando a API da Groq.

    Args:
        user_prompt: O tópico para o quiz.
        num_questions: O número de questões a serem geradas.

    Returns:
        Um dicionário contendo os dados do quiz gerado.

    Raises:
        APIKeyNotConfiguredError: Se a GROQ_API_KEY não estiver configurada.
        APICommunicationError: Se ocorrer um erro na comunicação com a API da Groq.
    """
    api_key = GROQ_API_KEY
    if not api_key:
        raise APIKeyNotConfiguredError("A chave da API da Groq (GROQ_API_KEY) não está configurada no servidor.")

    client = Groq(api_key=api_key)

    system_prompt = """
    Você é um assistente especialista em criar quizzes educacionais.
    Sua tarefa é gerar um quiz em formato JSON bem estruturado, baseado no tema fornecido.
    O JSON deve seguir rigorosamente a seguinte estrutura:
    {
      "title": "Um título criativo para o quiz",
      "questions": [
        {
          "question_text": "O texto da pergunta.",
          "options": ["Opção A", "Opção B", "Opção C", "Opção D"],
          "correct_option_index": 2,
          "explanation": "Uma breve explicação do porquê a resposta está correta."
        }
      ]
    }
    REGRAS ESSENCIAIS:
    1. Sua resposta deve conter APENAS o objeto JSON. Nenhum texto antes ou depois.
    2. O campo "options" deve ter exatamente 4 strings.
    3. O campo "correct_option_index" deve ser um número de 0 a 3.
    """

    try:
        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Gere um quiz com {num_questions} questões sobre o seguinte tema: '{user_prompt}'."},
            ],
            model="llama-3.1-8b-instant",
            temperature=0.7,
            response_format={"type": "json_object"},
        )
        
        response_content = chat_completion.choices[0].message.content
        quiz_data = json.loads(response_content)
        return quiz_data

    except GroqError as e:
        raise APICommunicationError(f"Erro na API da Groq: {e}")
    except json.JSONDecodeError:
        raise APICommunicationError("A resposta da API da Groq não era um JSON válido.")
    except Exception as e:
        raise APICommunicationError(f"Um erro inesperado ocorreu: {e}")