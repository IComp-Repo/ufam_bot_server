class QuizGenerationError(Exception):
    """Exceção base para erros na geração de quizzes."""
    pass

class APIKeyNotConfiguredError(QuizGenerationError):
    """Lançada quando a chave da API não está configurada."""
    pass

class APICommunicationError(QuizGenerationError):
    """Lançada quando há um erro de comunicação com a API externa."""
    pass