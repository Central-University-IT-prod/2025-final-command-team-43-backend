import pytest

from api.logic.checker import from_json


@pytest.mark.parametrize(
    "answer", ["2"]
)
@pytest.mark.parametrize(
    ("args", "points"),
    [
        ({"pattern": "2"}, 100),
        ({"pattern": "3"}, 0),
    ],
)
def test_match_checker(answer, args, points):
    checker = from_json({"type": "match", "args": args})
    verdict = checker.check(answer, points)
    assert verdict.score == points


@pytest.mark.parametrize(
    "answer", ["hello"]
)
@pytest.mark.parametrize(
    ("args", "points"),
    [
        ({"pattern": "hello"}, 100),
        ({"pattern": "hel*o"}, 100),
        ({"pattern": "ello"}, 0),
    ],
)
def test_regex_checker(answer, args, points):
    checker = from_json({"type": "regex", "args": args})
    verdict = checker.check(answer, points)
    assert verdict.score == points


@pytest.mark.parametrize(
    "answer", ["2.6"]
)
@pytest.mark.parametrize(
    ("args", "points"),
    [
        ({"from_number": 2, "to_number": 3}, 100),
        ({"from_number": 2, "to_number": 2.6}, 100),
        ({"from_number": 2.6, "to_number": 3}, 100),
        ({"from_number": 2.7, "to_number": 3}, 0),
    ],
)
def test_range_checker(answer, args, points):
    checker = from_json({"type": "range", "args": args})
    verdict = checker.check(answer, points)
    assert verdict.score == points


@pytest.mark.parametrize(
    "answer",
    ["...23", "abc", "1.2.3", "1."]
)
def test_range_checker_invalid_format(answer):
    checker = from_json({
        "type": "range",
        "args": {"from_number": 2, "to_number": 3}
    })
    verdict = checker.check(answer, 100)
    assert not verdict.is_successful
