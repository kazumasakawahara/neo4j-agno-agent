from app.agents.gemini_agent import parse_json_from_response, get_extraction_prompt


def test_parse_json_direct():
    assert parse_json_from_response('{"nodes":[],"relationships":[]}') == {"nodes": [], "relationships": []}


def test_parse_json_markdown():
    raw = '```json\n{"nodes":[{"temp_id":"c1","label":"Client","properties":{"name":"田中"}}],"relationships":[]}\n```'
    result = parse_json_from_response(raw)
    assert result is not None
    assert result["nodes"][0]["label"] == "Client"


def test_parse_json_invalid():
    assert parse_json_from_response("not json") is None


def test_extraction_prompt_exists():
    prompt = get_extraction_prompt()
    assert "Client" in prompt
    assert "NgAction" in prompt
