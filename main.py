# Главный файл приложения
from fastapi import FastAPI, HTTPException
from typing import List, Dict, Any
from datetime import datetime

app = FastAPI(
    title="ToDo лист API",
    description="API для управления задачами с использованием матрицы Эйзенхауэра",
    version="1.0.0",
    contact={"name": "Ксения"}
)

# Временное хранилище (позже будет заменено на PostgreSQL)
tasks_db: List[Dict[str, Any]] = [
    {
        "id": 1,
        "title": "Сдать проект по FastAPI",
        "description": "Завершить разработку API и написать документацию",
        "is_important": True,
        "is_urgent": True,
        "quadrant": "Q1",
        "completed": False,
        "created_at": datetime.now()
    },
    {
        "id": 2,
        "title": "Изучить SQLAlchemy",
        "description": "Прочитать документацию и попробовать примеры",
        "is_important": True,
        "is_urgent": False,
        "quadrant": "Q2",
        "completed": False,
        "created_at": datetime.now()
    },
    {
        "id": 3,
        "title": "Сходить на лекцию",
        "description": None,
        "is_important": False,
        "is_urgent": True,
        "quadrant": "Q3",
        "completed": False,
        "created_at": datetime.now()
    },
    {
        "id": 4,
        "title": "Посмотреть сериал",
        "description": "Новый сезон любимого сериала",
        "is_important": False,
        "is_urgent": False,
        "quadrant": "Q4",
        "completed": True,
        "created_at": datetime.now()
    },
]


@app.get("/")
async def welcome() -> dict:
    return {
        "title": app.title,
        "description": app.description,
        "version": app.version,
        "contact": app.contact,
    }


@app.get("/tasks")
async def get_all_tasks() -> dict:
    return {
        "count": len(tasks_db),  # считает количество записей в хранилище
        "tasks": tasks_db        # выводит всё, что есть в хранилище
    }


@app.get("/tasks/stats")
async def get_tasks_stats() -> dict:
    total_tasks = len(tasks_db)

    quadrant_stats = {quadrant: 0 for quadrant in ["Q1", "Q2", "Q3", "Q4"]}
    for task in tasks_db:
        quadrant = task.get("quadrant")
        if quadrant in quadrant_stats:
            quadrant_stats[quadrant] += 1

    completed_count = sum(1 for task in tasks_db if task.get("completed"))

    return {
        "total_tasks": total_tasks,
        "by_quadrant": quadrant_stats,
        "by_status": {
            "completed": completed_count,
            "pending": total_tasks - completed_count
        }
    }


@app.get("/tasks/search")
async def search_tasks(q: str) -> dict:
    query = q.strip()
    if len(query) < 2:
        raise HTTPException(
            status_code=400,
            detail="Поисковый запрос должен содержать минимум 2 символа"
        )

    query_lower = query.lower()
    filtered_tasks = [
        task for task in tasks_db
        if (task.get("title") and query_lower in task["title"].lower())
        or (task.get("description") and query_lower in task["description"].lower())
    ]

    if not filtered_tasks:
        raise HTTPException(
            status_code=404,
            detail="Задачи по запросу не найдены"
        )

    return {
        "query": query,
        "count": len(filtered_tasks),
        "tasks": filtered_tasks
    }


@app.get("/tasks/status/{status}")
async def get_tasks_by_status(status: str) -> dict:
    if status not in ["completed", "pending"]:
        raise HTTPException(
            status_code=404,
            detail="Указанный статус не найден. Используйте: completed, pending"
        )

    should_be_completed = status == "completed"
    filtered_tasks = [
        task for task in tasks_db if task.get("completed") == should_be_completed
    ]

    return {
        "status": status,
        "count": len(filtered_tasks),
        "tasks": filtered_tasks
    }


@app.get("/tasks/quadrant/{quadrant}")
async def get_tasks_by_quadrant(quadrant: str) -> dict:
    if quadrant not in ["Q1", "Q2", "Q3", "Q4"]:
        raise HTTPException(
            status_code=400,
            detail="Неверный квадрант. Используйте: Q1, Q2, Q3, Q4"
        )

    filtered_tasks = [
        task                     # ЧТО добавляем в список
        for task in tasks_db     # ОТКУДА берём элементы
        if task["quadrant"] == quadrant  # УСЛОВИЕ фильтрации
    ]

    return {
        "quadrant": quadrant,
        "count": len(filtered_tasks),
        "tasks": filtered_tasks
    }


@app.get("/tasks/{task_id}")
async def get_task_by_id(task_id: int) -> dict:
    for task in tasks_db:
        if task["id"] == task_id:
            return task

    raise HTTPException(
        status_code=404,
        detail="Задача не найдена"
    )
