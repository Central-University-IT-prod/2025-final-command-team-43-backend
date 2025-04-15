import uuid

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema_view, extend_schema, OpenApiExample
from rest_framework.generics import get_object_or_404, ListAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.serializers import JSONField

from api import models, serializers
from api.accessor import (
    get_total_user_metrics,
    get_activity_graph,
    get_total_team_metrics,
    get_standings,
)


@extend_schema_view(
    get=extend_schema(
        summary="Get user statistics",
        description="Get user statistics (total solutions, successful solutions and activity graph)",
        responses=serializers.UserStatsSerializer,
    )
)
class GetUserStatsView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, user_id):
        user = get_object_or_404(models.User.objects.all(), id=user_id)
        total_solutions, successful_solutions = get_total_user_metrics(user.id)
        activity_graph = get_activity_graph(user.id)
        return Response(
            {
                "total": total_solutions,
                "successful": successful_solutions,
                "activity": activity_graph,
            }
        )


@extend_schema_view(
    get=extend_schema(
        summary="Get team statistics",
        description="Get team statistics (total solutions, successful solutions)",
        responses=serializers.TeamStatsSerializer,
    ),
)
class GetTeamStatsView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, team_id):
        team = get_object_or_404(models.Team.objects.all(), id=team_id)
        total_solutions, successful_solutions = get_total_team_metrics(team.id)
        return Response(
            {
                "total": total_solutions,
                "successful": successful_solutions,
            }
        )


@extend_schema_view(
    get=extend_schema(
        summary="Get user achievements",
        responses=serializers.AchievementSerializer(many=True),
    ),
)
class ListUserAchievementsView(ListAPIView):
    queryset = models.Achievement.objects.all()
    serializer_class = serializers.AchievementSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        return super().get_queryset().filter(team__in=self.request.user.teams.all())


@extend_schema_view(
    get=extend_schema(
        summary="Get team achievements",
        responses=serializers.AchievementSerializer(many=True),
    ),
)
class ListTeamAchievementsView(ListAPIView):
    queryset = models.Achievement.objects.all()
    serializer_class = serializers.AchievementSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        return super().get_queryset().filter(team__id=self.kwargs.get("team_id"))


@extend_schema_view(
    get=extend_schema(
        summary="Get top teams by points for given contest",
        responses={
            200: {
                "type": "object",
                "description": "key - team id, value - total points"
            }
        },
        examples=[
            OpenApiExample(
                "Standings",
                value={
                    "62816ed1-35ad-41d8-9041-a689bda58673": 432,
                    "ef82bf66-897d-4e16-8be6-b5aef82467e6": 321,
                    "e8f3e625-ef84-4028-ab26-0af9a20eba5e": 212,
                },
            )
        ],
        tags=["contests", "stats"],
    )
)
class GetStandings(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, contest_id):
        return Response(data=get_standings(contest_id), status=200)
