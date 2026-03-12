from fastapi.testclient import TestClient
from app import app, extract_answer


client = TestClient(app)


def test_index_page():
    """Test that the homepage loads successfully."""
    response = client.get("/")
    assert response.status_code == 200


def test_extract_answer_string():
    """Test extract_answer with a plain string."""
    assert extract_answer("hello") == "hello"


def test_extract_answer_dict_output():
    """Test extract_answer with a dict containing 'output' key."""
    assert extract_answer({"output": "world"}) == "world"


def test_extract_answer_list():
    """Test extract_answer with a list response."""
    assert extract_answer([{"output": "from list"}]) == "from list"


def test_extract_answer_empty_list():
    """Test extract_answer with an empty list."""
    result = extract_answer([])
    assert isinstance(result, str)


def test_chat_empty_query():
    """Test that an empty query returns 400."""
    response = client.post("/chat", json={"query": ""})
    assert response.status_code == 400
