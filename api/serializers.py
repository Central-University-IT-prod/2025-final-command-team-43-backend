from django.conf import settings
from drf_spectacular.utils import extend_schema_field, OpenApiResponse
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from django.utils import timezone

from api import models


class ShortUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.User
        fields = ["id", "username", "profile_pic"]
        extra_kwargs = {
            "id": {"read_only": True},
            "profile_pic": {"read_only": True},
        }


class TeamSerializer(serializers.ModelSerializer):
    members = ShortUserSerializer(many=True, read_only=True)

    class Meta:
        model = models.Team
        fields = ["id", "name", "members"]
        extra_kwargs = {
            "id": {"read_only": True},
        }


class UserSerializer(serializers.ModelSerializer):
    teams = serializers.SerializerMethodField()
    individual_team = serializers.SerializerMethodField()

    class Meta:
        model = models.User
        fields = [
            "id",
            "username",
            "email",
            "password",
            "profile_pic",
            "role",
            "teams",
            "individual_team",
        ]
        extra_kwargs = {
            "id": {"read_only": True},
            "email": {"required": True},
            "profile_pic": {"read_only": True},
            "password": {"write_only": True},
            "role": {"read_only": not settings.DEBUG},
        }

    @extend_schema_field(TeamSerializer(many=True))
    def get_teams(self, obj: models.User):
        teams = obj.teams.filter(individual=False)
        return TeamSerializer(teams, many=True).data

    @extend_schema_field(TeamSerializer())
    def get_individual_team(self, obj: models.User):
        team = obj.teams.get(individual=True)
        return TeamSerializer(team).data


class UserFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.UserFile
        fields = ("id", "file")


class OrgFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.OrgFile
        fields = ("id", "file")


class UserTaskSerializer(serializers.ModelSerializer):
    user_files = UserFileSerializer(read_only=True, many=True)

    class Meta:
        model = models.Task
        exclude = ["org_text", "checker"]
        extra_kwargs = {
            "id": {"read_only": True},
            "contest": {"read_only": True},
        }


class OrgTaskSerializer(serializers.ModelSerializer):
    user_files = UserFileSerializer(read_only=True, many=True)
    org_files = OrgFileSerializer(read_only=True, many=True)

    class Meta:
        model = models.Task
        fields = "__all__"
        extra_kwargs = {
            "id": {"read_only": True},
            "contest": {"read_only": True},
        }


TaskRequest = OrgTaskSerializer
TaskResponse = OpenApiResponse(
    OrgTaskSerializer,
    description=(
        "Information about the task in contest. "
        "org_text, org_files and checker are only returned if the user is an organiser"
    ),
)
TaskResponseMany = OpenApiResponse(
    OrgTaskSerializer(many=TaskResponse),
    description=(
        "Information about the tasks in contest. "
        "org_text, org_files and checker are only returned if the user is an organiser"
    ),
)


def validate_contest_datetime(attrs: dict) -> dict:
    if end_datetime := attrs.get("end_datetime", None):
        if end_datetime < timezone.now() and not settings.DEBUG:
            raise ValidationError("End datetime must be in future")
        if start_datetime := attrs.get("end_datetime", None):
            if end_datetime < start_datetime:
                raise ValidationError("End datetime must be later than start datetime")
    return attrs


class OrgContestSerializer(serializers.ModelSerializer):
    organisers = UserSerializer(many=True, read_only=True)
    tasks = OrgTaskSerializer(many=True, read_only=True)

    class Meta:
        model = models.Contest
        fields = [
            "id",
            "title",
            "description",
            "start_datetime",
            "end_datetime",
            "stage",
            "organisers",
            "tasks",
            "cross_check_org_count",
        ]
        extra_kwargs = {"id": {"read_only": True}, "stage": {"read_only": True}}

    def validate(self, attrs: dict):
        return validate_contest_datetime(attrs)


ContestRequest = OrgContestSerializer
ContestResponse = OpenApiResponse(
    OrgContestSerializer,
    description=(
        "Information about the contest. "
        "Organisers are only returned if the user is an organiser"
    ),
)
ContestResponseMany = OpenApiResponse(
    OrgContestSerializer(many=True),
    description=(
        "Information about contests. "
        "Organisers are only returned if the user is an organiser"
    ),
)


class ContestSerializer(serializers.ModelSerializer):
    tasks = UserTaskSerializer(many=True, read_only=True)

    class Meta:
        model = models.Contest
        fields = [
            "id",
            "title",
            "description",
            "start_datetime",
            "end_datetime",
            "stage",
            "tasks",
            "cross_check_org_count",
        ]
        extra_kwargs = {
            "id": {"read_only": True},
            "stage": {"read_only": True},
        }
        depth = 1

    def validate(self, attrs: dict):
        return validate_contest_datetime(attrs)


class CreateTaskSerializer(OrgTaskSerializer): ...


class SolutionSerializer(serializers.ModelSerializer):
    author = TeamSerializer()

    class Meta:
        model = models.Solution
        fields = [
            "id",
            "task",
            "author",
            "content",
            "points",
            "is_successful",
            "file",
            "is_public",
            "is_checked",
        ]
        extra_kwargs = {
            "id": {"read_only": True},
        }


class TeamMemberActionSerializer(serializers.ListSerializer):
    child = serializers.UUIDField(
        help_text="List of user IDs to add to or remove from the team"
    )


class AchievementSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Achievement
        fields = "__all__"
        depth = 1


class SubmitSolutionSerializer(serializers.Serializer):
    team_id = serializers.UUIDField()
    answer = serializers.JSONField()


class TeamStatsSerializer(serializers.Serializer):
    total = serializers.IntegerField()
    successful = serializers.IntegerField()


class UserStatsSerializer(TeamStatsSerializer):
    activity = serializers.JSONField(
        default={
            "2022-01-01": 10,
            "2022-01-02": 5,
        },
        help_text="A mapping of date to count of submissions",
    )


class ManageOrganisersSchemaSerializer(serializers.Serializer):
    action = serializers.CharField()
