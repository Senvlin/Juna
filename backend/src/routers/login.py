from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/api/login", tags=["登录"])


@router.post("/start")
async def start_login_api():
    from backend.src.services.login_service import start_login

    task_id = start_login()
    return {"task_id": task_id, "message": "登录任务已启动"}


@router.get("/status/{task_id}")
async def login_status_api(task_id: str):
    from backend.src.services.login_service import get_login_task

    task = get_login_task(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="登录任务不存在或已过期")
    return {"task_id": task_id, "status": task["status"], "message": task["message"]}
