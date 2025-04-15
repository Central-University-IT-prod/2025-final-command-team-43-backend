from django.db.models import Q
from drf_spectacular.utils import extend_schema_view, extend_schema, OpenApiResponse
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.generics import (
    CreateAPIView,
    ListAPIView,
    GenericAPIView,
    RetrieveUpdateDestroyAPIView,
)
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

import statistics

from rest_framework.serializers import ListSerializer, UUIDField

from api import models, serializers
from api.accessor import get_standings, get_unchecked_tasks
from api.permissions import IsOrganiserOrReadOnly, HasOrganiserRole
from api.serializers import ContestResponse, ContestRequest, ContestResponseMany


class BaseContestView:
    serializer_class = serializers.ContestSerializer
    queryset = models.Contest.objects.all()
    permission_classes = (IsAuthenticated,)


@extend_schema_view(
    post=extend_schema(
        summary="Create contest",
        responses=serializers.ContestSerializer,
    ),
)
class CreateContestView(BaseContestView, CreateAPIView):
    permission_classes = (IsAuthenticated, HasOrganiserRole)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        contest = models.Contest.objects.create(**serializer.validated_data)
        contest.organisers.add(request.user)
        return Response(
            self.serializer_class(contest).data, status=status.HTTP_201_CREATED
        )


@extend_schema_view(
    get=extend_schema(
        summary="Get list of contests",
        responses=ContestResponseMany,
    ),
)
class ContestListView(BaseContestView, ListAPIView):
    def get(self, request, *args, **kwargs):
        if request.user.role == "organiser":
            return Response(
                serializers.OrgContestSerializer(
                    list(reversed(list(models.Contest.objects.all()))), many=True
                ).data,
                status=status.HTTP_200_OK,
            )

        public = list(
            models.Contest.objects.filter(Q(stage="in_progress") | Q(stage="finished"))
        )
        return Response(
            serializers.ContestSerializer(list(reversed(public)), many=True).data,
            status=status.HTTP_200_OK,
        )


contest_response = OpenApiResponse(
    serializers.OrgContestSerializer,
    description=(
        "Information about the contest. "
        "Organisers are only returned if the user is an organiser"
    ),
)


@extend_schema_view(
    get=extend_schema(
        summary="Get contest info",
        responses=ContestResponse,
    ),
    put=extend_schema(
        summary="Update contest info",
        request=ContestRequest,
        responses=ContestResponse,
    ),
    patch=extend_schema(
        summary="Update contest info partially",
        request=ContestRequest,
        responses=ContestResponse,
    ),
    delete=extend_schema(
        summary="Delete contest",
    ),
)
class ContestView(BaseContestView, RetrieveUpdateDestroyAPIView):
    permission_classes = (IsAuthenticated, IsOrganiserOrReadOnly)

    def get_serializer_class(self):
        if self.request.user in self.get_object().organisers.all():
            return serializers.OrgContestSerializer
        return serializers.ContestSerializer


@extend_schema_view(
    post=extend_schema(
        summary="Move contest from checking stage to finished",
        request=None,
        responses={204: None},
    ),
)
class EndCheckingView(BaseContestView, GenericAPIView):
    permission_classes = (IsAuthenticated, IsOrganiserOrReadOnly)

    def post(self, request, **kwargs):
        contest = self.get_object()
        if contest.stage != models.Contest.Stages.CHECKING:
            raise PermissionDenied("Contest is not in checking stage")
        # Check if all solutions were checked
        # by required number of organisators
        # solutions = (
        #     models.Solution.objects.filter(task__contest=contest, is_checked=False)
        #     .annotate(verdict_count=Count("verdict"))
        #     .filter(verdict_count__lt=contest.cross_check_org_count)
        #     .annotate(
        #         distinct_name=Concat("task__id", "author__id", output_field=TextField())
        #     )
        #     .distinct()
        #     .count()
        # )
        #if len(get_unchecked_tasks(contest.id)) > 0:
        #    raise PermissionDenied("Not all solutions are checked")
        # Calculate median score and set is_checked = True
        solutions = models.Solution.objects.filter(
            task__contest=contest, is_checked=False
        ).prefetch_related("verdicts")
        for solution in solutions:
            scores = solution.verdicts.values_list("points", flat=True)
            if scores:
                solution.points = round(statistics.median(scores))
            else:
                solution.points = 0
            solution.is_checked = True
        models.Solution.objects.bulk_update(solutions, ["points", "is_checked"])
        # Set finished stage
        contest.stage = models.Contest.Stages.FINISHED
        contest.save()

        standings = get_standings(contest.id)
        achievements = []
        for i, team in enumerate(standings):
            if i > 3:
                break
            achievements.append(
                models.Achievement(
                    team=models.Team.objects.get(id=team), contest=contest, place=i + 1
                )
            )
        models.Achievement.objects.bulk_create(achievements)

        return Response(status=status.HTTP_204_NO_CONTENT)


@extend_schema_view(
    post=extend_schema(
        summary="Move contest from preparing stage to in_progress",
        request=None,
        responses={204: None},
    ),
)
class MarkContestReadyView(BaseContestView, GenericAPIView):
    permission_classes = (IsAuthenticated, IsOrganiserOrReadOnly)

    def post(self, request, *args, **kwargs):
        contest = self.get_object()
        if contest.stage != models.Contest.Stages.PREPARING:
            raise PermissionDenied("Contest is not in preparing stage")
        contest.stage = models.Contest.Stages.IN_PROGRESS
        contest.save()
        return Response(status=status.HTTP_204_NO_CONTENT)


@extend_schema_view(
    post=extend_schema(
        summary="Add/remove organisers of contest",
        request=ListSerializer(child=UUIDField()),
    )
)
class ManageOrganisersView(BaseContestView, GenericAPIView):
    permission_classes = (IsAuthenticated, IsOrganiserOrReadOnly)
    action = "add"

    def post(self, request, *args, **kwargs) -> Response:
        contest = self.get_object()
        if not isinstance(request.data, list):
            raise ValidationError("You must provide only an array of user ids")
        users = models.User.objects.filter(pk__in=request.data)
        if len(users) != len(request.data):
            raise ValidationError("Some users were not found")
        # Check if all users are organisers
        for user in users:
            if user.role != "organiser":
                raise ValidationError(
                    "User %s (%s) is not an organiser" % (user.username, user.pk)
                )
        match self.action:
            case "add":
                contest.organisers.add(*users)
            case "remove":
                contest.organisers.remove(*users)
        return Response(self.serializer_class(contest).data, status=status.HTTP_200_OK)
