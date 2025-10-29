from fastapi import APIRouter, HTTPException, Query, Response, status
from datetime import datetime
from typing import Dict, Any

from database import tasks_db
from schemas import TaskCreate, TaskResponse, TaskUpdate

router = APIRouter()

@router.post("/", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(task: TaskCreate) -> TaskResponse:
    """
    Создание новой задачи
    
    - title: Название задачи (обязательное, 3-100 символов)
    - description: Описание задачи (опциональное, до 500 символов)
    - is_important: Важная ли задача
    - is_urgent: Срочная ли задача
    """
    # Определяем квадрант
    if task.is_important and task.is_urgent:
        quadrant = "Q1"
    elif task.is_important and not task.is_urgent:
        quadrant = "Q2"
    elif not task.is_important and task.is_urgent:
        quadrant = "Q3"
    else:
        quadrant = "Q4"
    
    new_id = max([t["id"] for t in tasks_db], default=0) + 1  # Генерируем новый ID

    new_task = {
        "id": new_id,
        "title": task.title,
        "description": task.description,
        "is_important": task.is_important,
        "is_urgent": task.is_urgent,
        "quadrant": quadrant,
        "completed": False,
        "created_at": datetime.now()
    }
    
    tasks_db.append(new_task)  # "Сохраняем" в нашу "базу данных"

    # Возвращаем созданную задачу (FastAPI автоматически преобразует dict в Pydantic-модель TaskResponse)
    return new_task


@router.get("/", response_model=Dict[str, Any])
async def get_all_tasks() -> dict:
    return {
        "count": len(tasks_db),
        "tasks": tasks_db
    }


@router.get("/search")
async def search_tasks(q: str = Query(..., min_length=2)) -> dict:
    keyword = q.lower()
    results = [
        task for task in tasks_db
        if keyword in task["title"].lower()
        or (task["description"] and keyword in task["description"].lower())
    ]

    if not results:
        raise HTTPException(status_code=404, detail=f"Задачи, содержащие '{q}', не найдены")

    return {
        "query": q,
        "count": len(results),
        "tasks": results
    }


@router.get("/status/{status}")
async def get_tasks_by_status(status: str) -> dict:
    valid_statuses = ["completed", "pending"]
    if status not in valid_statuses:
        raise HTTPException(
            status_code=404, 
            detail=f"Статус '{status}' не найден. Допустимые статусы: {valid_statuses}"
        )
    
    # Преобразуем строковый статус в булево значение
    is_completed = status == "completed"
    
    filtered_tasks = [task for task in tasks_db if task["completed"] == is_completed]
    
    return {
        "status": status,
        "count": len(filtered_tasks),
        "tasks": filtered_tasks
    }


@router.get("/quadrant/{quadrant}")
async def get_tasks_by_quadrant(quadrant: str) -> dict:
    valid_quadrants = ["Q1", "Q2", "Q3", "Q4"]
    if quadrant not in valid_quadrants:
        raise HTTPException(
            status_code=404, 
            detail=f"Квадрант '{quadrant}' не найден. Допустимые квадранты: {valid_quadrants}"
        )
    
    filtered_tasks = [task for task in tasks_db if task["quadrant"] == quadrant]
    
    return {
        "quadrant": quadrant,
        "count": len(filtered_tasks),
        "tasks": filtered_tasks
    }


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task_by_id(task_id: int) -> TaskResponse:
    task = next((
        task for task in tasks_db
        if task["id"] == task_id),
        None
    )
    if not task:
        raise HTTPException(status_code=404, detail="Задача не найдена")
    return task

@router.put("/{task_id}", response_model=TaskResponse)
async def update_task(task_id: int, task_update: TaskUpdate) -> TaskResponse:
    # ШАГ 1: по аналогии с GET ищем задачу по ID
    task = next((task for task in tasks_db if task["id"] == task_id), None)
    if not task:
        raise HTTPException(status_code=404, detail="Задача не найдена")

    # ШАГ 2: Получаем и обновляем только переданные поля (exclude_unset=True)
    # Без exclude_unset=True все None поля тоже попадут в словарь
    update_data = task_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        task[field] = value

    # ШАГ 3: Пересчитываем квадрант, если изменились важность или срочность
    if "is_important" in update_data or "is_urgent" in update_data:
        if task["is_important"] and task["is_urgent"]:
            task["quadrant"] = "Q1"
        elif task["is_important"] and not task["is_urgent"]:
            task["quadrant"] = "Q2"
        elif not task["is_important"] and task["is_urgent"]:
            task["quadrant"] = "Q3"
        else:
            task["quadrant"] = "Q4"

    return task


@router.patch("/{task_id}/complete", response_model=TaskResponse)
async def complete_task(task_id: int) -> TaskResponse:
    task = next((task for task in tasks_db if task["id"] == task_id), None)
    if not task:
        raise HTTPException(status_code=404, detail="Задача не найдена")

    task["completed"] = True
    task["completed_at"] = datetime.now()

    return task


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(task_id: int):
    task = next((task for task in tasks_db if task["id"] == task_id), None)
    if not task:
        raise HTTPException(status_code=404, detail="Задача не найдена")

    tasks_db.remove(task)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
