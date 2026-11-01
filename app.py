"""Небольшое асинхронное API для задания по покрытию тестами.

Запуск: uvicorn app:app --reload
"""

from typing import Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

app = FastAPI(title="Notes API")

NOTES: dict[int, dict] = {}
_next_id = 1


class NoteIn(BaseModel):
    title: str = Field(min_length=1, max_length=120)
    body: str = Field(default="", max_length=2000)


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}


@app.get("/notes")
async def list_notes(tag: Optional[str] = None) -> list[dict]:
    items = list(NOTES.values())
    if tag:
        items = [note for note in items if tag in note["tags"]]
    return items


@app.post("/notes", status_code=201)
async def create_note(payload: NoteIn, tags: str = "") -> dict:
    global _next_id
    note = {
        "id": _next_id,
        "title": payload.title,
        "body": payload.body,
        "tags": [tag.strip() for tag in tags.split(",") if tag.strip()],
    }
    NOTES[_next_id] = note
    _next_id += 1
    return note


@app.get("/notes/{note_id}")
async def get_note(note_id: int) -> dict:
    if note_id not in NOTES:
        raise HTTPException(status_code=404, detail="note not found")
    return NOTES[note_id]


@app.delete("/notes/{note_id}", status_code=204)
async def delete_note(note_id: int) -> None:
    if note_id not in NOTES:
        raise HTTPException(status_code=404, detail="note not found")
    NOTES.pop(note_id)
