from rest_framework import serializers
from django.core.validators import RegexValidator
from .models import User, Job, Application
import re
import cloudinary.uploader

class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    name = serializers.CharField(validators=[RegexValidator(r'^[a-zA-Z\s]+$', 'Name must contain only alphabets')])

    class Meta:
        model = User
        fields = ['id', 'name', 'email', 'password', 'role']
        read_only_fields = ['id']

    def validate_password(self, value):
        if not re.match(r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$', value):
            raise serializers.ValidationError('Password must be at least 8 characters, include one uppercase, one lowercase, one number, and one special character.')
        return value

    def create(self, validated_data):
        user = User.objects.create_user(
            email=validated_data['email'],
            name=validated_data['name'],
            password=validated_data['password'],
            role=validated_data['role']
        )
        return user

class JobSerializer(serializers.ModelSerializer):
    created_by = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Job
        fields = ['id', 'title', 'description', 'location', 'created_by', 'created_at']
        read_only_fields = ['id', 'created_by', 'created_at']

    def validate_title(self, value):
        if not 1 <= len(value) <= 100:
            raise serializers.ValidationError('Title must be 1-100 characters.')
        return value

    def validate_description(self, value):
        if not 20 <= len(value) <= 2000:
            raise serializers.ValidationError('Description must be 20-2000 characters.')
        return value

class ApplicationSerializer(serializers.ModelSerializer):
    applicant = serializers.PrimaryKeyRelatedField(read_only=True)
    job = serializers.PrimaryKeyRelatedField(queryset=Job.objects.all())
    resume = serializers.FileField(write_only=True)

    class Meta:
        model = Application
        fields = ['id', 'applicant', 'job', 'resume', 'resume_link', 'cover_letter', 'status', 'applied_at']
        read_only_fields = ['id', 'applicant', 'resume_link', 'status', 'applied_at']

    def validate_resume(self, value):
        if not value.name.endswith('.pdf'):
            raise serializers.ValidationError('Resume must be a PDF file.')
        return value

    def validate_cover_letter(self, value):
        if value and len(value) > 200:
            raise serializers.ValidationError('Cover letter must be under 200 characters.')
        return value

    def create(self, validated_data):
        resume = validated_data.pop('resume')
        upload_result = cloudinary.uploader.upload(resume, resource_type='raw', folder='resumes')
        validated_data['resume_link'] = upload_result['secure_url']
        validated_data['applicant'] = self.context['request'].user
        return Application.objects.create(**validated_data)