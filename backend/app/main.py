from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
from uuid import uuid4
import hashlib

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, create_engine, func, select
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, relationship

ROOT = Path(__file__).resolve().parents[2]
UPLOAD_DIR = ROOT / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)
engine = create_engine(f"sqlite:///{ROOT / 'cms.db'}", connect_args={"check_same_thread": False})

class Base(DeclarativeBase):
    pass

class Video(Base):
    __tablename__ = "videos"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    content_id: Mapped[str] = mapped_column(String(32), unique=True)
    title: Mapped[str] = mapped_column(String(240))
    source: Mapped[str] = mapped_column(String(30), default="upload")
    filename: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    file_hash: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    status: Mapped[str] = mapped_column(String(40), default="UPLOADED")
    transcript: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    content: Mapped[Optional["Content"]] = relationship(back_populates="video", uselist=False, cascade="all, delete-orphan")

class Content(Base):
    __tablename__ = "contents"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    video_id: Mapped[int] = mapped_column(ForeignKey("videos.id"), unique=True)
    status: Mapped[str] = mapped_column(String(40), default="DRAFT")
    style: Mapped[str] = mapped_column(String(40), default="Informative")
    caption: Mapped[str] = mapped_column(Text, default="")
    short_caption: Mapped[str] = mapped_column(Text, default="")
    hook: Mapped[str] = mapped_column(Text, default="")
    hashtags: Mapped[str] = mapped_column(Text, default="")
    keywords: Mapped[str] = mapped_column(Text, default="")
    summary: Mapped[str] = mapped_column(Text, default="")
    instagram: Mapped[str] = mapped_column(Text, default="")
    x_post: Mapped[str] = mapped_column(Text, default="")
    telegram: Mapped[str] = mapped_column(Text, default="")
    publishing_status: Mapped[str] = mapped_column(String(40), default="NOT_PUBLISHED")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    video: Mapped[Video] = relationship(back_populates="content")

Base.metadata.create_all(engine)
app = FastAPI(title="MoneyPurse-CMS Content Studio API", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

class ContentUpdate(BaseModel):
    caption: Optional[str] = None
    short_caption: Optional[str] = None
    hook: Optional[str] = None
    hashtags: Optional[str] = None
    keywords: Optional[str] = None
    instagram: Optional[str] = None
    x_post: Optional[str] = None
    telegram: Optional[str] = None
    style: Optional[str] = None

DEMO_TRANSCRIPT = "ఈ రోజు మనం మన జీవితంలో చిన్న మార్పులు ఎలా పెద్ద ఫలితాలను ఇస్తాయో తెలుసుకుందాం. ప్రతిరోజూ ఒక మంచి అలవాటును ప్రారంభిస్తే మన ప్రయాణం మరింత అందంగా మారుతుంది."

def demo_content(title: str, style: str = "Informative") -> dict[str, str]:
    hook = "ఒక్క చిన్న మార్పు... మీ రోజును పూర్తిగా మార్చగలదు!"
    caption = f"{title} గురించి కొన్ని ఆలోచనలు. {DEMO_TRANSCRIPT} ఈ విషయాన్ని మీ స్నేహితులతో పంచుకోండి."
    hashtags = "#తెలుగు #మనసుమాట #ప్రేరణ #MoneyPurse-CMSContent"
    return {"hook": hook, "caption": caption, "short_caption": "చిన్న అడుగు, గొప్ప మార్పు.", "hashtags": hashtags, "keywords": "తెలుగు, ప్రేరణ, మంచి అలవాట్లు", "summary": "చిన్న అలవాట్లు జీవితంలో సానుకూల మార్పును తీసుకువస్తాయి.", "instagram": f"{hook}\n\n{caption}\n\n{hashtags}", "x_post": f"{hook}\n{caption[:180]}\n{hashtags}", "telegram": f"{title}\n\n{caption}\n\nమీ అభిప్రాయాన్ని కామెంట్ చేయండి.\n{hashtags}"}

def serialize(video: Video, content: Optional[Content]) -> dict:
    return {"id": video.id, "content_id": video.content_id, "title": video.title, "source": video.source, "filename": video.filename, "status": content.status if content else video.status, "video_status": video.status, "transcript": video.transcript, "created_at": video.created_at.isoformat(), "content": ({"id": content.id, "style": content.style, "caption": content.caption, "short_caption": content.short_caption, "hook": content.hook, "hashtags": content.hashtags, "keywords": content.keywords, "summary": content.summary, "instagram": content.instagram, "x_post": content.x_post, "telegram": content.telegram, "publishing_status": content.publishing_status} if content else None)}

@app.get("/api/health")
def health():
    return {"status": "ok", "mode": "demo"}

@app.get("/api/dashboard/summary")
def summary():
    with Session(engine) as db:
        total = db.scalar(select(func.count(Video.id))) or 0
        generated = db.scalar(select(func.count(Content.id))) or 0
        pending = db.scalar(select(func.count(Content.id)).where(Content.status == "PENDING_APPROVAL")) or 0
        published = db.scalar(select(func.count(Content.id)).where(Content.publishing_status == "DEMO_PUBLISHED")) or 0
        return {"total_videos": total, "content_generated": generated, "pending_approval": pending, "published_posts": published, "failed_publishing": 0}

@app.get("/api/content")
def list_content():
    with Session(engine) as db:
        return [serialize(v, v.content) for v in db.scalars(select(Video).order_by(Video.created_at.desc())).all()]

@app.get("/api/content/{content_id}")
def get_content(content_id: int):
    with Session(engine) as db:
        video = db.get(Video, content_id)
        if not video: raise HTTPException(404, "Content not found")
        return serialize(video, video.content)

@app.post("/api/videos/upload")
def upload_video(file: UploadFile = File(...), title: str = Form(...), description: str = Form("")):
    allowed = {"video/mp4", "video/quicktime", "video/webm"}
    if file.content_type not in allowed: raise HTTPException(400, "Only MP4, MOV and WebM videos are supported")
    data = file.file.read()
    if len(data) > 500 * 1024 * 1024: raise HTTPException(400, "Video must be smaller than 500 MB")
    suffix = Path(file.filename or "video.mp4").suffix.lower()
    safe_name = f"{uuid4().hex}{suffix}"
    (UPLOAD_DIR / safe_name).write_bytes(data)
    digest = hashlib.sha256(data).hexdigest()
    with Session(engine) as db:
        video = Video(content_id=f"TEL-{uuid4().hex[:8].upper()}", title=title, filename=safe_name, file_hash=digest)
        db.add(video); db.commit(); db.refresh(video)
        return serialize(video, None)

@app.post("/api/videos/{video_id}/process")
def process_video(video_id: int):
    with Session(engine) as db:
        video = db.get(Video, video_id)
        if not video: raise HTTPException(404, "Video not found")
        video.status = "CONTENT_GENERATED"
        video.transcript = DEMO_TRANSCRIPT
        generated = demo_content(video.title)
        content = video.content or Content(video=video)
        for key, value in generated.items(): setattr(content, key, value)
        content.status = "DRAFT"
        db.add(content); db.commit(); db.refresh(video)
        return serialize(video, content)

@app.post("/api/content/{video_id}/approve")
def approve(video_id: int):
    with Session(engine) as db:
        video = db.get(Video, video_id)
        if not video or not video.content: raise HTTPException(404, "Generated content not found")
        video.content.status = "APPROVED"; db.commit(); return serialize(video, video.content)

@app.post("/api/content/{video_id}/publish")
def publish(video_id: int):
    with Session(engine) as db:
        video = db.get(Video, video_id)
        if not video or not video.content: raise HTTPException(404, "Generated content not found")
        if video.content.status != "APPROVED": raise HTTPException(409, "Content must be approved before publishing")
        video.content.status = "PUBLISHED"; video.content.publishing_status = "DEMO_PUBLISHED"; db.commit(); return serialize(video, video.content)

@app.put("/api/content/{video_id}")
def update_content(video_id: int, update: ContentUpdate):
    with Session(engine) as db:
        video = db.get(Video, video_id)
        if not video or not video.content: raise HTTPException(404, "Generated content not found")
        for key, value in update.model_dump(exclude_none=True).items(): setattr(video.content, key, value)
        db.commit(); return serialize(video, video.content)
