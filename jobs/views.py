from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from django_filters.rest_framework import DjangoFilterBackend
from .models import User, Job, Application
from .serializers import UserSerializer, JobSerializer, ApplicationSerializer
from .permissions import IsCompany, IsApplicant, IsJobOwner, IsApplicationJobOwner
from rest_framework import viewsets, status, permissions

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        if self.action in ['list', 'retrieve']:
            return User.objects.filter(id=self.request.user.id)
        return super().get_queryset()

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response({
            'success': True,
            'message': 'User created successfully',
            'object': serializer.data,
            'errors': None
        }, status=status.HTTP_201_CREATED)

class JobViewSet(viewsets.ModelViewSet):
    queryset = Job.objects.all()
    serializer_class = JobSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = {
        'title': ['icontains'],
        'location': ['exact', 'icontains'],
        'created_by__name': ['icontains'],
    }

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsCompany(), IsJobOwner()]
        elif self.action == 'list':
            return [IsApplicant()]
        return [permissions.IsAuthenticated()]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response({
            'success': True,
            'message': 'Job created successfully',
            'object': serializer.data,
            'errors': None
        }, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response({
            'success': True,
            'message': 'Job updated successfully',
            'object': serializer.data,
            'errors': None
        })

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response({
            'success': True,
            'message': 'Job deleted successfully',
            'object': None,
            'errors': None
        })

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response({
                'success': True,
                'message': 'Jobs retrieved successfully',
                'object': serializer.data,
                'pageNumber': self.paginator.page.number,
                'pageSize': self.paginator.page_size,
                'totalSize': self.paginator.page.paginator.count,
                'errors': None
            })
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'success': True,
            'message': 'Jobs retrieved successfully',
            'object': serializer.data,
            'errors': None
        })

class ApplicationViewSet(viewsets.ModelViewSet):
    queryset = Application.objects.all()
    serializer_class = ApplicationSerializer

    def get_permissions(self):
        if self.action == 'create':
            return [IsApplicant()]
        elif self.action in ['list', 'retrieve']:
            return [IsApplicant()]
        elif self.action == 'update_status':
            return [IsCompany(), IsApplicationJobOwner()]
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        if self.action == 'list' and self.request.user.role == 'applicant':
            return Application.objects.filter(applicant=self.request.user)
        elif self.action == 'list' and self.request.user.role == 'company':
            return Application.objects.filter(job__created_by=self.request.user)
        return super().get_queryset()

    def create(self, request, *args, **kwargs):
        if Application.objects.filter(applicant=request.user, job_id=request.data.get('job')).exists():
            return Response({
                'success': False,
                'message': 'You have already applied to this job',
                'object': None,
                'errors': ['Duplicate application']
            }, status=status.HTTP_400_BAD_REQUEST)
        serializer = self.get_serializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        application = serializer.save()
        return Response({
            'success': True,
            'message': 'Application submitted successfully',
            'object': serializer.data,
            'errors': None
        }, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['patch'], url_path='status')
    def update_status(self, request, pk=None):
        application = self.get_object()
        status = request.data.get('status')
        if status not in dict(Application.STATUS_CHOICES).keys():
            return Response({
                'success': False,
                'message': 'Invalid status',
                'object': None,
                'errors': ['Invalid status']
            }, status=status.HTTP_400_BAD_REQUEST)
        application.status = status
        application.save()
        serializer = self.get_serializer(application)
        return Response({
            'success': True,
            'message': 'Application status updated',
            'object': serializer.data,
            'errors': None
        })