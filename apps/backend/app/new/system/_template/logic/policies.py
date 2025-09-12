
class Quota:
    def __init__(self, limit_per_minute=120):
        self.limit = limit_per_minute
    def check(self, message):
        # Заглушка: здесь должны быть лимиты и счётчики
        return True
