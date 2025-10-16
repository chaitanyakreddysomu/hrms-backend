"""
Admin Dashboard APIs for complete system management
Includes: System overview, all companies, all employees, system-wide analytics, user management
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


class IsAdmin(permissions.BasePermission):
    """
    Custom permission for Admin role
    """
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        try:
            employee = Employee.objects.get(
                Q(employee_code=request.user.username) | Q(email=request.user.email)
            )
            return employee.role == 'Admin'
        except Employee.DoesNotExist:
            return False


class AdminDashboardViewSet(viewsets.ViewSet):
    """
    Admin Dashboard ViewSet for complete system management
    
    Features:
    - System Overview & Statistics
    - Complete Company Management (Main & Sub)
    - All Employee Management
    - System-wide Attendance Tracking
    - Complete Salary & Payroll Management
    - System-wide Analytics & Reports
    - User & Role Management
    - System Configuration
    
    Access: Admin Role ONLY
    """
    permission_classes = [IsAdmin]

    def _get_admin_employee(self, request):
        """Helper method to get admin's employee record"""
        try:
            return Employee.objects.get(
                Q(employee_code=request.user.username) | Q(email=request.user.email)
            )
        except Employee.DoesNotExist:
            return None

    # ==================== SYSTEM OVERVIEW ====================
    
    @action(detail=False, methods=['get'], url_path='system-overview')
    def system_overview(self, request):
        """
        Get comprehensive system overview with all statistics
        
        Query Parameters:
        - month (optional): Month for statistics (1-12)
        - year (optional): Year for statistics
        
        Returns:
        - Complete system statistics
        - All companies overview
        - Total employees across system
        - System-wide attendance
        - Total payroll
        - Recent activities
        """
        admin = self._get_admin_employee(request)
        if not admin:
            return Response({
                'success': False,
                'error': 'Admin employee record not found'
            }, status=status.HTTP_404_NOT_FOUND)

        # Get parameters
        month = int(request.query_params.get('month', timezone.now().month))
        year = int(request.query_params.get('year', timezone.now().year))

        # All companies statistics
        total_companies = Company.objects.count()
        main_companies = Company.objects.filter(is_main_company=True).count()
        sub_companies = Company.objects.filter(is_main_company=False).count()

        # All employees statistics
        all_employees = Employee.objects.all()
        active_employees = all_employees.filter(status='ACTIVE')

        # Employee statistics by role
        by_role = active_employees.values('role').annotate(count=Count('id')).order_by('-count')

        # Employee statistics by department
        by_department = active_employees.values(
            'officialdetails__department'
        ).annotate(count=Count('id')).order_by('-count')[:10]

        # Date range for monthly stats
        start_date = datetime(year, month, 1).date()
        if month == 12:
            end_date = datetime(year + 1, 1, 1).date() - timedelta(days=1)
        else:
            end_date = datetime(year, month + 1, 1).date() - timedelta(days=1)

        # System-wide attendance statistics
        attendance_stats = Attendance.objects.filter(
            date__range=[start_date, end_date]
        ).aggregate(
            total_records=Count('id'),
            present=Count('id', filter=Q(status='P')),
            absent=Count('id', filter=Q(status='A')),
            weekly_off=Count('id', filter=Q(status='WO')),
            holiday=Count('id', filter=Q(status='H')),
            half_day=Count('id', filter=Q(status='HD'))
        )

        total_att_records = attendance_stats['total_records'] or 0
        attendance_percentage = (
            (attendance_stats['present'] / total_att_records * 100)
            if total_att_records > 0 else 0
        )

        # System-wide overtime statistics
        overtime_stats = OvertimeRecord.objects.filter(
            date__range=[start_date, end_date]
        ).aggregate(
            total_hours=Sum('hours'),
            records_count=Count('id')
        )

        # System-wide salary statistics
        salary_stats = SalaryStructure.objects.all().aggregate(
            total_payroll=Sum('CTC'),
            avg_salary=Avg('CTC'),
            min_salary=Min('CTC'),
            max_salary=Max('CTC')
        )

        # System-wide payslip statistics for the month
        payslip_stats = Payslip.objects.filter(
            month=month,
            year=year
        ).aggregate(
            total_gross=Sum('gross_salary'),
            total_net=Sum('net_salary'),
            total_deductions=Sum('deductions'),
            count=Count('id')
        )

        # Recent joinings (last 30 days)
        thirty_days_ago = timezone.now().date() - timedelta(days=30)
        recent_joinings = all_employees.filter(
            officialdetails__date_of_joining__gte=thirty_days_ago
        ).count()

        # Top companies by employee count
        top_companies = []
        for company in Company.objects.all()[:10]:
            emp_count = Employee.objects.filter(
                Q(main_company=company) | Q(sub_company=company)
            ).count()
            if emp_count > 0:
                top_companies.append({
                    'id': company.id,
                    'name': company.name,
                    'is_main_company': company.is_main_company,
                    'employee_count': emp_count
                })
        
        top_companies.sort(key=lambda x: x['employee_count'], reverse=True)

        return Response({
            'success': True,
            'admin': {
                'id': admin.id,
                'name': admin.full_name,
                'employee_code': admin.employee_code,
            },
            'data': {
                'companies': {
                    'total': total_companies,
                    'main_companies': main_companies,
                    'sub_companies': sub_companies,
                    'top_companies': top_companies[:5]
                },
                'employees': {
                    'total': all_employees.count(),
                    'active': active_employees.count(),
                    'inactive': all_employees.exclude(status='ACTIVE').count(),
                    'recent_joinings': recent_joinings,
                    'by_role': list(by_role),
                    'by_department': list(by_department),
                },
                'attendance': {
                    'month': month,
                    'year': year,
                    'total_records': total_att_records,
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
                'payroll': {
                    'month': month,
                    'year': year,
                    'total_gross': float(payslip_stats['total_gross'] or 0),
                    'total_net': float(payslip_stats['total_net'] or 0),
                    'total_deductions': float(payslip_stats['total_deductions'] or 0),
                    'payslips_count': payslip_stats['count'] or 0,
                }
            }
        })

    # ==================== COMPANY MANAGEMENT ====================
    
    @action(detail=False, methods=['get'], url_path='companies')
    def list_companies(self, request):
        """
        Get list of all companies (main and sub)
        
        Query Parameters:
        - is_main_company (optional): Filter by company type (true/false)
        - search (optional): Search by company name
        """
        admin = self._get_admin_employee(request)
        if not admin:
            return Response({
                'success': False,
                'error': 'Admin not found'
            }, status=status.HTTP_404_NOT_FOUND)

        # Get parameters
        is_main = request.query_params.get('is_main_company')
        search = request.query_params.get('search')

        # Build query
        companies = Company.objects.all()

        if is_main is not None:
            is_main_bool = is_main.lower() == 'true'
            companies = companies.filter(is_main_company=is_main_bool)

        if search:
            companies = companies.filter(name__icontains=search)

        # Add employee counts
        companies_data = []
        for company in companies:
            emp_count = Employee.objects.filter(
                Q(main_company=company) | Q(sub_company=company)
            ).count()
            active_emp_count = Employee.objects.filter(
                Q(main_company=company) | Q(sub_company=company),
                status='ACTIVE'
            ).count()

            company_dict = CompanySerializer(company).data
            company_dict['employee_count'] = emp_count
            company_dict['active_employee_count'] = active_emp_count
            companies_data.append(company_dict)

        return Response({
            'success': True,
            'data': companies_data,
            'total': len(companies_data)
        })

    @action(detail=False, methods=['get'], url_path='companies/(?P<company_id>[^/.]+)')
    def get_company_details(self, request, company_id=None):
        """
        Get detailed information about a specific company
        
        Path Parameters:
        - company_id: Company ID
        
        Returns:
        - Company details
        - Employee statistics
        - Salary statistics
        - Department breakdown
        """
        admin = self._get_admin_employee(request)
        if not admin:
            return Response({
                'success': False,
                'error': 'Admin not found'
            }, status=status.HTTP_404_NOT_FOUND)

        try:
            company = Company.objects.get(id=company_id)
        except Company.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Company not found'
            }, status=status.HTTP_404_NOT_FOUND)

        # Get employees
        employees = Employee.objects.filter(
            Q(main_company=company) | Q(sub_company=company)
        )
        active_employees = employees.filter(status='ACTIVE')

        # Statistics by department
        by_department = active_employees.values(
            'officialdetails__department'
        ).annotate(count=Count('id')).order_by('-count')

        # Statistics by role
        by_role = active_employees.values('role').annotate(count=Count('id')).order_by('-count')

        # Salary statistics
        salary_stats = SalaryStructure.objects.filter(
            employee__in=active_employees
        ).aggregate(
            total_payroll=Sum('CTC'),
            avg_salary=Avg('CTC')
        )

        # Sub-companies if main company
        sub_companies_data = []
        if company.is_main_company:
            sub_companies = Company.objects.filter(parent_company=company)
            for sub in sub_companies:
                sub_emp_count = Employee.objects.filter(sub_company=sub).count()
                sub_companies_data.append({
                    'id': sub.id,
                    'name': sub.name,
                    'employee_count': sub_emp_count
                })

        return Response({
            'success': True,
            'data': {
                'company': CompanySerializer(company).data,
                'statistics': {
                    'total_employees': employees.count(),
                    'active_employees': active_employees.count(),
                    'by_department': list(by_department),
                    'by_role': list(by_role),
                    'total_payroll': float(salary_stats['total_payroll'] or 0),
                    'average_salary': float(salary_stats['avg_salary'] or 0),
                },
                'sub_companies': sub_companies_data if company.is_main_company else None
            }
        })

    # ==================== EMPLOYEE MANAGEMENT ====================
    
    @action(detail=False, methods=['get'], url_path='employees')
    def list_employees(self, request):
        """
        Get list of all employees across all companies
        
        Query Parameters:
        - company_id (optional): Filter by specific company
        - department (optional): Filter by department
        - designation (optional): Filter by designation
        - role (optional): Filter by role
        - status (optional): Filter by status (ACTIVE, INACTIVE, LEFT)
        - search (optional): Search by name, email, or employee code
        - page (optional): Page number
        - page_size (optional): Items per page (default: 50)
        """
        admin = self._get_admin_employee(request)
        if not admin:
            return Response({
                'success': False,
                'error': 'Admin not found'
            }, status=status.HTTP_404_NOT_FOUND)

        # Get parameters
        company_id = request.query_params.get('company_id')
        department = request.query_params.get('department')
        designation = request.query_params.get('designation')
        role = request.query_params.get('role')
        emp_status = request.query_params.get('status')
        search = request.query_params.get('search')

        # Build query
        employees = Employee.objects.all()

        if company_id:
            employees = employees.filter(
                Q(main_company_id=company_id) | Q(sub_company_id=company_id)
            )

        if department:
            employees = employees.filter(officialdetails__department=department)

        if designation:
            employees = employees.filter(officialdetails__designation=designation)

        if role:
            employees = employees.filter(role=role)

        if emp_status:
            employees = employees.filter(status=emp_status)

        if search:
            employees = employees.filter(
                Q(full_name__icontains=search) |
                Q(email__icontains=search) |
                Q(employee_code__icontains=search)
            )

        # Pagination
        page = int(request.query_params.get('page', 1))
        page_size = int(request.query_params.get('page_size', 50))
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
        Get complete detailed information about a specific employee
        
        Path Parameters:
        - employee_id: Employee ID
        """
        admin = self._get_admin_employee(request)
        if not admin:
            return Response({
                'success': False,
                'error': 'Admin not found'
            }, status=status.HTTP_404_NOT_FOUND)

        try:
            employee = Employee.objects.get(id=employee_id)
        except Employee.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Employee not found'
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
        ).order_by('-year', '-month')[:6]

        # Documents
        documents = Document.objects.filter(employee=employee)

        return Response({
            'success': True,
            'data': {
                'employee': EmployeeSerializer(employee).data,
                'official_details': OfficialDetailsSerializer(official_details).data if official_details else None,
                'salary_structure': SalaryStructureSerializer(salary_structure).data if salary_structure else None,
                'recent_attendance': AttendanceSerializer(recent_attendance, many=True).data,
                'recent_payslips': PayslipSerializer(recent_payslips, many=True).data,
                'documents_count': documents.count(),
            }
        })

    # ==================== ATTENDANCE MANAGEMENT ====================
    
    @action(detail=False, methods=['get'], url_path='attendance')
    def get_attendance(self, request):
        """
        Get system-wide attendance records
        
        Query Parameters:
        - employee_id (optional): Filter by specific employee
        - company_id (optional): Filter by specific company
        - department (optional): Filter by department
        - date_from (optional): Start date (YYYY-MM-DD)
        - date_to (optional): End date (YYYY-MM-DD)
        - status (optional): Filter by status (P, A, WO, H, HD)
        - page (optional): Page number
        - page_size (optional): Items per page (default: 100)
        """
        admin = self._get_admin_employee(request)
        if not admin:
            return Response({
                'success': False,
                'error': 'Admin not found'
            }, status=status.HTTP_404_NOT_FOUND)

        # Get parameters
        employee_id = request.query_params.get('employee_id')
        company_id = request.query_params.get('company_id')
        department = request.query_params.get('department')
        date_from = request.query_params.get('date_from')
        date_to = request.query_params.get('date_to')
        att_status = request.query_params.get('status')

        # Build query
        attendance_query = Attendance.objects.all()

        if employee_id:
            attendance_query = attendance_query.filter(employee_id=employee_id)

        if company_id:
            attendance_query = attendance_query.filter(
                Q(employee__main_company_id=company_id) | 
                Q(employee__sub_company_id=company_id)
            )

        if department:
            attendance_query = attendance_query.filter(
                employee__officialdetails__department=department
            )

        if date_from:
            attendance_query = attendance_query.filter(date__gte=date_from)

        if date_to:
            attendance_query = attendance_query.filter(date__lte=date_to)

        if att_status:
            attendance_query = attendance_query.filter(status=att_status)

        attendance_query = attendance_query.order_by('-date')

        # Pagination
        page = int(request.query_params.get('page', 1))
        page_size = int(request.query_params.get('page_size', 100))
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

    @action(detail=False, methods=['get'], url_path='attendance/statistics')
    def attendance_statistics(self, request):
        """
        Get system-wide attendance statistics
        
        Query Parameters:
        - month: Month (1-12, required)
        - year: Year (required)
        - company_id (optional): Filter by specific company
        - department (optional): Filter by department
        """
        admin = self._get_admin_employee(request)
        if not admin:
            return Response({
                'success': False,
                'error': 'Admin not found'
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

        company_id = request.query_params.get('company_id')
        department = request.query_params.get('department')

        # Date range
        start_date = datetime(year, month, 1).date()
        if month == 12:
            end_date = datetime(year + 1, 1, 1).date() - timedelta(days=1)
        else:
            end_date = datetime(year, month + 1, 1).date() - timedelta(days=1)

        # Build query
        employees = Employee.objects.filter(status='ACTIVE')

        if company_id:
            employees = employees.filter(
                Q(main_company_id=company_id) | Q(sub_company_id=company_id)
            )

        if department:
            employees = employees.filter(officialdetails__department=department)

        # Overall statistics
        overall_stats = Attendance.objects.filter(
            employee__in=employees,
            date__range=[start_date, end_date]
        ).aggregate(
            total_records=Count('id'),
            present=Count('id', filter=Q(status='P')),
            absent=Count('id', filter=Q(status='A')),
            weekly_off=Count('id', filter=Q(status='WO')),
            holiday=Count('id', filter=Q(status='H')),
            half_day=Count('id', filter=Q(status='HD'))
        )

        # Statistics by department
        dept_stats = []
        departments = employees.values_list('officialdetails__department', flat=True).distinct()
        
        for dept in departments:
            if not dept:
                continue
                
            dept_employees = employees.filter(officialdetails__department=dept)
            dept_attendance = Attendance.objects.filter(
                employee__in=dept_employees,
                date__range=[start_date, end_date]
            ).aggregate(
                present=Count('id', filter=Q(status='P')),
                absent=Count('id', filter=Q(status='A')),
                total=Count('id')
            )
            
            dept_stats.append({
                'department': dept,
                'employee_count': dept_employees.count(),
                'present': dept_attendance['present'] or 0,
                'absent': dept_attendance['absent'] or 0,
                'total_records': dept_attendance['total'] or 0,
            })

        return Response({
            'success': True,
            'data': {
                'month': month,
                'year': year,
                'overall': overall_stats,
                'by_department': dept_stats
            }
        })

    # ==================== SALARY & PAYROLL ====================
    
    @action(detail=False, methods=['get'], url_path='salary-structures')
    def get_salary_structures(self, request):
        """
        Get system-wide salary structures
        
        Query Parameters:
        - employee_id (optional): Filter by specific employee
        - company_id (optional): Filter by specific company
        - department (optional): Filter by department
        - min_salary (optional): Minimum CTC
        - max_salary (optional): Maximum CTC
        - page (optional): Page number
        - page_size (optional): Items per page (default: 50)
        """
        admin = self._get_admin_employee(request)
        if not admin:
            return Response({
                'success': False,
                'error': 'Admin not found'
            }, status=status.HTTP_404_NOT_FOUND)

        # Get parameters
        employee_id = request.query_params.get('employee_id')
        company_id = request.query_params.get('company_id')
        department = request.query_params.get('department')
        min_salary = request.query_params.get('min_salary')
        max_salary = request.query_params.get('max_salary')

        # Build query
        salary_query = SalaryStructure.objects.all()

        if employee_id:
            salary_query = salary_query.filter(employee_id=employee_id)

        if company_id:
            salary_query = salary_query.filter(
                Q(employee__main_company_id=company_id) | 
                Q(employee__sub_company_id=company_id)
            )

        if department:
            salary_query = salary_query.filter(
                employee__officialdetails__department=department
            )

        if min_salary:
            salary_query = salary_query.filter(CTC__gte=float(min_salary))

        if max_salary:
            salary_query = salary_query.filter(CTC__lte=float(max_salary))

        # Pagination
        page = int(request.query_params.get('page', 1))
        page_size = int(request.query_params.get('page_size', 50))
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
        Get system-wide payslips
        
        Query Parameters:
        - employee_id (optional): Filter by specific employee
        - company_id (optional): Filter by specific company
        - month (optional): Filter by month (1-12)
        - year (optional): Filter by year
        - department (optional): Filter by department
        - page (optional): Page number
        - page_size (optional): Items per page (default: 100)
        """
        admin = self._get_admin_employee(request)
        if not admin:
            return Response({
                'success': False,
                'error': 'Admin not found'
            }, status=status.HTTP_404_NOT_FOUND)

        # Get parameters
        employee_id = request.query_params.get('employee_id')
        company_id = request.query_params.get('company_id')
        month = request.query_params.get('month')
        year = request.query_params.get('year')
        department = request.query_params.get('department')

        # Build query
        payslip_query = Payslip.objects.all()

        if employee_id:
            payslip_query = payslip_query.filter(employee_id=employee_id)

        if company_id:
            payslip_query = payslip_query.filter(
                Q(employee__main_company_id=company_id) | 
                Q(employee__sub_company_id=company_id)
            )

        if month:
            payslip_query = payslip_query.filter(month=int(month))

        if year:
            payslip_query = payslip_query.filter(year=int(year))

        if department:
            payslip_query = payslip_query.filter(
                employee__officialdetails__department=department
            )

        payslip_query = payslip_query.order_by('-year', '-month')

        # Pagination
        page = int(request.query_params.get('page', 1))
        page_size = int(request.query_params.get('page_size', 100))
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

    # ==================== REPORTS & ANALYTICS ====================
    
    @action(detail=False, methods=['get'], url_path='reports/company-wise')
    def company_wise_report(self, request):
        """
        Get company-wise comprehensive report
        
        Query Parameters:
        - month (optional): Month for report (1-12)
        - year (optional): Year for report
        """
        admin = self._get_admin_employee(request)
        if not admin:
            return Response({
                'success': False,
                'error': 'Admin not found'
            }, status=status.HTTP_404_NOT_FOUND)

        # Get parameters
        month = int(request.query_params.get('month', timezone.now().month))
        year = int(request.query_params.get('year', timezone.now().year))

        # Date range
        start_date = datetime(year, month, 1).date()
        if month == 12:
            end_date = datetime(year + 1, 1, 1).date() - timedelta(days=1)
        else:
            end_date = datetime(year, month + 1, 1).date() - timedelta(days=1)

        companies_report = []
        for company in Company.objects.all():
            employees = Employee.objects.filter(
                Q(main_company=company) | Q(sub_company=company)
            )
            active_employees = employees.filter(status='ACTIVE')

            # Attendance stats
            attendance_stats = Attendance.objects.filter(
                employee__in=active_employees,
                date__range=[start_date, end_date]
            ).aggregate(
                present=Count('id', filter=Q(status='P')),
                absent=Count('id', filter=Q(status='A'))
            )

            # Salary stats
            salary_stats = SalaryStructure.objects.filter(
                employee__in=active_employees
            ).aggregate(
                total_payroll=Sum('CTC'),
                avg_salary=Avg('CTC')
            )

            # Payslip stats
            payslip_stats = Payslip.objects.filter(
                employee__in=active_employees,
                month=month,
                year=year
            ).aggregate(
                total_net=Sum('net_salary')
            )

            companies_report.append({
                'company_id': company.id,
                'company_name': company.name,
                'is_main_company': company.is_main_company,
                'total_employees': employees.count(),
                'active_employees': active_employees.count(),
                'attendance': {
                    'present': attendance_stats['present'] or 0,
                    'absent': attendance_stats['absent'] or 0,
                },
                'salary': {
                    'total_payroll': float(salary_stats['total_payroll'] or 0),
                    'average_salary': float(salary_stats['avg_salary'] or 0),
                },
                'payroll_paid': float(payslip_stats['total_net'] or 0)
            })

        return Response({
            'success': True,
            'data': {
                'month': month,
                'year': year,
                'companies': companies_report
            }
        })

    @action(detail=False, methods=['get'], url_path='reports/role-wise')
    def role_wise_report(self, request):
        """
        Get role-wise employee distribution and statistics
        """
        admin = self._get_admin_employee(request)
        if not admin:
            return Response({
                'success': False,
                'error': 'Admin not found'
            }, status=status.HTTP_404_NOT_FOUND)

        role_stats = []
        roles = Employee.objects.values_list('role', flat=True).distinct()

        for role in roles:
            role_employees = Employee.objects.filter(role=role)
            active_role_employees = role_employees.filter(status='ACTIVE')

            salary_stats = SalaryStructure.objects.filter(
                employee__in=active_role_employees
            ).aggregate(
                total_payroll=Sum('CTC'),
                avg_salary=Avg('CTC')
            )

            role_stats.append({
                'role': role,
                'total_count': role_employees.count(),
                'active_count': active_role_employees.count(),
                'total_payroll': float(salary_stats['total_payroll'] or 0),
                'average_salary': float(salary_stats['avg_salary'] or 0),
            })

        return Response({
            'success': True,
            'data': {
                'roles': role_stats
            }
        })

    @action(detail=False, methods=['get'], url_path='analytics/trends')
    def get_analytics_trends(self, request):
        """
        Get system-wide analytics trends for the last 12 months
        
        Returns:
        - Monthly employee count trends
        - Monthly attendance trends
        - Monthly payroll trends
        """
        admin = self._get_admin_employee(request)
        if not admin:
            return Response({
                'success': False,
                'error': 'Admin not found'
            }, status=status.HTTP_404_NOT_FOUND)

        current_date = timezone.now().date()
        trends = []

        for i in range(11, -1, -1):
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

            # Employee count
            employee_count = Employee.objects.filter(status='ACTIVE').count()

            # Attendance stats
            attendance_stats = Attendance.objects.filter(
                date__range=[start_date, end_date]
            ).aggregate(
                present=Count('id', filter=Q(status='P')),
                total=Count('id')
            )

            attendance_rate = (
                (attendance_stats['present'] / attendance_stats['total'] * 100)
                if attendance_stats['total'] > 0 else 0
            )

            # Payroll stats
            payroll_stats = Payslip.objects.filter(
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

    @action(detail=False, methods=['get'], url_path='analytics/dashboard-stats')
    def dashboard_stats(self, request):
        """
        Get quick dashboard statistics for admin panel
        """
        admin = self._get_admin_employee(request)
        if not admin:
            return Response({
                'success': False,
                'error': 'Admin not found'
            }, status=status.HTTP_404_NOT_FOUND)

        # Today's date
        today = timezone.now().date()
        current_month = today.month
        current_year = today.year

        # Company stats
        total_main_companies = Company.objects.filter(is_main_company=True).count()
        total_sub_companies = Company.objects.filter(is_main_company=False).count()
        
        # Employee stats by role
        hr_count = Employee.objects.filter(role='HR').count()
        supervisor_count = Employee.objects.filter(role='Supervisor').count()
        employee_count = Employee.objects.filter(role='Employee').count()
        manager_count = Employee.objects.filter(role='Manager').count()
        sub_manager_count = Employee.objects.filter(role='Sub-Manager').count()
        accounts_count = Employee.objects.filter(role='Accounts').count()

        # Quick stats
        stats = {
            # Company breakdown
            'total_companies': Company.objects.count(),
            'total_main_companies': total_main_companies,
            'total_sub_companies': total_sub_companies,
            
            # Employee counts by role
            'total_employees': Employee.objects.count(),
            'hr_count': hr_count,
            'supervisor_count': supervisor_count,
            'employee_count': employee_count,
            'manager_count': manager_count,
            'sub_manager_count': sub_manager_count,
            'accounts_count': accounts_count,
            
            # Status counts
            'active_employees': Employee.objects.filter(status='ACTIVE').count(),
            'today_present': Attendance.objects.filter(date=today, status='P').count(),
            'today_absent': Attendance.objects.filter(date=today, status='A').count(),
            
            # Financial stats
            'pending_payslips': Employee.objects.filter(status='ACTIVE').count() - Payslip.objects.filter(month=current_month, year=current_year).count(),
            'total_monthly_payroll': float(SalaryStructure.objects.aggregate(total=Sum('CTC'))['total'] or 0),
        }

        return Response({
            'success': True,
            'data': stats
        })
