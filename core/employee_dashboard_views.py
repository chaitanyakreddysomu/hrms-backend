# employee_dashboard_views.py
"""
Employee Dashboard API Views
Comprehensive APIs for employee self-service portal
"""

from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.db.models import Q, Sum, Count
from django.utils import timezone
from django.http import FileResponse, HttpResponse
from datetime import datetime, timedelta
import calendar

from .models import (
    Employee, OfficialDetails, IdentityDocument, BankDetails,
    SalaryStructure, Payslip, IncrementHistory, Attendance,
    OvertimeRecord, Document, Report
)
from .additional_models import Notification, ProfileUpdateRequest
from .serializers import (
    EmployeeDashboardSerializer, EmployeeProfileSerializer,
    NotificationSerializer, OfficialDetailsSerializer,
    IdentityDocumentSerializer, BankDetailsSerializer,
    SalaryStructureSerializer, PayslipSerializer,
    IncrementHistorySerializer, AttendanceSerializer,
    OvertimeRecordSerializer, DocumentSerializer,
    ReportSerializer, ProfileUpdateRequestSerializer
)


class IsEmployeeOwner(permissions.BasePermission):
    """
    Custom permission to only allow employees to access their own data.
    """
    def has_object_permission(self, request, view, obj):
        # Check if obj is an Employee or has an employee attribute
        if isinstance(obj, Employee):
            return obj.employee_code == request.user.username or obj.email == request.user.email
        if hasattr(obj, 'employee'):
            return obj.employee.employee_code == request.user.username or obj.employee.email == request.user.email
        return False


class EmployeeDashboardViewSet(viewsets.ViewSet):
    """
    Employee Dashboard APIs
    Provides dashboard stats, notifications, and quick links
    """
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['get'], url_path='stats')
    def dashboard_stats(self, request):
        """
        GET /api/employee-dashboard/stats/
        Returns: Present days, absent days, OT hours, and take-home salary for current month
        """
        try:
            # Get employee by username or email
            employee = Employee.objects.filter(
                Q(employee_code=request.user.username) | Q(email=request.user.email)
            ).first()
            
            if not employee:
                return Response(
                    {"error": "Employee profile not found"},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Get current month and year
            now = timezone.now()
            current_month = now.month
            current_year = now.year
            
            # Calculate attendance stats for current month
            attendance_records = Attendance.objects.filter(
                employee=employee,
                date__month=current_month,
                date__year=current_year
            )
            
            present_days = attendance_records.filter(status='P').count()
            absent_days = attendance_records.filter(status='A').count()
            half_days = attendance_records.filter(status='HD').count()
            
            # Calculate OT hours for current month
            ot_hours = OvertimeRecord.objects.filter(
                employee=employee,
                date__month=current_month,
                date__year=current_year
            ).aggregate(total_hours=Sum('hours'))['total_hours'] or 0
            
            # Get latest payslip for take-home salary
            latest_payslip = Payslip.objects.filter(
                employee=employee
            ).order_by('-year', '-month').first()
            
            take_home_salary = latest_payslip.net_salary if latest_payslip else 0
            
            stats = {
                "employee_name": employee.full_name,
                "employee_code": employee.employee_code,
                "profile_photo": employee.photo.url if employee.photo else None,
                "present_days": present_days,
                "absent_days": absent_days,
                "half_days": half_days,
                "ot_hours": float(ot_hours),
                "take_home_salary": float(take_home_salary),
                "current_month": now.strftime("%B %Y")
            }
            
            return Response(stats, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'], url_path='notifications')
    def recent_notifications(self, request):
        """
        GET /api/employee-dashboard/notifications/
        Returns: Recent notifications (last 10)
        Query params: ?limit=10&unread_only=false
        """
        try:
            employee = Employee.objects.filter(
                Q(employee_code=request.user.username) | Q(email=request.user.email)
            ).first()
            
            if not employee:
                return Response(
                    {"error": "Employee profile not found"},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            limit = int(request.query_params.get('limit', 10))
            unread_only = request.query_params.get('unread_only', 'false').lower() == 'true'
            
            notifications = Notification.objects.filter(employee=employee)
            
            if unread_only:
                notifications = notifications.filter(is_read=False)
            
            notifications = notifications[:limit]
            
            serializer = NotificationSerializer(notifications, many=True)
            
            return Response({
                "notifications": serializer.data,
                "unread_count": Notification.objects.filter(
                    employee=employee, is_read=False
                ).count()
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['post'], url_path='mark-read')
    def mark_notification_read(self, request, pk=None):
        """
        POST /api/employee-dashboard/{notification_id}/mark-read/
        Marks a notification as read
        """
        try:
            notification = get_object_or_404(Notification, pk=pk)
            
            # Verify employee owns this notification
            employee = Employee.objects.filter(
                Q(employee_code=request.user.username) | Q(email=request.user.email)
            ).first()
            
            if notification.employee != employee:
                return Response(
                    {"error": "Unauthorized"},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            notification.is_read = True
            notification.save()
            
            return Response(
                {"message": "Notification marked as read"},
                status=status.HTTP_200_OK
            )
            
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['post'], url_path='mark-all-read')
    def mark_all_read(self, request):
        """
        POST /api/employee-dashboard/mark-all-read/
        Marks all notifications as read for the current employee
        """
        try:
            employee = Employee.objects.filter(
                Q(employee_code=request.user.username) | Q(email=request.user.email)
            ).first()
            
            if not employee:
                return Response(
                    {"error": "Employee profile not found"},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            updated = Notification.objects.filter(
                employee=employee, is_read=False
            ).update(is_read=True)
            
            return Response(
                {"message": f"{updated} notifications marked as read"},
                status=status.HTTP_200_OK
            )
            
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class EmployeeProfileViewSet(viewsets.ViewSet):
    """
    Employee Profile APIs
    Provides complete employee profile information
    """
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['get'], url_path='personal-info')
    def personal_information(self, request):
        """
        GET /api/employee-profile/personal-info/
        Returns: Full name, employee code, DOB, gender, marital status
        """
        try:
            employee = Employee.objects.filter(
                Q(employee_code=request.user.username) | Q(email=request.user.email)
            ).first()
            
            if not employee:
                return Response(
                    {"error": "Employee profile not found"},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            data = {
                "full_name": employee.full_name,
                "employee_code": employee.employee_code,
                "date_of_birth": employee.date_of_birth,
                "gender": employee.get_gender_display(),
                "gender_code": employee.gender,
                "marital_status": employee.get_marital_status_display(),
                "marital_status_code": employee.marital_status,
                "photo": employee.photo.url if employee.photo else None,
            }
            
            return Response(data, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'], url_path='contact-info')
    def contact_information(self, request):
        """
        GET /api/employee-profile/contact-info/
        Returns: Mobile, email, current address, permanent address
        """
        try:
            employee = Employee.objects.filter(
                Q(employee_code=request.user.username) | Q(email=request.user.email)
            ).first()
            
            if not employee:
                return Response(
                    {"error": "Employee profile not found"},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            data = {
                "mobile_number": employee.mobile_number,
                "email": employee.email,
                "current_address": employee.current_address,
                "permanent_address": employee.permanent_address,
            }
            
            return Response(data, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'], url_path='official-info')
    def official_information(self, request):
        """
        GET /api/employee-profile/official-info/
        Returns: DOJ, department, designation, location, supervisor
        """
        try:
            employee = Employee.objects.filter(
                Q(employee_code=request.user.username) | Q(email=request.user.email)
            ).first()
            
            if not employee:
                return Response(
                    {"error": "Employee profile not found"},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            official_details = OfficialDetails.objects.filter(employee=employee).first()
            
            if not official_details:
                return Response(
                    {"error": "Official details not found"},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            data = {
                "date_of_joining": official_details.date_of_joining,
                "department": official_details.department,
                "designation": official_details.designation,
                "location": official_details.location,
                "supervisor_name": official_details.supervisor_name,
                "salary_type": official_details.salary_type,
            }
            
            return Response(data, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'], url_path='identity-docs')
    def identity_documents(self, request):
        """
        GET /api/employee-profile/identity-docs/
        Returns: Aadhaar, PAN, ESI, PF UAN numbers
        """
        try:
            employee = Employee.objects.filter(
                Q(employee_code=request.user.username) | Q(email=request.user.email)
            ).first()
            
            if not employee:
                return Response(
                    {"error": "Employee profile not found"},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            identity_doc = IdentityDocument.objects.filter(employee=employee).first()
            
            if not identity_doc:
                return Response(
                    {"error": "Identity documents not found"},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            data = {
                "aadhaar_number": identity_doc.aadhaar_number,
                "pan_number": identity_doc.pan_number,
                "esi_number": identity_doc.esi_number,
                "pf_uan_number": identity_doc.pf_uan_number,
                "passport_number": identity_doc.passport_number,
            }
            
            return Response(data, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'], url_path='bank-info')
    def bank_information(self, request):
        """
        GET /api/employee-profile/bank-info/
        Returns: Bank name, account number, IFSC code
        """
        try:
            employee = Employee.objects.filter(
                Q(employee_code=request.user.username) | Q(email=request.user.email)
            ).first()
            
            if not employee:
                return Response(
                    {"error": "Employee profile not found"},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            bank_details = BankDetails.objects.filter(employee=employee).first()
            
            if not bank_details:
                return Response(
                    {"error": "Bank details not found"},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            data = {
                "bank_name": bank_details.bank_name,
                "account_number": bank_details.account_number,
                "ifsc_code": bank_details.ifsc_code,
                "branch_name": bank_details.branch_name,
            }
            
            return Response(data, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'], url_path='complete')
    def complete_profile(self, request):
        """
        GET /api/employee-profile/complete/
        Returns: Complete employee profile in one call
        """
        try:
            employee = Employee.objects.filter(
                Q(employee_code=request.user.username) | Q(email=request.user.email)
            ).first()
            
            if not employee:
                return Response(
                    {"error": "Employee profile not found"},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            official_details = OfficialDetails.objects.filter(employee=employee).first()
            identity_doc = IdentityDocument.objects.filter(employee=employee).first()
            bank_details = BankDetails.objects.filter(employee=employee).first()
            
            data = {
                "personal_information": {
                    "full_name": employee.full_name,
                    "employee_code": employee.employee_code,
                    "date_of_birth": employee.date_of_birth,
                    "gender": employee.get_gender_display(),
                    "marital_status": employee.get_marital_status_display(),
                    "photo": employee.photo.url if employee.photo else None,
                },
                "contact_information": {
                    "mobile_number": employee.mobile_number,
                    "email": employee.email,
                    "current_address": employee.current_address,
                    "permanent_address": employee.permanent_address,
                },
                "official_information": {
                    "date_of_joining": official_details.date_of_joining if official_details else None,
                    "department": official_details.department if official_details else None,
                    "designation": official_details.designation if official_details else None,
                    "location": official_details.location if official_details else None,
                    "supervisor_name": official_details.supervisor_name if official_details else None,
                    "salary_type": official_details.salary_type if official_details else None,
                },
                "identity_documents": {
                    "aadhaar_number": identity_doc.aadhaar_number if identity_doc else None,
                    "pan_number": identity_doc.pan_number if identity_doc else None,
                    "esi_number": identity_doc.esi_number if identity_doc else None,
                    "pf_uan_number": identity_doc.pf_uan_number if identity_doc else None,
                },
                "bank_information": {
                    "bank_name": bank_details.bank_name if bank_details else None,
                    "account_number": bank_details.account_number if bank_details else None,
                    "ifsc_code": bank_details.ifsc_code if bank_details else None,
                    "branch_name": bank_details.branch_name if bank_details else None,
                }
            }
            
            return Response(data, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['post'], url_path='request-update')
    def request_profile_update(self, request):
        """
        POST /api/employee-profile/request-update/
        Body: {
            "field_name": "mobile_number",
            "requested_value": "9876543210",
            "reason": "Changed mobile number"
        }
        Creates a profile update request for HR approval
        """
        try:
            employee = Employee.objects.filter(
                Q(employee_code=request.user.username) | Q(email=request.user.email)
            ).first()
            
            if not employee:
                return Response(
                    {"error": "Employee profile not found"},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            field_name = request.data.get('field_name')
            requested_value = request.data.get('requested_value')
            reason = request.data.get('reason')
            
            if not all([field_name, requested_value, reason]):
                return Response(
                    {"error": "field_name, requested_value, and reason are required"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Get current value
            current_value = getattr(employee, field_name, None)
            
            # Create update request
            update_request = ProfileUpdateRequest.objects.create(
                employee=employee,
                field_name=field_name,
                current_value=str(current_value),
                requested_value=requested_value,
                reason=reason
            )
            
            # Create notification for HR
            Notification.objects.create(
                employee=employee,
                notification_type='GENERAL',
                title='Profile Update Request Submitted',
                message=f'Your request to update {field_name} has been submitted for approval.'
            )
            
            serializer = ProfileUpdateRequestSerializer(update_request)
            
            return Response({
                "message": "Update request submitted successfully",
                "request": serializer.data
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'], url_path='update-requests')
    def profile_update_requests(self, request):
        """
        GET /api/employee-profile/update-requests/
        Returns: List of all profile update requests by the employee
        """
        try:
            employee = Employee.objects.filter(
                Q(employee_code=request.user.username) | Q(email=request.user.email)
            ).first()
            
            if not employee:
                return Response(
                    {"error": "Employee profile not found"},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            requests = ProfileUpdateRequest.objects.filter(employee=employee)
            serializer = ProfileUpdateRequestSerializer(requests, many=True)
            
            return Response(serializer.data, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class EmployeeDocumentsViewSet(viewsets.ViewSet):
    """
    Employee Documents APIs
    Provides access to employee documents
    """
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['get'], url_path='list')
    def list_documents(self, request):
        """
        GET /api/employee-documents/list/
        Returns: List of all documents for the employee
        """
        try:
            employee = Employee.objects.filter(
                Q(employee_code=request.user.username) | Q(email=request.user.email)
            ).first()
            
            if not employee:
                return Response(
                    {"error": "Employee profile not found"},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            documents = Document.objects.filter(employee=employee)
            serializer = DocumentSerializer(documents, many=True)
            
            return Response(serializer.data, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'], url_path='appointment-order')
    def appointment_order(self, request):
        """
        GET /api/employee-documents/appointment-order/
        Returns: Appointment order document
        """
        try:
            employee = Employee.objects.filter(
                Q(employee_code=request.user.username) | Q(email=request.user.email)
            ).first()
            
            if not employee:
                return Response(
                    {"error": "Employee profile not found"},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            document = Document.objects.filter(
                employee=employee,
                doc_type='APPOINTMENT'
            ).first()
            
            if not document:
                return Response(
                    {"error": "Appointment order not found"},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            serializer = DocumentSerializer(document)
            return Response(serializer.data, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'], url_path='esi-card')
    def esi_card(self, request):
        """
        GET /api/employee-documents/esi-card/
        Returns: ESI card document
        """
        try:
            employee = Employee.objects.filter(
                Q(employee_code=request.user.username) | Q(email=request.user.email)
            ).first()
            
            if not employee:
                return Response(
                    {"error": "Employee profile not found"},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            document = Document.objects.filter(
                employee=employee,
                doc_type='ESI_CARD'
            ).first()
            
            if not document:
                return Response(
                    {"error": "ESI card not found"},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            serializer = DocumentSerializer(document)
            return Response(serializer.data, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'], url_path='id-card')
    def id_card(self, request):
        """
        GET /api/employee-documents/id-card/
        Returns: ID card document
        """
        try:
            employee = Employee.objects.filter(
                Q(employee_code=request.user.username) | Q(email=request.user.email)
            ).first()
            
            if not employee:
                return Response(
                    {"error": "Employee profile not found"},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            document = Document.objects.filter(
                employee=employee,
                doc_type='ID_CARD'
            ).first()
            
            if not document:
                return Response(
                    {"error": "ID card not found"},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            serializer = DocumentSerializer(document)
            return Response(serializer.data, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'], url_path='relieving-letter')
    def relieving_letter(self, request):
        """
        GET /api/employee-documents/relieving-letter/
        Returns: Relieving letter document
        """
        try:
            employee = Employee.objects.filter(
                Q(employee_code=request.user.username) | Q(email=request.user.email)
            ).first()
            
            if not employee:
                return Response(
                    {"error": "Employee profile not found"},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            document = Document.objects.filter(
                employee=employee,
                doc_type='RELIEVING'
            ).first()
            
            if not document:
                return Response(
                    {"error": "Relieving letter not found"},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            serializer = DocumentSerializer(document)
            return Response(serializer.data, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['get'], url_path='download')
    def download_document(self, request, pk=None):
        """
        GET /api/employee-documents/{document_id}/download/
        Downloads the specified document
        """
        try:
            document = get_object_or_404(Document, pk=pk)
            
            # Verify employee owns this document
            employee = Employee.objects.filter(
                Q(employee_code=request.user.username) | Q(email=request.user.email)
            ).first()
            
            if document.employee != employee:
                return Response(
                    {"error": "Unauthorized"},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            # Return file for download
            return FileResponse(
                document.file.open('rb'),
                as_attachment=True,
                filename=document.file.name.split('/')[-1]
            )
            
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class EmployeeSalaryViewSet(viewsets.ViewSet):
    """
    Employee Salary APIs
    Provides salary structure, payslips, and increment history
    """
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['get'], url_path='structure')
    def salary_structure(self, request):
        """
        GET /api/employee-salary/structure/
        Returns: Complete salary structure with components
        """
        try:
            employee = Employee.objects.filter(
                Q(employee_code=request.user.username) | Q(email=request.user.email)
            ).first()
            
            if not employee:
                return Response(
                    {"error": "Employee profile not found"},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            salary_structure = SalaryStructure.objects.filter(employee=employee).first()
            
            if not salary_structure:
                return Response(
                    {"error": "Salary structure not found"},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            data = {
                "earnings": {
                    "basic": float(salary_structure.basic),
                    "da": float(salary_structure.da),
                    "hra": float(salary_structure.hra),
                    "conveyance": float(salary_structure.conveyance),
                    "bonus": float(salary_structure.bonus),
                    "other_allowances": float(salary_structure.other_allowances),
                },
                "deductions": {
                    "pf": float(salary_structure.pf_deduction),
                    "esi": float(salary_structure.esi_deduction),
                    "pt": float(salary_structure.pt_deduction),
                    "lwf": float(salary_structure.lwf_deduction),
                    "insurance": float(salary_structure.insurance),
                    "advance": float(salary_structure.advance),
                },
                "net_salary": float(salary_structure.net_salary),
                "ctc": float(salary_structure.CTC),
            }
            
            return Response(data, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'], url_path='payslips')
    def payslip_history(self, request):
        """
        GET /api/employee-salary/payslips/
        Returns: Monthly payslip history
        Query params: ?year=2024&month=12
        """
        try:
            employee = Employee.objects.filter(
                Q(employee_code=request.user.username) | Q(email=request.user.email)
            ).first()
            
            if not employee:
                return Response(
                    {"error": "Employee profile not found"},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            payslips = Payslip.objects.filter(employee=employee)
            
            # Filter by year and month if provided
            year = request.query_params.get('year')
            month = request.query_params.get('month')
            
            if year:
                payslips = payslips.filter(year=int(year))
            if month:
                payslips = payslips.filter(month=int(month))
            
            payslips = payslips.order_by('-year', '-month')
            
            data = []
            for payslip in payslips:
                data.append({
                    "id": payslip.id,
                    "month": payslip.month,
                    "year": payslip.year,
                    "month_name": calendar.month_name[payslip.month],
                    "gross_salary": float(payslip.gross_salary),
                    "deductions": float(payslip.deductions),
                    "net_salary": float(payslip.net_salary),
                    "pdf_url": payslip.pdf_file.url if payslip.pdf_file else None,
                })
            
            return Response(data, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['get'], url_path='download')
    def download_payslip(self, request, pk=None):
        """
        GET /api/employee-salary/{payslip_id}/download/
        Downloads the specified payslip PDF
        """
        try:
            payslip = get_object_or_404(Payslip, pk=pk)
            
            # Verify employee owns this payslip
            employee = Employee.objects.filter(
                Q(employee_code=request.user.username) | Q(email=request.user.email)
            ).first()
            
            if payslip.employee != employee:
                return Response(
                    {"error": "Unauthorized"},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            # Return file for download
            return FileResponse(
                payslip.pdf_file.open('rb'),
                as_attachment=True,
                filename=f"payslip_{payslip.month}_{payslip.year}.pdf"
            )
            
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'], url_path='increments')
    def increment_history(self, request):
        """
        GET /api/employee-salary/increments/
        Returns: Increment history
        """
        try:
            employee = Employee.objects.filter(
                Q(employee_code=request.user.username) | Q(email=request.user.email)
            ).first()
            
            if not employee:
                return Response(
                    {"error": "Employee profile not found"},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            increments = IncrementHistory.objects.filter(
                employee=employee
            ).order_by('-effective_date')
            
            data = []
            for increment in increments:
                data.append({
                    "id": increment.id,
                    "effective_date": increment.effective_date,
                    "old_salary": float(increment.old_salary),
                    "new_salary": float(increment.new_salary),
                    "increment_amount": float(increment.new_salary - increment.old_salary),
                    "increment_percentage": round(
                        ((increment.new_salary - increment.old_salary) / increment.old_salary) * 100, 2
                    ) if increment.old_salary > 0 else 0,
                })
            
            return Response(data, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class EmployeeAttendanceViewSet(viewsets.ViewSet):
    """
    Employee Attendance APIs
    Provides attendance calendar, summary, and overtime details
    """
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['get'], url_path='calendar')
    def attendance_calendar(self, request):
        """
        GET /api/employee-attendance/calendar/
        Returns: Monthly attendance calendar
        Query params: ?year=2024&month=12
        """
        try:
            employee = Employee.objects.filter(
                Q(employee_code=request.user.username) | Q(email=request.user.email)
            ).first()
            
            if not employee:
                return Response(
                    {"error": "Employee profile not found"},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Get year and month from query params or use current
            now = timezone.now()
            year = int(request.query_params.get('year', now.year))
            month = int(request.query_params.get('month', now.month))
            
            # Get attendance records for the month
            attendance_records = Attendance.objects.filter(
                employee=employee,
                date__year=year,
                date__month=month
            ).order_by('date')
            
            # Create calendar data
            calendar_data = []
            for record in attendance_records:
                calendar_data.append({
                    "date": record.date,
                    "day": record.date.strftime("%A"),
                    "status": record.status,
                    "status_display": record.get_status_display(),
                })
            
            return Response({
                "year": year,
                "month": month,
                "month_name": calendar.month_name[month],
                "attendance": calendar_data
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'], url_path='summary')
    def attendance_summary(self, request):
        """
        GET /api/employee-attendance/summary/
        Returns: Attendance summary for a month
        Query params: ?year=2024&month=12
        """
        try:
            employee = Employee.objects.filter(
                Q(employee_code=request.user.username) | Q(email=request.user.email)
            ).first()
            
            if not employee:
                return Response(
                    {"error": "Employee profile not found"},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Get year and month from query params or use current
            now = timezone.now()
            year = int(request.query_params.get('year', now.year))
            month = int(request.query_params.get('month', now.month))
            
            # Get attendance records for the month
            attendance_records = Attendance.objects.filter(
                employee=employee,
                date__year=year,
                date__month=month
            )
            
            # Calculate summary
            total_working_days = attendance_records.exclude(
                status__in=['WO', 'H']
            ).count()
            days_present = attendance_records.filter(status='P').count()
            days_absent = attendance_records.filter(status='A').count()
            weekly_offs = attendance_records.filter(status='WO').count()
            holidays = attendance_records.filter(status='H').count()
            half_days = attendance_records.filter(status='HD').count()
            
            # Get overtime hours
            ot_hours = OvertimeRecord.objects.filter(
                employee=employee,
                date__year=year,
                date__month=month
            ).aggregate(total_hours=Sum('hours'))['total_hours'] or 0
            
            summary = {
                "year": year,
                "month": month,
                "month_name": calendar.month_name[month],
                "total_working_days": total_working_days,
                "days_present": days_present,
                "days_absent": days_absent,
                "weekly_offs": weekly_offs,
                "holidays": holidays,
                "half_days": half_days,
                "overtime_hours": float(ot_hours),
            }
            
            return Response(summary, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'], url_path='overtime')
    def overtime_details(self, request):
        """
        GET /api/employee-attendance/overtime/
        Returns: Overtime details for a month
        Query params: ?year=2024&month=12
        """
        try:
            employee = Employee.objects.filter(
                Q(employee_code=request.user.username) | Q(email=request.user.email)
            ).first()
            
            if not employee:
                return Response(
                    {"error": "Employee profile not found"},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Get year and month from query params or use current
            now = timezone.now()
            year = int(request.query_params.get('year', now.year))
            month = int(request.query_params.get('month', now.month))
            
            # Get overtime records for the month
            ot_records = OvertimeRecord.objects.filter(
                employee=employee,
                date__year=year,
                date__month=month
            ).order_by('date')
            
            data = []
            for record in ot_records:
                data.append({
                    "date": record.date,
                    "hours": float(record.hours),
                })
            
            total_hours = sum(float(record.hours) for record in ot_records)
            
            return Response({
                "year": year,
                "month": month,
                "month_name": calendar.month_name[month],
                "overtime_records": data,
                "total_hours": total_hours,
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class EmployeeReportsViewSet(viewsets.ViewSet):
    """
    Employee Reports APIs
    Provides salary statements, deduction statements, and certificates
    """
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['get'], url_path='list')
    def list_reports(self, request):
        """
        GET /api/employee-reports/list/
        Returns: List of all reports for the employee
        """
        try:
            employee = Employee.objects.filter(
                Q(employee_code=request.user.username) | Q(email=request.user.email)
            ).first()
            
            if not employee:
                return Response(
                    {"error": "Employee profile not found"},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            reports = Report.objects.filter(employee=employee).order_by('-generated_on')
            serializer = ReportSerializer(reports, many=True)
            
            return Response(serializer.data, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'], url_path='salary-statement')
    def salary_statement(self, request):
        """
        GET /api/employee-reports/salary-statement/
        Returns: Salary statement report
        Query params: ?period=yearly&year=2024
        """
        try:
            employee = Employee.objects.filter(
                Q(employee_code=request.user.username) | Q(email=request.user.email)
            ).first()
            
            if not employee:
                return Response(
                    {"error": "Employee profile not found"},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            report = Report.objects.filter(
                employee=employee,
                report_type='SALARY_STATEMENT'
            ).first()
            
            if not report:
                return Response(
                    {"error": "Salary statement not found"},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            serializer = ReportSerializer(report)
            return Response(serializer.data, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'], url_path='deduction-statement')
    def deduction_statement(self, request):
        """
        GET /api/employee-reports/deduction-statement/
        Returns: Deduction statement report (PF/ESI/PT/LWF)
        """
        try:
            employee = Employee.objects.filter(
                Q(employee_code=request.user.username) | Q(email=request.user.email)
            ).first()
            
            if not employee:
                return Response(
                    {"error": "Employee profile not found"},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            report = Report.objects.filter(
                employee=employee,
                report_type='DEDUCTION_STATEMENT'
            ).first()
            
            if not report:
                return Response(
                    {"error": "Deduction statement not found"},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            serializer = ReportSerializer(report)
            return Response(serializer.data, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['get'], url_path='download')
    def download_report(self, request, pk=None):
        """
        GET /api/employee-reports/{report_id}/download/
        Downloads the specified report
        """
        try:
            report = get_object_or_404(Report, pk=pk)
            
            # Verify employee owns this report
            employee = Employee.objects.filter(
                Q(employee_code=request.user.username) | Q(email=request.user.email)
            ).first()
            
            if report.employee != employee:
                return Response(
                    {"error": "Unauthorized"},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            # Return file for download
            return FileResponse(
                report.file.open('rb'),
                as_attachment=True,
                filename=report.file.name.split('/')[-1]
            )
            
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
