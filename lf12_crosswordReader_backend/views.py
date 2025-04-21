import os
from rest_framework import generics
from rest_framework.parsers import MultiPartParser, FormParser
from .models import CrosswordModel
from .serializers import CreateImageSerializer, OverviewSerializer, ImagePathSerializer
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiResponse
from rest_framework.exceptions import ValidationError
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.response import Response
from rest_framework import status

from . import settings
from CrosswordSolverLogic import CrosswordSolver


class Delete(generics.DestroyAPIView):
    queryset = CrosswordModel.objects.all()

    @extend_schema(
        description="Delete specific crossword entry by ID",
    )
    def delete(self, request, *args, **kwargs):
        return super().delete(request, *args, **kwargs)

    def perform_destroy(self, instance):
        # Collect file paths for deletion
        original_image_path = (
            instance.original_image.path if instance.original_image else None
        )
        solved_image_path = (
            instance.solved_image.path if instance.solved_image else None
        )

        # Delete the database instance
        super().perform_destroy(instance)

        # Remove the files from the filesystem
        if original_image_path and os.path.exists(original_image_path):
            os.remove(original_image_path)

        if solved_image_path and os.path.exists(solved_image_path):
            os.remove(solved_image_path)


class Overview(generics.ListAPIView):
    serializer_class = OverviewSerializer
    queryset = CrosswordModel.objects.all()
    pagination_class = LimitOffsetPagination
    filter_backends = [SearchFilter]
    search_fields = ["title"]

    @extend_schema(
        description="Get an overview of all crossword images with search and pagination",
        parameters=[
            OpenApiParameter(
                name="search",
                type=str,
                location=OpenApiParameter.QUERY,
                description="Search by title",
            ),
            OpenApiParameter(
                name="limit",
                type=int,
                location=OpenApiParameter.QUERY,
                description="Number of records to return",
            ),
            OpenApiParameter(
                name="offset",
                type=int,
                location=OpenApiParameter.QUERY,
                description="Number of records to skip",
            ),
        ],
        responses={200: OverviewSerializer(many=True)},
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class ImagePath(generics.RetrieveAPIView):
    queryset = CrosswordModel.objects.all()
    serializer_class = ImagePathSerializer

    @extend_schema(
        description="Get a specific crossword image by ID, including both original and solved images",
        responses={200: ImagePathSerializer()},
    )
    def get(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)


class UploadImage(generics.CreateAPIView):
    queryset = CrosswordModel.objects.all()
    serializer_class = CreateImageSerializer
    parser_classes = (MultiPartParser, FormParser)

    @extend_schema(
        description="Upload a new crossword image",
        request=CreateImageSerializer,
        responses={
            201: OpenApiResponse(
                response={"id": str}, description="ID of the created crossword entry"
            )
        },
    )
    def perform_create(self, serializer):
        instance = serializer.save()
        if not os.path.isdir(os.path.join(settings.MEDIA_ROOT, "solved")):
            os.makedirs(os.path.join(settings.MEDIA_ROOT, "solved"))
        CrosswordSolver.solve(instance.original_image.path)
        return instance

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        instance = self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(
            {"id": str(instance.id)}, status=status.HTTP_201_CREATED, headers=headers
        )
