from drf_spectacular.utils import extend_schema_view, extend_schema
from rest_framework.generics import (
    ListCreateAPIView,
    RetrieveUpdateDestroyAPIView,
    GenericAPIView,
)
from rest_framework.generics import DestroyAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.request import Request
from rest_framework.parsers import MultiPartParser
from rest_framework import status

from django.shortcuts import get_object_or_404

from api import models, serializers
from api.permissions import IsOrganiserOrReadOnly, IsOrgOfFile
from api.serializers import TaskResponse, TaskResponseMany, TaskRequest


class BaseTaskView:
    serializer_class = serializers.UserTaskSerializer
    queryset = models.Task.objects.all()
    permission_classes = (IsAuthenticated,)

    def get_serializer_class(self):
        if self.request.user in self.get_contest().organisers.all():
            return serializers.OrgTaskSerializer
        return serializers.UserTaskSerializer


class SubContestView:
    def get_contest(self) -> models.Contest:
        return get_object_or_404(models.Contest, pk=self.kwargs["contest_pk"])

    def get_queryset(self):
        return models.Task.objects.filter(contest=self.get_contest())


@extend_schema_view(
    get=extend_schema(
        summary="List tasks",
        tags=["tasks"],
        responses=TaskResponseMany,
    ),
    post=extend_schema(
        summary="Create task in the contest",
        tags=["tasks"],
        request=serializers.OrgTaskSerializer,
        responses=TaskResponse,
    ),
)
class ListCreateTaskView(BaseTaskView, SubContestView, ListCreateAPIView):
    permission_classes = (IsAuthenticated, IsOrganiserOrReadOnly)

    def create(self, request: Request, *args, **kwargs):
        contest = self.get_contest()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data | {"contest": contest}
        task = models.Task.objects.create(**data)
        return Response(self.get_serializer(task).data, status=status.HTTP_201_CREATED)


@extend_schema_view(
    get=extend_schema(
        summary="Get task",
        tags=["tasks"],
        responses=serializers.OrgTaskSerializer,
    ),
    put=extend_schema(
        summary="Update task",
        tags=["tasks"],
        request=TaskRequest,
        responses=TaskResponse,
    ),
    patch=extend_schema(
        summary="Update task partially",
        tags=["tasks"],
        request=TaskRequest,
        responses=TaskResponse,
    ),
    delete=extend_schema(summary="Delete task", tags=["tasks"]),
)
class TaskView(BaseTaskView, SubContestView, RetrieveUpdateDestroyAPIView):
    permission_classes = (IsAuthenticated, IsOrganiserOrReadOnly)

    def get_queryset(self):
        return models.Task.objects.filter(contest=self.get_contest())


@extend_schema_view(
    post=extend_schema(
        summary="Upload files that should be shown in task description (visibility depends on method)",
        description="Upload any number of files with any keys.",
        request={
            'multipart/form-data': {
                'type': 'object',
                'properties': {
                    'file': {
                        'type': 'string',
                        'format': 'binary'
                    }
                }
            }
        },
        tags=["task files"],
        responses={204: None},
    ),
)
class UploadTaskFiles(BaseTaskView, SubContestView, GenericAPIView):
    parser_classes = (MultiPartParser,)
    permission_classes = (IsAuthenticated, IsOrganiserOrReadOnly)
    files_for = "users"

    def post(self, request: Request, *args, **kwargs) -> Response:
        task = self.get_object()
        #raise ValueError(f"{request.FILES}")
        if not request.FILES:
            raise ValidationError("You must provide files")

        match self.files_for:
            case "users":
                file_model = models.UserFile
            case "orgs":
                file_model = models.OrgFile
            case _:
                raise ValidationError("Unknown files_for")

        files = [file_model(task=task, file=file) for file in request.FILES.values()]
        file_model.objects.bulk_create(files)

        return Response(status=status.HTTP_204_NO_CONTENT)


@extend_schema_view(
    delete=extend_schema(
        summary="Delete file uploaded by upload-user-files",
        tags=["task files"],
    ),
)
class DeleteUserFileView(DestroyAPIView):
    queryset = models.UserFile.objects.all()
    permission_classes = (IsAuthenticated, IsOrgOfFile)


@extend_schema_view(
    delete=extend_schema(
        summary="Delete file uploaded by upload-org-files",
        tags=["task files"],
    ),
)
class DeleteOrgFileView(DestroyAPIView):
    queryset = models.OrgFile.objects.all()
    permission_classes = (IsAuthenticated, IsOrgOfFile)
