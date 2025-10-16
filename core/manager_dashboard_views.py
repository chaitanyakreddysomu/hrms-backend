"""
Manager Dashboard APIs for main company management
Includes: Company overview, employee management, attendance, salary, reports, analytics
"""

from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Count, Sum, Avg, Q, Min, Max
from django.utils import timezone
from datetime import datetime, timedelta
from decimal import Decimal

from .models import (
    Employee, Attendance, OvertimeRecord, OfficialDetails,
    SalaryStructure, Payslip, Company, IncrementHistory, Document
)
from .serializers import (
    EmployeeSerializer, AttendanceSerializer, OvertimeRecordSerializer,
    OfficialDetailsSerializer, SalaryStructureSerializer, PayslipSerializer,
    CompanySerializer
)


class IsManager(permissions.BasePermission):
    """
    Custom permission for Manager role
    """
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        try:
            employee = Employee.objects.get(
                Q(employee_code=request.user.username) | Q(email=request.user.email)
            )
            return employee.role == 'Manager'
        except Employee.DoesNotExist:
            return False


class ManagerDashboardViewSet(viewsets.ViewSet):
    """
    Manager Dashboard ViewSet for main company management
    
    Features:
    - Company Overview & Statistics
    - Employee Management (Main Company & Sub-Companies)
    - Attendance Tracking & Reports
    - Salary Management
    - Payslip Generation
    - Overtime Management
    - Analytics & Reports
    - Sub-Company Management
    
    Access: Manager Role ONLY
    """
    permission_classes = [IsManager]

    def _get_manager_employee(self, request):
        """Helper method to get manager's employee record"""
        try:
            return Employee.objects.get(
                Q(employee_code=request.user.username) | Q(email=request.user.email)
            )
        except Employee.DoesNotExist:
            return None

    def _get_manager_company(self, manager_employee):
        """Helper method to get manager's main company"""
        if not manager_employee:
            return None
        return manager_employee.main_company

    def _get_company_employees(self, company, include_sub_companies=True, filters=None):
        """Helper method to get all employees under manager's company"""
        if not company:
            return Employee.objects.none()
        
        if include_sub_companies:
            # Get all sub-companies
            sub_companies = Company.objects.filter(parent_company=company)
            queryset = Employee.objects.filter(
                Q(main_company=company) | Q(sub_company__in=sub_companies)
            )
        else:
            queryset = Employee.objects.filter(main_company=company)
        
        if filters:
            if filters.get('department'):
                queryset = queryset.filter(officialdetails__department=filters['department'])
            if filters.get('designation'):
                queryset = queryset.filter(officialdetails__designation=filters['designation'])
            if filters.get('status'):
                queryset = queryset.filter(status=filters['status'])
            if filters.get('company_id'):
                queryset = queryset.filter(Q(main_company_id=filters['company_id']) | Q(sub_company_id=filters['company_id']))
        
        return queryset

    # ==================== COMPANY OVERVIEW ====================
    
    @action(detail=False, methods=['get'], url_path='company-overview')
    def company_overview(self, request):
        """
        Get comprehensive overview of main company and all sub-companies
        
        Query Parameters:
        - month (optional): Month for statistics (1-12)
        - year (optional): Year for statistics
        - include_sub_companies (optional): Include sub-companies data (default: true)
        
        Returns:
        - Company details
        - Employee statistics
        - Attendance statistics
        - Salary statistics
        - Sub-companies overview
        """
        manager = self._get_manager_employee(request)
        if not manager:
            return Response({
                'success': False,
                'error': 'Manager employee record not found'
            }, status=status.HTTP_404_NOT_FOUND)

        company = self._get_manager_company(manager)
        if not company:
            return Response({
                'success': False,
                'error': 'Main company not found'
            }, status=status.HTTP_404_NOT_FOUND)

        # Get parameters
        month = int(request.query_params.get('month', timezone.now().month))
        year = int(request.query_params.get('year', timezone.now().year))
        include_sub = request.query_params.get('include_sub_companies', 'true').lower() == 'true'

        # Company employees
        all_employees = self._get_company_employees(company, include_sub_companies=include_sub)
        active_employees = all_employees.filter(status='ACTIVE')

        # Employee statistics by department
        by_department = active_employees.values(
            'officialdetails__department'
        ).annotate(count=Count('id')).order_by('-count')

        # Employee statistics by designation
        by_designation = active_employees.values(
            'officialdetails__designation'
        ).annotate(count=Count('id')).order_by('-count')

        # Attendance statistics for the month
        start_date = datetime(year, month, 1).date()
        if month == 12:
            end_date = datetime(year + 1, 1, 1).date() - timedelta(days=1)
        else:
            end_date = datetime(year, month + 1, 1).date() - timedelta(days=1)

        attendance_stats = Attendance.objects.filter(
            employee__in=active_employees,
            date__range=[start_date, end_date]
        ).aggregate(
            present=Count('id', filter=Q(status='P')),
            absent=Count('id', filter=Q(status='A')),
            weekly_off=Count('id', filter=Q(status='WO')),
            holiday=Count('id', filter=Q(status='H')),
            half_day=Count('id', filter=Q(status='HD'))
        )

        total_attendance_records = sum(attendance_stats.values())
        attendance_percentage = (
            (attendance_stats['present'] / total_attendance_records * 100)
            if total_attendance_records > 0 else 0
        )

        # Overtime statistics
        overtime_stats = OvertimeRecord.objects.filter(
            employee__in=active_employees,
            date__range=[start_date, end_date]
        ).aggregate(
            total_hours=Sum('hours'),
            records_count=Count('id')
        )

        # Salary statistics
        salary_stats = SalaryStructure.objects.filter(
            employee__in=active_employees
        ).aggregate(
            total_payroll=Sum('CTC'),
            avg_salary=Avg('CTC'),
            min_salary=Min('CTC'),
            max_salary=Max('CTC')
        )

        # Sub-companies overview
        sub_companies = Company.objects.filter(parent_company=company)
        sub_companies_data = []
        for sub_company in sub_companies:
            sub_employees = Employee.objects.filter(sub_company=sub_company)
            sub_companies_data.append({
                'id': sub_company.id,
                'name': sub_company.name,
                'total_employees': sub_employees.count(),
                'active_employees': sub_employees.filter(status='ACTIVE').count(),
            })

        # Recent joinings (last 30 days)
        thirty_days_ago = timezone.now().date() - timedelta(days=30)
        recent_joinings = all_employees.filter(
            officialdetails__date_of_joining__gte=thirty_days_ago
        ).count()

        return Response({
            'success': True,
            'manager': {
                'id': manager.id,
                'name': manager.full_name,
                'employee_code': manager.employee_code,
            },
            'company': {
                'id': company.id,
                'name': company.name,
                'address': company.address,
                'gst_number': company.gst_number,
            },
            'data': {
                'employees': {
                    'total': all_employees.count(),
                    'active': active_employees.count(),
                    'inactive': all_employees.exclude(status='ACTIVE').count(),
                    'recent_joinings': recent_joinings,
                    'by_department': list(by_department),
                    'by_designation': list(by_designation),
                },
                'attendance': {
                    'month': month,
                    'year': year,
                    'present': attendance_stats['present'] or 0,
                    'absent': attendance_stats['absent'] or 0,
                    'weekly_off': attendance_stats['weekly_off'] or 0,
                    'holiday': attendance_stats['holiday'] or 0,
                    'half_day': attendance_stats['half_day'] or 0,
                    'attendance_percentage': round(attendance_percentage, 2),
                },
                'overtime': {
                    'total_hours': float(overtime_stats['total_hours'] or 0),
                    'records_count': overtime_stats['records_count'] or 0,
                },
                'salary': {
                    'total_payroll': float(salary_stats['total_payroll'] or 0),
                    'average_salary': float(salary_stats['avg_salary'] or 0),
                    'min_salary': float(salary_stats['min_salary'] or 0),
                    'max_salary': float(salary_stats['max_salary'] or 0),
                },
                'sub_companies': {
                    'total': sub_companies.count(),
                    'companies': sub_companies_data,
                }
            }
        })

    # ==================== EMPLOYEE MANAGEMENT ====================
    
    @action(detail=False, methods=['get'], url_path='employees')
    def list_employees(self, request):
        """
        Get list of all employees under manager's company
        
        Query Parameters:
        - department (optional): Filter by department
        - designation (optional): Filter by designation
        - status (optional): Filter by status (ACTIVE, INACTIVE, LEFT)
        - company_id (optional): Filter by specific company (main or sub)
        - include_sub_companies (optional): Include sub-company employees (default: true)
        - search (optional): Search by name, email, or employee code
        - page (optional): Page number for pagination
        - page_size (optional): Items per page (default: 20)
        """
        manager = self._get_manager_employee(request)
        if not manager:
            return Response({
                'success': False,
                'error': 'Manager not found'
            }, status=status.HTTP_404_NOT_FOUND)

        company = self._get_manager_company(manager)
        if not company:
            return Response({
                'success': False,
                'error': 'Company not found'
            }, status=status.HTTP_404_NOT_FOUND)

        # Get query parameters
        include_sub = request.query_params.get('include_sub_companies', 'true').lower() == 'true'
        filters = {
            'department': request.query_params.get('department'),
            'designation': request.query_params.get('designation'),
            'status': request.query_params.get('status'),
            'company_id': request.query_params.get('company_id'),
        }
        search = request.query_params.get('search')

        # Get employees
        employees = self._get_company_employees(company, include_sub_companies=include_sub, filters=filters)

        # Search filter
        if search:
            employees = employees.filter(
                Q(full_name__icontains=search) |
                Q(email__icontains=search) |
                Q(employee_code__icontains=search)
            )

        # Pagination
        page = int(request.query_params.get('page', 1))
        page_size = int(request.query_params.get('page_size', 20))
        start = (page - 1) * page_size
        end = start + page_size
        total = employees.count()

        serializer = EmployeeSerializer(employees[start:end], many=True)

        return Response({
            'success': True,
            'data': serializer.data,
            'pagination': {
                'page': page,
                'page_size': page_size,
                'total': total,
                'total_pages': (total + page_size - 1) // page_size,
            }
        })

    @action(detail=False, methods=['get'], url_path='employees/(?P<employee_id>[^/.]+)')
    def get_employee_details(self, request, employee_id=None):
        """
        Get detailed information about a specific employee
        
        Path Parameters:
        - employee_id: Employee ID
        
        Returns:
        - Complete employee profile
        - Official details
        - Salary structure
        - Recent attendance
        - Recent payslips
        """
        manager = self._get_manager_employee(request)
        if not manager:
            return Response({
                'success': False,
                'error': 'Manager not found'
            }, status=status.HTTP_404_NOT_FOUND)

        company = self._get_manager_company(manager)
        if not company:
            return Response({
                'success': False,
                'error': 'Company not found'
            }, status=status.HTTP_404_NOT_FOUND)

        # Get employee
        try:
            employee = self._get_company_employees(company, include_sub_companies=True).get(id=employee_id)
        except Employee.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Employee not found or not under your management'
            }, status=status.HTTP_404_NOT_FOUND)

        # Get related data
        official_details = None
        try:
            official_details = OfficialDetails.objects.get(employee=employee)
        except OfficialDetails.DoesNotExist:
            pass

        salary_structure = None
        try:
            salary_structure = SalaryStructure.objects.get(employee=employee)
        except SalaryStructure.DoesNotExist:
            pass

        # Recent attendance (last 30 days)
        thirty_days_ago = timezone.now().date() - timedelta(days=30)
        recent_attendance = Attendance.objects.filter(
            employee=employee,
            date__gte=thirty_days_ago
        ).order_by('-date')[:30]

        # Recent payslips (last 6 months)
        recent_payslips = Payslip.objects.filter(
            employee=employee
        ).order_by('-month', '-year')[:6]

        return Response({
            'success': True,
            'data': {
                'employee': EmployeeSerializer(employee).data,
                'official_details': OfficialDetailsSerializer(official_details).data if official_details else None,
                'salary_structure': SalaryStructureSerializer(salary_structure).data if salary_structure else None,
                'recent_attendance': AttendanceSerializer(recent_attendance, many=True).data,
                'recent_payslips': PayslipSerializer(recent_payslips, many=True).data,
            }
        })

    # ==================== ATTENDANCE MANAGEMENT ====================
    
    @action(detail=False, methods=['get'], url_path='attendance')
    def get_attendance(self, request):
        """
        Get attendance records for employees
        
        Query Parameters:
        - employee_id (optional): Filter by specific employee
        - department (optional): Filter by department
        - date_from (optional): Start date (YYYY-MM-DD)
        - date_to (optional): End date (YYYY-MM-DD)
        - status (optional): Filter by status (P, A, WO, H, HD)
        - include_sub_companies (optional): Include sub-company employees (default: true)
        - page (optional): Page number
        - page_size (optional): Items per page (default: 50)
        """
        manager = self._get_manager_employee(request)
        if not manager:
            return Response({
                'success': False,
                'error': 'Manager not found'
            }, status=status.HTTP_404_NOT_FOUND)

        company = self._get_manager_company(manager)
        if not company:
            return Response({
                'success': False,
                'error': 'Company not found'
            }, status=status.HTTP_404_NOT_FOUND)

        # Get parameters
        include_sub = request.query_params.get('include_sub_companies', 'true').lower() == 'true'
        employee_id = request.query_params.get('employee_id')
        department = request.query_params.get('department')
        date_from = request.query_params.get('date_from')
        date_to = request.query_params.get('date_to')
        att_status = request.query_params.get('status')

        # Get employees
        employees = self._get_company_employees(company, include_sub_companies=include_sub)

        # Build query
        attendance_query = Attendance.objects.filter(employee__in=employees)

        if employee_id:
            attendance_query = attendance_query.filter(employee_id=employee_id)
        
        if department:
            attendance_query = attendance_query.filter(employee__officialdetails__department=department)

        if date_from:
            attendance_query = attendance_query.filter(date__gte=date_from)
        
        if date_to:
            attendance_query = attendance_query.filter(date__lte=date_to)
        
        if att_status:
            attendance_query = attendance_query.filter(status=att_status)

        attendance_query = attendance_query.order_by('-date')

        # Pagination
        page = int(request.query_params.get('page', 1))
        page_size = int(request.query_params.get('page_size', 50))
        start = (page - 1) * page_size
        end = start + page_size
        total = attendance_query.count()

        serializer = AttendanceSerializer(attendance_query[start:end], many=True)

        return Response({
            'success': True,
            'data': serializer.data,
            'pagination': {
                'page': page,
                'page_size': page_size,
                'total': total,
                'total_pages': (total + page_size - 1) // page_size,
            }
        })

    @action(detail=False, methods=['get'], url_path='attendance/summary')
    def attendance_summary(self, request):
        """
        Get attendance summary for a specific period
        
        Query Parameters:
        - month: Month (1-12, required)
        - year: Year (required)
        - department (optional): Filter by department
        - include_sub_companies (optional): Include sub-company employees (default: true)
        """
        manager = self._get_manager_employee(request)
        if not manager:
            return Response({
                'success': False,
                'error': 'Manager not found'
            }, status=status.HTTP_404_NOT_FOUND)

        company = self._get_manager_company(manager)
        if not company:
            return Response({
                'success': False,
                'error': 'Company not found'
            }, status=status.HTTP_404_NOT_FOUND)

        # Get parameters
        try:
            month = int(request.query_params.get('month'))
            year = int(request.query_params.get('year'))
        except (TypeError, ValueError):
            return Response({
                'success': False,
                'error': 'Month and year are required'
            }, status=status.HTTP_400_BAD_REQUEST)

        include_sub = request.query_params.get('include_sub_companies', 'true').lower() == 'true'
        department = request.query_params.get('department')

        # Date range
        start_date = datetime(year, month, 1).date()
        if month == 12:
            end_date = datetime(year + 1, 1, 1).date() - timedelta(days=1)
        else:
            end_date = datetime(year, month + 1, 1).date() - timedelta(days=1)

        # Get employees
        filters = {'department': department} if department else {}
        employees = self._get_company_employees(company, include_sub_companies=include_sub, filters=filters)

        # Get attendance summary by employee
        summary = []
        for employee in employees:
            attendance_records = Attendance.objects.filter(
                employee=employee,
                date__range=[start_date, end_date]
            )
            
            stats = attendance_records.aggregate(
                present=Count('id', filter=Q(status='P')),
                absent=Count('id', filter=Q(status='A')),
                weekly_off=Count('id', filter=Q(status='WO')),
                holiday=Count('id', filter=Q(status='H')),
                half_day=Count('id', filter=Q(status='HD'))
            )
            
            total_working_days = stats['present'] + stats['absent'] + stats['half_day']
            attendance_percentage = (
                (stats['present'] / total_working_days * 100) if total_working_days > 0 else 0
            )

            summary.append({
                'employee_id': employee.id,
                'employee_code': employee.employee_code,
                'employee_name': employee.full_name,
                'department': employee.officialdetails.department if hasattr(employee, 'officialdetails') else None,
                'present': stats['present'],
                'absent': stats['absent'],
                'weekly_off': stats['weekly_off'],
                'holiday': stats['holiday'],
                'half_day': stats['half_day'],
                'attendance_percentage': round(attendance_percentage, 2),
            })

        return Response({
            'success': True,
            'data': {
                'month': month,
                'year': year,
                'summary': summary
            }
        })

    # ==================== SALARY & PAYROLL MANAGEMENT ====================
    
    @action(detail=False, methods=['get'], url_path='salary-structures')
    def get_salary_structures(self, request):
        """
        Get salary structures for employees
        
        Query Parameters:
        - employee_id (optional): Filter by specific employee
        - department (optional): Filter by department
        - include_sub_companies (optional): Include sub-company employees (default: true)
        - page (optional): Page number
        - page_size (optional): Items per page (default: 20)
        """
        manager = self._get_manager_employee(request)
        if not manager:
            return Response({
                'success': False,
                'error': 'Manager not found'
            }, status=status.HTTP_404_NOT_FOUND)

        company = self._get_manager_company(manager)
        if not company:
            return Response({
                'success': False,
                'error': 'Company not found'
            }, status=status.HTTP_404_NOT_FOUND)

        # Get parameters
        include_sub = request.query_params.get('include_sub_companies', 'true').lower() == 'true'
        employee_id = request.query_params.get('employee_id')
        department = request.query_params.get('department')

        # Get employees
        filters = {'department': department} if department else {}
        employees = self._get_company_employees(company, include_sub_companies=include_sub, filters=filters)

        # Build query
        salary_query = SalaryStructure.objects.filter(employee__in=employees)

        if employee_id:
            salary_query = salary_query.filter(employee_id=employee_id)

        # Pagination
        page = int(request.query_params.get('page', 1))
        page_size = int(request.query_params.get('page_size', 20))
        start = (page - 1) * page_size
        end = start + page_size
        total = salary_query.count()

        serializer = SalaryStructureSerializer(salary_query[start:end], many=True)

        return Response({
            'success': True,
            'data': serializer.data,
            'pagination': {
                'page': page,
                'page_size': page_size,
                'total': total,
                'total_pages': (total + page_size - 1) // page_size,
            }
        })

    @action(detail=False, methods=['get'], url_path='payslips')
    def get_payslips(self, request):
        """
        Get payslips for employees
        
        Query Parameters:
        - employee_id (optional): Filter by specific employee
        - month (optional): Filter by month (1-12)
        - year (optional): Filter by year
        - department (optional): Filter by department
        - include_sub_companies (optional): Include sub-company employees (default: true)
        - page (optional): Page number
        - page_size (optional): Items per page (default: 50)
        """
        manager = self._get_manager_employee(request)
        if not manager:
            return Response({
                'success': False,
                'error': 'Manager not found'
            }, status=status.HTTP_404_NOT_FOUND)

        company = self._get_manager_company(manager)
        if not company:
            return Response({
                'success': False,
                'error': 'Company not found'
            }, status=status.HTTP_404_NOT_FOUND)

        # Get parameters
        include_sub = request.query_params.get('include_sub_companies', 'true').lower() == 'true'
        employee_id = request.query_params.get('employee_id')
        department = request.query_params.get('department')
        month = request.query_params.get('month')
        year = request.query_params.get('year')

        # Get employees
        filters = {'department': department} if department else {}
        employees = self._get_company_employees(company, include_sub_companies=include_sub, filters=filters)

        # Build query
        payslip_query = Payslip.objects.filter(employee__in=employees)

        if employee_id:
            payslip_query = payslip_query.filter(employee_id=employee_id)
        
        if month:
            payslip_query = payslip_query.filter(month=int(month))
        
        if year:
            payslip_query = payslip_query.filter(year=int(year))

        payslip_query = payslip_query.order_by('-year', '-month')

        # Pagination
        page = int(request.query_params.get('page', 1))
        page_size = int(request.query_params.get('page_size', 50))
        start = (page - 1) * page_size
        end = start + page_size
        total = payslip_query.count()

        serializer = PayslipSerializer(payslip_query[start:end], many=True)

        return Response({
            'success': True,
            'data': serializer.data,
            'pagination': {
                'page': page,
                'page_size': page_size,
                'total': total,
                'total_pages': (total + page_size - 1) // page_size,
            }
        })

    # ==================== OVERTIME MANAGEMENT ====================
    
    @action(detail=False, methods=['get'], url_path='overtime')
    def get_overtime_records(self, request):
        """
        Get overtime records for employees
        
        Query Parameters:
        - employee_id (optional): Filter by specific employee
        - date_from (optional): Start date (YYYY-MM-DD)
        - date_to (optional): End date (YYYY-MM-DD)
        - department (optional): Filter by department
        - include_sub_companies (optional): Include sub-company employees (default: true)
        - page (optional): Page number
        - page_size (optional): Items per page (default: 50)
        """
        manager = self._get_manager_employee(request)
        if not manager:
            return Response({
                'success': False,
                'error': 'Manager not found'
            }, status=status.HTTP_404_NOT_FOUND)

        company = self._get_manager_company(manager)
        if not company:
            return Response({
                'success': False,
                'error': 'Company not found'
            }, status=status.HTTP_404_NOT_FOUND)

        # Get parameters
        include_sub = request.query_params.get('include_sub_companies', 'true').lower() == 'true'
        employee_id = request.query_params.get('employee_id')
        department = request.query_params.get('department')
        date_from = request.query_params.get('date_from')
        date_to = request.query_params.get('date_to')

        # Get employees
        filters = {'department': department} if department else {}
        employees = self._get_company_employees(company, include_sub_companies=include_sub, filters=filters)

        # Build query
        overtime_query = OvertimeRecord.objects.filter(employee__in=employees)

        if employee_id:
            overtime_query = overtime_query.filter(employee_id=employee_id)
        
        if date_from:
            overtime_query = overtime_query.filter(date__gte=date_from)
        
        if date_to:
            overtime_query = overtime_query.filter(date__lte=date_to)

        overtime_query = overtime_query.order_by('-date')

        # Pagination
        page = int(request.query_params.get('page', 1))
        page_size = int(request.query_params.get('page_size', 50))
        start = (page - 1) * page_size
        end = start + page_size
        total = overtime_query.count()

        serializer = OvertimeRecordSerializer(overtime_query[start:end], many=True)

        return Response({
            'success': True,
            'data': serializer.data,
            'pagination': {
                'page': page,
                'page_size': page_size,
                'total': total,
                'total_pages': (total + page_size - 1) // page_size,
            }
        })

    # ==================== SUB-COMPANY MANAGEMENT ====================
    
    @action(detail=False, methods=['get'], url_path='sub-companies')
    def list_sub_companies(self, request):
        """
        Get list of all sub-companies under manager's main company
        
        Returns:
        - List of sub-companies with employee statistics
        """
        manager = self._get_manager_employee(request)
        if not manager:
            return Response({
                'success': False,
                'error': 'Manager not found'
            }, status=status.HTTP_404_NOT_FOUND)

        company = self._get_manager_company(manager)
        if not company:
            return Response({
                'success': False,
                'error': 'Company not found'
            }, status=status.HTTP_404_NOT_FOUND)

        # Get sub-companies
        sub_companies = Company.objects.filter(parent_company=company)

        sub_companies_data = []
        for sub_company in sub_companies:
            employees = Employee.objects.filter(sub_company=sub_company)
            active_employees = employees.filter(status='ACTIVE')

            # Get sub-manager
            sub_manager = employees.filter(role='Sub-Manager').first()

            sub_companies_data.append({
                'id': sub_company.id,
                'name': sub_company.name,
                'address': sub_company.address,
                'gst_number': sub_company.gst_number,
                'sub_manager': {
                    'id': sub_manager.id,
                    'name': sub_manager.full_name,
                    'employee_code': sub_manager.employee_code,
                } if sub_manager else None,
                'statistics': {
                    'total_employees': employees.count(),
                    'active_employees': active_employees.count(),
                    'departments': employees.values('officialdetails__department').distinct().count(),
                }
            })

        return Response({
            'success': True,
            'data': sub_companies_data
        })

    @action(detail=False, methods=['get'], url_path='sub-companies/(?P<company_id>[^/.]+)')
    def get_sub_company_details(self, request, company_id=None):
        """
        Get detailed information about a specific sub-company
        
        Path Parameters:
        - company_id: Sub-company ID
        """
        manager = self._get_manager_employee(request)
        if not manager:
            return Response({
                'success': False,
                'error': 'Manager not found'
            }, status=status.HTTP_404_NOT_FOUND)

        company = self._get_manager_company(manager)
        if not company:
            return Response({
                'success': False,
                'error': 'Company not found'
            }, status=status.HTTP_404_NOT_FOUND)

        # Get sub-company
        try:
            sub_company = Company.objects.get(id=company_id, parent_company=company)
        except Company.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Sub-company not found'
            }, status=status.HTTP_404_NOT_FOUND)

        # Get employees
        employees = Employee.objects.filter(sub_company=sub_company)
        active_employees = employees.filter(status='ACTIVE')

        # Employee statistics
        by_department = active_employees.values(
            'officialdetails__department'
        ).annotate(count=Count('id')).order_by('-count')

        by_designation = active_employees.values(
            'officialdetails__designation'
        ).annotate(count=Count('id')).order_by('-count')

        # Salary statistics
        salary_stats = SalaryStructure.objects.filter(
            employee__in=active_employees
        ).aggregate(
            total_payroll=Sum('CTC'),
            avg_salary=Avg('CTC')
        )

        # Sub-manager
        sub_manager = employees.filter(role='Sub-Manager').first()

        return Response({
            'success': True,
            'data': {
                'company': CompanySerializer(sub_company).data,
                'sub_manager': EmployeeSerializer(sub_manager).data if sub_manager else None,
                'statistics': {
                    'total_employees': employees.count(),
                    'active_employees': active_employees.count(),
                    'by_department': list(by_department),
                    'by_designation': list(by_designation),
                    'total_payroll': float(salary_stats['total_payroll'] or 0),
                    'average_salary': float(salary_stats['avg_salary'] or 0),
                }
            }
        })

    # ==================== REPORTS & ANALYTICS ====================
    
    @action(detail=False, methods=['get'], url_path='reports/department-wise')
    def department_wise_report(self, request):
        """
        Get department-wise comprehensive report
        
        Query Parameters:
        - month (optional): Month for report (1-12)
        - year (optional): Year for report
        - include_sub_companies (optional): Include sub-company data (default: true)
        """
        manager = self._get_manager_employee(request)
        if not manager:
            return Response({
                'success': False,
                'error': 'Manager not found'
            }, status=status.HTTP_404_NOT_FOUND)

        company = self._get_manager_company(manager)
        if not company:
            return Response({
                'success': False,
                'error': 'Company not found'
            }, status=status.HTTP_404_NOT_FOUND)

        # Get parameters
        month = int(request.query_params.get('month', timezone.now().month))
        year = int(request.query_params.get('year', timezone.now().year))
        include_sub = request.query_params.get('include_sub_companies', 'true').lower() == 'true'

        # Date range
        start_date = datetime(year, month, 1).date()
        if month == 12:
            end_date = datetime(year + 1, 1, 1).date() - timedelta(days=1)
        else:
            end_date = datetime(year, month + 1, 1).date() - timedelta(days=1)

        # Get employees
        employees = self._get_company_employees(company, include_sub_companies=include_sub)

        # Get all departments
        departments = employees.values_list('officialdetails__department', flat=True).distinct()

        department_reports = []
        for department in departments:
            if not department:
                continue

            dept_employees = employees.filter(officialdetails__department=department)
            active_dept_employees = dept_employees.filter(status='ACTIVE')

            # Attendance stats
            attendance_stats = Attendance.objects.filter(
                employee__in=active_dept_employees,
                date__range=[start_date, end_date]
            ).aggregate(
                present=Count('id', filter=Q(status='P')),
                absent=Count('id', filter=Q(status='A'))
            )

            # Salary stats
            salary_stats = SalaryStructure.objects.filter(
                employee__in=active_dept_employees
            ).aggregate(
                total_payroll=Sum('CTC'),
                avg_salary=Avg('CTC')
            )

            department_reports.append({
                'department': department,
                'total_employees': dept_employees.count(),
                'active_employees': active_dept_employees.count(),
                'attendance': {
                    'present': attendance_stats['present'] or 0,
                    'absent': attendance_stats['absent'] or 0,
                },
                'salary': {
                    'total_payroll': float(salary_stats['total_payroll'] or 0),
                    'average_salary': float(salary_stats['avg_salary'] or 0),
                }
            })

        return Response({
            'success': True,
            'data': {
                'month': month,
                'year': year,
                'departments': department_reports
            }
        })

    @action(detail=False, methods=['get'], url_path='reports/monthly-summary')
    def monthly_summary_report(self, request):
        """
        Get comprehensive monthly summary report
        
        Query Parameters:
        - month: Month for report (1-12, required)
        - year: Year for report (required)
        - include_sub_companies (optional): Include sub-company data (default: true)
        """
        manager = self._get_manager_employee(request)
        if not manager:
            return Response({
                'success': False,
                'error': 'Manager not found'
            }, status=status.HTTP_404_NOT_FOUND)

        company = self._get_manager_company(manager)
        if not company:
            return Response({
                'success': False,
                'error': 'Company not found'
            }, status=status.HTTP_404_NOT_FOUND)

        # Get parameters
        try:
            month = int(request.query_params.get('month'))
            year = int(request.query_params.get('year'))
        except (TypeError, ValueError):
            return Response({
                'success': False,
                'error': 'Month and year are required'
            }, status=status.HTTP_400_BAD_REQUEST)

        include_sub = request.query_params.get('include_sub_companies', 'true').lower() == 'true'

        # Date range
        start_date = datetime(year, month, 1).date()
        if month == 12:
            end_date = datetime(year + 1, 1, 1).date() - timedelta(days=1)
        else:
            end_date = datetime(year, month + 1, 1).date() - timedelta(days=1)

        # Get employees
        employees = self._get_company_employees(company, include_sub_companies=include_sub)
        active_employees = employees.filter(status='ACTIVE')

        # Attendance summary
        attendance_stats = Attendance.objects.filter(
            employee__in=active_employees,
            date__range=[start_date, end_date]
        ).aggregate(
            total_records=Count('id'),
            present=Count('id', filter=Q(status='P')),
            absent=Count('id', filter=Q(status='A')),
            weekly_off=Count('id', filter=Q(status='WO')),
            holiday=Count('id', filter=Q(status='H')),
            half_day=Count('id', filter=Q(status='HD'))
        )

        # Overtime summary
        overtime_stats = OvertimeRecord.objects.filter(
            employee__in=active_employees,
            date__range=[start_date, end_date]
        ).aggregate(
            total_hours=Sum('hours'),
            total_records=Count('id')
        )

        # Payslip summary
        payslip_stats = Payslip.objects.filter(
            employee__in=active_employees,
            month=month,
            year=year
        ).aggregate(
            total_gross=Sum('gross_salary'),
            total_net=Sum('net_salary'),
            total_deductions=Sum('total_deductions'),
            payslips_generated=Count('id')
        )

        # New joinings in the month
        new_joinings = employees.filter(
            officialdetails__date_of_joining__range=[start_date, end_date]
        ).count()

        # Employees who left in the month
        # Assuming there's a field or we can track this
        employees_left = 0  # Update this based on your tracking mechanism

        return Response({
            'success': True,
            'data': {
                'month': month,
                'year': year,
                'employees': {
                    'total': employees.count(),
                    'active': active_employees.count(),
                    'new_joinings': new_joinings,
                    'employees_left': employees_left,
                },
                'attendance': attendance_stats,
                'overtime': {
                    'total_hours': float(overtime_stats['total_hours'] or 0),
                    'total_records': overtime_stats['total_records'] or 0,
                },
                'payroll': {
                    'total_gross_salary': float(payslip_stats['total_gross'] or 0),
                    'total_net_salary': float(payslip_stats['total_net'] or 0),
                    'total_deductions': float(payslip_stats['total_deductions'] or 0),
                    'payslips_generated': payslip_stats['payslips_generated'] or 0,
                }
            }
        })

    @action(detail=False, methods=['get'], url_path='analytics/trends')
    def get_analytics_trends(self, request):
        """
        Get analytics trends for the last 6 months
        
        Query Parameters:
        - include_sub_companies (optional): Include sub-company data (default: true)
        """
        manager = self._get_manager_employee(request)
        if not manager:
            return Response({
                'success': False,
                'error': 'Manager not found'
            }, status=status.HTTP_404_NOT_FOUND)

        company = self._get_manager_company(manager)
        if not company:
            return Response({
                'success': False,
                'error': 'Company not found'
            }, status=status.HTTP_404_NOT_FOUND)

        include_sub = request.query_params.get('include_sub_companies', 'true').lower() == 'true'
        employees = self._get_company_employees(company, include_sub_companies=include_sub)

        # Get last 6 months
        current_date = timezone.now().date()
        trends = []

        for i in range(5, -1, -1):
            # Calculate month and year
            target_date = current_date - timedelta(days=30 * i)
            month = target_date.month
            year = target_date.year

            # Date range
            start_date = datetime(year, month, 1).date()
            if month == 12:
                end_date = datetime(year + 1, 1, 1).date() - timedelta(days=1)
            else:
                end_date = datetime(year, month + 1, 1).date() - timedelta(days=1)

            # Employee count at that time
            employee_count = employees.filter(status='ACTIVE').count()

            # Attendance stats
            attendance_stats = Attendance.objects.filter(
                employee__in=employees,
                date__range=[start_date, end_date]
            ).aggregate(
                present=Count('id', filter=Q(status='P')),
                absent=Count('id', filter=Q(status='A'))
            )

            total_records = attendance_stats['present'] + attendance_stats['absent']
            attendance_rate = (
                (attendance_stats['present'] / total_records * 100)
                if total_records > 0 else 0
            )

            # Payroll stats
            payroll_stats = Payslip.objects.filter(
                employee__in=employees,
                month=month,
                year=year
            ).aggregate(
                total_payroll=Sum('net_salary')
            )

            trends.append({
                'month': month,
                'year': year,
                'month_name': datetime(year, month, 1).strftime('%B %Y'),
                'employee_count': employee_count,
                'attendance_rate': round(attendance_rate, 2),
                'total_payroll': float(payroll_stats['total_payroll'] or 0),
            })

        return Response({
            'success': True,
            'data': {
                'trends': trends
            }
        })
