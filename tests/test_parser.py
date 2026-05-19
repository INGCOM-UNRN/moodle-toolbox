import pytest
from questions.core.parser import parse_gift_file

def test_parse_simple_gift(tmp_path):
    gift_content = "::Title:: Question {=Ans ~Wrong}"
    d = tmp_path / "test.gift"
    d.write_text(gift_content)
    
    result = parse_gift_file(str(d))
    
    assert result["success"] is True
    assert result["questionCount"] == 1
    assert result["questions"][0]["title"] == "Title"
    assert result["questions"][0]["type"] == "MC"

def test_parse_multiple_questions(tmp_path):
    gift_content = "::Q1:: Q1 {=A}\n\n::Q2:: Q2 {=B}"
    d = tmp_path / "test.gift"
    d.write_text(gift_content)
    
    result = parse_gift_file(str(d))
    
    assert result["questionCount"] == 2
    assert result["questions"][0]["title"] == "Q1"
    assert result["questions"][1]["title"] == "Q2"
