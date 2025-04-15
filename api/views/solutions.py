from django.db.models import Q
from django.utils import timezone
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework.exceptions import ParseError, PermissionDenied
from rest_framework.generics import get_object_or_404, ListAPIView
from rest_framework.parsers import JSONParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from api import models, serializers
from api.logic import checker
from api.permissions import IsOrgOfThisContest


@extend_schema_view(
    post=extend_schema(
        summary="Submit solution for checking",
        description=(
            "Pass string, float, integer or file as answer. "
            "If file is passed, team_id should be passed as a query parameter"
        ),
        request=serializers.SubmitSolutionSerializer,
        responses={204: None},
        tags=["solutions"],
    )
)
class PostSolutionAPIView(APIView):
    permission_classes = (IsAuthenticated,)
    parser_classes = (JSONParser, MultiPartParser)

    def post(self, request, contest_id, task_id):
        contest = get_object_or_404(models.Contest.objects.all(), id=contest_id)
        task = get_object_or_404(models.Task.objects.all(), id=task_id)
        # raise ValueError(f"{task.checker}, {task.answer_type}")
        self._validate_input(task, request)
        team_id = (
            request.data["team_id"]
            if task.answer_type != models.Task.AnswerTypes.FILE
            else request.GET["team_id"]
        )
        team = get_object_or_404(models.Team.objects.all(), id=team_id)
        self._validate_state(contest, task, team)
        solution = models.Solution(
            task=task,
            author=team,
            points=0,
            is_successful=False,
            content=None,
            is_public=False,
        )
        if (
            task.answer_type != models.Task.AnswerTypes.FILE
            and task.checker is not None
        ):
            solution.content = str(request.data["answer"])
            checker_inst = checker.from_json(task.checker)
            verdict = checker_inst.check(str(solution.content), task.max_points)
            print(verdict.is_successful, verdict.score)
            solution.is_successful = verdict.is_successful
            solution.points = verdict.score
            solution.is_checked = True
        if task.answer_type != models.Task.AnswerTypes.FILE:
            solution.content = str(request.data["answer"])
        solution.save()
        if task.answer_type == models.Task.AnswerTypes.FILE:
            solution.file = request.FILES["answer"]
            solution.save()
        # solution = models.Solution.objects.get(id=solution.id)
        return Response(data=None, status=204)

    def _validate_input(self, task, request):
        if task.answer_type == models.Task.AnswerTypes.FILE:
            if "answer" not in request.FILES:
                raise ParseError("answer file should be present")
        elif task.answer_type == models.Task.AnswerTypes.TEXT:
            print(request.data)
            if not isinstance(request.data.get("answer"), str):
                raise ParseError("answer field should be present")
        elif task.answer_type == models.Task.AnswerTypes.NUMBER:
            if not isinstance(request.data.get("answer"), (int, float)):
                raise ParseError("answer field should be present")
        elif task.answer_type == models.Task.AnswerTypes.CHOICE:
            if not isinstance(request.data.get("answer"), str):
                raise ParseError("answer field should be present")
        else:
            raise ParseError("unknown answer type")
        if not (
            isinstance(request.GET.get("team_id"), str)
            and task.answer_type == models.Task.AnswerTypes.FILE
            or isinstance(request.data.get("team_id"), str)
        ):
            raise ParseError("team_id should be present")

    def _validate_state(self, contest, task, team):
        if self.request.user not in team.members.all():
            raise PermissionDenied("not a member")
        if contest.start_datetime is None:
            return
        if task.max_attempts is None:
            return
        attempts = models.Solution.objects.filter(task=task, author=team).count()
        if attempts >= task.max_attempts:
            raise PermissionDenied("attempt limit reached")
        now = timezone.now()
        if not (contest.start_datetime <= now <= contest.end_datetime):
            raise PermissionDenied("contest not running")
        if contest.stage != models.Contest.Stages.IN_PROGRESS:
            raise PermissionDenied("contest not running")


@extend_schema_view(
    get=extend_schema(
        summary="List solutions submitted by current user",
        responses=serializers.SolutionSerializer(many=True),
        tags=["solutions"],
    )
)
class ListMySolutionsView(ListAPIView):
    queryset = models.Solution.objects.all().order_by("-created_at")
    serializer_class = serializers.SolutionSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        try:
            return (
                super()
                .get_queryset()
                .filter(
                    author__id=self.kwargs["team_id"],
                    task__contest__id=self.kwargs["contest_id"],
                )
            )
        except:
            raise ParseError("invalid data")


@extend_schema_view(
    get=extend_schema(
        summary="List solutions marked as public",
        responses=serializers.SolutionSerializer(many=True),
        tags=["solutions"],
    )
)
class ListOpenSolutionsView(ListAPIView):
    queryset = models.Solution.objects.all().order_by("-created_at")
    serializer_class = serializers.SolutionSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        try:
            return (
                super()
                .get_queryset()
                .filter(task__contest__id=self.kwargs["contest_id"], is_public=True)
            )
        except:
            raise ParseError("invalid data")


@extend_schema_view(
    put=extend_schema(
        summary="Mark solution as published",
        responses={204: None},
        tags=["solutions"],
    )
)
class PublishSolutionView(APIView):
    permission_classes = (IsAuthenticated,)
    parser_classes = (JSONParser,)

    def put(self, request, solution_id, team_id):
        solution = get_object_or_404(models.Solution, id=solution_id)
        team = get_object_or_404(models.Team, id=team_id)
        if request.user not in team.members.all():
            raise PermissionDenied
        if solution.author != team:
            raise PermissionDenied
        solution.is_public = True
        solution.save()
        return Response(data=None, status=204)


@extend_schema_view(
    post=extend_schema(
        summary="Post a verdict for solution",
        request={
            "application/json": {
                "type": "object",
                "properties": {"points": {"type": "integer"}},
            }
        },
        responses={204: None},
        tags=["solutions: organisers"],
    )
)
class PostVerdictView(APIView):
    permission_classes = (IsAuthenticated,)
    parser_classes = (JSONParser,)

    def post(self, request, solution_id):
        solution = get_object_or_404(models.Solution.objects.all(), id=solution_id)
        self._validate_request(request, solution)
        self._validate_state(request, solution)
        models.OrgVerdict.objects.create(
            solution=solution, org=request.user, points=int(request.data["points"])
        )
        return Response(data={"status": "ok"}, status=201)

    def _validate_request(self, request, solution):
        points = request.data.get("points")
        if not isinstance(points, int):
            raise ParseError("points must be present as an int")
        if points < 0 or points > solution.task.max_points:
            return ParseError("points must be >= 0 and <= task's max points")

    def _validate_state(self, request, solution):
        verdict_max = solution.task.contest.cross_check_org_count
        if solution.verdicts.count() >= verdict_max:
            raise PermissionDenied("this task is already checked")
        if request.user.role != "organiser":
            raise PermissionDenied("not an organiser")


@extend_schema_view(
    get=extend_schema(
        summary="List all unchecked solutions",
        responses=serializers.SolutionSerializer(many=True),
        tags=["solutions: organisers"],
    )
)
class ListUncheckedSolutionsView(ListAPIView):
    queryset = models.Solution.objects.all().order_by("-created_at")
    serializer_class = serializers.SolutionSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        contest = get_object_or_404(
            models.Contest.objects.all(), id=self.kwargs["contest_id"]
        )
        max_verdicts = contest.cross_check_org_count
        # qs = (
        #    super()
        #    .get_queryset()
        #    .all()
        #    .annotate(
        #        verdict_count=Count("verdict"),
        #        distinct_name=Concat(
        #            "task__id", "author__id", output_field=TextField()
        #        ),
        #    )
        #    .distinct("distinct_name")
        # )
        # qs = qs.filter(
        #    verdict_count__lt=max_verdicts, task__contest=contest, is_checked=False
        # )
        used = set()
        ids = set()
        for sol in (
            super()
            .get_queryset()
            .filter(task__contest__id=self.kwargs.get("contest_id"), is_checked=False)
        ):
            distinct = f"{sol.task.id}{sol.author.id}"
            if distinct in used:
                continue
            if sol.verdicts.count() >= max_verdicts:
                continue
            used.add(distinct)
            ids.add(sol.id)
        # return qs
        return super().get_queryset().filter(id__in=ids)


@extend_schema_view(
    get=extend_schema(
        summary="List all solutions",
        responses=serializers.SolutionSerializer(many=True),
        tags=["solutions: organisers"],
    )
)
class ListAllSolutionsView(ListAPIView):
    queryset = models.Solution.objects.all().order_by("-created_at")
    serializer_class = serializers.SolutionSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        # raise ValueError
        used = set()
        ids = set()
        for sol in (
            super()
            .get_queryset()
            .filter(task__contest__id=self.kwargs.get("contest_id"))
        ):
            distinct = f"{sol.task.id}{sol.author.id}"
            if distinct in used:
                continue
            used.add(distinct)
            ids.add(sol.id)

        # qs = (
        #    super()
        #    .get_queryset()
        #    .all()
        #   .annotate(
        #        distinct_name=Concat("task__id", "author__id", output_field=TextField())
        #    )
        #    .distinct("distinct_name")
        # )
        # qs = qs.filter(task__contest__id=self.kwargs.get("contest_id"))
        # return qs
        return super().get_queryset().filter(id__in=ids)


@extend_schema_view(
    get=extend_schema(
        summary="Get solution; for organizers",
        responses=serializers.SolutionSerializer(many=True),
        tags=["solutions"],
    )
)
class GetSolutionView(ListAPIView):
    queryset = models.Solution.objects.all().order_by("-created_at")
    serializer_class = serializers.SolutionSerializer
    permission_classes = (IsAuthenticated, IsOrgOfThisContest)

    def get_queryset(self):
        qs = super().get_queryset()
        qs = qs.filter(Q(is_public=True) | Q(author__in=self.request.user.teams.all()))
        return qs
