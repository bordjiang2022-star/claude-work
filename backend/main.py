# main.py - FastAPI主服务器
import os
import asyncio
from datetime import datetime, timedelta
from typing import Optional, List
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse, Response
from pydantic import BaseModel, EmailStr
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
import json
import io
import httpx

from database import init_db, get_db, User, TranslationSession, Transcript, UserStatistics
from auth import (
    authenticate_user,
    create_user,
    create_access_token,
    get_current_user,
    ACCESS_TOKEN_EXPIRE_MINUTES
)
from translation_service import translation_service
from audio_control import audio_controller

# 创建FastAPI应用
app = FastAPI(title="LiveTranslate API", version="2.0")

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============ Pydantic模型 ============

class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserRegister(BaseModel):
    email: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str


class TranslationConfig(BaseModel):
    target_language: str
    voice: Optional[str] = "Cherry"
    audio_enabled: bool = True


class TranscriptResponse(BaseModel):
    id: int
    timestamp: datetime
    source_text: Optional[str]
    translated_text: Optional[str]


class SessionResponse(BaseModel):
    id: int
    source_language: Optional[str]
    target_language: str
    voice: Optional[str]
    started_at: datetime
    ended_at: Optional[datetime]
    duration_seconds: float


class StatisticsResponse(BaseModel):
    total_sessions: int
    total_duration_seconds: float
    total_characters_translated: int
    last_updated: datetime


# ============ 启动和关闭事件 ============

@app.on_event("startup")
async def startup_event():
    """应用启动时初始化数据库"""
    await init_db()
    print("[Server] Database initialized")


@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭时清理资源"""
    print("[Server] Shutting down...")


# ============ 认证端点 ============

@app.post("/api/auth/register", response_model=Token)
async def register(user_data: UserRegister, db: AsyncSession = Depends(get_db)):
    """用户注册"""
    user = await create_user(db, user_data.email, user_data.password)

    access_token = create_access_token(
        data={"sub": user.email},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )

    return {"access_token": access_token, "token_type": "bearer"}


@app.post("/api/auth/login", response_model=Token)
async def login(user_data: UserLogin, db: AsyncSession = Depends(get_db)):
    """用户登录"""
    user = await authenticate_user(db, user_data.email, user_data.password)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 更新最后登录时间
    user.last_login = datetime.utcnow()
    await db.commit()

    access_token = create_access_token(
        data={"sub": user.email},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )

    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/api/auth/me")
async def get_me(current_user: User = Depends(get_current_user)):
    """获取当前用户信息"""
    return {
        "id": current_user.id,
        "email": current_user.email,
        "created_at": current_user.created_at,
        "last_login": current_user.last_login
    }


# ============ 翻译控制端点 ============

@app.post("/api/translation/start")
async def start_translation(
    config: TranslationConfig,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """启动翻译会话"""
    # 获取API密钥
    api_key = os.getenv("DASHSCOPE_API_KEY", "")
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="API key not configured"
        )

    # 检查是否已有活动会话
    if translation_service.is_session_active(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Translation session already active"
        )

    # 切换到虚拟音频线缆
    if config.audio_enabled:
        audio_controller.switch_to_virtual_cable()

    # 创建会话记录
    session = TranslationSession(
        user_id=current_user.id,
        target_language=config.target_language,
        voice=config.voice,
        started_at=datetime.utcnow()
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)

    # 定义文本接收回调函数
    async def on_text_received(text: str):
        """当收到翻译文本时的回调"""
        # 发送到WebSocket
        await manager.send_message(current_user.id, {
            "type": "transcript",
            "data": {
                "source_text": "",  # API不提供源文本
                "translated_text": text.strip()
            }
        })

        # 保存到数据库（仅保存完整的句子，不保存增量）
        if text.strip() and text.endswith("\n"):
            transcript = Transcript(
                session_id=session.id,
                timestamp=datetime.utcnow(),
                source_text=None,
                translated_text=text.strip()
            )
            db.add(transcript)
            await db.commit()

    # 启动翻译服务
    # 注意：audio_enabled设为False，因为TTS在前端浏览器播放（使用Web Speech API）
    # 这样可以减少API成本和网络延迟
    success = await translation_service.start_translation(
        user_id=current_user.id,
        api_key=api_key,
        target_language=config.target_language,
        voice=None,  # 不使用后端TTS
        audio_enabled=False,  # 前端使用Web Speech API播放
        on_text_callback=on_text_received
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to start translation service"
        )

    return {
        "status": "started",
        "session_id": session.id,
        "target_language": config.target_language,
        "voice": config.voice
    }


@app.post("/api/translation/stop")
async def stop_translation(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """停止翻译会话"""
    # 停止翻译服务
    await translation_service.stop_translation(current_user.id)

    # 恢复默认音频设备
    audio_controller.restore_default_device()

    # 更新会话记录（取最新的一个未结束会话）
    result = await db.execute(
        select(TranslationSession)
        .where(TranslationSession.user_id == current_user.id)
        .where(TranslationSession.ended_at.is_(None))
        .order_by(TranslationSession.started_at.desc())
        .limit(1)
    )
    session = result.scalar_one_or_none()

    if session:
        session.ended_at = datetime.utcnow()
        session.duration_seconds = (session.ended_at - session.started_at).total_seconds()

        # 更新用户统计
        stats_result = await db.execute(
            select(UserStatistics).where(UserStatistics.user_id == current_user.id)
        )
        stats = stats_result.scalar_one_or_none()

        if stats:
            stats.total_sessions += 1
            stats.total_duration_seconds += session.duration_seconds
            stats.last_updated = datetime.utcnow()

        await db.commit()

    return {"status": "stopped"}


@app.get("/api/translation/status")
async def get_translation_status(current_user: User = Depends(get_current_user)):
    """获取翻译状态"""
    status_info = await translation_service.get_session_status(current_user.id)
    return status_info


# ============ 会话和转录端点 ============

@app.get("/api/sessions", response_model=List[SessionResponse])
async def get_sessions(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    limit: int = 10
):
    """获取用户的翻译会话列表"""
    result = await db.execute(
        select(TranslationSession)
        .where(TranslationSession.user_id == current_user.id)
        .order_by(TranslationSession.started_at.desc())
        .limit(limit)
    )
    sessions = result.scalars().all()
    return sessions


@app.get("/api/sessions/{session_id}/transcripts", response_model=List[TranscriptResponse])
async def get_transcripts(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取会话的转录文本"""
    # 验证会话属于当前用户
    session_result = await db.execute(
        select(TranslationSession)
        .where(TranslationSession.id == session_id)
        .where(TranslationSession.user_id == current_user.id)
    )
    session = session_result.scalar_one_or_none()

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # 获取转录
    transcripts_result = await db.execute(
        select(Transcript)
        .where(Transcript.session_id == session_id)
        .order_by(Transcript.timestamp)
    )
    transcripts = transcripts_result.scalars().all()

    return transcripts


@app.get("/api/sessions/{session_id}/download/{type}")
async def download_transcript(
    session_id: int,
    type: str,  # "source" or "translation"
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """下载转录文本文件"""
    # 验证会话
    session_result = await db.execute(
        select(TranslationSession)
        .where(TranslationSession.id == session_id)
        .where(TranslationSession.user_id == current_user.id)
    )
    session = session_result.scalar_one_or_none()

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # 获取转录
    transcripts_result = await db.execute(
        select(Transcript)
        .where(Transcript.session_id == session_id)
        .order_by(Transcript.timestamp)
    )
    transcripts = transcripts_result.scalars().all()

    # 生成文本内容
    content = []
    for t in transcripts:
        timestamp = t.timestamp.strftime("%Y-%m-%d %H:%M:%S")
        text = t.source_text if type == "source" else t.translated_text
        if text:
            content.append(f"[{timestamp}] {text}")

    file_content = "\n".join(content)
    filename = f"transcript_{type}_{session_id}.txt"

    return StreamingResponse(
        io.BytesIO(file_content.encode("utf-8")),
        media_type="text/plain",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


# ============ 统计端点 ============

@app.get("/api/statistics", response_model=StatisticsResponse)
async def get_statistics(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取用户统计"""
    result = await db.execute(
        select(UserStatistics).where(UserStatistics.user_id == current_user.id)
    )
    stats = result.scalar_one_or_none()

    if not stats:
        # 创建新的统计记录
        stats = UserStatistics(user_id=current_user.id)
        db.add(stats)
        await db.commit()
        await db.refresh(stats)

    return stats


# ============ WebSocket端点 ============

class ConnectionManager:
    """WebSocket连接管理器"""

    def __init__(self):
        self.active_connections: dict[int, WebSocket] = {}

    async def connect(self, user_id: int, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[user_id] = websocket

    def disconnect(self, user_id: int):
        if user_id in self.active_connections:
            del self.active_connections[user_id]

    async def send_message(self, user_id: int, message: dict):
        if user_id in self.active_connections:
            try:
                await self.active_connections[user_id].send_json(message)
            except Exception as e:
                print(f"[WebSocket] Error sending to user {user_id}: {e}")

    async def broadcast(self, message: dict):
        for websocket in self.active_connections.values():
            try:
                await websocket.send_json(message)
            except Exception:
                pass


manager = ConnectionManager()


async def get_user_from_token(token: str, db: AsyncSession) -> Optional[User]:
    """从token获取用户"""
    try:
        from jose import jwt, JWTError
        from auth import SECRET_KEY, ALGORITHM

        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            return None

        result = await db.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()
        return user
    except JWTError:
        return None
    except Exception as e:
        print(f"[WebSocket] Token validation error: {e}")
        return None


@app.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    token: Optional[str] = None
):
    """
    WebSocket端点用于实时翻译数据传输
    客户端连接时需要提供token参数
    """
    if not token:
        await websocket.close(code=1008, reason="Missing token")
        return

    # 验证token并获取用户
    async for db in get_db():
        user = await get_user_from_token(token, db)
        if not user:
            await websocket.close(code=1008, reason="Invalid token")
            return

        user_id = user.id
        await manager.connect(user_id, websocket)

        try:
            while True:
                # 接收客户端消息
                data = await websocket.receive_text()
                message = json.loads(data)

                # 处理不同类型的消息
                if message.get("type") == "ping":
                    await manager.send_message(user_id, {"type": "pong"})

        except WebSocketDisconnect:
            manager.disconnect(user_id)
            print(f"[WebSocket] User {user_id} disconnected")
        except Exception as e:
            print(f"[WebSocket] Error: {e}")
            manager.disconnect(user_id)
        finally:
            break


# ============ TTS代理端点 ============

@app.get("/api/tts/proxy")
async def tts_proxy(text: str, lang: str = "en"):
    """
    代理Google TTS请求以避免CORS问题
    参数:
        text: 要转换为语音的文本
        lang: 语言代码（如 en, zh, ja）
    """
    try:
        # Google Translate TTS API
        encoded_text = httpx.QueryParams({"q": text})
        url = f"https://translate.google.com/translate_tts?ie=UTF-8&client=tw-ob&tl={lang}&{encoded_text}"

        async with httpx.AsyncClient() as client:
            response = await client.get(
                url,
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                },
                timeout=10.0
            )

            if response.status_code != 200:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Google TTS API returned status {response.status_code}"
                )

            # 返回音频数据
            return Response(
                content=response.content,
                media_type="audio/mpeg",
                headers={
                    "Cache-Control": "public, max-age=3600",
                    "Access-Control-Allow-Origin": "*"
                }
            )
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="TTS request timeout")
    except httpx.RequestError as e:
        raise HTTPException(status_code=502, detail=f"TTS request failed: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


# ============ 健康检查 ============

@app.get("/")
async def root():
    """根路径"""
    return {"message": "LiveTranslate API Server", "version": "2.0"}


@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
