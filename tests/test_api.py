import asyncio

import pytest
from httpx import ASGITransport, AsyncClient

import app as app_module
from app import app


@pytest.fixture(autouse=True)
def clean_storage():
    app_module.NOTES.clear()
    app_module._next_id = 1
    yield
    app_module.NOTES.clear()


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.mark.asyncio
async def test_health(client):
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_create_and_get_note(client):
    created = await client.post("/notes", json={"title": "Первая", "body": "текст"}, params={"tags": "работа, срочно"})
    assert created.status_code == 201
    note = created.json()
    assert note["id"] == 1
    assert note["tags"] == ["работа", "срочно"]

    fetched = await client.get("/notes/1")
    assert fetched.status_code == 200
    assert fetched.json()["title"] == "Первая"


@pytest.mark.asyncio
async def test_filter_by_tag(client):
    await client.post("/notes", json={"title": "a"}, params={"tags": "дом"})
    await client.post("/notes", json={"title": "b"}, params={"tags": "работа"})

    filtered = await client.get("/notes", params={"tag": "дом"})
    assert [note["title"] for note in filtered.json()] == ["a"]

    all_notes = await client.get("/notes")
    assert len(all_notes.json()) == 2


@pytest.mark.asyncio
async def test_validation_error(client):
    response = await client.post("/notes", json={"title": ""})
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_get_missing_note(client):
    response = await client.get("/notes/999")
    assert response.status_code == 404
    assert response.json()["detail"] == "note not found"


@pytest.mark.asyncio
async def test_delete_note(client):
    await client.post("/notes", json={"title": "удалить"})
    deleted = await client.delete("/notes/1")
    assert deleted.status_code == 204

    missing = await client.delete("/notes/1")
    assert missing.status_code == 404


@pytest.mark.asyncio
async def test_parallel_requests(client):
    responses = await asyncio.gather(*[
        client.post("/notes", json={"title": f"заметка {i}"})
        for i in range(5)
    ])
    assert all(response.status_code == 201 for response in responses)
    assert len({response.json()["id"] for response in responses}) == 5
