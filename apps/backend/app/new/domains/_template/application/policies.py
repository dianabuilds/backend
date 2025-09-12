
# Здесь только решение "можно/нельзя". Вызовы к systems/iam делаются через тонкий клиент.
# В шаблоне оставлены заглушки.

class Forbidden(Exception):
    pass

def check_read(subject: dict, resource_id: str) -> None:
    # пример: владелец или модератор
    if subject.get("role") in {"admin", "moderator"}:
        return
    if subject.get("user_id") == resource_id:
        return
    raise Forbidden("access_denied")

def check_update(subject: dict, resource: dict) -> None:
    # пример: владелец ресурса
    if subject.get("role") in {"admin", "moderator"}:
        return
    if subject.get("user_id") == resource.get("id"):
        return
    raise Forbidden("access_denied")
