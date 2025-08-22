# Quests (Контент/Авторинг)

Назначение:
- Импорт/сохранение JSON-графа в сущности Quest/QuestVersion/GraphNode/GraphEdge
- Валидация квеста и графа версии (reachability/exitability/self-loops/duplicates)
- В дальнейшем: операции авторинга (редактор графа), публикация/архивация, блокировки

Модули:
- importer.py — persist_generated_quest
- validation.py — validate_version_graph, validate_quest
