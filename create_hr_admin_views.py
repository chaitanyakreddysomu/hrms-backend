#!/usr/bin/env python3
"""Script to create hr_admin_views.py file"""

content = '''# hr_admin_views.py
"""
HR/Admin/Manager/Supervisor APIs for Employee Data Management
APIs for adding and updating employee official info, identity docs, and bank details
"""

from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.db.models import Q
from django.utils import timezone

from .models import (
    Employee, OfficialDetails, IdentityDocument, BankDetails,
    Company
)
from .serializers import (
    OfficialDetailsSerializer, IdentityDocumentSerializer,
    BankDetailsSerializer, EmployeeSerializer
)


class IsHROrAdminOrManager(permissions.BasePermission):
    """
    Custom permission for HR, Admin, Manager, Sub-Manager roles
    """
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        # Check if user has Employee record with appropriate role
        try:
            employee = Employee.objects.get(
                Q(employee_code=request.user.username) | Q(email=request.user.email)
            )
            return employee.role in ['Admin', 'Manager', 'Sub-Manager', 'HR']
        except Employee.DoesNotExist:
            return False


class IsHROrAdminOrSupervisor(permissions.BasePermission):
    """
    Custom permission for HR, Admin, Supervisor, Manager, Sub-Manager roles
    """
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        try:
            employee = Employee.objects.get(
                Q(employee_code=request.user.username) | Q(email=request.user.email)
            )
            return employee.role in ['Admin', 'Manager', 'Sub-Manager', 'HR', 'Supervisor']
        except Employee.DoesNotExist:
            return False


class EmployeeDataManagementViewSet(viewsets.ViewSet):
    """
    HR/Admin/Manager/Supervisor APIs for managing employee data
    """
    permission_classes = [IsAuthenticated, IsHROrAdminOrSupervisor]

    @action(detail=False, methods=['post'], url_path='add-official-details')
    def add_official_details(self, request):
        """
        POST /api/employee-data-management/add-official-details/
        
        Add official details for an employee
        """
        try:
            employee_id = request.data.get('employee_id')
            
            if not employee_id:
                return Response(
                    {"error": "employee_id is required"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            employee = get_object_or_404(Employee, id=employee_id)
            
            if OfficialDetails.objects.filter(employee=employee).exists():
                return Response(
                    {"error": "Official details already exist for this employee. Use update API instead."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            requester = Employee.objects.get(
                Q(employee_code=request.user.username) | Q(email=request.user.email)
            )
            
            if requester.role == 'Sub-Manager':
                if employee.sub_company != requester.sub_company:
                    return Response(
                        {"error": "You can only manage employees in your sub-company"},
                        status=status.HTTP_403_FORBIDDEN
                    )
            elif requester.role in ['HR', 'Supervisor']:
                if employee.main_company != requester.main_company and employee.sub_company != requester.sub_company:
                    return Response(
                        {"error": "You can only manage employees in your company"},
                        status=status.HTTP_403_FORBIDDEN
                    )
            
            data = request.data.copy()
            data.pop('employee_id', None)
            
            serializer = OfficialDetailsSerializer(data=data)
            
            if serializer.is_valid():
                official_details = serializer.save(employee=employee)
                
                return Response({
                    "message": "Official details added successfully",
                    "data": OfficialDetailsSerializer(official_details).data
                }, status=status.HTTP_201_CREATED)
            else:
                return Response(
                    {"error": serializer.errors},
                    status=status.HTTP_400_BAD_REQUEST
                )
                
        except Employee.DoesNotExist:
            return Response(
                {"error": "Requester employee profile not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['put'], url_path='update-official-details')
    def update_official_details(self, request):
        """
        PUT /api/employee-data-management/update-official-details/
        """
        try:
            employee_id = request.data.get('employee_id')
            
            if not employee_id:
                return Response(
                    {"error": "employee_id is required"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            employee = get_object_or_404(Employee, id=employee_id)
            official_details = get_object_or_404(OfficialDetails, employee=employee)
            
            requester = Employee.objects.get(
                Q(employee_code=request.user.username) | Q(email=request.user.email)
            )
            
            if requester.role == 'Sub-Manager':
                if employee.sub_company != requester.sub_company:
                    return Response(
                        {"error": "You can only manage employees in your sub-company"},
                        status=status.HTTP_403_FORBIDDEN
                    )
            elif requester.role in ['HR', 'Supervisor']:
                if employee.main_company != requester.main_company and employee.sub_company != requester.sub_company:
                    return Response(
                        {"error": "You can only manage employees in your company"},
                        status=status.HTTP_403_FORBIDDEN
                    )
            
            serializer = OfficialDetailsSerializer(official_details, data=request.data, partial=True)
            
            if serializer.is_valid():
                updated_details = serializer.save()
                
                return Response({
                    "message": "Official details updated successfully",
                    "data": OfficialDetailsSerializer(updated_details).data
                }, status=status.HTTP_200_OK)
            else:
                return Response(
                    {"error": serializer.errors},
                    status=status.HTTP_400_BAD_REQUEST
                )
                
        except Employee.DoesNotExist:
            return Response(
                {"error": "Requester employee profile not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['post'], url_path='add-identity-documents')
    def add_identity_documents(self, request):
        """
        POST /api/employee-data-management/add-identity-documents/
        """
        try:
            employee_id = request.data.get('employee_id')
            
            if not employee_id:
                return Response(
                    {"error": "employee_id is required"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            employee = get_object_or_404(Employee, id=employee_id)
            
            if IdentityDocument.objects.filter(employee=employee).exists():
                return Response(
                    {"error": "Identity documents already exist for this employee. Use update API instead."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            requester = Employee.objects.get(
                Q(employee_code=request.user.username) | Q(email=request.user.email)
            )
            
            if requester.role == 'Sub-Manager':
                if employee.sub_company != requester.sub_company:
                    return Response(
                        {"error": "You can only manage employees in your sub-company"},
                        status=status.HTTP_403_FORBIDDEN
                    )
            elif requester.role in ['HR', 'Supervisor']:
                if employee.main_company != requester.main_company and employee.sub_company != requester.sub_company:
                    return Response(
                        {"error": "You can only manage employees in your company"},
                        status=status.HTTP_403_FORBIDDEN
                    )
            
            data = request.data.copy()
            data.pop('employee_id', None)
            
            serializer = IdentityDocumentSerializer(data=data)
            
            if serializer.is_valid():
                identity_docs = serializer.save(employee=employee)
                
                return Response({
                    "message": "Identity documents added successfully",
                    "data": IdentityDocumentSerializer(identity_docs).data
                }, status=status.HTTP_201_CREATED)
            else:
                return Response(
                    {"error": serializer.errors},
                    status=status.HTTP_400_BAD_REQUEST
                )
                
        except Employee.DoesNotExist:
            return Response(
                {"error": "Requester employee profile not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['put'], url_path='update-identity-documents')
    def update_identity_documents(self, request):
        """
        PUT /api/employee-data-management/update-identity-documents/
        """
        try:
            employee_id = request.data.get('employee_id')
            
            if not employee_id:
                return Response(
                    {"error": "employee_id is required"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            employee = get_object_or_404(Employee, id=employee_id)
            identity_docs = get_object_or_404(IdentityDocument, employee=employee)
            
            requester = Employee.objects.get(
                Q(employee_code=request.user.username) | Q(email=request.user.email)
            )
            
            if requester.role == 'Sub-Manager':
                if employee.sub_company != requester.sub_company:
                    return Response(
                        {"error": "You can only manage employees in your sub-company"},
                        status=status.HTTP_403_FORBIDDEN
                    )
            elif requester.role in ['HR', 'Supervisor']:
                if employee.main_company != requester.main_company and employee.sub_company != requester.sub_company:
                    return Response(
                        {"error": "You can only manage employees in your company"},
                        status=status.HTTP_403_FORBIDDEN
                    )
            
            serializer = IdentityDocumentSerializer(identity_docs, data=request.data, partial=True)
            
            if serializer.is_valid():
                updated_docs = serializer.save()
                
                return Response({
                    "message": "Identity documents updated successfully",
                    "data": IdentityDocumentSerializer(updated_docs).data
                }, status=status.HTTP_200_OK)
            else:
                return Response(
                    {"error": serializer.errors},
                    status=status.HTTP_400_BAD_REQUEST
                )
                
        except Employee.DoesNotExist:
            return Response(
                {"error": "Requester employee profile not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['post'], url_path='add-bank-details')
    def add_bank_details(self, request):
        """
        POST /api/employee-data-management/add-bank-details/
        """
        try:
            employee_id = request.data.get('employee_id')
            
            if not employee_id:
                return Response(
                    {"error": "employee_id is required"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            employee = get_object_or_404(Employee, id=employee_id)
            
            if BankDetails.objects.filter(employee=employee).exists():
                return Response(
                    {"error": "Bank details already exist for this employee. Use update API instead."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            requester = Employee.objects.get(
                Q(employee_code=request.user.username) | Q(email=request.user.email)
            )
            
            if requester.role == 'Sub-Manager':
                if employee.sub_company != requester.sub_company:
                    return Response(
                        {"error": "You can only manage employees in your sub-company"},
                        status=status.HTTP_403_FORBIDDEN
                    )
            elif requester.role in ['HR', 'Supervisor']:
                if employee.main_company != requester.main_company and employee.sub_company != requester.sub_company:
                    return Response(
                        {"error": "You can only manage employees in your company"},
                        status=status.HTTP_403_FORBIDDEN
                    )
            
            data = request.data.copy()
            data.pop('employee_id', None)
            
            serializer = BankDetailsSerializer(data=data)
            
            if serializer.is_valid():
                bank_details = serializer.save(employee=employee)
                
                return Response({
                    "message": "Bank details added successfully",
                    "data": BankDetailsSerializer(bank_details).data
                }, status=status.HTTP_201_CREATED)
            else:
                return Response(
                    {"error": serializer.errors},
                    status=status.HTTP_400_BAD_REQUEST
                )
                
        except Employee.DoesNotExist:
            return Response(
                {"error": "Requester employee profile not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['put'], url_path='update-bank-details')
    def update_bank_details(self, request):
        """
        PUT /api/employee-data-management/update-bank-details/
        """
        try:
            employee_id = request.data.get('employee_id')
            
            if not employee_id:
                return Response(
                    {"error": "employee_id is required"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            employee = get_object_or_404(Employee, id=employee_id)
            bank_details = get_object_or_404(BankDetails, employee=employee)
            
            requester = Employee.objects.get(
                Q(employee_code=request.user.username) | Q(email=request.user.email)
            )
            
            if requester.role == 'Sub-Manager':
                if employee.sub_company != requester.sub_company:
                    return Response(
                        {"error": "You can only manage employees in your sub-company"},
                        status=status.HTTP_403_FORBIDDEN
                    )
            elif requester.role in ['HR', 'Supervisor']:
                if employee.main_company != requester.main_company and employee.sub_company != requester.sub_company:
                    return Response(
                        {"error": "You can only manage employees in your company"},
                        status=status.HTTP_403_FORBIDDEN
                    )
            
            serializer = BankDetailsSerializer(bank_details, data=request.data, partial=True)
            
            if serializer.is_valid():
                updated_details = serializer.save()
                
                return Response({
                    "message": "Bank details updated successfully",
                    "data": BankDetailsSerializer(updated_details).data
                }, status=status.HTTP_200_OK)
            else:
                return Response(
                    {"error": serializer.errors},
                    status=status.HTTP_400_BAD_REQUEST
                )
                
        except Employee.DoesNotExist:
            return Response(
                {"error": "Requester employee profile not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'], url_path='get-employee-details')
    def get_employee_details(self, request):
        """
        GET /api/employee-data-management/get-employee-details/?employee_id=1
        """
        try:
            employee_id = request.query_params.get('employee_id')
            
            if not employee_id:
                return Response(
                    {"error": "employee_id is required"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            employee = get_object_or_404(Employee, id=employee_id)
            
            requester = Employee.objects.get(
                Q(employee_code=request.user.username) | Q(email=request.user.email)
            )
            
            if requester.role == 'Sub-Manager':
                if employee.sub_company != requester.sub_company:
                    return Response(
                        {"error": "You can only view employees in your sub-company"},
                        status=status.HTTP_403_FORBIDDEN
                    )
            elif requester.role in ['HR', 'Supervisor']:
                if employee.main_company != requester.main_company and employee.sub_company != requester.sub_company:
                    return Response(
                        {"error": "You can only view employees in your company"},
                        status=status.HTTP_403_FORBIDDEN
                    )
            
            official_details = None
            identity_docs = None
            bank_details = None
            
            try:
                official_details = OfficialDetails.objects.get(employee=employee)
            except OfficialDetails.DoesNotExist:
                pass
            
            try:
                identity_docs = IdentityDocument.objects.get(employee=employee)
            except IdentityDocument.DoesNotExist:
                pass
            
            try:
                bank_details = BankDetails.objects.get(employee=employee)
            except BankDetails.DoesNotExist:
                pass
            
            return Response({
                "employee": EmployeeSerializer(employee).data,
                "official_details": OfficialDetailsSerializer(official_details).data if official_details else None,
                "identity_documents": IdentityDocumentSerializer(identity_docs).data if identity_docs else None,
                "bank_details": BankDetailsSerializer(bank_details).data if bank_details else None
            }, status=status.HTTP_200_OK)
            
        except Employee.DoesNotExist:
            return Response(
                {"error": "Requester employee profile not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'], url_path='list-employees')
    def list_employees(self, request):
        """
        GET /api/employee-data-management/list-employees/
        """
        try:
            requester = Employee.objects.get(
                Q(employee_code=request.user.username) | Q(email=request.user.email)
            )
            
            if requester.role == 'Admin':
                employees = Employee.objects.all()
            elif requester.role == 'Manager':
                allowed_companies = [requester.main_company] + list(requester.main_company.subcompanies.all() if requester.main_company else [])
                employees = Employee.objects.filter(
                    Q(main_company__in=allowed_companies) | Q(sub_company__in=allowed_companies)
                )
            elif requester.role == 'Sub-Manager':
                employees = Employee.objects.filter(sub_company=requester.sub_company)
            else:
                employees = Employee.objects.filter(
                    Q(main_company=requester.main_company) | Q(sub_company=requester.sub_company)
                )
            
            role = request.query_params.get('role')
            status_filter = request.query_params.get('status')
            company_id = request.query_params.get('company_id')
            
            if role:
                employees = employees.filter(role=role)
            if status_filter:
                employees = employees.filter(status=status_filter)
            if company_id:
                employees = employees.filter(
                    Q(main_company_id=company_id) | Q(sub_company_id=company_id)
                )
            
            return Response({
                "count": employees.count(),
                "employees": EmployeeSerializer(employees, many=True).data
            }, status=status.HTTP_200_OK)
            
        except Employee.DoesNotExist:
            return Response(
                {"error": "Requester employee profile not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
'''

# Write to file
with open('core/hr_admin_views.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("File created successfully!")
