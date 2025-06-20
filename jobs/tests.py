from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from django.urls import reverse
from .models import User, Job, Application
import uuid
from unittest.mock import patch
import json

class JobPlatformTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.company = User.objects.create_user(
            email='company@test.com',
            name='Test Company',
            password='Test@1234',
            role='company'
        )
        self.applicant = User.objects.create_user(
            email='applicant@test.com',
            name='Test Applicant',
            password='Test@1234',
            role='applicant'
        )
        self.job = Job.objects.create(
            id=uuid.uuid4(),
            title='Test Job',
            description='A test job description with sufficient length to meet validation requirements.',
            location='Remote',
            created_by=self.company
        )
        self.company_token = self.client.post(reverse('token_obtain_pair'), {
            'email': 'company@test.com',
            'password': 'Test@1234'
        }).data['access']
        self.applicant_token = self.client.post(reverse('token_obtain_pair'), {
            'email': 'applicant@test.com',
            'password': 'Test@1234'
        }).data['access']

    def test_user_signup_success(self):
        response = self.client.post(reverse('user-list'), {
            'name': 'New User',
            'email': 'newuser@test.com',
            'password': 'New@1234',
            'role': 'applicant'
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['object']['email'], 'newuser@test.com')
        self.assertEqual(response.data['errors'], None)

    def test_user_signup_invalid_password(self):
        response = self.client.post(reverse('user-list'), {
            'name': 'New User',
            'email': 'newuser2@test.com',
            'password': 'weak',
            'role': 'applicant'
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])
        self.assertIn('Password must be at least 8 characters', str(response.data))

    def test_user_signup_invalid_name(self):
        response = self.client.post(reverse('user-list'), {
            'name': 'User123',
            'email': 'newuser3@test.com',
            'password': 'Test@1234',
            'role': 'applicant'
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])
        self.assertIn('Name must contain only alphabets', str(response.data))

    def test_user_login_success(self):
        response = self.client.post(reverse('token_obtain_pair'), {
            'email': 'applicant@test.com',
            'password': 'Test@1234'
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)

    def test_user_login_invalid_credentials(self):
        response = self.client.post(reverse('token_obtain_pair'), {
            'email': 'applicant@test.com',
            'password': 'Wrong@1234'
        })
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn('No active account found', str(response.data))

    def test_create_job_company_success(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.company_token}')
        response = self.client.post(reverse('job-list'), {
            'title': 'New Job',
            'description': 'A new job description with sufficient length to meet validation requirements.',
            'location': 'Office'
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['object']['title'], 'New Job')
        self.assertEqual(response.data['errors'], None)

    def test_create_job_applicant_unauthorized(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.applicant_token}')
        response = self.client.post(reverse('job-list'), {
            'title': 'New Job',
            'description': 'A new job description with sufficient length to meet validation requirements.',
            'location': 'Office'
        })
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertFalse(response.data['success'])
        self.assertIn('You do not have permission', str(response.data))

    def test_update_job_company_success(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.company_token}')
        response = self.client.put(reverse('job-detail', kwargs={'pk': self.job.id}), {
            'title': 'Updated Job',
            'description': 'Updated description with sufficient length to meet validation requirements.',
            'location': 'Hybrid'
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['object']['title'], 'Updated Job')

    def test_update_job_unauthorized(self):
        other_company = User.objects.create_user(
            email='other@test.com', name='Other Company', password='Test@1234', role='company'
        )
        other_token = self.client.post(reverse('token_obtain_pair'), {
            'email': 'other@test.com',
            'password': 'Test@1234'
        }).data['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {other_token}')
        response = self.client.put(reverse('job-detail', kwargs={'pk': self.job.id}), {
            'title': 'Unauthorized Update',
            'description': 'Updated description with sufficient length.',
            'location': 'Office'
        })
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertFalse(response.data['success'])
        self.assertIn('You do not have permission', str(response.data))

    def test_delete_job_company_success(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.company_token}')
        response = self.client.delete(reverse('job-detail', kwargs={'pk': self.job.id}))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['message'], 'Job deleted successfully')

    def test_browse_jobs_applicant_success(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.applicant_token}')
        response = self.client.get(reverse('job-list') + '?title=test&location=remote')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertIn('object', response.data)
        self.assertEqual(response.data['pageNumber'], 1)
        self.assertEqual(response.data['pageSize'], 10)

    def test_browse_jobs_company_unauthorized(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.company_token}')
        response = self.client.get(reverse('job-list'))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertFalse(response.data['success'])
        self.assertIn('You do not have permission', str(response.data))

    @patch('cloudinary.uploader.upload')
    def test_apply_job_success(self, mock_upload):
        mock_upload.return_value = {'secure_url': 'http://cloudinary.com/test.pdf'}
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.applicant_token}')
        with open('test.pdf', 'wb') as f:
            f.write(b'Dummy PDF content')
        response = self.client.post(reverse('application-list'), {
            'job': str(self.job.id),
            'resume': open('test.pdf', 'rb'),
            'cover_letter': 'Interested in this job.'
        }, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['object']['status'], 'Applied')
        self.assertEqual(response.data['errors'], None)

    @patch('cloudinary.uploader.upload')
    def test_apply_job_duplicate(self, mock_upload):
        mock_upload.return_value = {'secure_url': 'http://cloudinary.com/test.pdf'}
        Application.objects.create(applicant=self.applicant, job=self.job, resume_link='http://test.com/resume.pdf')
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.applicant_token}')
        with open('test.pdf', 'wb') as f:
            f.write(b'Dummy PDF content')
        response = self.client.post(reverse('application-list'), {
            'job': str(self.job.id),
            'resume': open('test.pdf', 'rb'),
            'cover_letter': 'Interested again.'
        }, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])
        self.assertIn('You have already applied', str(response.data))

    def test_track_applications_applicant(self):
        Application.objects.create(applicant=self.applicant, job=self.job, resume_link='http://test.com/resume.pdf')
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.applicant_token}')
        response = self.client.get(reverse('application-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(len(response.data['object']), 1)
        self.assertEqual(response.data['object'][0]['job'], str(self.job.id))

    def test_view_posted_jobs_company(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.company_token}')
        response = self.client.get(reverse('job-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(len(response.data['object']), 1)
        self.assertEqual(response.data['object'][0]['title'], 'Test Job')

    def test_view_job_details(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.applicant_token}')
        response = self.client.get(reverse('job-detail', kwargs={'pk': self.job.id}))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['object']['title'], 'Test Job')

    def test_view_job_details_not_found(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.applicant_token}')
        response = self.client.get(reverse('job-detail', kwargs={'pk': uuid.uuid4()}))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertFalse(response.data['success'])
        self.assertEqual(response.data['message'], 'Job not found')

    def test_view_job_applications_company(self):
        Application.objects.create(applicant=self.applicant, job=self.job, resume_link='http://test.com/resume.pdf')
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.company_token}')
        response = self.client.get(reverse('application-list') + f'?job={self.job.id}')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(len(response.data['object']), 1)
        self.assertEqual(response.data['object'][0]['applicant'], str(self.applicant.id))

    def test_update_application_status_company(self):
        application = Application.objects.create(applicant=self.applicant, job=self.job, resume_link='http://test.com/resume.pdf')
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.company_token}')
        response = self.client.patch(
            reverse('application-update_status', kwargs={'pk': application.id}),
            {'status': 'Interview'},
            content_type='application/json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['object']['status'], 'Interview')

    def test_update_application_status_unauthorized(self):
        application = Application.objects.create(applicant=self.applicant, job=self.job, resume_link='http://test.com/resume.pdf')
        other_company = User.objects.create_user(
            email='other@test.com', name='Other Company', password='Test@1234', role='company'
        )
        other_token = self.client.post(reverse('token_obtain_pair'), {
            'email': 'other@test.com',
            'password': 'Test@1234'
        }).data['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {other_token}')
        response = self.client.patch(
            reverse('application-update_status', kwargs={'pk': application.id}),
            {'status': 'Interview'},
            content_type='application/json'
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertFalse(response.data['success'])
        self.assertIn('You do not have permission', str(response.data))