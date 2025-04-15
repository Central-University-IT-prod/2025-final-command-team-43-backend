from drf_spectacular.utils import extend_schema_view, extend_schema
from rest_framework.views import APIView
from rest_framework.generics import CreateAPIView, RetrieveUpdateAPIView, ListAPIView
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status

from api import models, serializers


@extend_schema_view(
    post=extend_schema(
        summary="Register a new user",
    )
)
class CreateUserView(CreateAPIView):
    """Register a user."""

    role = "participant"  # default role, can be overridden in urls.py
    queryset = models.User.objects.all()
    serializer_class = serializers.UserSerializer

    def create(self, request, *args, **kwargs):
        # Create User
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user_data = {"role": self.role} | serializer.validated_data
        password = user_data.pop("password")
        user = models.User.objects.create_user(**user_data)
        user.set_password(password)
        user.save()
        # Create an individual team
        team = models.Team.objects.create(name=user.username, individual=True)
        user.teams.add(team)
        return Response(
            self.serializer_class(user).data, status=status.HTTP_201_CREATED
        )


@extend_schema_view(
    post=extend_schema(
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
        }
    )
)
class UploadProfilePicView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request: Request, *args, **kwargs) -> Response:
        if request.user.profile_pic is not None:
            request.user.profile_pic.delete()
            request.user.profile_pic = None
        if request.FILES:
            request.user.profile_pic = list(request.FILES.values())[0]

        request.user.save()
        return Response(status=status.HTTP_204_NO_CONTENT)


@extend_schema_view(
    get=extend_schema(
        summary="Get profile of current user",
    ),
    put=extend_schema(
        summary="Update current user profile data",
    ),
    patch=extend_schema(
        summary="Update profile partially",
    ),
)
class ProfileView(RetrieveUpdateAPIView):
    """Access profile data and modify it."""

    queryset = models.User.objects.all()
    permission_classes = (IsAuthenticated,)
    serializer_class = serializers.UserSerializer

    def get_object(self):
        return self.request.user

    def update(self, request, *args, **kwargs):
        resp = super().update(request, *args, **kwargs)
        if "password" in request.data:
            self.request.user.set_password(request.data["password"])
            self.request.user.save()
        return resp


@extend_schema_view(
    get=extend_schema(
        summary="List all users (to choose when adding team members)",
    )
)
class ListUserView(ListAPIView):
    serializer_class = serializers.ShortUserSerializer
    queryset = models.User.objects.all()
    permission_classes = (IsAuthenticated,)
