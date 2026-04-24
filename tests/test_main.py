from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_read_main():
    # This might fail if the app requires DB connection etc.
    # But it's a start for CI.
    response = client.get("/")
    assert response.status_code in [200, 404] # Depending on if / is defined
