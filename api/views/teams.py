from drf_spectacular.utils import extend_schema_view, extend_schema
from rest_framework.generics import (
    GenericAPIView,
    ListCreateAPIView,
    RetrieveUpdateDestroyAPIView,
)
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError, PermissionDenied
from rest_framework import status

from api import models, serializers


class BaseTeamView:
    serializer_class = serializers.TeamSerializer
    queryset = models.Team.objects.all()
    permission_classes = (IsAuthenticated,)


@extend_schema_view(
    get=extend_schema(
        summary="List all teams",
        responses=serializers.TeamSerializer(many=True),
    ),
    post=extend_schema(
        summary="Create a team",
        request=serializers.TeamSerializer,
        responses=serializers.TeamSerializer,
    ),
)
class ListCreateTeamView(BaseTeamView, ListCreateAPIView):
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        team = models.Team.objects.create(**serializer.validated_data)
        team.members.add(self.request.user)
        headers = self.get_success_headers(serializer.data)
        return Response(
            self.get_serializer(team).data,
            status=status.HTTP_201_CREATED,
            headers=headers,
        )


@extend_schema_view(
    get=extend_schema(
        summary="Get a team",
        responses=serializers.TeamSerializer,
    ),
    put=extend_schema(
        summary="Update a team",
        request=serializers.TeamSerializer,
        responses=serializers.TeamSerializer,
    ),
    patch=extend_schema(
        summary="Update a team partially",
        request=serializers.TeamSerializer,
        responses=serializers.TeamSerializer,
    ),
    delete=extend_schema(
        summary="Delete a team",
    ),
)
class TeamView(BaseTeamView, RetrieveUpdateDestroyAPIView):
    pass


@extend_schema_view(
    post=extend_schema(
        summary="Update team members",
        request=serializers.TeamMemberActionSerializer,
        responses={
            200: serializers.TeamSerializer,
            400: {
                "type": "object",
                "properties": {
                    "detail": {
                        "type": "string",
                        "example": "You must provide only an array of user ids",
                    }
                },
            },
        },
    )
)
class TeamMemberActionView(BaseTeamView, GenericAPIView):
    action = "add"

    def post(self, request, *args, **kwargs) -> Response:
        team = self.get_object()
        if team.individual is True:
            raise PermissionDenied("You cannot manage members in individual team")
        if not isinstance(request.data, list):
            raise ValidationError("You must provide only an array of user ids")
        users = models.User.objects.filter(pk__in=request.data)
        if len(users) != len(request.data):
            raise ValidationError("Some users were not found")
        match self.action:
            case "add":
                team.members.add(*users)
            case "remove":
                team.members.remove(*users)
        return Response(self.serializer_class(team).data, status=status.HTTP_200_OK)
