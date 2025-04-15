import re
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import TypeVar, Generic


@dataclass
class CheckerVerdict:
    score: int
    is_successful: bool


class CheckerParams:
    """"""


Param_T = TypeVar("Param_T", bound=CheckerParams)


class AbstractChecker(ABC, Generic[Param_T]):
    _param_class = CheckerParams

    def __init__(self, params: Param_T) -> None:
        self.params = params

    @abstractmethod
    def check(self, solution_str: str, max_points: int) -> CheckerVerdict:
        """Check the solution"""


@dataclass
class TextCheckerParams(CheckerParams):
    pattern: str


class RegexChecker(AbstractChecker[TextCheckerParams]):
    _param_class = TextCheckerParams

    def check(self, solution_str: str, max_points: int) -> CheckerVerdict:
        is_ok = re.fullmatch(self.params.pattern, solution_str) is not None
        return CheckerVerdict(
            is_successful=is_ok,
            score=max_points if is_ok else 0
        )


class MatchChecker(AbstractChecker[TextCheckerParams]):
    _param_class = TextCheckerParams

    def check(self, solution_str: str, max_points: int) -> CheckerVerdict:
        is_ok = str(self.params.pattern).strip() == solution_str.strip()
        return CheckerVerdict(
            is_successful=is_ok,
            score=max_points if is_ok else 0
        )


@dataclass
class RangeCheckerParams(CheckerParams):
    from_number: float
    to_number: float


class RangeChecker(AbstractChecker[RangeCheckerParams]):
    _param_class = RangeCheckerParams

    def check(self, solution_str: str, max_points: int) -> CheckerVerdict:
        try:
            number = float(solution_str)
        except ValueError:
            return CheckerVerdict(is_successful=False, score=0)
        is_ok = self.params.from_number <= number <= self.params.to_number
        return CheckerVerdict(
            is_successful=is_ok,
            score=max_points if is_ok else 0
        )


@dataclass
class ChoiceCheckerParams(CheckerParams):
    correct_answers: list[str]


class ChoiceChecker(AbstractChecker[ChoiceCheckerParams]):
    _param_class = ChoiceCheckerParams

    def check(self, solution_str: str, max_points: int) -> CheckerVerdict:
        submitted = set(solution_str.split(";"))
        correct = set(self.params.correct_answers)
        is_ok = submitted == correct
        return CheckerVerdict(
            is_successful=is_ok,
            score=max_points if is_ok else 0
        )


ALL_CHECKERS = {
    "regex": RegexChecker,
    "match": MatchChecker,
    "range": RangeChecker,
    "choice": ChoiceChecker
}


def from_json(data: dict) -> AbstractChecker:
    if "type" not in data:
        raise ValueError
    if not isinstance(data.get("args"), dict):
        raise ValueError
    checker_cls = ALL_CHECKERS[data["type"]]
    return checker_cls(params=checker_cls._param_class(**data["args"]))
