"""
Sub-Manager Dashboard APIs for sub-company management
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


class IsSubManager(permissions.BasePermission):
    """
    Custom permission for Sub-Manager role
    """
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        try:
            employee = Employee.objects.get(
                Q(employee_code=request.user.username) | Q(email=request.user.email)
            )
            return employee.role == 'Sub-Manager'
        except Employee.DoesNotExist:
            return False


class SubManagerDashboardViewSet(viewsets.ViewSet):
    """
    Sub-Manager Dashboard ViewSet for sub-company management
    
    Features:
    - Company Overview & Statistics
    - Employee Management
    - Attendance Tracking & Reports
    - Salary Management
    - Payslip Generation
    - Overtime Management
    - Analytics & Reports
    
    Access: Sub-Manager Role ONLY
    """
    permission_classes = [IsSubManager]

    def _get_submanager_employee(self, request):
        """Helper method to get sub-manager's employee record"""
        try:
            return Employee.objects.get(
                Q(employee_code=request.user.username) | Q(email=request.user.email)
            )
        except Employee.DoesNotExist:
            return None

    def _get_submanager_company(self, submanager_employee):
        """Helper method to get sub-manager's company"""
        if not submanager_employee:
            return None
        return submanager_employee.sub_company

    def _get_company_employees(self, company, filters=None):
        """Helper method to get all employees under sub-manager's company"""
        if not company:
            return Employee.objects.none()
        
        queryset = Employee.objects.filter(sub_company=company)
        
        if filters:
            if filters.get('department'):
                queryset = queryset.filter(officialdetails__department=filters['department'])
            if filters.get('designation'):
                queryset = queryset.filter(officialdetails__designation=filters['designation'])
            if filters.get('status'):
                queryset = queryset.filter(status=filters['status'])
        
        return queryset

    # ==================== COMPANY OVERVIEW ====================
    
    @action(detail=False, methods=['get'], url_path='company-overview')
    def company_overview(self, request):
        """
        Get comprehensive overview of sub-company
        
        Query Parameters:
        - month (optional): Month for statistics (1-12)
        - year (optional): Year for statistics
        """
        submanager = self._get_submanager_employee(request)
        if not submanager:
            return Response({
                'success': False,
                'error': 'Sub-Manager employee record not found'
            }, status=status.HTTP_404_NOT_FOUND)

        company = self._get_submanager_company(submanager)
        if not company:
            return Response({
                'success': False,
                'error': 'Sub-company not found'
            }, status=status.HTTP_404_NOT_FOUND)

        # Get month and year from query params
        month = int(request.query_params.get('month', timezone.now().month))
        year = int(request.query_params.get('year', timezone.now().year))

        # Company employees
        all_employees = self._get_company_employees(company)
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

        # Recent joinings (last 30 days)
        thirty_days_ago = timezone.now().date() - timedelta(days=30)
        recent_joinings = all_employees.filter(
            created_at__date__gte=thirty_days_ago
        ).count()

        return Response({
            'success': True,
            'sub_manager': {
                'id': submanager.id,
                'name': submanager.full_name,
                'employee_code': submanager.employee_code,
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
                    'inactive': all_employees.filter(status='INACTIVE').count(),
                    'left': all_employees.filter(status='LEFT').count(),
                    'recent_joinings': recent_joinings,
                    'by_department': list(by_department),
                    'by_designation': list(by_designation),
                },
                'attendance': {
                    'month': month,
                    'year': year,
                    'statistics': attendance_stats,
                    'attendance_percentage': round(attendance_percentage, 2),
                    'total_records': total_attendance_records,
                },
                'overtime': {
                    'month': month,
                    'year': year,
                    'total_hours': float(overtime_stats['total_hours'] or 0),
                    'records_count': overtime_stats['records_count'],
                },
                'salary': {
                    'total_monthly_payroll': float(salary_stats['total_payroll'] or 0),
                    'average_salary': float(salary_stats['avg_salary'] or 0),
                    'min_salary': float(salary_stats['min_salary'] or 0),
                    'max_salary': float(salary_stats['max_salary'] or 0),
                },
            }
        })

    # ==================== EMPLOYEE MANAGEMENT ====================

    @action(detail=False, methods=['get'], url_path='company-employees')
    def company_employees(self, request):
        """
        Get list of all employees in sub-company
        
        Query Parameters:
        - department (optional): Filter by department
        - designation (optional): Filter by designation
        - status (optional): Filter by status (ACTIVE/INACTIVE/LEFT)
        """
        submanager = self._get_submanager_employee(request)
        if not submanager:
            return Response({
                'success': False,
                'error': 'Sub-Manager employee record not found'
            }, status=status.HTTP_404_NOT_FOUND)

        company = self._get_submanager_company(submanager)
        if not company:
            return Response({
                'success': False,
                'error': 'Sub-company not found'
            }, status=status.HTTP_404_NOT_FOUND)

        filters = {
            'department': request.query_params.get('department'),
            'designation': request.query_params.get('designation'),
            'status': request.query_params.get('status'),
        }

        employees = self._get_company_employees(company, filters)

        employees_data = []
        for emp in employees:
            official_details = OfficialDetails.objects.filter(employee=emp).first()
            employees_data.append({
                'employee_id': emp.id,
                'employee_code': emp.employee_code,
                'full_name': emp.full_name,
                'email': emp.email,
                'mobile_number': emp.mobile_number,
                'role': emp.role,
                'department': official_details.department if official_details else 'N/A',
                'designation': official_details.designation if official_details else 'N/A',
                'date_of_joining': official_details.date_of_joining if official_details else None,
                'status': emp.status,
            })

        return Response({
            'success': True,
            'sub_manager': {
                'id': submanager.id,
                'name': submanager.full_name,
            },
            'company': {
                'id': company.id,
                'name': company.name,
            },
            'total_employees': len(employees_data),
            'employees': employees_data,
        })

    @action(detail=False, methods=['get'], url_path='employee-details')
    def employee_details(self, request):
        """
        Get detailed information about a specific employee
        
        Query Parameters:
        - employee_id (required): Employee ID
        """
        submanager = self._get_submanager_employee(request)
        if not submanager:
            return Response({
                'success': False,
                'error': 'Sub-Manager employee record not found'
            }, status=status.HTTP_404_NOT_FOUND)

        company = self._get_submanager_company(submanager)
        employee_id = request.query_params.get('employee_id')

        if not employee_id:
            return Response({
                'success': False,
                'error': 'employee_id is required'
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            employee = Employee.objects.get(id=employee_id, sub_company=company)
        except Employee.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Employee not found or not in your company'
            }, status=status.HTTP_404_NOT_FOUND)

        # Get all related information
        official_details = OfficialDetails.objects.filter(employee=employee).first()
        salary_structure = SalaryStructure.objects.filter(employee=employee).first()
        
        # Recent attendance (last 30 days)
        thirty_days_ago = timezone.now().date() - timedelta(days=30)
        recent_attendance = Attendance.objects.filter(
            employee=employee,
            date__gte=thirty_days_ago
        ).values('date', 'status').order_by('-date')[:30]

        # Overtime records (last 30 days)
        recent_overtime = OvertimeRecord.objects.filter(
            employee=employee,
            date__gte=thirty_days_ago
        ).aggregate(total_hours=Sum('hours'))

        return Response({
            'success': True,
            'employee': {
                'id': employee.id,
                'employee_code': employee.employee_code,
                'full_name': employee.full_name,
                'email': employee.email,
                'mobile_number': employee.mobile_number,
                'role': employee.role,
                'status': employee.status,
                'date_of_birth': employee.date_of_birth,
                'gender': employee.gender,
            },
            'official_details': {
                'department': official_details.department if official_details else None,
                'designation': official_details.designation if official_details else None,
                'date_of_joining': official_details.date_of_joining if official_details else None,
                'supervisor_name': official_details.supervisor_name if official_details else None,
            } if official_details else None,
            'salary': {
                'CTC': float(salary_structure.CTC) if salary_structure else 0,
                'net_salary': float(salary_structure.net_salary) if salary_structure else 0,
            } if salary_structure else None,
            'recent_performance': {
                'attendance_records': list(recent_attendance),
                'overtime_hours': float(recent_overtime['total_hours'] or 0),
            }
        })

    # ==================== ATTENDANCE MANAGEMENT ====================

    @action(detail=False, methods=['post'], url_path='mark-attendance')
    def mark_attendance(self, request):
        """
        Mark attendance for an employee
        
        Request Body:
        - employee_id (required)
        - date (required): YYYY-MM-DD format
        - status (required): P/A/WO/H/HD
        """
        submanager = self._get_submanager_employee(request)
        if not submanager:
            return Response({
                'success': False,
                'error': 'Sub-Manager employee record not found'
            }, status=status.HTTP_404_NOT_FOUND)

        company = self._get_submanager_company(submanager)
        employee_id = request.data.get('employee_id')
        date_str = request.data.get('date')
        attendance_status = request.data.get('status')

        if not all([employee_id, date_str, attendance_status]):
            return Response({
                'success': False,
                'error': 'employee_id, date, and status are required'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Verify employee belongs to company
        try:
            employee = Employee.objects.get(id=employee_id, sub_company=company)
        except Employee.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Employee not found or not in your company'
            }, status=status.HTTP_404_NOT_FOUND)

        # Parse date
        try:
            attendance_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            return Response({
                'success': False,
                'error': 'Invalid date format. Use YYYY-MM-DD'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Create or update attendance
        attendance, created = Attendance.objects.update_or_create(
            employee=employee,
            date=attendance_date,
            defaults={'status': attendance_status}
        )

        serializer = AttendanceSerializer(attendance)
        
        return Response({
            'success': True,
            'message': f"Attendance {'marked' if created else 'updated'} successfully",
            'data': serializer.data,
        }, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)

    @action(detail=False, methods=['post'], url_path='bulk-mark-attendance')
    def bulk_mark_attendance(self, request):
        """
        Mark attendance for multiple employees
        
        Request Body:
        - date (required): YYYY-MM-DD format
        - attendance_records (required): List of {employee_id, status}
        """
        submanager = self._get_submanager_employee(request)
        if not submanager:
            return Response({
                'success': False,
                'error': 'Sub-Manager employee record not found'
            }, status=status.HTTP_404_NOT_FOUND)

        company = self._get_submanager_company(submanager)
        date_str = request.data.get('date')
        attendance_records = request.data.get('attendance_records', [])

        if not date_str or not attendance_records:
            return Response({
                'success': False,
                'error': 'date and attendance_records are required'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Parse date
        try:
            attendance_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            return Response({
                'success': False,
                'error': 'Invalid date format. Use YYYY-MM-DD'
            }, status=status.HTTP_400_BAD_REQUEST)

        created_count = 0
        updated_count = 0
        errors = []

        for record in attendance_records:
            employee_id = record.get('employee_id')
            attendance_status = record.get('status')

            if not employee_id or not attendance_status:
                errors.append({
                    'employee_id': employee_id,
                    'error': 'Missing employee_id or status'
                })
                continue

            # Verify employee belongs to company
            try:
                employee = Employee.objects.get(id=employee_id, sub_company=company)
            except Employee.DoesNotExist:
                errors.append({
                    'employee_id': employee_id,
                    'error': 'Employee not found or not in your company'
                })
                continue

            # Create or update attendance
            _, created = Attendance.objects.update_or_create(
                employee=employee,
                date=attendance_date,
                defaults={'status': attendance_status}
            )

            if created:
                created_count += 1
            else:
                updated_count += 1

        return Response({
            'success': True,
            'message': 'Bulk attendance marking completed',
            'summary': {
                'created': created_count,
                'updated': updated_count,
                'errors': len(errors),
            },
            'errors': errors if errors else None,
        })

    @action(detail=False, methods=['get'], url_path='attendance-report')
    def attendance_report(self, request):
        """
        Get attendance report for company employees
        
        Query Parameters:
        - start_date (required): YYYY-MM-DD
        - end_date (required): YYYY-MM-DD
        - employee_id (optional): Specific employee
        """
        submanager = self._get_submanager_employee(request)
        if not submanager:
            return Response({
                'success': False,
                'error': 'Sub-Manager employee record not found'
            }, status=status.HTTP_404_NOT_FOUND)

        company = self._get_submanager_company(submanager)
        start_date_str = request.query_params.get('start_date')
        end_date_str = request.query_params.get('end_date')
        employee_id = request.query_params.get('employee_id')

        if not start_date_str or not end_date_str:
            return Response({
                'success': False,
                'error': 'start_date and end_date are required'
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        except ValueError:
            return Response({
                'success': False,
                'error': 'Invalid date format. Use YYYY-MM-DD'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Get employees
        employees = self._get_company_employees(company)
        if employee_id:
            employees = employees.filter(id=employee_id)

        report_data = []
        for emp in employees:
            attendance_records = Attendance.objects.filter(
                employee=emp,
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
                (stats['present'] / total_working_days * 100)
                if total_working_days > 0 else 0
            )

            official_details = OfficialDetails.objects.filter(employee=emp).first()

            report_data.append({
                'employee_id': emp.id,
                'employee_code': emp.employee_code,
                'employee_name': emp.full_name,
                'designation': official_details.designation if official_details else 'N/A',
                'statistics': stats,
                'total_working_days': total_working_days,
                'attendance_percentage': round(attendance_percentage, 2),
            })

        return Response({
            'success': True,
            'sub_manager': {
                'id': submanager.id,
                'name': submanager.full_name,
            },
            'company': {
                'id': company.id,
                'name': company.name,
            },
            'period': {
                'start_date': start_date_str,
                'end_date': end_date_str,
            },
            'total_employees': len(report_data),
            'data': report_data,
        })

    # ==================== SALARY MANAGEMENT ====================

    @action(detail=False, methods=['post'], url_path='create-salary-structure')
    def create_salary_structure(self, request):
        """
        Create salary structure for an employee
        
        Request Body:
        - employee_id (required)
        - CTC, basic, da, hra, conveyance, bonus, other_allowances
        - pf_deduction, esi_deduction, pt_deduction, lwf_deduction, insurance, advance
        """
        submanager = self._get_submanager_employee(request)
        if not submanager:
            return Response({
                'success': False,
                'error': 'Sub-Manager employee record not found'
            }, status=status.HTTP_404_NOT_FOUND)

        company = self._get_submanager_company(submanager)
        employee_id = request.data.get('employee_id')

        if not employee_id:
            return Response({
                'success': False,
                'error': 'employee_id is required'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Verify employee belongs to company
        try:
            employee = Employee.objects.get(id=employee_id, sub_company=company)
        except Employee.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Employee not found or not in your company'
            }, status=status.HTTP_404_NOT_FOUND)

        # Check if salary structure already exists
        if SalaryStructure.objects.filter(employee=employee).exists():
            return Response({
                'success': False,
                'error': 'Salary structure already exists for this employee'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Create salary structure
        salary_data = {
            'employee': employee,
            'CTC': Decimal(str(request.data.get('CTC', 0))),
            'basic': Decimal(str(request.data.get('basic', 0))),
            'da': Decimal(str(request.data.get('da', 0))),
            'hra': Decimal(str(request.data.get('hra', 0))),
            'conveyance': Decimal(str(request.data.get('conveyance', 0))),
            'bonus': Decimal(str(request.data.get('bonus', 0))),
            'other_allowances': Decimal(str(request.data.get('other_allowances', 0))),
            'pf_deduction': Decimal(str(request.data.get('pf_deduction', 0))),
            'esi_deduction': Decimal(str(request.data.get('esi_deduction', 0))),
            'pt_deduction': Decimal(str(request.data.get('pt_deduction', 0))),
            'lwf_deduction': Decimal(str(request.data.get('lwf_deduction', 0))),
            'insurance': Decimal(str(request.data.get('insurance', 0))),
            'advance': Decimal(str(request.data.get('advance', 0))),
        }

        # Calculate net salary
        total_earnings = (salary_data['basic'] + salary_data['da'] + salary_data['hra'] + 
                         salary_data['conveyance'] + salary_data['bonus'] + salary_data['other_allowances'])
        total_deductions = (salary_data['pf_deduction'] + salary_data['esi_deduction'] + 
                           salary_data['pt_deduction'] + salary_data['lwf_deduction'] + 
                           salary_data['insurance'] + salary_data['advance'])
        salary_data['net_salary'] = total_earnings - total_deductions

        salary_structure = SalaryStructure.objects.create(**salary_data)
        serializer = SalaryStructureSerializer(salary_structure)

        return Response({
            'success': True,
            'message': 'Salary structure created successfully',
            'data': serializer.data,
        }, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['get'], url_path='salary-report')
    def salary_report(self, request):
        """
        Get salary report for company employees
        
        Query Parameters:
        - department (optional): Filter by department
        """
        submanager = self._get_submanager_employee(request)
        if not submanager:
            return Response({
                'success': False,
                'error': 'Sub-Manager employee record not found'
            }, status=status.HTTP_404_NOT_FOUND)

        company = self._get_submanager_company(submanager)
        department = request.query_params.get('department')

        filters = {'department': department} if department else None
        employees = self._get_company_employees(company, filters)

        report_data = []
        total_payroll = 0

        for emp in employees:
            salary_structure = SalaryStructure.objects.filter(employee=emp).first()
            official_details = OfficialDetails.objects.filter(employee=emp).first()

            if salary_structure:
                total_payroll += float(salary_structure.CTC)
                report_data.append({
                    'employee_id': emp.id,
                    'employee_code': emp.employee_code,
                    'employee_name': emp.full_name,
                    'department': official_details.department if official_details else 'N/A',
                    'designation': official_details.designation if official_details else 'N/A',
                    'CTC': float(salary_structure.CTC),
                    'net_salary': float(salary_structure.net_salary),
                })

        return Response({
            'success': True,
            'sub_manager': {
                'id': submanager.id,
                'name': submanager.full_name,
            },
            'company': {
                'id': company.id,
                'name': company.name,
            },
            'total_employees': len(report_data),
            'total_annual_payroll': total_payroll,
            'average_salary': total_payroll / len(report_data) if report_data else 0,
            'data': report_data,
        })

    # ==================== OVERTIME MANAGEMENT ====================

    @action(detail=False, methods=['post'], url_path='record-overtime')
    def record_overtime(self, request):
        """
        Record overtime for an employee
        
        Request Body:
        - employee_id (required)
        - date (required): YYYY-MM-DD
        - hours (required): Decimal hours
        """
        submanager = self._get_submanager_employee(request)
        if not submanager:
            return Response({
                'success': False,
                'error': 'Sub-Manager employee record not found'
            }, status=status.HTTP_404_NOT_FOUND)

        company = self._get_submanager_company(submanager)
        employee_id = request.data.get('employee_id')
        date_str = request.data.get('date')
        hours = request.data.get('hours')

        if not all([employee_id, date_str, hours]):
            return Response({
                'success': False,
                'error': 'employee_id, date, and hours are required'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Verify employee belongs to company
        try:
            employee = Employee.objects.get(id=employee_id, sub_company=company)
        except Employee.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Employee not found or not in your company'
            }, status=status.HTTP_404_NOT_FOUND)

        # Parse date
        try:
            overtime_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            return Response({
                'success': False,
                'error': 'Invalid date format. Use YYYY-MM-DD'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Create overtime record
        overtime = OvertimeRecord.objects.create(
            employee=employee,
            date=overtime_date,
            hours=Decimal(str(hours))
        )

        serializer = OvertimeRecordSerializer(overtime)

        return Response({
            'success': True,
            'message': 'Overtime recorded successfully',
            'data': serializer.data,
        }, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['get'], url_path='overtime-report')
    def overtime_report(self, request):
        """
        Get overtime report for company employees
        
        Query Parameters:
        - start_date (required): YYYY-MM-DD
        - end_date (required): YYYY-MM-DD
        """
        submanager = self._get_submanager_employee(request)
        if not submanager:
            return Response({
                'success': False,
                'error': 'Sub-Manager employee record not found'
            }, status=status.HTTP_404_NOT_FOUND)

        company = self._get_submanager_company(submanager)
        start_date_str = request.query_params.get('start_date')
        end_date_str = request.query_params.get('end_date')

        if not start_date_str or not end_date_str:
            return Response({
                'success': False,
                'error': 'start_date and end_date are required'
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        except ValueError:
            return Response({
                'success': False,
                'error': 'Invalid date format. Use YYYY-MM-DD'
            }, status=status.HTTP_400_BAD_REQUEST)

        employees = self._get_company_employees(company)

        report_data = []
        total_overtime_hours = 0

        for emp in employees:
            overtime_records = OvertimeRecord.objects.filter(
                employee=emp,
                date__range=[start_date, end_date]
            )

            employee_overtime = overtime_records.aggregate(
                total_hours=Sum('hours'),
                records_count=Count('id')
            )

            if employee_overtime['total_hours']:
                total_overtime_hours += float(employee_overtime['total_hours'])
                official_details = OfficialDetails.objects.filter(employee=emp).first()

                report_data.append({
                    'employee_id': emp.id,
                    'employee_code': emp.employee_code,
                    'employee_name': emp.full_name,
                    'designation': official_details.designation if official_details else 'N/A',
                    'total_overtime_hours': float(employee_overtime['total_hours']),
                    'records_count': employee_overtime['records_count'],
                })

        return Response({
            'success': True,
            'sub_manager': {
                'id': submanager.id,
                'name': submanager.full_name,
            },
            'company': {
                'id': company.id,
                'name': company.name,
            },
            'period': {
                'start_date': start_date_str,
                'end_date': end_date_str,
            },
            'total_employees': len(report_data),
            'total_overtime_hours': total_overtime_hours,
            'data': report_data,
        })

    # ==================== ANALYTICS ====================

    @action(detail=False, methods=['get'], url_path='company-analytics')
    def company_analytics(self, request):
        """
        Get comprehensive analytics for sub-company
        
        Query Parameters:
        - year (optional): Year for analytics
        """
        submanager = self._get_submanager_employee(request)
        if not submanager:
            return Response({
                'success': False,
                'error': 'Sub-Manager employee record not found'
            }, status=status.HTTP_404_NOT_FOUND)

        company = self._get_submanager_company(submanager)
        year = int(request.query_params.get('year', timezone.now().year))

        employees = self._get_company_employees(company)
        active_employees = employees.filter(status='ACTIVE')

        # Headcount analysis
        headcount = {
            'total_active': active_employees.count(),
            'by_role': list(active_employees.values('role').annotate(count=Count('id'))),
            'by_gender': list(active_employees.values('gender').annotate(count=Count('id'))),
            'by_department': list(active_employees.values('officialdetails__department').annotate(count=Count('id'))),
        }

        # Salary analysis
        salary_stats = SalaryStructure.objects.filter(
            employee__in=active_employees
        ).aggregate(
            min_ctc=Min('CTC'),
            max_ctc=Max('CTC'),
            avg_ctc=Avg('CTC'),
            total_payroll=Sum('CTC')
        )

        # Attendance trends (last 12 months)
        attendance_trends = []
        for month in range(1, 13):
            start_date = datetime(year, month, 1).date()
            if month == 12:
                end_date = datetime(year + 1, 1, 1).date() - timedelta(days=1)
            else:
                end_date = datetime(year, month + 1, 1).date() - timedelta(days=1)

            stats = Attendance.objects.filter(
                employee__in=active_employees,
                date__range=[start_date, end_date]
            ).aggregate(
                present=Count('id', filter=Q(status='P')),
                absent=Count('id', filter=Q(status='A'))
            )

            attendance_trends.append({
                'month': start_date.strftime('%B %Y'),
                'present': stats['present'],
                'absent': stats['absent'],
            })

        # Turnover analysis
        year_start = datetime(year, 1, 1).date()
        year_end = datetime(year, 12, 31).date()
        
        joinings = employees.filter(created_at__date__range=[year_start, year_end]).count()
        leavings = employees.filter(status='LEFT', updated_at__date__range=[year_start, year_end]).count()
        
        avg_headcount = (active_employees.count() + leavings) / 2
        turnover_rate = (leavings / avg_headcount * 100) if avg_headcount > 0 else 0

        return Response({
            'success': True,
            'sub_manager': {
                'id': submanager.id,
                'name': submanager.full_name,
            },
            'company': {
                'id': company.id,
                'name': company.name,
            },
            'year': year,
            'headcount': headcount,
            'salary_analysis': {
                'min_ctc': float(salary_stats['min_ctc'] or 0),
                'max_ctc': float(salary_stats['max_ctc'] or 0),
                'avg_ctc': float(salary_stats['avg_ctc'] or 0),
                'total_annual_payroll': float(salary_stats['total_payroll'] or 0),
            },
            'attendance_trends': attendance_trends,
            'turnover': {
                'joinings': joinings,
                'leavings': leavings,
                'turnover_rate': round(turnover_rate, 2),
            },
        })

    # ==================== QUICK ACTIONS ====================

    @action(detail=False, methods=['get'], url_path='today-summary')
    def today_summary(self, request):
        """
        Get today's quick summary for the company
        """
        submanager = self._get_submanager_employee(request)
        if not submanager:
            return Response({
                'success': False,
                'error': 'Sub-Manager employee record not found'
            }, status=status.HTTP_404_NOT_FOUND)

        company = self._get_submanager_company(submanager)
        today = timezone.now().date()

        employees = self._get_company_employees(company).filter(status='ACTIVE')
        total_employees = employees.count()

        # Today's attendance
        today_attendance = Attendance.objects.filter(
            employee__in=employees,
            date=today
        )

        attendance_stats = today_attendance.aggregate(
            present=Count('id', filter=Q(status='P')),
            absent=Count('id', filter=Q(status='A')),
            not_marked=total_employees - Count('id')
        )

        # Get individual status
        employees_status = []
        for emp in employees:
            attendance = today_attendance.filter(employee=emp).first()
            official_details = OfficialDetails.objects.filter(employee=emp).first()
            
            status_display = 'Not Marked'
            status_code = None
            if attendance:
                status_map = {'P': 'Present', 'A': 'Absent', 'WO': 'Weekly Off', 'H': 'Holiday', 'HD': 'Half Day'}
                status_display = status_map.get(attendance.status, 'Unknown')
                status_code = attendance.status

            employees_status.append({
                'employee_id': emp.id,
                'employee_code': emp.employee_code,
                'full_name': emp.full_name,
                'department': official_details.department if official_details else 'N/A',
                'status': status_display,
                'status_code': status_code,
            })

        return Response({
            'success': True,
            'sub_manager': {
                'id': submanager.id,
                'name': submanager.full_name,
            },
            'company': {
                'id': company.id,
                'name': company.name,
            },
            'date': today.strftime('%Y-%m-%d'),
            'summary': {
                'total_employees': total_employees,
                'present': attendance_stats['present'],
                'absent': attendance_stats['absent'],
                'not_marked': total_employees - today_attendance.count(),
            },
            'employees_status': employees_status,
        })
