import asyncio
import json
from datetime import datetime
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from apscheduler.schedulers.background import BackgroundScheduler
from typing import Dict

router = APIRouter(
    prefix="/notifications",
    tags=["Notifications"],
    responses={404: {"description": "Not found"}},
)

# 사용자 ID와 WebSocket 매핑
connections: Dict[str, WebSocket] = {}
scheduler = BackgroundScheduler()
scheduler.start()


# WebSocket 연결 관리
@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, user_id: str = Query(...)):
    await websocket.accept()
    connections[user_id] = websocket
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        connections.pop(user_id, None)  # 연결 종료 시 제거


# 특정 사용자에게 알림 전송
async def send_notification_to_user(user_id: str, title: str, body: str, image: str):
    if user_id in connections:
        websocket = connections[user_id]
        data = json.dumps(
            {
                "title": title,
                "body": body,
                "image": image,
                "time": datetime.now().isoformat(),
            },
            ensure_ascii=False,
        )
        try:
            await websocket.send_text(data)
        except Exception:
            connections.pop(user_id, None)  # 오류 발생 시 연결 제거


# 즉시 특정 사용자에게 알림 전송
@router.post("/send-notification/")
async def send_notification_now(user_id: str, title: str, body: str, image: str):
    if user_id not in connections:
        return {
            "status": "User not connected",
            "user_id": user_id,
        }

    await send_notification_to_user(user_id, title, body, image)
    return {
        "status": "Notification sent",
        "user_id": user_id,
        "title": title,
        "body": body,
        "image": image,
    }


# 관리자가 특정 사용자에게 알림 예약
@router.post("/schedule-notification/")
async def schedule_notification(
    user_id: str, title: str, message: str, image: str, notify_time: datetime
):
    # 스케줄러에 작업 추가
    def schedule_task():
        asyncio.create_task(send_notification_to_user(user_id, title, message, image))

    scheduler.add_job(schedule_task, "date", run_date=notify_time)
    return {
        "status": "Notification scheduled",
        "user_id": user_id,
        "message": message,
        "image": image,
        "notify_time": notify_time.isoformat(),
    }
