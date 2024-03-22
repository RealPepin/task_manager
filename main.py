from fastapi import FastAPI
from sqlalchemy import *
from sqlalchemy.orm import *
from enum import Enum as PyEnum
from datetime import datetime
from typing import Optional
from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

app = FastAPI()

Base = declarative_base()

DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class TaskStatus(str, PyEnum):
    done = "завершено"
    pending = "в ожидании"
    working = "в работе"


class Task(Base):
    __tablename__ = "tasks"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    description = Column(String, index=True)
    status = Column(Enum(TaskStatus))
    creation_time = Column(DateTime, default=datetime.now())


Base.metadata.create_all(bind=engine)

class TaskBase(BaseModel):
    title: str
    description: str
    status: TaskStatus


class TaskCreate(BaseModel):
    title: str
    description: str
    status: str


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None


def get_db():
    db = SessionLocal()
    try:
        return db
    finally:
        db.close()


@app.post("/tasks/")
def create_task(task: TaskCreate, db: Session = Depends(get_db)):
    db_task = Task(**task.dict())
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    return db_task


@app.get("/tasks/")
def get_tasks(db: Session = Depends(get_db)):
    return db.query(Task).all()


@app.get("/tasks/{task_id}")
def get_task(task_id: int, db: Session = Depends(get_db)):
    return db.query(Task).filter(Task.id == task_id).first()


@app.put("/tasks/{task_id}")
def update_task(task_id: int, task: TaskUpdate, db: Session = Depends(get_db)):
    db_task = db.query(Task).filter(Task.id == task_id).first()
    if task.status and task.status not in [s.value for s in TaskStatus]:
        raise HTTPException(status_code=422, detail="Invalid task status")
    if db_task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    for key, value in task.dict(exclude_unset=True).items():
        setattr(db_task, key, value)
    db.commit()
    db.refresh(db_task)
    return db_task


@app.delete("/tasks/{task_id}")
def delete_task(task_id: int, db: Session = Depends(get_db)):
    db_task = db.query(Task).filter(Task.id == task_id).first()
    if db_task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    db.delete(db_task)
    db.commit()
    return {"message": "Task deleted successfully"}
