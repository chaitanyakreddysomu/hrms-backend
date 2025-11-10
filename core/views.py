import boto3
import time
import os
import csv
import io
import re

import razorpay
import random
from botocore.exceptions import ClientError
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from django.conf import settings
from rest_framework.authtoken.models import Token
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q
from .models import User,Admins,ExamQuestion,ExamSchedule
from django.utils import timezone
from .serializers import (
    UserSerializer,ExamQuestionSerializer,AdminSerializer,AdminLoginSerializer,ExamScheduleSerializer
)
from django.utils.timezone import now
# from .utils.s3_signed import generate_presigned_url
from core.utils import build_presigned_get_url, generate_presigned_url

from google.oauth2 import id_token
# from google.oauth2 import id_token
# from google.auth.transport import requests
import requests 
from google.auth.transport import requests as googleRequest

import hmac
from django.shortcuts import get_object_or_404
import hashlib
from rest_framework.parsers import MultiPartParser, FormParser,JSONParser
from .utils import get_redirect_url
import uuid
from rest_framework.views import APIView
from django.core.cache import cache
from django.core.mail import send_mail
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q
# from razorpay_client import client
from django.utils import timezone
from datetime import timedelta
import razorpay
from django.shortcuts import redirect
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.http import HttpResponseBadRequest
from razorpay.errors import SignatureVerificationError
# client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
from django.http import StreamingHttpResponse
import pytz
from datetime import datetime, timedelta
from decimal import Decimal

import tempfile
import logging

logger = logging.getLogger(__name__)
ist = pytz.timezone('Asia/Kolkata')
schedule_time = datetime.now(ist) + timedelta(minutes=2)
payment_schedule_date = schedule_time.isoformat()

def verify_signature(payment_id, subscription_id, signature, secret):
    msg = f"{payment_id}|{subscription_id}".encode()
    generated_signature = hmac.new(
        key=secret.encode(),
        msg=msg,
        digestmod=hashlib.sha256
    ).hexdigest()

    return hmac.compare_digest(generated_signature, signature)
# Custom Permissions
class IsOwnerOrReadOnly(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.user == request.user

class IsHROrAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role in ['hr', 'admin']

class IsAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'admin'
class AllowAnyPermission(permissions.BasePermission):
    """
    Custom permission that always allows access.
    Equivalent to rest_framework.permissions.AllowAny
    """
    def has_permission(self, request, view):
        return True


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all().order_by('-created_at')
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser,JSONParser]
    
    def get_queryset(self):
        if self.request.user.role == 'admin':
            return User.objects.all().order_by('-created_at')
        else:
            return User.objects.filter(id=self.request.user.id)
        
        

        
 

    @action(detail=False, methods=['get'])
    def profile(self, request):
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)
    
  

class AddAdminView(APIView):
    permission_classes = [AllowAnyPermission]
    authentication_classes = []  # Disable auth for login endpoint

    def post(self, request):
        serializer = AdminSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({'message': 'Admin created successfully', 'data': serializer.data}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class AdminLoginView(APIView):
    permission_classes = [AllowAnyPermission]
    authentication_classes = []  # Disable auth for login endpoint

    def post(self, request):
        serializer = AdminLoginSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            password = serializer.validated_data['password']
            
            try:
                admin = Admins.objects.get(email=email)
            except Admins.DoesNotExist:
                return Response({'error': 'Invalid email or password'}, status=status.HTTP_401_UNAUTHORIZED)
            
            # Use check_password to verify hashed password
            if not admin.check_password(password):
                return Response({'error': 'Invalid email or password'}, status=status.HTTP_401_UNAUTHORIZED)
            
            # If login success, you can return admin info or token if you implement JWT etc.
            return Response({'message': 'Login successful', 'admin_id': admin.id, 'email': admin.email}, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class AddExamQuestionView(APIView):
    permission_classes = [AllowAnyPermission]
    authentication_classes = []  # Disable auth for login endpoint

    def post(self, request):
        serializer = ExamQuestionSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({'message': 'Question added successfully', 'data': serializer.data}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AddExamScheduleView(APIView):
    authentication_classes = []  # No auth required, optional
    permission_classes = [AllowAnyPermission]

    def post(self, request):
        serializer = ExamScheduleSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({
                'message': 'Exam schedule added successfully',
                'data': serializer.data
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from datetime import datetime, timedelta
from .models import ExamSchedule
from .serializers import UserSerializer
from django.utils.timezone import make_aware
from django.utils.timezone import make_aware, now as timezone_now
from django.utils.timezone import make_aware,is_aware, get_current_timezone, now as timezone_now

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.utils.timezone import (
    make_aware, is_aware, get_current_timezone, now as timezone_now
)
from datetime import datetime

from .models import ExamSchedule, User
from .serializers import UserSerializer
from pytz import timezone as pytz_timezone

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.utils.timezone import get_current_timezone, make_aware, now as timezone_now
from datetime import datetime
from .models import ExamSchedule, User
from .serializers import UserSerializer


class StartExamView(APIView):
    authentication_classes = []  # No authentication
    permission_classes = [AllowAnyPermission]  # Allow anyone

    def post(self, request):
        exam_id = request.data.get('exam')
        if not exam_id:
            return Response({'error': 'Exam ID is required.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            exam = ExamSchedule.objects.get(id=exam_id)
        except ExamSchedule.DoesNotExist:
            return Response({'error': 'Invalid exam ID.'}, status=status.HTTP_404_NOT_FOUND)

        # Get timezone
        ist = pytz.timezone('Asia/Kolkata')
        tz = get_current_timezone()

        # Convert string times to datetime.time
        try:
            start_time = datetime.strptime(exam.exam_start_time, "%H:%M:%S").time()
            end_time = datetime.strptime(exam.exam_end_time, "%H:%M:%S").time()
        except (ValueError, TypeError):
            return Response({'error': 'Invalid time format in exam schedule.'}, status=400)

        # Combine with date and make timezone-aware (IST)
        exam_start_dt = ist.localize(datetime.combine(exam.exam_date, start_time))
        exam_end_dt = ist.localize(datetime.combine(exam.exam_date, end_time))
        current_time = datetime.now(ist)

        # Debugging/logging (optional)
        print("IST Exam Start:", exam_start_dt.strftime("%Y-%m-%d %H:%M:%S %Z"))
        print("IST Exam End:  ", exam_end_dt.strftime("%Y-%m-%d %H:%M:%S %Z"))
        print("IST Now:       ", current_time.strftime("%Y-%m-%d %H:%M:%S %Z"))

        # If exam is over
        if current_time > exam_end_dt:
            return Response({
                "message": f"Exam '{exam.exam_name}' is already completed. Ended at {exam.exam_end_time} on {exam.exam_date} (IST)."
            }, status=status.HTTP_400_BAD_REQUEST)

        # If exam has not started
        if current_time < exam_start_dt:
            return Response({
                "message": f"Exam '{exam.exam_name}' has not started yet. Starts at {exam.exam_start_time} on {exam.exam_date} (IST)."
            }, status=status.HTTP_400_BAD_REQUEST)

        # Exam is ongoing — save user
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            time_left = exam_end_dt - current_time
            return Response({
                'message': 'Exam started.',
                'session_id': user.id,
                'email': user.email,
                'time_left': str(time_left).split('.')[0]  # Format as HH:MM:SS
            }, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class SubmitScoreView(APIView):
    authentication_classes = []  # No auth required, optional
    permission_classes = [AllowAnyPermission]
    def post(self, request, session_id):
        try:
            user = User.objects.get(id=session_id)
        except User.DoesNotExist:
            return Response({'error': 'Invalid session ID'}, status=404)

        score = request.data.get('score')
        if not score:
            return Response({'error': 'Score is required'}, status=400)

        user.score = score
        user.save()

        return Response({'message': 'Score submitted successfully'}, status=200)



class ExamQuestionListView(APIView):
    authentication_classes = []  # No auth required, optional
    permission_classes = [AllowAnyPermission]
    def get(self, request):
        questions = ExamQuestion.objects.all()
        serializer = ExamQuestionSerializer(questions, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class ExamScheduleListView(APIView):
    authentication_classes = []  # No auth required, optional
    permission_classes = [AllowAnyPermission]

    def get(self, request):
        schedules = ExamSchedule.objects.all()
        serializer = ExamScheduleSerializer(schedules, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class AdminListView(APIView):
    authentication_classes = []  # No auth required, optional
    permission_classes = [AllowAnyPermission]
    def get(self, request):
        admins = Admins.objects.all()
        serializer = AdminSerializer(admins, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework import status

class Pagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Q

class UserListView(APIView):
    authentication_classes = []
    permission_classes = [AllowAnyPermission]

    def get(self, request):
        search = request.GET.get('search', '')
        college_code = request.GET.get('college_code')
        score_gt = request.GET.get('score_gt')
        score_lt = request.GET.get('score_lt')
        ordering = request.GET.get('ordering')  # e.g., 'score' or '-score'

        queryset = User.objects.all()

        # Apply search filter (exam, email, roll_number)
        if search:
            queryset = queryset.filter(
                Q(exam__id__icontains=search) |
                Q(email__icontains=search) |
                Q(roll_number__icontains=search)
            )

        # Filter by college_code
        if college_code:
            queryset = queryset.filter(college_code=college_code)

        # Filter by score greater than
        if score_gt:
            queryset = queryset.filter(score__gt=score_gt)

        # Filter by score less than
        if score_lt:
            queryset = queryset.filter(score__lt=score_lt)

        # Apply ordering (only by score)
        if ordering in ['score', '-score']:
            queryset = queryset.order_by(ordering)

        # Paginate results
        paginator = Pagination()
        page = paginator.paginate_queryset(queryset, request)
        serializer = UserSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)

from rest_framework.decorators import api_view, authentication_classes, permission_classes
@api_view(['DELETE'])
@authentication_classes([])  # No authentication
@permission_classes([AllowAnyPermission])
def delete_user_view(request, id):
    user = get_object_or_404(User, id=id)
    user.delete()
    return Response({"detail": "User deleted successfully."}, status=status.HTTP_204_NO_CONTENT)




 
@api_view(['PUT'])
@authentication_classes([])
@permission_classes([AllowAnyPermission])
def edit_exam_question(request, id):
    question = get_object_or_404(ExamQuestion, id=id)
    serializer = ExamQuestionSerializer(question, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['DELETE'])
@authentication_classes([])
@permission_classes([AllowAnyPermission])
def delete_exam_question(request, id):
    question = get_object_or_404(ExamQuestion, id=id)
    question.delete()
    return Response({"detail": "Question deleted successfully."}, status=status.HTTP_204_NO_CONTENT)   


@api_view(['PUT'])
@authentication_classes([])
@permission_classes([AllowAnyPermission])
def edit_exam_schedule(request, id):
    schedule = get_object_or_404(ExamSchedule, id=id)
    serializer = ExamScheduleSerializer(schedule, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['DELETE'])
@authentication_classes([])
@permission_classes([AllowAnyPermission])
def delete_exam_schedule(request, id):
    schedule = get_object_or_404(ExamSchedule, id=id)
    schedule.delete()
    return Response({"detail": "Schedule deleted successfully."}, status=status.HTTP_204_NO_CONTENT)







# views.py
from rest_framework import generics, status, permissions, viewsets
from rest_framework.response import Response
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from django.db.models import Q, Sum, Count
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from datetime import datetime, date
import calendar
from .models import *
from .serializers import *
from .permissions import ClientProfilePermission
from .utils import generate_pdf_report, send_email_with_attachment



class IsAdminOrManager(permissions.BasePermission):
    """
    Custom permission to only allow admins or managers to create companies
    """
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        # Allow superusers
        if request.user.is_superuser:
            return True
            
        # Allow users in Admin or Manager groups
        return request.user.groups.filter(name__in=['Admin', 'Manager']).exists()

class AuthViewSet(viewsets.ViewSet):
    """Authentication endpoints"""
    
    @action(detail=False, methods=['post'], permission_classes=[])
    def login(self, request):
        """Login endpoint with proper error handling and company information
        Supports login with either username or email"""
        try:
            username_or_email = request.data.get('username')
            password = request.data.get('password')
            
            # Validate input
            if not username_or_email or not password:
                return Response({
                    'error': 'Username/Email and password are required',
                    'details': 'Both username/email and password fields must be provided'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            logger.info(f"Login attempt for: {username_or_email}")
            
            # Try to authenticate with username first
            user = authenticate(username=username_or_email, password=password)
            
            # If authentication failed, try with email
            if not user:
                try:
                    # Check if the input is an email format
                    if '@' in username_or_email:
                        logger.info(f"Attempting email lookup for: {username_or_email}")
                        # Try to find user by email
                        user_obj = User.objects.filter(email=username_or_email).first()
                        logger.info(f"Email lookup result: {'Found' if user_obj else 'Not found'}")
                        if user_obj:
                            logger.info(f"Authenticating with username: {user_obj.username}")
                            # Authenticate using the username from the user object
                            user = authenticate(username=user_obj.username, password=password)
                            logger.info(f"Authentication result: {'Success' if user else 'Failed'}")
                except User.DoesNotExist:
                    logger.error(f"User.DoesNotExist exception for email: {username_or_email}")
                    pass
            
            if not user:
                logger.warning(f"Failed login attempt for: {username_or_email}")
                return Response({
                    'error': 'Invalid credentials',
                    'details': 'Username/Email or password is incorrect'
                }, status=status.HTTP_401_UNAUTHORIZED)
            
            if not user.is_active:
                return Response({
                    'error': 'Account disabled',
                    'details': 'Your account has been disabled. Please contact administrator.'
                }, status=status.HTTP_401_UNAUTHORIZED)
            
            # Generate JWT tokens
            refresh = RefreshToken.for_user(user)
            
            # Get all main companies (for admin/manager dropdown)
            main_companies = Company.objects.filter(is_main_company=True)
            
            # Try to get user's employee record with company details
            employee_data = None
            main_company_data = None
            sub_company_data = None
            
            try:
                employee = Employee.objects.select_related(
                    'main_company', 
                    'sub_company',
                    'sub_company__parent_company'
                ).get(email=user.email)
                
                # Build employee data
                employee_data = EmployeeSerializer(employee).data
                
                # Role-based company data display logic
                employee_role = employee.role
                
                # Case 1: Admin - Don't show any company (they manage all)
                if employee_role == 'Admin':
                    main_company_data = None
                    sub_company_data = None
                
                # Case 2: Manager (Main Company) - Show main company only
                elif employee_role == 'Manager' and employee.main_company:
                    main_company_data = CompanySerializer(employee.main_company).data
                    sub_company_data = None
                
                # Case 3: Sub-Manager (Sub Company) - Show parent company as main_company, sub_company as null
                elif employee_role == 'Sub-Manager' and employee.sub_company:
                    # Show parent company as main_company
                    if employee.sub_company.parent_company:
                        main_company_data = CompanySerializer(employee.sub_company.parent_company).data
                    sub_company_data = None
                
                # Case 4: HR/Supervisor/Employee - Show both main and sub companies
                else:
                    # Get main company info
                    if employee.main_company:
                        main_company_data = CompanySerializer(employee.main_company).data
                    
                    # Get sub company info (and its parent)
                    if employee.sub_company:
                        sub_company_data = CompanySerializer(employee.sub_company).data
                        
                        # Add parent company details for reference
                        if employee.sub_company.parent_company:
                            sub_company_data['parent_company_details'] = CompanySerializer(
                                employee.sub_company.parent_company
                            ).data
                
            except Employee.DoesNotExist:
                logger.warning(f"No employee record found for user: {username_or_email}")
            
            # Build response
            response_data = {
                'success': True,
                'access_token': str(refresh.access_token),
                'refresh_token': str(refresh),
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'is_superuser': user.is_superuser,
                    'groups': [group.name for group in user.groups.all()]
                },
                'employee': employee_data,
                'main_company': main_company_data,
                'sub_company': sub_company_data,
                'all_main_companies': CompanySerializer(main_companies, many=True).data
            }

            # Add supervised companies list and cache it for supervisors so frontend can switch
            try:
                supervised_companies = []
                can_switch = False
                # If employee object exists and has supervised_companies M2M
                if employee is not None and hasattr(employee, 'supervised_companies'):
                    supervised_qs = employee.supervised_companies.all()
                    if supervised_qs.exists():
                        supervised_companies = CompanySerializer(supervised_qs, many=True).data
                        can_switch = supervised_qs.count() > 1

                        # Cache the supervised company ids for quick retrieval (24h)
                        try:
                            cache_key = f"user_companies_{user.id}"
                            cache.set(cache_key, [c.id for c in supervised_qs], timeout=24*3600)
                        except Exception:
                            # caching should not block login
                            pass

                # Attach to response
                response_data['supervised_companies'] = supervised_companies
                response_data['can_switch_company'] = can_switch
            except Exception:
                # non-fatal; keep login response working
                response_data['supervised_companies'] = []
                response_data['can_switch_company'] = False
            
            logger.info(f"Successful login for username: {username_or_email}")
            return Response(response_data)
            
        except Exception as e:
            logger.error(f"Login error: {str(e)}")
            return Response({
                'error': 'Login failed',
                'details': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def user_profile(self, request):
        """Get current user's complete profile with company information"""
        try:
            user = request.user
            
            # Try to get employee record
            try:
                employee = Employee.objects.select_related(
                    'main_company',
                    'sub_company',
                    'sub_company__parent_company'
                ).get(email=user.email)
                
                employee_data = EmployeeSerializer(employee).data
                
                # Role-based company display logic
                main_company = None
                sub_company = None
                employee_role = employee.role
                
                # Case 1: Admin - Don't show any company
                if employee_role == 'Admin':
                    main_company = None
                    sub_company = None
                
                # Case 2: Manager (Main Company) - Show main company only
                elif employee_role == 'Manager' and employee.main_company:
                    main_company = CompanySerializer(employee.main_company).data
                    sub_company = None
                
                # Case 3: Sub-Manager (Sub Company) - Show parent as main_company, sub_company as null
                elif employee_role == 'Sub-Manager' and employee.sub_company:
                    if employee.sub_company.parent_company:
                        main_company = CompanySerializer(employee.sub_company.parent_company).data
                    sub_company = None
                
                # Case 4: HR/Supervisor/Employee - Show both companies
                else:
                    if employee.main_company:
                        main_company = CompanySerializer(employee.main_company).data
                    
                    if employee.sub_company:
                        sub_company = CompanySerializer(employee.sub_company).data
                        # Add parent company details
                        if employee.sub_company.parent_company:
                            sub_company['parent_company_details'] = CompanySerializer(
                                employee.sub_company.parent_company
                            ).data
                
                return Response({
                    'user': {
                        'id': user.id,
                        'username': user.username,
                        'email': user.email,
                        'first_name': user.first_name,
                        'last_name': user.last_name,
                        'is_superuser': user.is_superuser,
                        'groups': [group.name for group in user.groups.all()]
                    },
                    'employee': employee_data,
                    'main_company': main_company,
                    'sub_company': sub_company
                })
                
            except Employee.DoesNotExist:
                return Response({
                    'error': 'No employee record found',
                    'user': {
                        'id': user.id,
                        'username': user.username,
                        'email': user.email,
                        'first_name': user.first_name,
                        'last_name': user.last_name,
                        'is_superuser': user.is_superuser,
                        'groups': [group.name for group in user.groups.all()]
                    }
                }, status=status.HTTP_404_NOT_FOUND)
                
        except Exception as e:
            logger.error(f"Profile fetch error: {str(e)}")
            return Response({
                'error': 'Failed to fetch profile',
                'details': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated], url_path='switch-company')
    def switch_company(self, request):
        """
        Switch active company for the authenticated user by returning new JWT tokens
        that include an `active_company` claim. This avoids server-side cache and
        relies on bearer tokens.

        Request body: { "company_id": 123 }

        Response: { success, active_company, access_token, refresh_token }
        """
        try:
            user = request.user
            emp = getattr(user, 'employee', None)

            # If no direct relation (user.employee), try other reasonable lookups
            if not emp:
                try:
                    # Try Employee linked by user_id (common OneToOneField naming)
                    emp = Employee.objects.filter(user_id=getattr(user, 'id', None)).first()
                except Exception:
                    emp = None

            if not emp and getattr(user, 'email', None):
                try:
                    # Fallback: match by email
                    emp = Employee.objects.filter(email=user.email).first()
                except Exception:
                    emp = None

            # Allow staff/admin to provide an employee id to act on behalf of (explicit)
            if not emp:
                supplied_emp = (request.data.get('employee_id') or request.data.get('supervisor_id') or
                                request.query_params.get('employee_id'))
                if supplied_emp and (getattr(user, 'is_staff', False) or getattr(user, 'is_superuser', False)):
                    try:
                        emp = Employee.objects.filter(id=int(supplied_emp)).first()
                    except Exception:
                        emp = None

            if not emp:
                return Response({'success': False, 'error': 'Employee profile required. Ensure the authenticated user has a linked Employee record, or call this endpoint with employee_id when using staff credentials.'}, status=status.HTTP_400_BAD_REQUEST)

            cid = request.data.get('company_id') or request.query_params.get('company_id')
            if not cid:
                return Response({'success': False, 'error': 'company_id is required'}, status=status.HTTP_400_BAD_REQUEST)

            try:
                cid_int = int(cid)
            except Exception:
                return Response({'success': False, 'error': 'invalid company_id'}, status=status.HTTP_400_BAD_REQUEST)

            # Validate authorization: user must be allowed for this company
            authorized = False
            try:
                if hasattr(emp, 'supervised_companies') and emp.supervised_companies.filter(id=cid_int).exists():
                    authorized = True
                if getattr(emp, 'main_company_id', None) == cid_int:
                    authorized = True
                if getattr(emp, 'sub_company_id', None) == cid_int:
                    authorized = True
            except Exception:
                # fallback to not authorized
                authorized = False

            if not authorized:
                return Response({'success': False, 'error': 'not authorized for this company'}, status=status.HTTP_403_FORBIDDEN)

            # Generate new tokens with active_company claim
            refresh = RefreshToken.for_user(user)
            # attach claim to refresh so access inherits it
            try:
                refresh['active_company'] = cid_int
            except Exception:
                # some token backends may restrict custom claims; ignore if not allowed
                pass

            access = refresh.access_token
            try:
                access['active_company'] = cid_int
            except Exception:
                pass

            # Return serialized company info along with tokens
            try:
                company = Company.objects.get(id=cid_int)
                company_data = CompanySerializer(company).data
            except Company.DoesNotExist:
                return Response({'success': False, 'error': 'Company not found'}, status=status.HTTP_404_NOT_FOUND)

            return Response({
                'success': True,
                'message': 'Active company switched (token updated)',
                'active_company': company_data,
                'access_token': str(access),
                'refresh_token': str(refresh)
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({'success': False, 'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            
class CompanyViewSet(viewsets.ModelViewSet):
    """Company management endpoints with proper permissions"""
    serializer_class = CompanySerializer
    permission_classes = [IsAdminOrManager]  # Updated permission
    queryset = Company.objects.all()

    def get_queryset(self):
        """Filter companies based on user role"""
        if self.request.user.is_superuser:
            return Company.objects.all()
        
        # For admin/manager users, show all companies they have access to
        try:
            user_employee = Employee.objects.get(email=self.request.user.email)
            if user_employee.main_company:
                # If user belongs to main company, show all companies
                return Company.objects.all()
            else:
                # If user belongs to sub company, show only their company
                return Company.objects.filter(id=user_employee.sub_company.id)
        except Employee.DoesNotExist:
            return Company.objects.none()

    @action(detail=False, methods=['post'])
    def create_main_company(self, request):
        """Create a new main company (Admin only)"""
        if not (request.user.is_superuser or request.user.groups.filter(name='Admin').exists()):
            return Response({
                'error': 'Permission denied',
                'message': 'Only admins can create main companies'
            }, status=status.HTTP_403_FORBIDDEN)
        
        try:
            with transaction.atomic():
                company_data = request.data.get('company_data', {})
                user_data = request.data.get('user_data', {})
                
                # Set main company properties
                company_data['is_main_company'] = True
                company_data.pop('parent_company', None)  # Main companies don't have parent
                
                # Create the main company
                serializer = CompanySerializer(data=company_data)
                if not serializer.is_valid():
                    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
                
                company = serializer.save()
                
                # Create user account for main company manager
                user_account = None
                if user_data:
                    user_account = self._create_user_for_company(company, user_data, is_main=True)
                
                response_data = {
                    'success': True,
                    'message': 'Main company created successfully',
                    'company': CompanySerializer(company).data
                }
                
                if user_account:
                    response_data['user_account'] = {
                        'id': user_account.id,
                        'username': user_account.username,
                        'email': user_account.email,
                        'role': 'Manager',
                        'message': 'Manager account created for main company'
                    }
                
                return Response(response_data, status=status.HTTP_201_CREATED)
                
        except Exception as e:
            return Response({
                'error': 'Main company creation failed',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['post'])
    def create_sub_company(self, request):
        """Create a sub-company under a main company"""
        try:
            with transaction.atomic():
                company_data = request.data.get('company_data', {})
                settings_data = request.data.get('settings_data', {})
                user_data = request.data.get('user_data', {})
                parent_company_id = request.data.get('parent_company_id')
                
                # Validate parent company
                if not parent_company_id:
                    return Response({
                        'error': 'parent_company_id is required'
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                try:
                    parent_company = Company.objects.get(
                        id=parent_company_id, 
                        is_main_company=True
                    )
                except Company.DoesNotExist:
                    return Response({
                        'error': 'Invalid parent company ID or parent is not a main company'
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                # Set sub-company properties
                company_data['is_main_company'] = False
                company_data['parent_company'] = parent_company_id
                
                # Create the sub-company
                company_serializer = CompanySerializer(data=company_data)
                if not company_serializer.is_valid():
                    return Response(company_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
                
                company = company_serializer.save()
                
                # Create client profile settings
                settings_data['client'] = company.id
                settings_serializer = ClientProfileSettingsSerializer(data=settings_data)
                if not settings_serializer.is_valid():
                    company.delete()
                    return Response(settings_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
                
                settings = settings_serializer.save()
                
                # Create user account if provided
                user_account = None
                if user_data:
                    user_account = self._create_user_for_company(company, user_data, is_main=False)
                
                response_data = {
                    'success': True,
                    'message': 'Sub-company created successfully',
                    'company': company_serializer.data,
                    'settings': ClientProfileSettingsSerializer(settings).data,
                    'parent_company': {
                        'id': parent_company.id,
                        'name': parent_company.name
                    }
                }
                
                if user_account:
                    response_data['user_account'] = {
                        'id': user_account.id,
                        'username': user_account.username,
                        'email': user_account.email,
                        'role': 'Sub-Manager',
                        'message': 'Sub-Manager account created for sub-company'
                    }
                
                return Response(response_data, status=status.HTTP_201_CREATED)
                
        except Exception as e:
            return Response({
                'error': 'Sub-company creation failed',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['get'])
    def sub_companies(self, request, pk=None):
        """Get all sub-companies under a main company"""
        try:
            main_company = self.get_object()
            if not main_company.is_main_company:
                return Response({
                    'error': 'This endpoint is only for main companies'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            sub_companies = Company.objects.filter(
                parent_company=main_company,
                is_main_company=False
            )
            
            serializer = CompanySerializer(sub_companies, many=True)
            return Response({
                'main_company': CompanySerializer(main_company).data,
                'sub_companies': serializer.data,
                'count': sub_companies.count()
            })
            
        except Exception as e:
            return Response({
                'error': 'Failed to fetch sub-companies',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['get'])
    def hierarchy(self, request):
        """Get complete company hierarchy"""
        try:
            main_companies = Company.objects.filter(is_main_company=True)
            hierarchy_data = []
            
            for main_company in main_companies:
                sub_companies = Company.objects.filter(
                    parent_company=main_company,
                    is_main_company=False
                )
                
                hierarchy_data.append({
                    'main_company': CompanySerializer(main_company).data,
                    'sub_companies': CompanySerializer(sub_companies, many=True).data,
                    'sub_companies_count': sub_companies.count()
                })
            
            return Response({
                'hierarchy': hierarchy_data,
                'total_main_companies': main_companies.count()
            })
            
        except Exception as e:
            return Response({
                'error': 'Failed to fetch company hierarchy',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def _create_user_for_company(self, company, user_data, is_main=False):
        """Helper method to create user account for company"""
        from django.contrib.auth import get_user_model
        
        User = get_user_model()
        
        username = user_data.get('username') or f"{'main' if is_main else 'client'}_{company.id}"
        email = user_data.get('email', f"{username}@example.com")
        password = user_data.get('password', f"{username}123")
        first_name = user_data.get('first_name', company.name.split()[0])
        last_name = user_data.get('last_name', 'Administrator')
        
        # Check if username exists
        if User.objects.filter(username=username).exists():
            counter = 1
            original_username = username
            while User.objects.filter(username=username).exists():
                username = f"{original_username}_{counter}"
                counter += 1
        
        # Check if email exists
        if User.objects.filter(email=email).exists():
            raise Exception(f'Email {email} is already registered')
        
        # Create user
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            is_active=True
        )
        
        # Different roles for main company vs sub-company
        if is_main:
            group_name = 'Manager'
            employee_role = 'Manager'
        else:
            group_name = 'Sub-Manager'
            employee_role = 'Sub-Manager'
        
        group, _ = Group.objects.get_or_create(name=group_name)
        user.groups.add(group)
        
        # Create employee record with appropriate role
        Employee.objects.create(
            full_name=f"{first_name} {last_name}",
            employee_code=f"{'MAIN' if is_main else 'SUB'}_{company.id}_ADMIN",
            date_of_birth=user_data.get('date_of_birth', '1990-01-01'),
            gender=user_data.get('gender', 'M'),
            marital_status=user_data.get('marital_status', 'S'),
            mobile_number=user_data.get('mobile_number', '0000000000'),
            email=email,
            current_address=company.address or 'Office Address',
            permanent_address=company.address or 'Office Address',
            role=employee_role,  # Manager for main, Sub-Manager for sub
            main_company=company if is_main else None,
            sub_company=company if not is_main else None,
            status='ACTIVE'
        )
        
        return user


@api_view(['POST'])
@permission_classes([IsAuthenticated])  # Only admin can create users
def create_client_user(request):
    """Create user account for existing client"""
    try:
        client_id = request.data.get('client_id')
        user_data = request.data.get('user_data', {})
        
        if not client_id:
            return Response({'error': 'client_id is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        client = get_object_or_404(Company, id=client_id, is_main_company=False)
        
        # Check if user already exists for this client
        if User.objects.filter(employee__sub_company=client).exists():
            return Response({
                'error': 'User already exists for this client'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        username = user_data.get('username') or f"client_{client_id}"
        email = user_data.get('email', f"client{client_id}@example.com")
        password = user_data.get('password', f"client{client_id}123")
        
        # Create user
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=user_data.get('first_name', client.name),
            last_name=user_data.get('last_name', 'Admin'),
            is_active=True
        )
        
        # Add to HR group

        manager_group, _ = Group.objects.get_or_create(name='Manager')
        client_user.groups.add(manager_group)
        
        return Response({
            'success': True,
            'user_account': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'password': password,  # Return password only once
                'message': 'Save these credentials - password will not be shown again'
            }
        }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        return Response({
            'error': 'User creation failed',
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class ClientProfileSettingsViewSet(viewsets.ModelViewSet):
    """Client profile settings management"""
    serializer_class = ClientProfileSettingsSerializer
    permission_classes = [IsAuthenticated, ClientProfilePermission]
    
    def get_queryset(self):
        client_id = self.request.query_params.get('client_id')
        if client_id:
            return ClientProfileSettings.objects.filter(client_id=client_id)
        return ClientProfileSettings.objects.all()

class EmployeeViewSet(viewsets.ModelViewSet):
    """Employee management endpoints"""
    permission_classes = [IsAuthenticated, ClientProfilePermission]
    
    def get_serializer_class(self):
        if self.action == 'create':
            return EmployeeCreateSerializer
        elif self.action == 'retrieve':
            return EmployeeDetailSerializer
        return EmployeeSerializer
    
    def get_queryset(self):
        client_id = self.request.query_params.get('client_id')
        status_filter = self.request.query_params.get('status', 'ACTIVE')
        
        # If no client_id provided, try to get from user's employee record
        if not client_id:
            try:
                user_employee = Employee.objects.get(email=self.request.user.email)
                if user_employee.sub_company:
                    client_id = user_employee.sub_company.id
            except Employee.DoesNotExist:
                pass
        
        queryset = Employee.objects.filter(status=status_filter)
        if client_id:
            queryset = queryset.filter(sub_company_id=client_id)
        
        return queryset
    
    def perform_create(self, serializer):
        """Override to set client company automatically"""
        client_id = self.request.data.get('client_id')
        
        # If no client_id provided, try to get from user's employee record
        if not client_id:
            try:
                user_employee = Employee.objects.get(email=self.request.user.email)
                if user_employee.sub_company:
                    client_id = user_employee.sub_company.id
            except Employee.DoesNotExist:
                raise ValidationError("Could not determine client company")
        
        # Validate client exists
        client = get_object_or_404(Company, id=client_id, is_main_company=False)
        
        # Save employee with client company
        serializer.save(sub_company=client)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_client_info(request):
    """Get current user's client information"""
    try:
        # Try to find user's employee record
        try:
            employee = Employee.objects.get(email=request.user.email)
            client = employee.sub_company
            
            if client:
                # Get client settings
                try:
                    settings = ClientProfileSettings.objects.get(client=client)
                    settings_data = ClientProfileSettingsSerializer(settings).data
                except ClientProfileSettings.DoesNotExist:
                    settings_data = None
                
                return Response({
                    'user': {
                        'id': request.user.id,
                        'username': request.user.username,
                        'email': request.user.email,
                        'first_name': request.user.first_name,
                        'last_name': request.user.last_name
                    },
                    'employee': EmployeeSerializer(employee).data,
                    'client': CompanySerializer(client).data,
                    'settings': settings_data
                })
            else:
                return Response({
                    'error': 'No client associated with user'
                }, status=status.HTTP_404_NOT_FOUND)
                
        except Employee.DoesNotExist:
            return Response({
                'error': 'No employee record found for user'
            }, status=status.HTTP_404_NOT_FOUND)
            
    except Exception as e:
        return Response({
            'error': 'Failed to get client info',
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class AttendanceViewSet(viewsets.ModelViewSet):

    @action(detail=False, methods=['get'], url_path='checkin_checkout_summary', permission_classes=[IsAuthenticated])
    def checkin_checkout_summary(self, request):
        """Admin: Get count of checked-in and checked-out members for today. Only admin can access."""
        if not request.user.is_superuser:
            return Response({'detail': 'You do not have permission to perform this action.'}, status=status.HTTP_403_FORBIDDEN)
        from datetime import date
        today = date.today()
        # Optional filters
        company_id = request.query_params.get('company_id')
        subcompany_id = request.query_params.get('subcompany_id')
        queryset = Attendance.objects.filter(date=today)
        if company_id:
            queryset = queryset.filter(employee__main_company_id=company_id)
        if subcompany_id:
            queryset = queryset.filter(employee__sub_company_id=subcompany_id)
        checked_in = queryset.filter(check_in_time__isnull=False).count()
        checked_out = queryset.filter(check_out_time__isnull=False).count()
        total = queryset.count()
        return Response({
            'date': str(today),
            'total_records': total,
            'checked_in': checked_in,
            'checked_out': checked_out
        })

    @action(detail=False, methods=['post'], url_path='checkin', permission_classes=[IsAuthenticated])
    def checkin(self, request):
        """Check-in for attendance: sets check_in_time to current IST time."""
        from django.utils import timezone
        from datetime import datetime
        import pytz
        data = request.data
        employee_id = data.get('employee')
        date_str = data.get('date')
        if not employee_id or not date_str:
            return Response({'error': 'employee and date are required'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            ist = pytz.timezone('Asia/Kolkata')
            now_ist = datetime.now(ist).time()
            attendance, created = Attendance.objects.get_or_create(
                employee_id=employee_id,
                date=date_str,
                defaults={'status': 'P'}
            )
            if attendance.check_in_time:
                return Response({'error': 'Already checked in'}, status=status.HTTP_400_BAD_REQUEST)
            attendance.check_in_time = now_ist
            attendance.save()
            return Response({'success': True, 'check_in_time': str(attendance.check_in_time)})
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['post'], url_path='checkout', permission_classes=[IsAuthenticated])
    def checkout(self, request):
        """Check-out for attendance: sets check_out_time to current IST time and calculates hours worked."""
        from django.utils import timezone
        from datetime import datetime, timedelta
        import pytz
        data = request.data
        employee_id = data.get('employee')
        date_str = data.get('date')
        if not employee_id or not date_str:
            return Response({'error': 'employee and date are required'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            ist = pytz.timezone('Asia/Kolkata')
            now_ist = datetime.now(ist).time()
            attendance = Attendance.objects.filter(employee_id=employee_id, date=date_str).first()
            if not attendance:
                return Response({'error': 'No check-in found for this date'}, status=status.HTTP_400_BAD_REQUEST)
            if attendance.check_out_time:
                return Response({'error': 'Already checked out'}, status=status.HTTP_400_BAD_REQUEST)
            attendance.check_out_time = now_ist
            # Calculate hours worked
            if attendance.check_in_time:
                dt_in = datetime.combine(attendance.date, attendance.check_in_time)
                dt_out = datetime.combine(attendance.date, now_ist)
                if dt_out < dt_in:
                    dt_out += timedelta(days=1)  # handle overnight
                attendance.hours_worked = dt_out - dt_in
            attendance.save()
            return Response({
                'success': True,
                'check_out_time': str(attendance.check_out_time),
                'hours_worked': str(attendance.hours_worked) if attendance.hours_worked else None
            })
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    """Attendance management"""
    serializer_class = AttendanceSerializer
    permission_classes = [IsAuthenticated, ClientProfilePermission]
    
    def get_queryset(self):
        client_id = self.request.query_params.get('client_id')
        month = self.request.query_params.get('month')
        year = self.request.query_params.get('year')
        
        queryset = Attendance.objects.all()
        if client_id:
            queryset = queryset.filter(employee__sub_company_id=client_id)
        if month and year:
            queryset = queryset.filter(date__month=month, date__year=year)
            
        return queryset
    
    @action(detail=False, methods=['post'])
    def bulk_upload(self, request):
        """Bulk attendance upload"""
        serializer = BulkAttendanceSerializer(data=request.data)
        if serializer.is_valid():
            data = serializer.validated_data
            month = data['month']
            year = data['year']
            company_id = data['company_id']
            attendance_data = data['attendance_data']
            
            created_count = 0
            for att_record in attendance_data:
                employee_id = att_record.get('employee_id')
                date_str = att_record.get('date')
                status = att_record.get('status')
                
                attendance_date = datetime.strptime(date_str, '%Y-%m-%d').date()
                
                attendance, created = Attendance.objects.update_or_create(
                    employee_id=employee_id,
                    date=attendance_date,
                    defaults={'status': status}
                )
                if created:
                    created_count += 1
            
            return Response({
                'message': f'Attendance uploaded successfully. {created_count} records created.'
            })
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def monthly_summary(self, request):
        """Get monthly attendance summary"""
        client_id = request.query_params.get('client_id')
        month = request.query_params.get('month')
        year = request.query_params.get('year')
        
        if not all([client_id, month, year]):
            return Response({'error': 'client_id, month, and year are required'}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        employees = Employee.objects.filter(
            sub_company_id=client_id,
            status='ACTIVE'
        )
        
        summary_data = []
        for employee in employees:
            attendance_records = Attendance.objects.filter(
                employee=employee,
                date__month=month,
                date__year=year
            )
            overtime_records = OvertimeRecord.objects.filter(
                employee=employee,
                date__month=month,
                date__year=year
            )
            total_days = calendar.monthrange(int(year), int(month))[1]
            present_days = attendance_records.filter(Q(shift_1_status='P') | Q(shift_2_status='P')).count()
            absent_days = attendance_records.filter(Q(shift_1_status='A') | Q(shift_2_status='A')).count()
            holidays = attendance_records.filter(Q(shift_1_status='H') | Q(shift_2_status='H')).count()
            weekly_offs = attendance_records.filter(Q(shift_1_status='WO') | Q(shift_2_status='WO')).count()
            overtime_hours = overtime_records.aggregate(
                total=Sum('hours')
            )['total'] or 0
            summary_data.append({
                'employee_id': employee.id,
                'employee_name': employee.full_name,
                'employee_code': employee.employee_code,
                'total_days': total_days,
                'present_days': present_days,
                'absent_days': absent_days,
                'holidays': holidays,
                'weekly_offs': weekly_offs,
                'overtime_hours': float(overtime_hours)
            })
        
        return Response(summary_data)

class SalaryStructureViewSet(viewsets.ModelViewSet):
    """Salary Structure CRUD operations"""
    serializer_class = SalaryStructureSerializer
    permission_classes = [IsAuthenticated, ClientProfilePermission]
    
    def get_queryset(self):
        """Filter salary structures by client_id if provided"""
        client_id = self.request.query_params.get('client_id')
        employee_id = self.request.query_params.get('employee_id')
        
        queryset = SalaryStructure.objects.all()
        
        if employee_id:
            queryset = queryset.filter(employee_id=employee_id)
        elif client_id:
            queryset = queryset.filter(employee__sub_company_id=client_id)
        
        return queryset.select_related('employee')
    
    def create(self, request, *args, **kwargs):
        """Create salary structure for an employee"""
        employee_id = request.data.get('employee')
        
        # Check if employee exists
        try:
            employee = Employee.objects.get(id=employee_id)
        except Employee.DoesNotExist:
            return Response({
                'error': 'Employee not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Check if salary structure already exists
        if hasattr(employee, 'salarystructure'):
            return Response({
                'error': 'Salary structure already exists for this employee',
                'message': 'Use PUT/PATCH to update existing salary structure'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        return super().create(request, *args, **kwargs)
    
    def update(self, request, *args, **kwargs):
        """Update salary structure"""
        user = request.user
        if not (user.is_superuser or user.groups.filter(name__in=['HR', 'Admin']).exists()):
            return Response({'error': 'permission denied'}, status=status.HTTP_403_FORBIDDEN)
        return super().update(request, *args, **kwargs)
    
    def partial_update(self, request, *args, **kwargs):
        """Partially update salary structure"""
        # Only allow HR or Admin groups to update salary structure
        user = request.user
        if not (user.is_superuser or user.groups.filter(name__in=['HR', 'Admin']).exists()):
            return Response({'error': 'permission denied'}, status=status.HTTP_403_FORBIDDEN)
        return super().partial_update(request, *args, **kwargs)
    
    def destroy(self, request, *args, **kwargs):
        """Delete salary structure"""
        return super().destroy(request, *args, **kwargs)
    
    @action(detail=False, methods=['get'])
    def by_employee(self, request):
        """Get salary structure by employee ID"""
        employee_id = request.query_params.get('employee_id')
        
        if not employee_id:
            return Response({
                'error': 'employee_id is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            salary_structure = SalaryStructure.objects.get(employee_id=employee_id)
            serializer = self.get_serializer(salary_structure)
            return Response(serializer.data)
        except SalaryStructure.DoesNotExist:
            return Response({
                'error': 'Salary structure not found for this employee'
            }, status=status.HTTP_404_NOT_FOUND)

    @action(detail=False, methods=['get'], url_path='hr/all', permission_classes=[IsAuthenticated])
    def hr_all(self, request):
        """HR/Admin: return all salary structures with employee snapshot. Requires HR/Admin group or superuser."""
        user = request.user
        if not (user.is_superuser or user.groups.filter(name__in=['HR', 'Admin']).exists()):
            return Response({'error': 'permission denied'}, status=status.HTTP_403_FORBIDDEN)

        queryset = self.get_queryset()
        data = []
        for s in queryset.select_related('employee'):
            emp = s.employee
            data.append({
                'id': s.id,
                'employee_id': emp.id if emp else None,
                'employee_code': emp.employee_code if emp else None,
                'employee_name': emp.full_name if emp else None,
                'CTC': float(s.CTC),
                'basic': float(s.basic),
                'da': float(s.da),
                'hra': float(s.hra),
                'conveyance': float(s.conveyance),
                'bonus': float(s.bonus),
                'other_allowances': float(s.other_allowances),
                'pf_deduction': float(s.pf_deduction),
                'esi_deduction': float(s.esi_deduction),
                'pt_deduction': float(s.pt_deduction),
                'lwf_deduction': float(s.lwf_deduction),
                'insurance': float(s.insurance),
                'advance': float(s.advance)
            })

        return Response(data)


class ComplaintViewSet(viewsets.ModelViewSet):
    """ViewSet to handle employee complaints (create, list, retrieve) and allow HR/Admin to update status."""
    serializer_class = ComplaintSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Employees see only their complaints unless user is admin/hr which can see all
        user = self.request.user
        # find employee record if present
        try:
            employee = Employee.objects.filter(email=user.email).first()
        except Exception:
            employee = None

        # If user is admin/hr (superuser, group membership, or employee.role), return all
        if self._is_hr_or_admin(user):
            return Complaint.objects.all()

        # Regular employee: show only their complaints
        if employee:
            return Complaint.objects.filter(employee=employee)

        # Fallback: filter by employee email snapshot
        return Complaint.objects.filter(employee_email=user.email)

    def _is_hr_or_admin(self, user):
        """Return True if user is admin or HR. Checks superuser, Django groups, user.role, and Employee.role."""
        try:
            if user.is_superuser:
                return True
        except Exception:
            pass

        # Check Django groups (case-insensitive)
        try:
            if user.groups.filter(name__iexact='Admin').exists() or user.groups.filter(name__iexact='HR').exists():
                return True
        except Exception:
            pass

        # Check a role attribute on the user (if present)
        try:
            if getattr(user, 'role', None) and str(user.role).lower() in ['admin', 'hr']:
                return True
        except Exception:
            pass

        # Finally, check Employee.role if an Employee record exists
        try:
            emp = Employee.objects.filter(email=getattr(user, 'email', None)).first()
            if emp and getattr(emp, 'role', None) and str(emp.role).lower() in ['admin', 'hr']:
                return True
        except Exception:
            pass

        return False

    def perform_create(self, serializer):
        # Attach employee snapshot when creating
        request = self.request
        user = request.user
        employee = None
        employee_name = None
        employee_email = None
        employee_id_text = None

        try:
            # Try to find linked Employee by user.email first
            if getattr(user, 'email', None):
                employee = Employee.objects.filter(email=user.email).first()
        except Exception:
            employee = None

        if employee:
            employee_name = employee.full_name
            employee_email = employee.email
            employee_id_text = getattr(employee, 'employee_code', None)
            serializer.save(employee=employee, employee_name=employee_name, employee_email=employee_email, employee_id_text=employee_id_text)
            return

        # Fallback: try to decode JWT/Access token and extract claims (email/name)
        try:
            auth_header = request.META.get('HTTP_AUTHORIZATION', '')
            parts = auth_header.split()
            if len(parts) == 2 and parts[0].lower() == 'bearer':
                token_str = parts[1]
                from rest_framework_simplejwt.tokens import AccessToken
                try:
                    access = AccessToken(token_str)
                    # common claim names: email, name, first_name, last_name
                    employee_email = access.get('email') or access.get('user_email')
                    employee_name = access.get('employee_name') or access.get('name') or (access.get('first_name') and access.get('last_name') and f"{access.get('first_name')} {access.get('last_name')}")
                    employee_id_text = access.get('employee_id') or access.get('employee_code')
                except Exception:
                    employee_email = None
        except Exception:
            employee_email = None

        # If we now have at least an email or name, save snapshot without Employee FK
        if not employee_name:
            employee_name = f"{getattr(user, 'first_name', '')} {getattr(user, 'last_name', '')}".strip() or getattr(user, 'username', '')
        if not employee_email:
            employee_email = getattr(user, 'email', None)

        serializer.save(employee=None, employee_name=employee_name, employee_email=employee_email, employee_id_text=employee_id_text)

    @action(detail=True, methods=['patch'], permission_classes=[IsAuthenticated])
    def update_status(self, request, pk=None):
        """HR/Admin can update the status of a complaint."""
        user = request.user
        if not self._is_hr_or_admin(user):
            return Response({'error': 'permission denied'}, status=status.HTTP_403_FORBIDDEN)

        complaint = self.get_object()
        new_status = request.data.get('status')
        if new_status not in dict(Complaint.STATUS_CHOICES).keys():
            return Response({'error': 'invalid status'}, status=status.HTTP_400_BAD_REQUEST)
        complaint.status = new_status
        complaint.save()
        return Response(ComplaintSerializer(complaint).data)

class PayrollViewSet(viewsets.ViewSet):
    """Payroll processing endpoints"""
    permission_classes = [IsAuthenticated, ClientProfilePermission]
    
    @action(detail=False, methods=['post'])
    def generate_salary_statement(self, request):
        """Generate salary statement for month"""
        serializer = SalaryStatementSerializer(data=request.data)
        if serializer.is_valid():
            data = serializer.validated_data
            employee_id = data['employee_id']
            month = data['month']
            year = data['year']
            days_payable = data['days_payable']
            overtime_hours = data.get('overtime_hours', 0)
            
            employee = get_object_or_404(Employee, id=employee_id)
            
            
            if not hasattr(employee, 'salarystructure'):
                return Response({'error': 'Salary structure not found for employee'}, 
                              status=status.HTTP_400_BAD_REQUEST)
            
            salary_structure = employee.salarystructure
            
            # Calculate prorated salary
            days_in_month = calendar.monthrange(year, month)[1]
            prorate_factor = days_payable / days_in_month
            
            # Calculate earnings
            basic_earned = salary_structure.basic * prorate_factor
            da_earned = salary_structure.da * prorate_factor
            hra_earned = salary_structure.hra * prorate_factor
            conveyance_earned = salary_structure.conveyance * prorate_factor
            bonus_earned = salary_structure.bonus * prorate_factor
            other_earned = salary_structure.other_allowances * prorate_factor
            
            # Calculate overtime
            overtime_amount = 0
            if overtime_hours > 0:
                hourly_rate = (salary_structure.basic + salary_structure.da) / (days_in_month * 8)
                overtime_amount = overtime_hours * hourly_rate * 2  # Double rate for OT
            
            gross_earned = (basic_earned + da_earned + hra_earned + 
                          conveyance_earned + bonus_earned + other_earned + overtime_amount)
            
            # Calculate deductions
            pf_deduction = basic_earned * 0.12  # 12% of basic
            esi_deduction = gross_earned * 0.0175 if gross_earned <= 25000 else 0  # 1.75% if <= 25k
            pt_deduction = salary_structure.pt_deduction if gross_earned > 10000 else 0
            
            total_deductions = (pf_deduction + esi_deduction + pt_deduction + 
                              salary_structure.lwf_deduction + salary_structure.insurance + 
                              salary_structure.advance)
            
            net_salary = gross_earned - total_deductions
            
            # Create or update payslip
            payslip, created = Payslip.objects.update_or_create(
                employee=employee,
                month=month,
                year=year,
                defaults={
                    'gross_salary': gross_earned,
                    'deductions': total_deductions,
                    'net_salary': net_salary
                }
            )
            
            return Response(PayslipSerializer(payslip).data)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'], url_path='salary-statement', permission_classes=[IsAuthenticated])
    def salary_statement(self, request):
        """Return a detailed salary statement for given employee/month/year.

        Query params: employee_id, month, year, days_payable (optional), overtime_hours (optional)
        Accessible to: the employee themself, HR group, Admin (superuser or Admin group)
        """
        emp_id = request.query_params.get('employee_id')
        month = request.query_params.get('month')
        year = request.query_params.get('year')
        days_payable = request.query_params.get('days_payable')
        overtime_hours = float(request.query_params.get('overtime_hours') or 0)

        # month/year required
        if not (month and year):
            return Response({'error': 'month and year are required'}, status=status.HTTP_400_BAD_REQUEST)

        month = int(month)
        year = int(year)
        days_in_month = calendar.monthrange(year, month)[1]
        days_payable = int(days_payable) if days_payable else days_in_month
        # Use Decimal for safe arithmetic with Decimal model fields
        days_in_month_d = Decimal(days_in_month)
        days_payable_d = Decimal(days_payable)
        prorate = (days_payable_d / days_in_month_d)

        user = request.user
        is_hr_or_admin = user.is_superuser or user.groups.filter(name__in=['HR', 'Admin']).exists()

        results = []

        # If no employee_id provided:
        if not emp_id:
            # If admin/HR: return statements for all employees (basic list)
            if is_hr_or_admin:
                employees = Employee.objects.filter(status='ACTIVE')
            else:
                # Employee: infer employee from user's email
                try:
                    emp = Employee.objects.get(email=user.email)
                    employees = [emp]
                except Employee.DoesNotExist:
                    return Response({'error': 'employee record not found for user'}, status=status.HTTP_404_NOT_FOUND)
        else:
            try:
                employees = [Employee.objects.get(id=emp_id)]
            except Employee.DoesNotExist:
                return Response({'error': 'employee not found'}, status=status.HTTP_404_NOT_FOUND)

        # Build statement per employee
        for emp in employees:
            # Permission: employee can view only their own unless hr/admin
            if not is_hr_or_admin and getattr(user, 'email', None) != emp.email:
                continue

            salary_structure = getattr(emp, 'salarystructure', None)
            if not salary_structure:
                # skip employees without salary structure
                continue

            # salary_structure fields are Decimal -> use Decimal arithmetic
            earned_basic_d = (salary_structure.basic or Decimal('0')) * prorate
            earned_da_d = (salary_structure.da or Decimal('0')) * prorate
            earned_special_d = (salary_structure.other_allowances or Decimal('0')) * prorate
            earned_hra_d = (salary_structure.hra or Decimal('0')) * prorate
            earned_conveyance_d = (salary_structure.conveyance or Decimal('0')) * prorate
            earned_bonus_d = (salary_structure.bonus or Decimal('0'))

            overtime_amount_d = Decimal('0')
            if overtime_hours > 0:
                # convert overtime_hours to Decimal
                overtime_hours_d = Decimal(str(overtime_hours))
                hourly_rate_d = (salary_structure.basic + salary_structure.da) / (Decimal(days_in_month) * Decimal('8'))
                overtime_amount_d = overtime_hours_d * hourly_rate_d * Decimal('2')

            gross_earned_d = earned_basic_d + earned_da_d + earned_special_d + earned_hra_d + earned_conveyance_d + earned_bonus_d + overtime_amount_d

            pf_d = earned_basic_d * Decimal('0.12')
            esi_d = (gross_earned_d * Decimal('0.0175')) if gross_earned_d <= Decimal('25000') else Decimal('0')
            pt_d = (salary_structure.pt_deduction or Decimal('0'))
            lwf_d = (salary_structure.lwf_deduction or Decimal('0'))
            canteen_d = Decimal('0')
            total_deductions_d = pf_d + esi_d + pt_d + lwf_d + (salary_structure.insurance or Decimal('0')) + (salary_structure.advance or Decimal('0')) + canteen_d

            take_home_d = gross_earned_d - total_deductions_d

            # attach payslip download URL if present
            payslip = Payslip.objects.filter(employee=emp, month=month, year=year).first()
            pdf_url = None
            if payslip and payslip.pdf_file:
                try:
                    pdf_url = request.build_absolute_uri(payslip.pdf_file.url)
                except Exception:
                    pdf_url = None

            fixed = {
                'Basic': float(salary_structure.basic or Decimal('0')),
                'DA': float(salary_structure.da or Decimal('0')),
                'Special Allowance': float(salary_structure.other_allowances or Decimal('0')),
                'Leave with Wages': 0.0,
                'Bonus': float(salary_structure.bonus or Decimal('0')),
                'Gross Salary': float((salary_structure.basic or Decimal('0')) + (salary_structure.da or Decimal('0')) + (salary_structure.hra or Decimal('0')) + (salary_structure.conveyance or Decimal('0')) + (salary_structure.bonus or Decimal('0')) + (salary_structure.other_allowances or Decimal('0')))
            }

            # gather profile info from related models (if available)
            try:
                official = emp.officialdetails
            except OfficialDetails.DoesNotExist:
                official = None

            try:
                identity = emp.identitydocument
            except IdentityDocument.DoesNotExist:
                identity = None

            profile = {
                'emp_code': emp.employee_code,
                'name': emp.full_name,
                'gender': emp.get_gender_display() if hasattr(emp, 'get_gender_display') else emp.gender,
                'designation': official.designation if official else None,
                'department': official.department if official else None,
                'dob': emp.date_of_birth.isoformat() if emp.date_of_birth else None,
                'esi_number': identity.esi_number if identity else None,
                'uan_number': identity.pf_uan_number if identity else None,
                'date_of_joining': official.date_of_joining.isoformat() if official and official.date_of_joining else None
            }

            payload = {
                'employee_id': emp.id,
                'month': month,
                'year': year,
                'profile': profile,
                'fixed': {k: round(v, 2) for k, v in fixed.items()},
                'earned': {
                    'Days Payable': days_payable,
                    'Extra Days': max(0, days_payable - days_in_month),
                    'Basic': round(float(earned_basic_d), 2),
                    'DA': round(float(earned_da_d), 2),
                    'Special Allowance': round(float(earned_special_d), 2),
                    'Leave with Wages': 0.0,
                    'Bonus': round(float(earned_bonus_d), 2),
                    'Other Allowance (NHF Days)': 0.0,
                    'Attendance Bonus': 0.0,
                    'Gross': round(float(gross_earned_d), 2)
                },
                'deductions': {
                    'ESI Deduction': round(float(esi_d), 2),
                    'PF Deduction': round(float(pf_d), 2),
                    'PT': round(float(pt_d), 2),
                    'LWF': round(float(lwf_d), 2),
                    'Canteen Deduction': round(float(canteen_d), 2)
                },
                'gross': round(float(gross_earned_d), 2),
                'total_deductions': round(float(total_deductions_d), 2),
                'take_home': round(float(take_home_d), 2),
                'payslip_download_url': pdf_url
            }

            results.append(payload)

        # If single employee result and the caller was not HR/Admin, return object instead of list
        if len(results) == 1 and not is_hr_or_admin:
            return Response(SalaryStatementDetailedSerializer(results[0]).data)

        # For admin/HR or multi results, return the list
        return Response(results)
    
    @action(detail=False, methods=['post'])
    def generate_invoice(self, request):
        """Generate invoice for client"""
        serializer = InvoiceGenerationSerializer(data=request.data)
        if serializer.is_valid():
            data = serializer.validated_data
            client_id = data['client_id']
            month = data['month']
            year = data['year']
            
            client = get_object_or_404(Company, id=client_id)
            
            # Get all payslips for the client for the month
            payslips = Payslip.objects.filter(
                employee__sub_company_id=client_id,
                month=month,
                year=year
            )
            
            if not payslips.exists():
                return Response({'error': 'No payslips found for the specified period'}, 
                              status=status.HTTP_400_BAD_REQUEST)
            
            # Calculate totals
            total_gross = payslips.aggregate(total=Sum('gross_salary'))['total'] or 0
            total_deductions = payslips.aggregate(total=Sum('deductions'))['total'] or 0
            
            # Get client settings for service charge
            try:
                client_settings = ClientProfileSettings.objects.get(client_id=client_id)
                if client_settings.service_charge_type == 'FIXED':
                    service_charge = client_settings.service_charge_value
                else:  # PERCENTAGE
                    service_charge = total_gross * (client_settings.service_charge_value / 100)
            except ClientProfileSettings.DoesNotExist:
                service_charge = 0
            
            # Calculate employer contributions
            pf_employer = total_gross * 0.13  # 13% employer contribution
            esi_employer = total_gross * 0.0325 if total_gross <= 25000 else 0  # 3.25%
            
            subtotal = total_gross + pf_employer + esi_employer + service_charge
            gst_amount = subtotal * 0.18  # 18% GST
            total_amount = subtotal + gst_amount
            
            invoice_data = {
                'client_name': client.name,
                'month': month,
                'year': year,
                'total_gross': float(total_gross),
                'pf_employer': float(pf_employer),
                'esi_employer': float(esi_employer),
                'service_charge': float(service_charge),
                'subtotal': float(subtotal),
                'gst_amount': float(gst_amount),
                'total_amount': float(total_amount),
                'payslip_count': payslips.count()
            }
            
            return Response(invoice_data)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ReportsViewSet(viewsets.ViewSet):
    """Reports generation endpoints"""
    permission_classes = [IsAuthenticated, ClientProfilePermission]
    
    @action(detail=False, methods=['post'])
    def statutory_report(self, request):
        """Generate statutory reports (ESI, PF, PT, LWF)"""
        serializer = MonthlyReportSerializer(data=request.data)
        if serializer.is_valid():
            data = serializer.validated_data
            company_id = data['company_id']
            month = data['month']
            year = data['year']
            report_type = data['report_type']
            
            company = get_object_or_404(Company, id=company_id)
            
            # Get employees for the company
            employees = Employee.objects.filter(
                sub_company_id=company_id,
                status='ACTIVE'
            )
            
            # Get payslips for the month
            payslips = Payslip.objects.filter(
                employee__in=employees,
                month=month,
                year=year
            )
            
            report_data = []
            
            if report_type == 'ESI':
                for payslip in payslips:
                    employee = payslip.employee
                    esi_number = getattr(employee.identitydocument, 'esi_number', '') if hasattr(employee, 'identitydocument') else ''
                    esi_employee = payslip.gross_salary * 0.0175 if payslip.gross_salary <= 25000 else 0
                    esi_employer = payslip.gross_salary * 0.0325 if payslip.gross_salary <= 25000 else 0
                    
                    report_data.append({
                        'employee_name': employee.full_name,
                        'esi_number': esi_number,
                        'gross_salary': float(payslip.gross_salary),
                        'esi_employee': float(esi_employee),
                        'esi_employer': float(esi_employer)
                    })
            
            elif report_type == 'PF':
                for payslip in payslips:
                    employee = payslip.employee
                    uan_number = getattr(employee.identitydocument, 'pf_uan_number', '') if hasattr(employee, 'identitydocument') else ''
                    basic_da = employee.salarystructure.basic + employee.salarystructure.da if hasattr(employee, 'salarystructure') else 0
                    pf_employee = basic_da * 0.12
                    pf_employer = basic_da * 0.13
                    
                    report_data.append({
                        'employee_name': employee.full_name,
                        'uan_number': uan_number,
                        'basic_da': float(basic_da),
                        'pf_employee': float(pf_employee),
                        'pf_employer': float(pf_employer)
                    })
            
            # Add similar logic for PT, LWF, INSURANCE reports
            
            return Response({
                'company_name': company.name,
                'month': month,
                'year': year,
                'report_type': report_type,
                'data': report_data,
                'total_records': len(report_data)
            })
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class DocumentViewSet(viewsets.ModelViewSet):
    """Document management endpoints"""
    serializer_class = DocumentSerializer
    permission_classes = [IsAuthenticated, ClientProfilePermission]
    
    def get_queryset(self):
        employee_id = self.request.query_params.get('employee_id')
        doc_type = self.request.query_params.get('doc_type')
        
        queryset = Document.objects.all()
        if employee_id:
            queryset = queryset.filter(employee_id=employee_id)
        if doc_type:
            queryset = queryset.filter(doc_type=doc_type)
            
        return queryset
    
    @action(detail=True, methods=['post'])
    def send_email(self, request, pk=None):
        """Send document via email"""
        document = self.get_object()
        email = request.data.get('email')
        
        if not email:
            return Response({'error': 'Email is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        # This would call an email utility function
        # send_email_with_attachment(email, document.file.path, document.doc_type)
        
        return Response({'message': 'Document sent successfully'})

# Utility API Views
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard_stats(request):
    """Dashboard statistics"""
    client_id = request.query_params.get('client_id')
    
    if not client_id:
        return Response({'error': 'client_id is required'}, status=status.HTTP_400_BAD_REQUEST)
    
    active_employees = Employee.objects.filter(
        sub_company_id=client_id,
        status='ACTIVE'
    ).count()
    
    left_employees = Employee.objects.filter(
        sub_company_id=client_id,
        status='LEFT'
    ).count()
    
    current_month = datetime.now().month
    current_year = datetime.now().year
    
    pending_payslips = Employee.objects.filter(
        sub_company_id=client_id,
        status='ACTIVE'
    ).exclude(
        payslip__month=current_month,
        payslip__year=current_year
    ).count()
    
    stats = {
        'active_employees': active_employees,
        'left_employees': left_employees,
        'pending_payslips': pending_payslips,
        'total_employees': active_employees + left_employees
    }
    
    return Response(stats)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def switch_client_profile(request):
    """Switch to different client profile (admin only)"""
    client_id = request.data.get('client_id')
    
    if not client_id:
        return Response({'error': 'client_id is required'}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        client = Company.objects.get(id=client_id, is_main_company=False)
        
        # Check if user has permission to switch (admin or associated with client)
        has_permission = (
            request.user.is_superuser or
            request.user.groups.filter(name='Admin').exists() or
            Employee.objects.filter(email=request.user.email, sub_company=client).exists()
        )
        
        if not has_permission:
            return Response({
                'error': 'Permission denied',
                'message': 'You do not have access to this client'
            }, status=status.HTTP_403_FORBIDDEN)
        
        try:
            client_settings = ClientProfileSettings.objects.get(client=client)
        except ClientProfileSettings.DoesNotExist:
            client_settings = None
        
        response_data = {
            'client': CompanySerializer(client).data,
            'settings': ClientProfileSettingsSerializer(client_settings).data if client_settings else None
        }
        
        return Response(response_data)
        
    except Company.DoesNotExist:
        return Response({'error': 'Client not found'}, status=status.HTTP_404_NOT_FOUND)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def master_data(request):
    """Get master data for dropdowns"""
    data = {
        'salary_components': SalaryComponentSerializer(
            SalaryComponent.objects.all(), many=True
        ).data,
        'designations': [
            'Unskilled', 'Semiskilled', 'Skilled', 'Helper', 'Loading & Unloading',
            'Housekeeping', 'Housekeeping Supervisor', 'Washroom Cleaner', 'Gardner',
            'Picker & Packer', 'Operator', 'Fitter', 'Electrician', 'Welder',
            'Technician', 'PLC Programmer', 'CNC Operator', 'CNC Programmer'
        ],
        'departments': [
            'Production', 'Maintenance', 'Assembly', 'Quality', 'HR', 'Housekeeping'
        ],
        'gender_choices': [
            {'value': 'M', 'label': 'Male'},
            {'value': 'F', 'label': 'Female'}
        ],
        'marital_status_choices': [
            {'value': 'S', 'label': 'Single'},
            {'value': 'M', 'label': 'Married'}
        ]
    }
    
    return Response(data)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def lock_salary_statement(request):
    """Lock salary statement after approval"""
    month = request.data.get('month')
    year = request.data.get('year')
    client_id = request.data.get('client_id')
    
    if not all([month, year, client_id]):
        return Response({'error': 'month, year, and client_id are required'}, 
                       status=status.HTTP_400_BAD_REQUEST)
    
    # Here you would implement the locking mechanism
    # This could be a separate model or a field in existing models
    
    return Response({'message': 'Salary statement locked successfully'})

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def bulk_document_send(request):
    """Send documents to multiple employees"""
    employee_ids = request.data.get('employee_ids', [])
    doc_type = request.data.get('doc_type')
    send_method = request.data.get('send_method', 'EMAIL')  # EMAIL or WHATSAPP
    
    if not employee_ids or not doc_type:
        return Response({'error': 'employee_ids and doc_type are required'}, 
                       status=status.HTTP_400_BAD_REQUEST)
    
    sent_count = 0
    failed_count = 0
    
    for emp_id in employee_ids:
        try:
            employee = Employee.objects.get(id=emp_id)
            document = Document.objects.filter(
                employee=employee, 
                doc_type=doc_type
            ).first()
            
            if document:
                # Send document logic here
                # send_document_via_email_or_whatsapp(employee, document, send_method)
                sent_count += 1
            else:
                failed_count += 1
                
        except Employee.DoesNotExist:
            failed_count += 1
    
    return Response({
        'message': f'Documents sent: {sent_count}, Failed: {failed_count}',
        'sent_count': sent_count,
        'failed_count': failed_count
    })

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def employee_search(request):
    """Search employees by name or code"""
    query = request.query_params.get('q', '')
    client_id = request.query_params.get('client_id')
    
    if not query:
        return Response({'error': 'Search query is required'}, 
                       status=status.HTTP_400_BAD_REQUEST)
    
    employees = Employee.objects.filter(
        Q(full_name__icontains=query) | Q(employee_code__icontains=query)
    )
    
    if client_id:
        employees = employees.filter(sub_company_id=client_id)
    
    return Response(EmployeeSerializer(employees[:10], many=True).data)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def generate_appointment_order(request):
    """Generate appointment order for employee"""
    employee_id = request.data.get('employee_id')
    template_data = request.data.get('template_data', {})
    
    if not employee_id:
        return Response({'error': 'employee_id is required'}, 
                       status=status.HTTP_400_BAD_REQUEST)
    
    try:
        employee = Employee.objects.get(id=employee_id)
        # Generate appointment order PDF
        # pdf_path = generate_appointment_order_pdf(employee, template_data)
        
        # Save as document
        document = Document.objects.create(
            employee=employee,
            doc_type='APPOINTMENT',
            # file=pdf_path,
            issued_date=date.today()
        )
        
        return Response(DocumentSerializer(document).data)
        
    except Employee.DoesNotExist:
        return Response({'error': 'Employee not found'}, 
                       status=status.HTTP_404_NOT_FOUND)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def attendance_template(request):
    """Download attendance template for bulk upload"""
    client_id = request.query_params.get('client_id')
    month = request.query_params.get('month')
    year = request.query_params.get('year')
    
    if not all([client_id, month, year]):
        return Response({'error': 'client_id, month, and year are required'}, 
                       status=status.HTTP_400_BAD_REQUEST)
    
    employees = Employee.objects.filter(
        sub_company_id=client_id,
        status='ACTIVE'
    )
    
    # Generate attendance template with employee list
    template_data = []
    days_in_month = calendar.monthrange(int(year), int(month))[1]
    
    for employee in employees:
        row = {
            'employee_id': employee.id,
            'employee_code': employee.employee_code,
            'employee_name': employee.full_name,
            'department': getattr(employee.officialdetails, 'department', '') if hasattr(employee, 'officialdetails') else '',
            'designation': getattr(employee.officialdetails, 'designation', '') if hasattr(employee, 'officialdetails') else ''
        }
        
        # Add day columns
        for day in range(1, days_in_month + 1):
            row[f'day_{day}'] = 'P'  # Default to Present
        
        row['overtime_hours'] = 0
        template_data.append(row)
    
    return Response({
        'template_data': template_data,
        'headers': list(template_data[0].keys()) if template_data else [],
        'total_employees': len(template_data)
    })

# Supervisor specific views
class SupervisorViewSet(viewsets.ViewSet):
    """Supervisor specific endpoints"""
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['get'])
    def assigned_employees(self, request):
        """Get employees assigned to supervisor"""
        supervisor_name = request.user.get_full_name() or request.user.username
        
        employees = Employee.objects.filter(
            officialdetails__supervisor_name=supervisor_name,
            status='ACTIVE'
        )
        
        return Response(EmployeeSerializer(employees, many=True).data)
    
    @action(detail=False, methods=['post'])
    def submit_attendance(self, request):
        """Submit attendance for approval"""
        # Supervisor submits attendance for HR approval
        month = request.data.get('month')
        year = request.data.get('year')
        client_id = request.data.get('client_id')
        attendance_data = request.data.get('attendance_data', [])
        
        # Process and save attendance
        for record in attendance_data:
            Attendance.objects.update_or_create(
                employee_id=record['employee_id'],
                date=record['date'],
                defaults={'status': record['status']}
            )
        
        # Create approval request (this would be another model)
        return Response({'message': 'Attendance submitted for approval'})

# HR specific views  
class HRViewSet(viewsets.ViewSet):
    """HR specific endpoints"""
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['get'])
    def pending_approvals(self, request):
        """Get pending approvals"""
        # This would return attendance submissions, employee changes etc. pending approval
        return Response({'pending_approvals': []})
    
    @action(detail=False, methods=['post'])
    def approve_attendance(self, request):
        """Approve attendance submitted by supervisor"""
        # Approve attendance and make it final
        return Response({'message': 'Attendance approved'})

# Admin specific views
class AdminViewSet(viewsets.ViewSet):
    """Admin specific endpoints"""
    permission_classes = [IsAuthenticated]  # Add admin permission check
    
    @action(detail=False, methods=['get'])
    def activity_log(self, request):
        """Get system activity log"""
        # Return activity log for past 6 months
        return Response({'activity_log': []})
    
    @action(detail=False, methods=['post'])
    def unlock_statement(self, request):
        """Unlock locked salary statement"""
        # Only admin can unlock locked statements
        return Response({'message': 'Statement unlocked'})

# File download views
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def download_payslip(request, payslip_id):
    """Download payslip PDF"""
    try:
        payslip = Payslip.objects.get(id=payslip_id)
        
        if payslip.pdf_file:
            response = HttpResponse(
                payslip.pdf_file.read(),
                content_type='application/pdf'
            )
            response['Content-Disposition'] = f'attachment; filename="payslip_{payslip.employee.employee_code}_{payslip.month}_{payslip.year}.pdf"'
            return response
        else:
            return Response({'error': 'PDF file not found'}, 
                           status=status.HTTP_404_NOT_FOUND)
            
    except Payslip.DoesNotExist:
        return Response({'error': 'Payslip not found'}, 
                       status=status.HTTP_404_NOT_FOUND)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def export_report(request):
    """Export various reports in Excel/PDF format"""
    report_type = request.query_params.get('report_type')
    format_type = request.query_params.get('format', 'excel')
    client_id = request.query_params.get('client_id')
    month = request.query_params.get('month')
    year = request.query_params.get('year')
    
    # Generate and return the requested report
    # This would call appropriate utility functions
    
    return Response({'message': 'Report generated successfully'})



# simple_admin_setup.py - Updated for your specific models
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.contrib.auth.models import User, Group
from django.db import transaction
from .models import (
    Company, Employee, SalaryComponent, ClientProfileSettings,
    OfficialDetails, IdentityDocument, BankDetails, SalaryStructure
)
from .serializers import CompanySerializer, EmployeeSerializer
import secrets
import string

@api_view(['GET'])
@permission_classes([AllowAny])
def check_system_status(request):
    """Check if system is initialized with detailed status"""
    try:
        is_initialized = User.objects.filter(is_superuser=True).exists()
        
        return Response({
            'is_initialized': is_initialized,
            'system_info': {
                'total_users': User.objects.count(),
                'superusers': User.objects.filter(is_superuser=True).count(),
                'total_companies': Company.objects.count(),
                'main_companies': Company.objects.filter(is_main_company=True).count(),
                'client_companies': Company.objects.filter(is_main_company=False).count(),
                'total_employees': Employee.objects.count(),
                'groups_created': Group.objects.count(),
                'salary_components': SalaryComponent.objects.count() if 'SalaryComponent' in globals() else 0
            }
        })
    except Exception as e:
        logger.error(f"System status check error: {str(e)}")
        return Response({
            'error': 'System status check failed',
            'details': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
@api_view(['POST'])
@permission_classes([AllowAny])
def create_admin_setup(request):
    """Create complete admin setup with Sub-Manager role support"""
    
    try:
        # Check if already initialized
        if User.objects.filter(is_superuser=True).exists():
            return Response({
                'error': 'System already initialized',
                'message': 'Admin user already exists.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Validate required fields
        required_fields = ['username', 'email', 'password']
        missing_fields = []
        for field in required_fields:
            if not request.data.get(field):
                missing_fields.append(field)
        
        if missing_fields:
            return Response({
                'error': 'Missing required fields',
                'missing_fields': missing_fields
            }, status=status.HTTP_400_BAD_REQUEST)
        
        admin_data = request.data
        
        # Validate username uniqueness
        if User.objects.filter(username=admin_data['username']).exists():
            return Response({
                'error': 'Username already exists',
                'message': 'Please choose a different username'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Validate email uniqueness
        if User.objects.filter(email=admin_data['email']).exists():
            return Response({
                'error': 'Email already exists',
                'message': 'Please choose a different email'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        with transaction.atomic():
            logger.info(f"Starting admin setup for username: {admin_data['username']}")
            
            # 1. Create Django admin user
            admin_user = User.objects.create_superuser(
                username=admin_data['username'],
                email=admin_data['email'],
                password=admin_data['password'],
                first_name=admin_data.get('first_name', 'System'),
                last_name=admin_data.get('last_name', 'Administrator')
            )
            logger.info(f"Created admin user: {admin_user.username}")
            
            # 2. Create user groups INCLUDING Sub-Manager
            groups_created = []
            for group_name in ['Admin', 'Manager', 'Sub-Manager', 'HR', 'Supervisor', 'Employee']:
                group, created = Group.objects.get_or_create(name=group_name)
                if created:
                    groups_created.append(group_name)
                    logger.info(f"Created group: {group_name}")
            
            # Assign admin to Admin group
            admin_group = Group.objects.get(name='Admin')
            admin_user.groups.add(admin_group)
            
            # 3. Create main companies (same as before)
            main_companies_data = [
                {
                    'name': 'RMS (RADIANT Manpower Services)',
                    'address': 'No 10, 1st Floor 100ft Outer Ring Road, 2nd Phase, Banashankari 3rd Stage Hosakerehalli, Bangaluru Urban, Karnataka, 560085',
                    'gst_number': '29AAGCI9587F1ZW',
                    'is_main_company': True
                },
                {
                    'name': 'IMS (InLine Manpower Services Pvt Ltd)',
                    'address': 'No 10, 1st Floor 100ft Outer Ring Road, 2nd Phase, Banashankari 3rd Stage Hosakerehalli, Bangaluru Urban, Karnataka, 560085',
                    'gst_number': '29AAGCI9587F1ZX',
                    'is_main_company': True
                },
                {
                    'name': 'KVS Manpower Solutions',
                    'address': 'No 10, 1st Floor 100ft Outer Ring Road, 2nd Phase, Banashankari 3rd Stage Hosakerehalli, Bangaluru Urban, Karnataka, 560085',
                    'gst_number': '29AAGCI9587F1ZY',
                    'is_main_company': True
                }
            ]
            
            companies_created = []
            for company_data in main_companies_data:
                try:
                    company = Company.objects.create(**company_data)
                    companies_created.append({
                        'id': company.id,
                        'name': company.name,
                        'gst_number': company.gst_number
                    })
                    logger.info(f"Created company: {company.name}")
                except Exception as e:
                    logger.error(f"Error creating company {company_data['name']}: {str(e)}")
            
            # 4. Create admin employee record
            admin_employee = None
            if companies_created:
                main_company = Company.objects.filter(is_main_company=True).first()
                if main_company:
                    try:
                        admin_employee = Employee.objects.create(
                            full_name=f"{admin_user.first_name} {admin_user.last_name}",
                            employee_code=admin_data.get('employee_code', 'ADMIN001'),
                            date_of_birth=admin_data.get('date_of_birth', '1990-01-01'),
                            gender=admin_data.get('gender', 'M'),
                            marital_status=admin_data.get('marital_status', 'S'),
                            mobile_number=admin_data.get('mobile_number', '9876543210'),
                            email=admin_user.email,
                            current_address=admin_data.get('current_address', 'Admin Office'),
                            permanent_address=admin_data.get('permanent_address', 'Admin Office'),
                            role='Admin',  # Admin role for setup user
                            main_company=main_company,
                            status='ACTIVE'
                        )
                        logger.info(f"Created admin employee: {admin_employee.employee_code}")
                    except Exception as e:
                        logger.error(f"Error creating admin employee: {str(e)}")
            
            # 5. Create salary components
            salary_components_created = []
            try:
                salary_components_created = create_default_salary_components()
                logger.info(f"Created {len(salary_components_created)} salary components")
            except Exception as e:
                logger.error(f"Error creating salary components: {str(e)}")
            
            response_data = {
                'success': True,
                'message': 'Admin setup completed successfully',
                'data': {
                    'admin_user': {
                        'id': admin_user.id,
                        'username': admin_user.username,
                        'email': admin_user.email,
                        'first_name': admin_user.first_name,
                        'last_name': admin_user.last_name,
                        'is_superuser': admin_user.is_superuser
                    },
                    'admin_employee': {
                        'id': admin_employee.id if admin_employee else None,
                        'employee_code': admin_employee.employee_code if admin_employee else None,
                        'full_name': admin_employee.full_name if admin_employee else None,
                        'role': admin_employee.role if admin_employee else None
                    } if admin_employee else None,
                    'groups_created': groups_created,
                    'companies_created': companies_created,
                    'salary_components_created': len(salary_components_created),
                    'roles_available': ['Admin', 'Manager', 'Sub-Manager', 'HR', 'Supervisor', 'Employee']
                }
            }
            
            logger.info("Admin setup completed successfully")
            return Response(response_data, status=status.HTTP_201_CREATED)
            
    except Exception as e:
        logger.error(f"Admin setup failed: {str(e)}")
        return Response({
            'error': 'Setup failed',
            'message': str(e),
            'type': type(e).__name__
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
@api_view(['POST'])
@permission_classes([AllowAny])
def quick_admin_setup(request):
    """Quick setup with auto-generated credentials"""
    
    try:
        if User.objects.filter(is_superuser=True).exists():
            return Response({
                'error': 'System already initialized',
                'message': 'Admin user already exists'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Auto-generate credentials
        username = 'admin'
        password = generate_secure_password()
        email = request.data.get('email', 'admin@example.com')
        
        # Check if username exists
        counter = 1
        original_username = username
        while User.objects.filter(username=username).exists():
            username = f"{original_username}{counter}"
            counter += 1
        
        with transaction.atomic():
            logger.info(f"Starting quick admin setup with username: {username}")
            
            # Create admin user
            admin_user = User.objects.create_superuser(
                username=username,
                email=email,
                password=password,
                first_name='System',
                last_name='Administrator'
            )
            
            # Create basic groups INCLUDING Sub-Manager
            groups_created = []
            for group_name in ['Admin', 'Manager', 'Sub-Manager', 'HR', 'Supervisor']:
                group, created = Group.objects.get_or_create(name=group_name)
                if created:
                    groups_created.append(group_name)
            
            admin_user.groups.add(Group.objects.get(name='Admin'))
            
            # Create RMS company (main)
            rms_company = None
            try:
                rms_company = Company.objects.create(
                    name='RMS (RADIANT Manpower Services)',
                    address='Bangalore, Karnataka, India',
                    gst_number='29AAGCI9587F1ZW',
                    is_main_company=True
                )
                logger.info(f"Created main company: {rms_company.name}")
            except Exception as e:
                logger.error(f"Error creating company: {str(e)}")
            
            # Create admin employee
            admin_employee = None
            if rms_company:
                try:
                    admin_employee = Employee.objects.create(
                        full_name='System Administrator',
                        employee_code='ADMIN001',
                        date_of_birth='1990-01-01',
                        gender='M',
                        marital_status='S',
                        mobile_number='9876543210',
                        email=email,
                        current_address='Admin Office',
                        permanent_address='Admin Office',
                        role='Admin',  # Admin role
                        main_company=rms_company,
                        status='ACTIVE'
                    )
                except Exception as e:
                    logger.error(f"Error creating admin employee: {str(e)}")
            
            # Create basic salary components
            components_created = []
            try:
                components_created = create_basic_salary_components()
            except Exception as e:
                logger.error(f"Error creating salary components: {str(e)}")
            
            response_data = {
                'success': True,
                'message': 'Quick setup completed successfully',
                'credentials': {
                    'username': username,
                    'password': password,
                    'email': email
                },
                'warning': 'SAVE THESE CREDENTIALS IMMEDIATELY - THEY WILL NOT BE SHOWN AGAIN',
                'data': {
                    'admin_employee': {
                        'id': admin_employee.id if admin_employee else None,
                        'employee_code': admin_employee.employee_code if admin_employee else None,
                        'full_name': admin_employee.full_name if admin_employee else None,
                        'role': admin_employee.role if admin_employee else None
                    } if admin_employee else None,
                    'company': {
                        'id': rms_company.id if rms_company else None,
                        'name': rms_company.name if rms_company else None
                    } if rms_company else None,
                    'groups_created': groups_created,
                    'components_created': len(components_created),
                    'roles_available': ['Admin', 'Manager', 'Sub-Manager', 'HR', 'Supervisor', 'Employee']
                }
            }
            
            logger.info("Quick admin setup completed successfully")
            return Response(response_data, status=status.HTTP_201_CREATED)
            
    except Exception as e:
        logger.error(f"Quick setup failed: {str(e)}")
        return Response({
            'error': 'Quick setup failed',
            'message': str(e),
            'type': type(e).__name__
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([AllowAny])
def create_sample_data(request):
    """Create sample client companies and data"""
    
    if not User.objects.filter(is_superuser=True).exists():
        return Response({
            'error': 'System not initialized',
            'message': 'Create admin first'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        with transaction.atomic():
            # Create sample client companies
            sample_clients = [
                {
                    'name': 'Brand Studio Lifestyle Pvt Ltd',
                    'address': 'Bangalore, Karnataka',
                    'gst_number': '29AAACO8088P1ZH',
                    'is_main_company': False
                },
                {
                    'name': 'Online Instruments India Pvt Ltd',
                    'address': 'Plot No 11, Lakshmanapura Village, Thyamagondlu Hobli Nelamangala Taluk, Bangalore Rural - 562 123',
                    'gst_number': '29AAACO8088P1ZI',
                    'is_main_company': False
                },
                {
                    'name': 'TVS Electronics Ltd',
                    'address': 'Bangalore, Karnataka',
                    'gst_number': '29AAACO8088P1ZJ',
                    'is_main_company': False
                },
                {
                    'name': 'Incap Contract Manufacturing Pvt Ltd',
                    'address': 'Bangalore, Karnataka',
                    'gst_number': '29AAACO8088P1ZK',
                    'is_main_company': False
                }
            ]
            
            clients_created = []
            for client_data in sample_clients:
                client = Company.objects.create(**client_data)
                clients_created.append({
                    'id': client.id,
                    'name': client.name
                })
                
                # Create basic client profile settings
                ClientProfileSettings.objects.create(
                    client=client,
                    esi_applicable=True,
                    pf_applicable=True,
                    pt_applicable=True,
                    lwf_applicable=False,
                    advance_applicable=True,
                    insurance_applicable=True,
                    service_charge_type='PERCENTAGE',
                    service_charge_value=6.0
                )
            
            # Create sample HR employee
            hr_employee = Employee.objects.create(
                full_name='HR Manager',
                employee_code='HR001',
                date_of_birth='1985-06-15',
                gender='F',
                marital_status='M',
                mobile_number='9876543211',
                email='hr@example.com',
                current_address='HR Office',
                permanent_address='HR Office',
                role='HR',
                main_company=Company.objects.filter(is_main_company=True).first(),
                status='ACTIVE'
            )
            
            # Create HR user account
            hr_user = User.objects.create_user(
                username='hr_user',
                email='hr@example.com',
                password='hr123456',
                first_name='HR',
                last_name='Manager'
            )
            
            hr_group, _ = Group.objects.get_or_create(name='HR')
            hr_user.groups.add(hr_group)
            
            return Response({
                'message': 'Sample data created successfully',
                'data': {
                    'clients_created': clients_created,
                    'hr_employee': {
                        'id': hr_employee.id,
                        'employee_code': hr_employee.employee_code,
                        'full_name': hr_employee.full_name
                    },
                    'hr_user_credentials': {
                        'username': 'hr_user',
                        'password': 'hr123456',
                        'email': 'hr@example.com'
                    }
                }
            }, status=status.HTTP_201_CREATED)
            
    except Exception as e:
        return Response({
            'error': 'Sample data creation failed',
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

def generate_secure_password(length=12):
    """Generate secure random password"""
    characters = string.ascii_letters + string.digits + "!@#$%^&*"
    password = ''.join(secrets.choice(characters) for _ in range(length))
    return password

def create_default_salary_components():
    """Create all salary components as per your requirements"""
    if 'SalaryComponent' not in globals():
        return []
        
    components_data = [
        # Earnings
        {'name': 'Basic & DA', 'is_earning': True},
        {'name': 'HRA', 'is_earning': True}, 
        {'name': 'Special Allowance', 'is_earning': True},
        {'name': 'Leave With Wages', 'is_earning': True},
        {'name': 'Bonus', 'is_earning': True},
        {'name': 'Night Shift Allowance', 'is_earning': True},
        {'name': 'Shift Allowance', 'is_earning': True},
        {'name': 'Transportation Allowance', 'is_earning': True},
        {'name': 'Arrears', 'is_earning': True},
        {'name': 'Other Allowances', 'is_earning': True},
        
        # Deductions
        {'name': 'ESI', 'is_earning': False},
        {'name': 'PF', 'is_earning': False},
        {'name': 'PT', 'is_earning': False},
        {'name': 'LWF', 'is_earning': False},
        {'name': 'Canteen', 'is_earning': False},
        {'name': 'Transportation', 'is_earning': False},
        {'name': 'Advance', 'is_earning': False},
        {'name': 'Insurance', 'is_earning': False},
        {'name': 'Other Deduction', 'is_earning': False}
    ]

    components = []
    for comp_data in components_data:
        try:
            component, created = SalaryComponent.objects.get_or_create(**comp_data)
            if created:
                components.append(component)
        except Exception as e:
            logger.error(f"Error creating salary component {comp_data['name']}: {str(e)}")

    return components
    
    from hrms.contrib.auth import get_user_model


def create_basic_salary_components():
    """Create basic salary components if SalaryComponent model doesn't exist"""
    try:
        if 'SalaryComponent' in globals():
            basic_components = [
                {'name': 'Basic & DA', 'is_earning': True},
                {'name': 'HRA', 'is_earning': True},
                {'name': 'Special Allowance', 'is_earning': True},
                {'name': 'ESI', 'is_earning': False},
                {'name': 'PF', 'is_earning': False},
                {'name': 'PT', 'is_earning': False}
            ]
            
            components = []
            for comp_data in basic_components:
                component, created = SalaryComponent.objects.get_or_create(**comp_data)
                if created:
                    components.append(component)
            return components
    except Exception as e:
        logger.error(f"Error creating basic salary components: {str(e)}")
    
    return []


@api_view(['GET'])
@permission_classes([AllowAny])
def test_setup(request):
    """Test endpoint to verify models and setup"""
    try:
        models_status = {}
        
        # Check each model
        model_names = ['User', 'Group', 'Company', 'Employee', 'SalaryComponent']
        
        for model_name in model_names:
            try:
                if model_name == 'User':
                    count = User.objects.count()
                elif model_name == 'Group':
                    count = Group.objects.count()
                elif model_name in globals():
                    model_class = globals()[model_name]
                    count = model_class.objects.count()
                else:
                    count = None
                    
                models_status[model_name] = {
                    'exists': model_name in globals() or model_name in ['User', 'Group'],
                    'count': count
                }
            except Exception as e:
                models_status[model_name] = {
                    'exists': False,
                    'error': str(e)
                }
        
        return Response({
            'models_status': models_status,
            'system_ready': User.objects.filter(is_superuser=True).exists()
        })
        
    except Exception as e:
        return Response({
            'error': 'Test failed',
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

User = get_user_model()





from rest_framework.decorators import api_view, permission_classes

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_main_companies(request):
    """Get all main companies for dropdown"""
    main_companies = Company.objects.filter(is_main_company=True)
    serializer = CompanySerializer(main_companies, many=True)
    return Response({
        'main_companies': serializer.data
    })


@api_view(['POST'])
@permission_classes([IsAdminOrManager])
def transfer_company(request):
    """Transfer a sub-company to different main company"""
    try:
        sub_company_id = request.data.get('sub_company_id')
        new_parent_id = request.data.get('new_parent_company_id')
        
        if not sub_company_id or not new_parent_id:
            return Response({
                'error': 'sub_company_id and new_parent_company_id are required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        sub_company = Company.objects.get(
            id=sub_company_id,
            is_main_company=False
        )
        
        new_parent = Company.objects.get(
            id=new_parent_id,
            is_main_company=True
        )
        
        old_parent = sub_company.parent_company
        sub_company.parent_company = new_parent
        sub_company.save()
        
        return Response({
            'success': True,
            'message': f'Company transferred successfully',
            'data': {
                'sub_company': CompanySerializer(sub_company).data,
                'old_parent': CompanySerializer(old_parent).data if old_parent else None,
                'new_parent': CompanySerializer(new_parent).data
            }
        })
        
    except Company.DoesNotExist:
        return Response({
            'error': 'Company not found'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({
            'error': 'Transfer failed',
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)




# Add this to your views.py

from rest_framework.exceptions import PermissionDenied, ValidationError

class CanCreateEmployeePermission(permissions.BasePermission):
    """
    Permission to check if user can create employees based on their role
    """
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        # Superusers can do anything
        if request.user.is_superuser:
            return True
        
        # Check user's role via employee record
        try:
            employee = Employee.objects.get(email=request.user.email)
            # These roles can create employees
            return employee.role in ['Admin', 'Manager', 'Sub-Manager', 'HR', 'Supervisor']
        except Employee.DoesNotExist:
            return False

@api_view(['POST'])
@permission_classes([IsAuthenticated, CanCreateEmployeePermission])
def create_employee_for_subcompany(request):
    """
    Create employee for a sub-company with role-based restrictions
    
    Role-based creation rules:
    - Admin: Can create any role for any company
    - Manager (Main Company): Can create HR, Supervisor, Employee for any sub-company under their main company
    - Sub-Manager: Can create HR, Supervisor, Employee for their own sub-company
    - HR: Can create Supervisor, Employee for their own sub-company
    - Supervisor: Can create Employee for their own sub-company
    """
    try:
        # Get logged-in user's employee record
        try:
            user_employee = Employee.objects.select_related(
                'main_company', 
                'sub_company'
            ).get(email=request.user.email)
        except Employee.DoesNotExist:
            return Response({
                'error': 'No employee record found for user'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Get request data
        sub_company_id = request.data.get('sub_company_id')
        employee_data = request.data.get('employee_data', {})
        new_employee_role = employee_data.get('role')
        
        # Validate required fields
        if not sub_company_id:
            return Response({
                'error': 'sub_company_id is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if not new_employee_role:
            return Response({
                'error': 'role is required in employee_data'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get target sub-company
        try:
            target_sub_company = Company.objects.select_related('parent_company').get(
                id=sub_company_id,
                is_main_company=False
            )
        except Company.DoesNotExist:
            return Response({
                'error': 'Invalid sub_company_id or company is not a sub-company'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Role-based authorization and validation
        user_role = user_employee.role
        
        # Define what roles each user can create
        role_creation_permissions = {
            'Admin': ['Manager', 'Sub-Manager', 'HR', 'Supervisor', 'Employee'],
            'Manager': ['HR', 'Supervisor', 'Employee'],
            'Sub-Manager': ['HR', 'Supervisor', 'Employee'],
            'HR': ['Supervisor', 'Employee'],
            'Supervisor': ['Employee']
        }
        
        # Check if user can create this role
        allowed_roles = role_creation_permissions.get(user_role, [])
        if new_employee_role not in allowed_roles:
            return Response({
                'error': 'Permission denied',
                'message': f'{user_role} cannot create {new_employee_role} role',
                'allowed_roles': allowed_roles
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Check if user has access to target sub-company
        if user_role == 'Admin':
            # Admin can create for any sub-company
            pass
        elif user_role == 'Manager' and user_employee.main_company:
            # Manager can create for any sub-company under their main company
            if target_sub_company.parent_company != user_employee.main_company:
                return Response({
                    'error': 'Permission denied',
                    'message': 'You can only create employees for sub-companies under your main company'
                }, status=status.HTTP_403_FORBIDDEN)
        elif user_role in ['Sub-Manager', 'HR', 'Supervisor']:
            # These roles can only create for their own sub-company
            if user_employee.sub_company != target_sub_company:
                return Response({
                    'error': 'Permission denied',
                    'message': 'You can only create employees for your own sub-company'
                }, status=status.HTTP_403_FORBIDDEN)
        
        # Prepare employee data
        employee_data['sub_company'] = target_sub_company.id
        employee_data['main_company'] = None  # Sub-company employees don't have main_company
        employee_data['status'] = 'ACTIVE'
        
        # Generate employee code if not provided
        if not employee_data.get('employee_code'):
            # Generate unique employee code
            last_emp = Employee.objects.filter(
                sub_company=target_sub_company
            ).order_by('-id').first()
            
            if last_emp and last_emp.employee_code:
                try:
                    last_num = int(last_emp.employee_code.split('_')[-1])
                    new_num = last_num + 1
                except:
                    new_num = 1
            else:
                new_num = 1
            
            employee_data['employee_code'] = f"EMP_{target_sub_company.id}_{new_num:04d}"
        
        # Create employee using serializer
        serializer = EmployeeCreateSerializer(data=employee_data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        # Save employee
        new_employee = serializer.save()
        
        # Optionally create user account if email and password provided
        user_account_data = None
        if employee_data.get('create_user_account') and employee_data.get('password'):
            try:
                user_account = _create_user_account_for_employee(
                    new_employee,
                    employee_data.get('password'),
                    new_employee_role
                )
                user_account_data = {
                    'username': user_account.username,
                    'email': user_account.email,
                    'role': new_employee_role
                }
            except Exception as e:
                # Employee created but user account failed
                return Response({
                    'success': True,
                    'message': 'Employee created but user account creation failed',
                    'employee': EmployeeSerializer(new_employee).data,
                    'user_account_error': str(e)
                }, status=status.HTTP_201_CREATED)
        
        response_data = {
            'success': True,
            'message': 'Employee created successfully',
            'employee': EmployeeSerializer(new_employee).data,
            'sub_company': CompanySerializer(target_sub_company).data
        }
        # --- Auto-assign supervisor when there is exactly one active supervisor for the sub-company ---
        try:
            # Supervisors considered if role='Supervisor' and active, and either explicitly supervise the company
            # via supervised_companies M2M or are assigned to the same sub_company
            supervisors_qs = Employee.objects.filter(
                role='Supervisor',
                status='ACTIVE'
            ).filter(
                Q(supervised_companies=target_sub_company) | Q(sub_company=target_sub_company)
            ).distinct()

            if supervisors_qs.count() == 1:
                sup = supervisors_qs.first()
                # Create or update OfficialDetails for the new employee to set supervisor_name
                # Use defaults for required OfficialDetails fields if not provided in payload
                official_payload = request.data.get('employee_data', {}).get('official_details', {}) or {}
                od_defaults = {
                    'date_of_joining': official_payload.get('date_of_joining', timezone.now().date()),
                    'department': official_payload.get('department', 'Unassigned'),
                    'designation': official_payload.get('designation', 'Employee'),
                    'location': official_payload.get('location', 'N/A'),
                    'supervisor_name': sup.full_name,
                    'salary_type': official_payload.get('salary_type', 'MONTHLY')
                }

                from .models import OfficialDetails
                OfficialDetails.objects.update_or_create(employee=new_employee, defaults=od_defaults)

                # Include info in response
                response_data['auto_assigned_supervisor'] = {
                    'id': sup.id,
                    'employee_code': sup.employee_code,
                    'full_name': sup.full_name
                }
        except Exception:
            # Non-fatal: don't block employee creation if auto-assign fails
            pass
        
        if user_account_data:
            response_data['user_account'] = user_account_data
        
        return Response(response_data, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        logger.error(f"Employee creation error: {str(e)}")
        return Response({
            'error': 'Employee creation failed',
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


def _create_user_account_for_employee(employee, password, role):
    """Helper function to create user account for employee"""
    from django.contrib.auth import get_user_model
    from django.contrib.auth.models import Group
    
    User = get_user_model()
    
    # Check if user already exists
    if User.objects.filter(email=employee.email).exists():
        raise ValidationError(f"User account with email {employee.email} already exists")
    
    # Generate username from email
    username = employee.email.split('@')[0]
    if User.objects.filter(username=username).exists():
        # Add number suffix if username exists
        counter = 1
        original_username = username
        while User.objects.filter(username=username).exists():
            username = f"{original_username}_{counter}"
            counter += 1
    
    # Create user
    user = User.objects.create_user(
        username=username,
        email=employee.email,
        password=password,
        first_name=employee.full_name.split()[0] if ' ' in employee.full_name else employee.full_name,
        last_name=' '.join(employee.full_name.split()[1:]) if ' ' in employee.full_name else '',
        is_active=True
    )
    
    # Assign to appropriate group based on role
    group_mapping = {
        'Manager': 'Manager',
        'Sub-Manager': 'Sub-Manager',
        'HR': 'HR',
        'Supervisor': 'Supervisor',
        'Employee': 'Employee'
    }
    
    group_name = group_mapping.get(role, 'Employee')
    group, _ = Group.objects.get_or_create(name=group_name)
    user.groups.add(group)
    
    return user


@api_view(['POST'])
@permission_classes([IsAuthenticated, CanCreateEmployeePermission])
def assign_supervisor(request):
    """
    Assign or change the supervisor for an employee.

    Request body:
    {
        "employee_id": 123,
        "supervisor_id": 456,
        // optional official details fields to keep required fields satisfied
        "official_details": {
            "date_of_joining": "2025-10-01",
            "department": "Sales",
            "designation": "Executive",
            "location": "City",
            "salary_type": "MONTHLY"
        }
    }
    """
    try:
        emp_id = request.data.get('employee_id')
        sup_id = request.data.get('supervisor_id')

        if not emp_id or not sup_id:
            return Response({'error': 'employee_id and supervisor_id are required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            emp = Employee.objects.get(id=emp_id)
            sup = Employee.objects.get(id=sup_id, role='Supervisor')
        except Employee.DoesNotExist:
            return Response({'error': 'Employee or Supervisor not found'}, status=status.HTTP_404_NOT_FOUND)

        official_payload = request.data.get('official_details', {}) or {}
        od_defaults = {
            'date_of_joining': official_payload.get('date_of_joining', timezone.now().date()),
            'department': official_payload.get('department', getattr(emp.officialdetails, 'department', 'Unassigned') if hasattr(emp, 'officialdetails') else 'Unassigned'),
            'designation': official_payload.get('designation', getattr(emp.officialdetails, 'designation', 'Employee') if hasattr(emp, 'officialdetails') else 'Employee'),
            'location': official_payload.get('location', getattr(emp.officialdetails, 'location', 'N/A') if hasattr(emp, 'officialdetails') else 'N/A'),
            'supervisor_name': sup.full_name,
            'salary_type': official_payload.get('salary_type', getattr(emp.officialdetails, 'salary_type', 'MONTHLY') if hasattr(emp, 'officialdetails') else 'MONTHLY')
        }

        OfficialDetails.objects.update_or_create(employee=emp, defaults=od_defaults)

        return Response({'success': True, 'message': 'Supervisor assigned'}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated, CanCreateEmployeePermission])
def manage_supervisor_companies(request):
    """
    Add or remove a sub-company to/from a supervisor's `supervised_companies` M2M.

    Request body:
    {
        "supervisor_id": 456,
        "company_id": 27,
        "action": "add"   # or "remove" (defaults to add)
    }

    Only users with CanCreateEmployeePermission (Admin/Manager/Sub-Manager/HR/Supervisor) can call.
    """
    try:
        supervisor_id = request.data.get('supervisor_id')
        company_id = request.data.get('company_id')
        action = (request.data.get('action') or 'add').lower()

        if not supervisor_id or not company_id:
            return Response({'error': 'supervisor_id and company_id are required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            supervisor = Employee.objects.get(id=supervisor_id, role='Supervisor')
        except Employee.DoesNotExist:
            return Response({'error': 'Supervisor not found'}, status=status.HTTP_404_NOT_FOUND)

        try:
            company = Company.objects.get(id=company_id)
        except Company.DoesNotExist:
            return Response({'error': 'Company not found'}, status=status.HTTP_404_NOT_FOUND)

        if action == 'add':
            supervisor.supervised_companies.add(company)
            msg = 'Company added to supervisor'
        elif action == 'remove':
            supervisor.supervised_companies.remove(company)
            msg = 'Company removed from supervisor'
        else:
            return Response({'error': 'Invalid action. Use "add" or "remove".'}, status=status.HTTP_400_BAD_REQUEST)

        # Return updated list of supervised companies
        companies = supervisor.supervised_companies.all()
        companies_data = [CompanySerializer(c).data for c in companies]

        return Response({'success': True, 'message': msg, 'supervised_companies': companies_data}, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_accessible_subcompanies(request):
    """
    Get sub-companies accessible to the logged-in user
    
    - Admin: All sub-companies
    - Manager (Main): All sub-companies under their main company
    - Sub-Manager/HR/Supervisor/Employee: Only their own sub-company
    """
    try:
        user_employee = Employee.objects.select_related(
            'main_company',
            'sub_company',
            'sub_company__parent_company'
        ).get(email=request.user.email)
        
        user_role = user_employee.role
        
        if user_role == 'Admin':
            # Admin sees all sub-companies
            sub_companies = Company.objects.filter(is_main_company=False)
        elif user_role == 'Manager' and user_employee.main_company:
            # Manager sees sub-companies under their main company
            sub_companies = Company.objects.filter(
                parent_company=user_employee.main_company,
                is_main_company=False
            )
        elif user_employee.sub_company:
            # Sub-Manager, HR, Supervisor, Employee see only their sub-company
            sub_companies = Company.objects.filter(id=user_employee.sub_company.id)
        else:
            sub_companies = Company.objects.none()
        
        serializer = CompanySerializer(sub_companies, many=True)
        
        return Response({
            'user_role': user_role,
            'sub_companies': serializer.data,
            'count': sub_companies.count()
        })
        
    except Employee.DoesNotExist:
        return Response({
            'error': 'No employee record found'
        }, status=status.HTTP_404_NOT_FOUND)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_employees_by_subcompany(request):
    """
    Get employees for sub-companies accessible to user
    Filters based on user's role and permissions
    """
    try:
        user_employee = Employee.objects.select_related(
            'main_company',
            'sub_company'
        ).get(email=request.user.email)
        
        sub_company_id = request.query_params.get('sub_company_id')
        status_filter = request.query_params.get('status', 'ACTIVE')
        
        # Determine which sub-companies user can access
        if user_employee.role == 'Admin':
            # Admin can access any sub-company
            if sub_company_id:
                employees = Employee.objects.filter(
                    sub_company_id=sub_company_id,
                    status=status_filter
                )
            else:
                employees = Employee.objects.filter(
                    sub_company__isnull=False,
                    status=status_filter
                )
        elif user_employee.role == 'Manager' and user_employee.main_company:
            # Manager can access employees from sub-companies under their main company
            if sub_company_id:
                # Verify the sub-company belongs to their main company
                sub_company = Company.objects.filter(
                    id=sub_company_id,
                    parent_company=user_employee.main_company
                ).first()
                
                if not sub_company:
                    return Response({
                        'error': 'You do not have access to this sub-company'
                    }, status=status.HTTP_403_FORBIDDEN)
                
                employees = Employee.objects.filter(
                    sub_company_id=sub_company_id,
                    status=status_filter
                )
            else:
                # Get all employees from sub-companies under their main company
                employees = Employee.objects.filter(
                    sub_company__parent_company=user_employee.main_company,
                    status=status_filter
                )
        else:
            # Sub-Manager, HR, Supervisor, Employee: only their own sub-company
            if not user_employee.sub_company:
                return Response({
                    'error': 'You are not associated with any sub-company'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # If they specify a different sub-company, deny access
            if sub_company_id and int(sub_company_id) != user_employee.sub_company.id:
                return Response({
                    'error': 'You can only view employees from your own sub-company'
                }, status=status.HTTP_403_FORBIDDEN)
            
            employees = Employee.objects.filter(
                sub_company=user_employee.sub_company,
                status=status_filter
            )
        
        serializer = EmployeeSerializer(employees, many=True)
        
        return Response({
            'user_role': user_employee.role,
            'employees': serializer.data,
            'count': employees.count()
        })
        
    except Employee.DoesNotExist:
        return Response({
            'error': 'No employee record found'
        }, status=status.HTTP_404_NOT_FOUND)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_creatable_roles(request):
    """
    Get list of roles that the logged-in user can create
    """
    try:
        user_employee = Employee.objects.get(email=request.user.email)
        user_role = user_employee.role
        
        role_creation_permissions = {
            'Admin': ['Manager', 'Sub-Manager', 'HR', 'Supervisor', 'Employee'],
            'Manager': ['HR', 'Supervisor', 'Employee'],
            'Sub-Manager': ['HR', 'Supervisor', 'Employee'],
            'HR': ['Supervisor', 'Employee'],
            'Supervisor': ['Employee']
        }
        
        allowed_roles = role_creation_permissions.get(user_role, [])
        
        return Response({
            'user_role': user_role,
            'creatable_roles': allowed_roles
        })
        
    except Employee.DoesNotExist:
        return Response({
            'error': 'No employee record found'
        }, status=status.HTTP_404_NOT_FOUND)