from drf_spectacular.utils import (extend_schema, OpenApiResponse,
                                   extend_schema_view)
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status


@extend_schema_view(
    get=extend_schema(
        summary="Ping server",
        responses={200: OpenApiResponse(description="Server is available")},
    ),
)
class PingView(APIView):
    @extend_schema(
        request=None,
    )
    def get(self, request, *args, **kwargs):
        return Response(status=status.HTTP_200_OK)
