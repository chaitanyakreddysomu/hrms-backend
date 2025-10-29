"""
HR Dashboard APIs for comprehensive HR management system
Includes: Dashboard stats, Attendance, Salary, Payslips, Reports, Analytics
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Count, Sum, Avg, Min, Max, Q
from django.db import models
from django.utils import timezone
from django.apps import apps
from datetime import datetime, timedelta
import json
from decimal import Decimal
from .models import (
    Employee, Attendance, SalaryStructure, Payslip, 
    IncrementHistory, OvertimeRecord, Document, Report,
    OfficialDetails, Company
)
from .serializers import (
    EmployeeSerializer, AttendanceSerializer, SalaryStructureSerializer,
    PayslipSerializer, IncrementHistorySerializer, OvertimeRecordSerializer,
    ReportSerializer
)
from .permissions import IsHROnly


class HRDashboardViewSet(viewsets.ViewSet):
    """
    HR Dashboard ViewSet with comprehensive HR management APIs
    
    Features:
    - Dashboard Statistics
    - Attendance Management (Mark, Bulk Upload, Reports)
    - Salary Structure Management
    - Payslip Generation
    - Report Generation
    - Overtime Management
    - Employee Analytics
    - Status Updates
    
    Access: HR Role ONLY
    """
    permission_classes = [IsHROnly]

    # ==================== DASHBOARD STATISTICS ====================
    
    @action(detail=False, methods=['get'], url_path='dashboard-stats')
    def dashboard_stats(self, request):
        """
        Get comprehensive dashboard statistics
        
        Query Parameters:
        - company_id (optional): Filter by specific company
        - month (optional): Month number (1-12)
        - year (optional): Year (e.g., 2024)
        
        Returns:
        - Total employees, active employees, departments
        - Attendance stats (present, absent, on leave)
        - Salary stats (total payroll, average salary)
        - Recent activities
        """
        try:
            company_id = request.query_params.get('company_id')
            month = request.query_params.get('month', timezone.now().month)
            year = request.query_params.get('year', timezone.now().year)
            
            # Filter employees based on company
            employees = Employee.objects.all()
            if company_id:
                employees = employees.filter(
                    Q(main_company_id=company_id) | Q(sub_company_id=company_id)
                )
            
            # Employee Statistics
            total_employees = employees.count()
            active_employees = employees.filter(status='ACTIVE').count()
            inactive_employees = employees.filter(status__in=['LEFT', 'TERMINATED']).count()
            
            # Department-wise breakdown
            departments = OfficialDetails.objects.filter(
                employee__in=employees
            ).values('department').annotate(count=Count('id'))
            
            # Role-wise breakdown
            roles = employees.values('role').annotate(count=Count('id'))
            
            # Attendance Statistics for current month
            start_date = datetime(int(year), int(month), 1).date()
            if int(month) == 12:
                end_date = datetime(int(year) + 1, 1, 1).date()
            else:
                end_date = datetime(int(year), int(month) + 1, 1).date()
            
            attendance_records = Attendance.objects.filter(
                employee__in=employees,
                date__gte=start_date,
                date__lt=end_date
            )
            
            attendance_stats = {
                'present': attendance_records.filter(Q(shift_1_status='P') | Q(shift_2_status='P')).count(),
                'absent': attendance_records.filter(Q(shift_1_status='A') | Q(shift_2_status='A')).count(),
                'weekly_off': attendance_records.filter(Q(shift_1_status='WO') | Q(shift_2_status='WO')).count(),
                'holiday': attendance_records.filter(Q(shift_1_status='H') | Q(shift_2_status='H')).count(),
                'half_day': attendance_records.filter(Q(shift_1_status='HD') | Q(shift_2_status='HD')).count(),
            }
            
            # Salary Statistics
            salary_structures = SalaryStructure.objects.filter(employee__in=employees)
            total_payroll = salary_structures.aggregate(total=Sum('CTC'))['total'] or 0
            average_salary = salary_structures.aggregate(avg=Avg('CTC'))['avg'] or 0
            
            # Payslip Statistics for current month
            payslips_generated = Payslip.objects.filter(
                employee__in=employees,
                month=month,
                year=year
            ).count()
            
            # Recent Activities (last 30 days)
            thirty_days_ago = timezone.now().date() - timedelta(days=30)
            recent_joinings = employees.filter(
                officialdetails__date_of_joining__gte=thirty_days_ago
            ).count()
            
            recent_leavings = employees.filter(
                status__in=['LEFT', 'TERMINATED']
            ).count()
            
            # Overtime Statistics
            overtime_records = OvertimeRecord.objects.filter(
                employee__in=employees,
                date__gte=start_date,
                date__lt=end_date
            )
            total_overtime_hours = overtime_records.aggregate(total=Sum('hours'))['total'] or 0

            # Profile update requests (optional model) - count pending for these employees
            pending_profile_updates = None
            try:
                ProfileUpdateRequest = apps.get_model('core', 'ProfileUpdateRequest')
                # Count pending requests related to these employees (if model and field names match)
                pending_qs = ProfileUpdateRequest.objects.filter(status='PENDING', employee__in=employees)
                pending_profile_updates = pending_qs.count()
            except LookupError:
                # Model not present - leave as None
                pending_profile_updates = None
            
            return Response({
                'success': True,
                'data': {
                    'employees': {
                        'total': total_employees,
                        'active': active_employees,
                        'inactive': inactive_employees,
                        'by_department': list(departments),
                        'by_role': list(roles),
                    },
                    'attendance': {
                        'month': month,
                        'year': year,
                        'statistics': attendance_stats,
                        'total_records': attendance_records.count(),
                    },
                    'salary': {
                        'total_payroll': float(total_payroll),
                        'average_salary': float(average_salary),
                        'employees_with_structure': salary_structures.count(),
                    },
                    'payslips': {
                        'month': month,
                        'year': year,
                        'generated': payslips_generated,
                        'pending': active_employees - payslips_generated,
                    },
                    'recent_activities': {
                        'new_joinings_30_days': recent_joinings,
                        'leavings': recent_leavings,
                    },
                    'overtime': {
                        'month': month,
                        'year': year,
                        'total_hours': float(total_overtime_hours),
                        'records_count': overtime_records.count(),
                    }
                ,
                'profile_update_requests': {
                    'pending': pending_profile_updates
                }
                }
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    # ==================== ATTENDANCE MANAGEMENT ====================
    
    @action(detail=False, methods=['post'], url_path='mark-attendance')
    def mark_attendance(self, request):
        """
        Mark attendance for an employee
        
        Request Body:
        {
            "employee_id": 1,
            "date": "2024-10-07",
            "status": "P"  // P, A, WO, H, HD
        }
        """
        try:
            employee_id = request.data.get('employee_id')
            date = request.data.get('date')

            # New per-shift fields. Backwards-compatible 'status' supported.
            shift_1_status = request.data.get('shift_1_status')
            shift_2_status = request.data.get('shift_2_status')
            attendance_status = request.data.get('status')

            if not all([employee_id, date]):
                return Response({
                    'success': False,
                    'error': 'employee_id and date are required'
                }, status=status.HTTP_400_BAD_REQUEST)

            if not any([shift_1_status, shift_2_status, attendance_status]):
                return Response({
                    'success': False,
                    'error': 'Provide at least one of: status, shift_1_status, shift_2_status'
                }, status=status.HTTP_400_BAD_REQUEST)

            employee = Employee.objects.get(id=employee_id)

            # Legacy status mapping -> tuple (shift1, shift2) where None means "no-op / keep existing if present"
            legacy_map = {
                'P': ('P', 'P'),
                'A': ('A', 'A'),
                'WO': ('WO', 'WO'),
                'H': ('H', 'H'),
                'HD': ('HD', 'HD'),
                # Partial codes: set only one shift (None = leave as-is when updating; default to 'A' when creating)
                'FSP': ('P', None),  # First shift present
                'SSP': (None, 'P'),  # Second shift present
                'FSA': ('A', None),  # First shift absent
                'SSA': (None, 'A'),  # Second shift absent
            }

            # Try to find existing attendance to preserve unspecified shifts
            existing = Attendance.objects.filter(employee=employee, date=date).first()

            # Determine final shift values
            final_shift_1 = None
            final_shift_2 = None

            if shift_1_status:
                final_shift_1 = shift_1_status

            if shift_2_status:
                final_shift_2 = shift_2_status

            if attendance_status and attendance_status in legacy_map:
                m1, m2 = legacy_map[attendance_status]
                if m1 is not None and final_shift_1 is None:
                    final_shift_1 = m1
                if m2 is not None and final_shift_2 is None:
                    final_shift_2 = m2

            # For any remaining None, if updating keep existing value; if creating, default to 'A' (absent)
            if existing:
                if final_shift_1 is None:
                    final_shift_1 = existing.shift_1_status
                if final_shift_2 is None:
                    final_shift_2 = existing.shift_2_status
            else:
                if final_shift_1 is None:
                    final_shift_1 = 'A'
                if final_shift_2 is None:
                    final_shift_2 = 'A'

            # Create or update attendance
            attendance, created = Attendance.objects.update_or_create(
                employee=employee,
                date=date,
                defaults={'shift_1_status': final_shift_1, 'shift_2_status': final_shift_2}
            )

            serializer = AttendanceSerializer(attendance)

            return Response({
                'success': True,
                'message': 'Attendance marked successfully' if created else 'Attendance updated successfully',
                'employee_id': employee.id,
                'data': serializer.data
            }, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)
            
        except Employee.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Employee not found'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['post'], url_path='bulk-mark-attendance')
    def bulk_mark_attendance(self, request):
        """
        Mark attendance for multiple employees at once
        
        Request Body:
        {
            "date": "2024-10-07",
            "attendance_records": [
                {"employee_id": 1, "status": "P"},
                {"employee_id": 2, "status": "A"},
                {"employee_id": 3, "status": "P"}
            ]
        }
        """
        try:
            date = request.data.get('date')
            attendance_records = request.data.get('attendance_records', [])
            
            if not date or not attendance_records:
                return Response({
                    'success': False,
                    'error': 'date and attendance_records are required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            created_count = 0
            updated_count = 0
            errors = []
            
            for record in attendance_records:
                try:
                    employee = Employee.objects.get(id=record['employee_id'])
                    # Accept shift_1_status/shift_2_status or legacy 'status'
                    r_shift_1 = record.get('shift_1_status')
                    r_shift_2 = record.get('shift_2_status')
                    r_status = record.get('status')

                    # Legacy mapping (same as single mark API)
                    legacy_map = {
                        'P': ('P', 'P'),
                        'A': ('A', 'A'),
                        'WO': ('WO', 'WO'),
                        'H': ('H', 'H'),
                        'HD': ('HD', 'HD'),
                        'FSP': ('P', None),
                        'SSP': (None, 'P'),
                        'FSA': ('A', None),
                        'SSA': (None, 'A'),
                    }

                    existing = Attendance.objects.filter(employee=employee, date=date).first()

                    final_shift_1 = r_shift_1
                    final_shift_2 = r_shift_2

                    if r_status and r_status in legacy_map:
                        m1, m2 = legacy_map[r_status]
                        if m1 is not None and final_shift_1 is None:
                            final_shift_1 = m1
                        if m2 is not None and final_shift_2 is None:
                            final_shift_2 = m2

                    if existing:
                        if final_shift_1 is None:
                            final_shift_1 = existing.shift_1_status
                        if final_shift_2 is None:
                            final_shift_2 = existing.shift_2_status
                    else:
                        if final_shift_1 is None:
                            final_shift_1 = 'A'
                        if final_shift_2 is None:
                            final_shift_2 = 'A'

                    attendance, created = Attendance.objects.update_or_create(
                        employee=employee,
                        date=date,
                        defaults={'shift_1_status': final_shift_1, 'shift_2_status': final_shift_2}
                    )

                    if created:
                        created_count += 1
                    else:
                        updated_count += 1
                except Exception as e:
                    errors.append({
                        'employee_id': record.get('employee_id'),
                        'error': str(e)
                    })
            
            return Response({
                'success': True,
                'message': 'Bulk attendance marking completed',
                'summary': {
                    'created': created_count,
                    'updated': updated_count,
                    'errors': len(errors),
                },
                'errors': errors if errors else None
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['get'], url_path='attendance-report')
    def attendance_report(self, request):
        """
        Get attendance report for employees
        
        Query Parameters:
        - employee_id (optional): Specific employee
        - company_id (optional): Filter by company
        - start_date (required): Start date (YYYY-MM-DD)
        - end_date (required): End date (YYYY-MM-DD)
        """
        try:
            employee_id = request.query_params.get('employee_id')
            company_id = request.query_params.get('company_id')
            start_date = request.query_params.get('start_date')
            end_date = request.query_params.get('end_date')
            
            if not start_date or not end_date:
                return Response({
                    'success': False,
                    'error': 'start_date and end_date are required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Filter attendance records
            attendance_qs = Attendance.objects.filter(
                date__gte=start_date,
                date__lte=end_date
            )
            
            if employee_id:
                attendance_qs = attendance_qs.filter(employee_id=employee_id)
            
            if company_id:
                attendance_qs = attendance_qs.filter(
                    Q(employee__main_company_id=company_id) | 
                    Q(employee__sub_company_id=company_id)
                )
            
            # Group by employee
            report_data = []
            employees = attendance_qs.values('employee').distinct()
            
            for emp in employees:
                emp_id = emp['employee']
                employee = Employee.objects.get(id=emp_id)
                emp_attendance = attendance_qs.filter(employee_id=emp_id)
                
                stats = {
                    'present': emp_attendance.filter(Q(shift_1_status='P') | Q(shift_2_status='P')).count(),
                    'absent': emp_attendance.filter(Q(shift_1_status='A') | Q(shift_2_status='A')).count(),
                    'weekly_off': emp_attendance.filter(Q(shift_1_status='WO') | Q(shift_2_status='WO')).count(),
                    'holiday': emp_attendance.filter(Q(shift_1_status='H') | Q(shift_2_status='H')).count(),
                    'half_day': emp_attendance.filter(Q(shift_1_status='HD') | Q(shift_2_status='HD')).count(),
                }
                
                report_data.append({
                    'employee_id': emp_id,
                    'employee_code': employee.employee_code,
                    'employee_name': employee.full_name,
                    'department': getattr(employee.officialdetails, 'department', 'N/A') if hasattr(employee, 'officialdetails') else 'N/A',
                    'statistics': stats,
                    'total_working_days': stats['present'] + stats['half_day'],
                })
            
            return Response({
                'success': True,
                'period': {
                    'start_date': start_date,
                    'end_date': end_date,
                },
                'total_employees': len(report_data),
                'data': report_data
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['get'], url_path='check-attendance')
    def check_attendance(self, request):
        """
        Check attendance rows for HR-available employees.

        Query parameters:
        - date (optional): YYYY-MM-DD (defaults to today)
        - status (optional): filter by computed status (P, A, WO, H, HD)
        - company_id (optional): filter employees by company (main or sub)

        Response: list of { username, email, employee_id, shift_1_status, shift_2_status, status }
        """
        try:
            date_str = request.query_params.get('date')
            status_filter = request.query_params.get('status')
            company_id = request.query_params.get('company_id')

            # parse date - accept ISO (YYYY-MM-DD), YYYY-MM-DD, or DD/MM/YYYY
            def _parse_date(s):
                if not s:
                    return None
                # try ISO / YYYY-MM-DD
                try:
                    return datetime.fromisoformat(s).date()
                except Exception:
                    pass
                # try common formats
                for fmt in ('%Y-%m-%d', '%d/%m/%Y'):
                    try:
                        return datetime.strptime(s, fmt).date()
                    except Exception:
                        continue
                return None

            if date_str:
                target_date = _parse_date(date_str)
                if target_date is None:
                    return Response({'success': False, 'error': 'Invalid date format. Use YYYY-MM-DD or DD/MM/YYYY'}, status=status.HTTP_400_BAD_REQUEST)
            else:
                target_date = timezone.now().date()

            # Base employee set: HR's available employees -> active employees
            employees = Employee.objects.filter(status='ACTIVE')
            if company_id:
                employees = employees.filter(Q(main_company_id=company_id) | Q(sub_company_id=company_id))

            # Preload attendance for the date. Use date__date only if Attendance.date is a DateTimeField
            date_field = Attendance._meta.get_field('date')
            if isinstance(date_field, models.DateTimeField):
                attendance_qs = Attendance.objects.filter(employee__in=employees).filter(
                    Q(date__date=target_date) | Q(date=target_date)
                )
            else:
                attendance_qs = Attendance.objects.filter(employee__in=employees, date=target_date)
            attendance_map = {a.employee_id: a for a in attendance_qs}

            # normalize and accept comma-separated status filters
            valid_statuses = {'P', 'A', 'WO', 'H', 'HD'}
            status_filters = None
            if status_filter:
                status_filters = {s.strip().upper() for s in status_filter.split(',') if s.strip()}
                # filter out invalid tokens
                status_filters = {s for s in status_filters if s in valid_statuses}
                if not status_filters:
                    return Response({'success': False, 'error': 'Invalid status filter. Allowed: P, A, WO, H, HD'}, status=status.HTTP_400_BAD_REQUEST)

            def compute_combined_status(s1, s2):
                # normalize
                s1 = (s1 or '').upper()
                s2 = (s2 or '').upper()
                # If both equal and non-empty -> that
                if s1 and s2 and s1 == s2:
                    return s1
                # Precedence: Present > Holiday > Weekly Off > Half Day > Absent
                if 'P' in (s1, s2):
                    return 'P'
                if 'H' in (s1, s2):
                    return 'H'
                if 'WO' in (s1, s2):
                    return 'WO'
                if 'HD' in (s1, s2):
                    return 'HD'
                if 'A' in (s1, s2):
                    return 'A'
                # Default to Absent
                return 'A'

            display_map = {
                'P': 'Present',
                'A': 'Absent',
                'WO': 'Weekly Off',
                'H': 'Holiday',
                'HD': 'Half Day'
            }

            results = []
            for emp in employees.select_related('officialdetails'):
                att = attendance_map.get(emp.id)
                if att:
                    s1 = (att.shift_1_status or '').upper()
                    s2 = (att.shift_2_status or '').upper()
                    record_exists = True
                    attendance_id = att.id
                else:
                    # No attendance record -> explicit Absent for both shifts
                    s1 = 'A'
                    s2 = 'A'
                    record_exists = False
                    attendance_id = None

                combined = compute_combined_status(s1, s2)

                # Apply status filter if provided
                if status_filters and combined not in status_filters:
                    continue

                results.append({
                    'employee_id': emp.id,
                    'username': getattr(emp, 'employee_code', None) or getattr(emp, 'username', None) or emp.full_name,
                    'email': getattr(emp, 'email', None),
                    'shift_1_status': s1,
                    'shift_1_display': display_map.get(s1, s1),
                    'shift_2_status': s2,
                    'shift_2_display': display_map.get(s2, s2),
                    'status': combined,
                    'status_display': display_map.get(combined, combined),
                    'record_exists': record_exists,
                    'attendance_id': attendance_id,
                })

            return Response({'success': True, 'date': str(target_date), 'count': len(results), 'data': results}, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({'success': False, 'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['get'], url_path='profile-update-requests')
    def profile_update_requests(self, request):
        """
        List employee profile update requests for HR to review.

        Query params:
        - status (optional): PENDING, APPROVED, REJECTED (comma-separated allowed)
        - employee_id (optional)
        - company_id (optional)

        Response: { count, data: [ { id, employee_id, employee_name, requested_data, status, created_at, updated_at } ] }
        """
        try:
            status_filter = request.query_params.get('status')
            employee_id = request.query_params.get('employee_id')
            company_id = request.query_params.get('company_id')

            try:
                ProfileUpdateRequest = apps.get_model('core', 'ProfileUpdateRequest')
            except LookupError:
                return Response({'success': False, 'error': 'ProfileUpdateRequest model not found'}, status=status.HTTP_404_NOT_FOUND)

            qs = ProfileUpdateRequest.objects.all()

            # Filter by status
            if status_filter:
                wanted = {s.strip().upper() for s in status_filter.split(',') if s.strip()}
                qs = qs.filter(status__in=wanted)

            if employee_id:
                qs = qs.filter(employee_id=employee_id)

            if company_id:
                qs = qs.filter(employee__main_company_id=company_id) | qs.filter(employee__sub_company_id=company_id)

            results = []
            for req in qs.select_related('employee'):
                emp = getattr(req, 'employee', None)
                emp_name = getattr(emp, 'full_name', None) if emp else None
                emp_email = getattr(emp, 'email', None) if emp else None
                status_val = getattr(req, 'status', None)

                # Prefer model fields that may exist on different implementations
                # 1) ApprovalWorkflow-style: requested_data (JSON/dict) and created_at
                # 2) ProfileUpdateRequest (this project): field_name, requested_value, reason, requested_at

                # Case A: explicit per-field model (field_name + requested_value)
                if hasattr(req, 'field_name') and hasattr(req, 'requested_value'):
                    field = getattr(req, 'field_name', None)
                    requested_value = getattr(req, 'requested_value', None)
                    reason = getattr(req, 'reason', None) or getattr(req, 'remarks', None) or getattr(req, 'notes', None)
                    requested_at = getattr(req, 'requested_at', None) or getattr(req, 'created_at', None)

                    results.append({
                        'id': req.id,
                        'employee_id': getattr(emp, 'id', None),
                        'employee_name': emp_name,
                        'email': emp_email,
                        'field': field,
                        'requested_value': requested_value,
                        'reason': reason,
                        'status': status_val,
                        'requested_at': requested_at.isoformat() if requested_at else None,
                    })
                    continue

                # Case B: JSON/dict blob stored in requested_data or request_data
                requested = getattr(req, 'requested_data', None) or getattr(req, 'request_data', None)
                reason = getattr(req, 'reason', None) or getattr(req, 'notes', None) or getattr(req, 'remarks', None)
                requested_at = getattr(req, 'created_at', None)

                req_dict = None
                if isinstance(requested, str):
                    try:
                        req_dict = json.loads(requested)
                    except Exception:
                        req_dict = None
                elif isinstance(requested, dict):
                    req_dict = requested

                if isinstance(req_dict, dict) and req_dict:
                    for field, val in req_dict.items():
                        results.append({
                            'id': req.id,
                            'employee_id': getattr(emp, 'id', None),
                            'employee_name': emp_name,
                            'email': emp_email,
                            'field': field,
                            'requested_value': val,
                            'reason': reason,
                            'status': status_val,
                            'requested_at': requested_at.isoformat() if requested_at else None,
                        })
                else:
                    # Fallback: include whatever raw data is available
                    raw_val = requested if requested is not None else None
                    results.append({
                        'id': req.id,
                        'employee_id': getattr(emp, 'id', None),
                        'employee_name': emp_name,
                        'email': emp_email,
                        'field': None,
                        'requested_value': raw_val,
                        'reason': reason,
                        'status': status_val,
                        'requested_at': requested_at.isoformat() if requested_at else None,
                    })

            return Response({'success': True, 'count': len(results), 'data': results}, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({'success': False, 'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['put'], url_path='profile-update-requests/review')
    def review_profile_update_request(self, request):
        """
        Approve or reject a ProfileUpdateRequest.

        Request body:
        {
          "request_id": 123,
          "status": "APPROVED" | "REJECTED",
          "remarks": "Optional remarks",
          "apply": true   # optional, default true for APPROVED; if true, apply the requested_value to the employee record
        }

        Response: updated request summary
        """
        try:
            req_id = request.data.get('request_id') or request.data.get('id')
            new_status = (request.data.get('status') or '').strip().upper()
            remarks = request.data.get('remarks')
            apply_change = request.data.get('apply')

            if not req_id:
                return Response({'success': False, 'error': 'request_id is required'}, status=status.HTTP_400_BAD_REQUEST)

            if new_status not in ('APPROVED', 'REJECTED'):
                return Response({'success': False, 'error': 'status must be APPROVED or REJECTED'}, status=status.HTTP_400_BAD_REQUEST)

            try:
                ProfileUpdateRequest = apps.get_model('core', 'ProfileUpdateRequest')
            except LookupError:
                return Response({'success': False, 'error': 'ProfileUpdateRequest model not found'}, status=status.HTTP_404_NOT_FOUND)

            try:
                req_obj = ProfileUpdateRequest.objects.select_related('employee').get(id=req_id)
            except ProfileUpdateRequest.DoesNotExist:
                return Response({'success': False, 'error': 'ProfileUpdateRequest not found'}, status=status.HTTP_404_NOT_FOUND)

            # Default apply behavior: for APPROVED if apply is None -> True; for REJECTED -> False
            if apply_change is None:
                apply_change = True if new_status == 'APPROVED' else False

            # Update request record
            req_obj.status = new_status
            if remarks is not None:
                # prefer to set reviewed remarks
                req_obj.remarks = remarks
            try:
                # set reviewer if available
                if hasattr(req_obj, 'reviewed_by') and request.user and request.user.is_authenticated:
                    req_obj.reviewed_by = request.user
                if hasattr(req_obj, 'reviewed_at'):
                    req_obj.reviewed_at = timezone.now()
            except Exception:
                # ignore reviewer assignment failures
                pass

            req_obj.save()

            # If approved and apply_change, attempt to apply to appropriate model
            applied = False
            apply_error = None
            if new_status == 'APPROVED' and apply_change:
                emp = getattr(req_obj, 'employee', None)
                field_name = getattr(req_obj, 'field_name', None)
                requested_value = getattr(req_obj, 'requested_value', None)

                # helper to parse dates
                def _parse_date_val(v):
                    if not v:
                        return None
                    try:
                        return datetime.fromisoformat(v).date()
                    except Exception:
                        for fmt in ('%Y-%m-%d', '%d/%m/%Y'):
                            try:
                                return datetime.strptime(v, fmt).date()
                            except Exception:
                                continue
                    return None

                from django.core.exceptions import FieldDoesNotExist
                try:
                    if emp and field_name:
                        applied_to = None
                        # Try Employee model first
                        try:
                            f = Employee._meta.get_field(field_name)
                            # convert value for date fields
                            if isinstance(f, models.DateField) or isinstance(f, models.DateTimeField):
                                parsed = _parse_date_val(requested_value)
                                if parsed is not None:
                                    setattr(emp, field_name, parsed)
                                else:
                                    setattr(emp, field_name, requested_value)
                            else:
                                setattr(emp, field_name, requested_value)
                            emp.save()
                            applied = True
                            applied_to = 'employee'
                        except FieldDoesNotExist:
                            # try OfficialDetails
                            try:
                                od_field = OfficialDetails._meta.get_field(field_name)
                                od = OfficialDetails.objects.filter(employee=emp).first()
                                if not od:
                                    od = OfficialDetails.objects.create(employee=emp, date_of_joining=timezone.now().date(), department='')
                                if isinstance(od_field, models.DateField) or isinstance(od_field, models.DateTimeField):
                                    parsed = _parse_date_val(requested_value)
                                    if parsed is not None:
                                        setattr(od, field_name, parsed)
                                    else:
                                        setattr(od, field_name, requested_value)
                                else:
                                    setattr(od, field_name, requested_value)
                                od.save()
                                applied = True
                                applied_to = 'officialdetails'
                            except FieldDoesNotExist:
                                # try IdentityDocument
                                try:
                                    id_field = IdentityDocument._meta.get_field(field_name)
                                    ident = IdentityDocument.objects.filter(employee=emp).first()
                                    if not ident:
                                        ident = IdentityDocument.objects.create(employee=emp)
                                    setattr(ident, field_name, requested_value)
                                    ident.save()
                                    applied = True
                                    applied_to = 'identitydocument'
                                except FieldDoesNotExist:
                                    # try BankDetails
                                    try:
                                        b_field = BankDetails._meta.get_field(field_name)
                                        bank = BankDetails.objects.filter(employee=emp).first()
                                        if not bank:
                                            bank = BankDetails.objects.create(employee=emp, bank_name='', account_number='', ifsc_code='', branch_name='')
                                        setattr(bank, field_name, requested_value)
                                        bank.save()
                                        applied = True
                                        applied_to = 'bankdetails'
                                    except FieldDoesNotExist:
                                        apply_error = f'Field "{field_name}" not found on Employee/OfficialDetails/IdentityDocument/BankDetails'
                except Exception as e:
                    apply_error = str(e)

            response = {
                'success': True,
                'request_id': req_obj.id,
                'status': req_obj.status,
                'applied': applied,
                'apply_error': apply_error,
            }

            return Response(response, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({'success': False, 'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['put'], url_path='edit-attendance')
    def edit_attendance(self, request):
        """
        Edit an existing attendance record.

        Request Body (one of):
        - attendance_id: existing attendance record id
        OR
        - employee_id and date

        Fields to update (any):
        - shift_1_status
        - shift_2_status
        - status (legacy codes: P,A,WO,H,HD or partial codes like FSP/SSA)
        """
        try:
            attendance_id = request.data.get('attendance_id')
            employee_id = request.data.get('employee_id')
            date = request.data.get('date')

            if attendance_id:
                attendance = Attendance.objects.get(id=attendance_id)
            else:
                if not all([employee_id, date]):
                    return Response({
                        'success': False,
                        'error': 'Provide attendance_id or employee_id and date'
                    }, status=status.HTTP_400_BAD_REQUEST)

                # Accept multiple date formats like DD/MM/YYYY or YYYY-MM-DD and match DateTimeField too
                parsed_date = None
                try:
                    parsed_date = datetime.fromisoformat(date).date()
                except Exception:
                    try:
                        parsed_date = datetime.strptime(date, '%d/%m/%Y').date()
                    except Exception:
                        try:
                            parsed_date = datetime.strptime(date, '%Y-%m-%d').date()
                        except Exception:
                            parsed_date = None

                if parsed_date is None:
                    return Response({'success': False, 'error': 'Invalid date format. Use YYYY-MM-DD or DD/MM/YYYY'}, status=status.HTTP_400_BAD_REQUEST)

                # Match DateField or DateTimeField on Attendance.date
                date_field = Attendance._meta.get_field('date')
                if isinstance(date_field, models.DateTimeField):
                    attendance = Attendance.objects.filter(employee_id=employee_id).filter(
                        Q(date__date=parsed_date) | Q(date=parsed_date)
                    ).first()
                else:
                    attendance = Attendance.objects.filter(employee_id=employee_id, date=parsed_date).first()
                if not attendance:
                    return Response({'success': False, 'error': 'Attendance record not found for given employee/date'}, status=status.HTTP_404_NOT_FOUND)

            # Incoming fields
            s1 = request.data.get('shift_1_status')
            s2 = request.data.get('shift_2_status')
            status_code = request.data.get('status')

            legacy_map = {
                'P': ('P', 'P'),
                'A': ('A', 'A'),
                'WO': ('WO', 'WO'),
                'H': ('H', 'H'),
                'HD': ('HD', 'HD'),
                'FSP': ('P', None),
                'SSP': (None, 'P'),
                'FSA': ('A', None),
                'SSA': (None, 'A'),
            }

            if status_code and status_code in legacy_map:
                m1, m2 = legacy_map[status_code]
                if m1 is not None and s1 is None:
                    s1 = m1
                if m2 is not None and s2 is None:
                    s2 = m2

            # Update only provided fields
            changed = False
            if s1 is not None:
                attendance.shift_1_status = s1
                changed = True
            if s2 is not None:
                attendance.shift_2_status = s2
                changed = True

            if changed:
                attendance.save()

            serializer = AttendanceSerializer(attendance)
            return Response({
                'success': True,
                'message': 'Attendance updated' if changed else 'No changes provided',
                'data': serializer.data
            }, status=status.HTTP_200_OK)

        except Attendance.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Attendance record not found'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    # ==================== SALARY MANAGEMENT ====================
    
    @action(detail=False, methods=['post'], url_path='create-salary-structure')
    def create_salary_structure(self, request):
        """
        Create salary structure for an employee
        
        Request Body:
        {
            "employee_id": 1,
            "CTC": 600000,
            "basic": 300000,
            "da": 50000,
            "hra": 100000,
            "conveyance": 20000,
            "bonus": 30000,
            "other_allowances": 100000,
            "pf_deduction": 36000,
            "esi_deduction": 12000,
            "pt_deduction": 2400,
            "lwf_deduction": 1200,
            "insurance": 5000,
            "advance": 0
        }
        """
        try:
            employee_id = request.data.get('employee_id')
            
            if not employee_id:
                return Response({
                    'success': False,
                    'error': 'employee_id is required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            employee = Employee.objects.get(id=employee_id)
            
            # Check if salary structure already exists
            if hasattr(employee, 'salarystructure'):
                return Response({
                    'success': False,
                    'error': 'Salary structure already exists for this employee. Use update API.'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Create salary structure
            data = request.data.copy()
            data.pop('employee_id', None)
            
            serializer = SalaryStructureSerializer(data=data)
            if serializer.is_valid():
                serializer.save(employee=employee)
                
                return Response({
                    'success': True,
                    'message': 'Salary structure created successfully',
                    'data': serializer.data
                }, status=status.HTTP_201_CREATED)
            
            return Response({
                'success': False,
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
            
        except Employee.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Employee not found'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['put'], url_path='update-salary-structure')
    def update_salary_structure(self, request):
        """
        Update salary structure for an employee
        Records increment in history
        
        Request Body:
        {
            "employee_id": 1,
            "CTC": 650000,
            "basic": 325000,
            ... (other salary components)
        }
        """
        try:
            employee_id = request.data.get('employee_id')
            
            if not employee_id:
                return Response({
                    'success': False,
                    'error': 'employee_id is required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            employee = Employee.objects.get(id=employee_id)
            
            if not hasattr(employee, 'salarystructure'):
                return Response({
                    'success': False,
                    'error': 'No salary structure found. Use create API first.'
                }, status=status.HTTP_404_NOT_FOUND)
            
            salary_structure = employee.salarystructure
            old_ctc = salary_structure.CTC
            new_ctc = request.data.get('CTC', old_ctc)
            
            # Update salary structure
            data = request.data.copy()
            data.pop('employee_id', None)
            
            serializer = SalaryStructureSerializer(salary_structure, data=data, partial=True)
            if serializer.is_valid():
                serializer.save()
                
                # Record increment if CTC changed
                if old_ctc != new_ctc:
                    IncrementHistory.objects.create(
                        employee=employee,
                        effective_date=timezone.now().date(),
                        old_salary=old_ctc,
                        new_salary=new_ctc
                    )
                
                return Response({
                    'success': True,
                    'message': 'Salary structure updated successfully',
                    'data': serializer.data,
                    'increment_recorded': old_ctc != new_ctc
                }, status=status.HTTP_200_OK)
            
            return Response({
                'success': False,
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
            
        except Employee.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Employee not found'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['get'], url_path='get-salary-structure')
    def get_salary_structure(self, request):
        """
        Get salary structure for an employee
        
        Query Parameters:
        - employee_id (required)
        """
        try:
            employee_id = request.query_params.get('employee_id')
            
            if not employee_id:
                return Response({
                    'success': False,
                    'error': 'employee_id is required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            employee = Employee.objects.get(id=employee_id)
            
            if not hasattr(employee, 'salarystructure'):
                return Response({
                    'success': False,
                    'error': 'No salary structure found for this employee'
                }, status=status.HTTP_404_NOT_FOUND)
            
            serializer = SalaryStructureSerializer(employee.salarystructure)
            
            return Response({
                'success': True,
                'data': serializer.data
            }, status=status.HTTP_200_OK)
            
        except Employee.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Employee not found'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    # ==================== PAYSLIP GENERATION ====================
    
    @action(detail=False, methods=['post'], url_path='generate-payslip')
    def generate_payslip(self, request):
        """
        Generate payslip for an employee
        
        Request Body:
        {
            "employee_id": 1,
            "month": 10,
            "year": 2024,
            "working_days": 26,
            "days_present": 24,
            "overtime_hours": 5,
            "advance_deduction": 5000,
            "other_deductions": 1000
        }
        """
        try:
            from reportlab.lib.pagesizes import A4
            from reportlab.pdfgen import canvas
            from io import BytesIO
            from django.core.files.base import ContentFile
            
            employee_id = request.data.get('employee_id')
            month = request.data.get('month')
            year = request.data.get('year')
            working_days = request.data.get('working_days', 26)
            days_present = request.data.get('days_present')
            
            if not all([employee_id, month, year, days_present]):
                return Response({
                    'success': False,
                    'error': 'employee_id, month, year, and days_present are required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            employee = Employee.objects.get(id=employee_id)
            
            if not hasattr(employee, 'salarystructure'):
                return Response({
                    'success': False,
                    'error': 'No salary structure found for this employee'
                }, status=status.HTTP_404_NOT_FOUND)
            
            salary_structure = employee.salarystructure
            
            # Calculate pro-rated salary based on attendance
            attendance_ratio = Decimal(str(days_present)) / Decimal(str(working_days))
            
            # Calculate earnings
            basic_earned = salary_structure.basic * attendance_ratio / 12
            da_earned = salary_structure.da * attendance_ratio / 12
            hra_earned = salary_structure.hra * attendance_ratio / 12
            conveyance_earned = salary_structure.conveyance * attendance_ratio / 12
            bonus_earned = salary_structure.bonus * attendance_ratio / 12
            other_allowances_earned = salary_structure.other_allowances * attendance_ratio / 12
            
            gross_salary = sum([
                basic_earned, da_earned, hra_earned, 
                conveyance_earned, bonus_earned, other_allowances_earned
            ])
            
            # Calculate deductions (pro-rated)
            pf_deduction = salary_structure.pf_deduction * attendance_ratio / 12
            esi_deduction = salary_structure.esi_deduction * attendance_ratio / 12
            pt_deduction = salary_structure.pt_deduction / 12
            lwf_deduction = salary_structure.lwf_deduction / 12
            insurance = salary_structure.insurance / 12
            advance = Decimal(str(request.data.get('advance_deduction', 0)))
            other_deductions = Decimal(str(request.data.get('other_deductions', 0)))
            
            total_deductions = sum([
                pf_deduction, esi_deduction, pt_deduction, 
                lwf_deduction, insurance, advance, other_deductions
            ])
            
            net_salary = gross_salary - total_deductions
            
            # Generate PDF
            buffer = BytesIO()
            pdf = canvas.Canvas(buffer, pagesize=A4)
            
            # Add content to PDF
            pdf.setFont("Helvetica-Bold", 16)
            pdf.drawString(200, 800, "PAYSLIP")
            
            pdf.setFont("Helvetica", 12)
            pdf.drawString(50, 750, f"Employee: {employee.full_name}")
            pdf.drawString(50, 730, f"Employee Code: {employee.employee_code}")
            pdf.drawString(50, 710, f"Month: {month}/{year}")
            pdf.drawString(50, 690, f"Working Days: {working_days}")
            pdf.drawString(50, 670, f"Days Present: {days_present}")
            
            # Earnings
            y_position = 630
            pdf.setFont("Helvetica-Bold", 14)
            pdf.drawString(50, y_position, "EARNINGS")
            y_position -= 30
            
            pdf.setFont("Helvetica", 11)
            earnings = [
                ("Basic", float(basic_earned)),
                ("DA", float(da_earned)),
                ("HRA", float(hra_earned)),
                ("Conveyance", float(conveyance_earned)),
                ("Bonus", float(bonus_earned)),
                ("Other Allowances", float(other_allowances_earned)),
            ]
            
            for item, amount in earnings:
                pdf.drawString(70, y_position, item)
                pdf.drawString(400, y_position, f"₹ {amount:.2f}")
                y_position -= 20
            
            pdf.setFont("Helvetica-Bold", 12)
            pdf.drawString(70, y_position, "Gross Salary")
            pdf.drawString(400, y_position, f"₹ {float(gross_salary):.2f}")
            y_position -= 40
            
            # Deductions
            pdf.setFont("Helvetica-Bold", 14)
            pdf.drawString(50, y_position, "DEDUCTIONS")
            y_position -= 30
            
            pdf.setFont("Helvetica", 11)
            deductions = [
                ("PF", float(pf_deduction)),
                ("ESI", float(esi_deduction)),
                ("PT", float(pt_deduction)),
                ("LWF", float(lwf_deduction)),
                ("Insurance", float(insurance)),
                ("Advance", float(advance)),
                ("Other Deductions", float(other_deductions)),
            ]
            
            for item, amount in deductions:
                pdf.drawString(70, y_position, item)
                pdf.drawString(400, y_position, f"₹ {amount:.2f}")
                y_position -= 20
            
            pdf.setFont("Helvetica-Bold", 12)
            pdf.drawString(70, y_position, "Total Deductions")
            pdf.drawString(400, y_position, f"₹ {float(total_deductions):.2f}")
            y_position -= 40
            
            # Net Salary
            pdf.setFont("Helvetica-Bold", 14)
            pdf.drawString(50, y_position, "NET SALARY")
            pdf.drawString(400, y_position, f"₹ {float(net_salary):.2f}")
            
            pdf.save()
            buffer.seek(0)
            
            # Create or update payslip
            payslip, created = Payslip.objects.update_or_create(
                employee=employee,
                month=month,
                year=year,
                defaults={
                    'gross_salary': gross_salary,
                    'deductions': total_deductions,
                    'net_salary': net_salary,
                }
            )
            
            # Save PDF file
            filename = f"payslip_{employee.employee_code}_{month}_{year}.pdf"
            payslip.pdf_file.save(filename, ContentFile(buffer.getvalue()), save=True)
            
            serializer = PayslipSerializer(payslip)
            
            return Response({
                'success': True,
                'message': 'Payslip generated successfully',
                'data': serializer.data
            }, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)
            
        except Employee.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Employee not found'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['get'], url_path='get-payslips')
    def get_payslips(self, request):
        """
        Get payslips for an employee or all employees
        
        Query Parameters:
        - employee_id (optional): Specific employee
        - month (optional): Month number
        - year (optional): Year
        - company_id (optional): Filter by company
        """
        try:
            employee_id = request.query_params.get('employee_id')
            month = request.query_params.get('month')
            year = request.query_params.get('year')
            company_id = request.query_params.get('company_id')
            
            payslips = Payslip.objects.all()
            
            if employee_id:
                payslips = payslips.filter(employee_id=employee_id)
            
            if month:
                payslips = payslips.filter(month=month)
            
            if year:
                payslips = payslips.filter(year=year)
            
            if company_id:
                payslips = payslips.filter(
                    Q(employee__main_company_id=company_id) | 
                    Q(employee__sub_company_id=company_id)
                )
            
            serializer = PayslipSerializer(payslips, many=True)
            
            return Response({
                'success': True,
                'count': payslips.count(),
                'data': serializer.data
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    # ==================== OVERTIME MANAGEMENT ====================
    
    @action(detail=False, methods=['post'], url_path='record-overtime')
    def record_overtime(self, request):
        """
        Record overtime hours for an employee
        
        Request Body:
        {
            "employee_id": 1,
            "date": "2024-10-07",
            "hours": 3.5
        }
        """
        try:
            employee_id = request.data.get('employee_id')
            date = request.data.get('date')
            hours = request.data.get('hours')
            
            if not all([employee_id, date, hours]):
                return Response({
                    'success': False,
                    'error': 'employee_id, date, and hours are required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            employee = Employee.objects.get(id=employee_id)
            
            overtime, created = OvertimeRecord.objects.update_or_create(
                employee=employee,
                date=date,
                defaults={'hours': hours}
            )
            
            serializer = OvertimeRecordSerializer(overtime)
            
            return Response({
                'success': True,
                'message': 'Overtime recorded successfully',
                'data': serializer.data
            }, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)
            
        except Employee.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Employee not found'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['get'], url_path='overtime-report')
    def overtime_report(self, request):
        """
        Get overtime report
        
        Query Parameters:
        - employee_id (optional): Specific employee
        - start_date (required): Start date
        - end_date (required): End date
        - company_id (optional): Filter by company
        """
        try:
            employee_id = request.query_params.get('employee_id')
            start_date = request.query_params.get('start_date')
            end_date = request.query_params.get('end_date')
            company_id = request.query_params.get('company_id')
            
            if not start_date or not end_date:
                return Response({
                    'success': False,
                    'error': 'start_date and end_date are required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            overtime_qs = OvertimeRecord.objects.filter(
                date__gte=start_date,
                date__lte=end_date
            )
            
            if employee_id:
                overtime_qs = overtime_qs.filter(employee_id=employee_id)
            
            if company_id:
                overtime_qs = overtime_qs.filter(
                    Q(employee__main_company_id=company_id) | 
                    Q(employee__sub_company_id=company_id)
                )
            
            # Group by employee
            report_data = []
            employees = overtime_qs.values('employee').distinct()
            
            for emp in employees:
                emp_id = emp['employee']
                employee = Employee.objects.get(id=emp_id)
                emp_overtime = overtime_qs.filter(employee_id=emp_id)
                
                total_hours = emp_overtime.aggregate(total=Sum('hours'))['total'] or 0
                
                report_data.append({
                    'employee_id': emp_id,
                    'employee_code': employee.employee_code,
                    'employee_name': employee.full_name,
                    'total_overtime_hours': float(total_hours),
                    'records_count': emp_overtime.count(),
                })
            
            return Response({
                'success': True,
                'period': {
                    'start_date': start_date,
                    'end_date': end_date,
                },
                'total_employees': len(report_data),
                'total_overtime_hours': sum([r['total_overtime_hours'] for r in report_data]),
                'data': report_data
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    # ==================== EMPLOYEE STATUS MANAGEMENT ====================
    
    @action(detail=False, methods=['put'], url_path='update-employee-status')
    def update_employee_status(self, request):
        """
        Update employee status (ACTIVE, LEFT, TERMINATED)
        
        Request Body:
        {
            "employee_id": 1,
            "status": "LEFT",
            "remarks": "Resigned"
        }
        """
        try:
            employee_id = request.data.get('employee_id')
            new_status = request.data.get('status')
            
            if not all([employee_id, new_status]):
                return Response({
                    'success': False,
                    'error': 'employee_id and status are required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            if new_status not in ['ACTIVE', 'LEFT', 'TERMINATED']:
                return Response({
                    'success': False,
                    'error': 'Invalid status. Must be ACTIVE, LEFT, or TERMINATED'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            employee = Employee.objects.get(id=employee_id)
            old_status = employee.status
            employee.status = new_status
            employee.save()
            
            return Response({
                'success': True,
                'message': f'Employee status updated from {old_status} to {new_status}',
                'data': {
                    'employee_id': employee.id,
                    'employee_name': employee.full_name,
                    'old_status': old_status,
                    'new_status': new_status,
                }
            }, status=status.HTTP_200_OK)
            
        except Employee.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Employee not found'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['put'], url_path='update-employee-full')
    def update_employee_full(self, request):
        """
        Update full employee data (personal, contact, official, identity, bank).

        Request body should include either `employee_id` or `employee_code` and can contain nested sections:
        personal_information, contact_information, official_information, identity_documents, bank_information
        """
        try:
            # Identify employee
            employee_id = request.data.get('employee_id') or request.query_params.get('employee_id')
            employee_code = request.data.get('employee_code') or request.query_params.get('employee_code')

            if not employee_id and not employee_code:
                return Response({'success': False, 'error': 'Provide employee_id or employee_code'}, status=status.HTTP_400_BAD_REQUEST)

            try:
                if employee_id:
                    employee = Employee.objects.get(id=employee_id)
                else:
                    employee = Employee.objects.get(employee_code=employee_code)
            except Employee.DoesNotExist:
                return Response({'success': False, 'error': 'Employee not found'}, status=status.HTTP_404_NOT_FOUND)

            payload = request.data

            # Helpers
            def _parse_date(s):
                if not s:
                    return None
                try:
                    return datetime.fromisoformat(s).date()
                except Exception:
                    for fmt in ('%Y-%m-%d', '%d/%m/%Y'):
                        try:
                            return datetime.strptime(s, fmt).date()
                        except Exception:
                            continue
                return None

            def _map_gender(g):
                if not g:
                    return None
                g = str(g).strip().lower()
                if g in ('m', 'male'):
                    return 'M'
                if g in ('f', 'female'):
                    return 'F'
                return 'O'

            def _map_marital(m):
                if not m:
                    return None
                m = str(m).strip().lower()
                if m in ('single', 's'):
                    return 'S'
                if m in ('married', 'm'):
                    return 'M'
                if m in ('divorced', 'd'):
                    return 'D'
                if m in ('widowed', 'w'):
                    return 'W'
                return m.upper()

            # 1) Personal information
            pi = payload.get('personal_information') or {}
            if pi:
                if 'full_name' in pi and pi.get('full_name') is not None:
                    employee.full_name = pi.get('full_name')
                if 'employee_code' in pi and pi.get('employee_code'):
                    employee.employee_code = pi.get('employee_code')
                if 'date_of_birth' in pi and pi.get('date_of_birth'):
                    dob = _parse_date(pi.get('date_of_birth'))
                    if dob:
                        employee.date_of_birth = dob
                if 'gender' in pi and pi.get('gender') is not None:
                    g = _map_gender(pi.get('gender'))
                    if g:
                        employee.gender = g
                if 'marital_status' in pi and pi.get('marital_status') is not None:
                    ms = _map_marital(pi.get('marital_status'))
                    if ms:
                        employee.marital_status = ms
                # photo handling skipped if null; accept base64/file through separate endpoint

            # 2) Contact information
            ci = payload.get('contact_information') or {}
            if ci:
                if 'mobile_number' in ci and ci.get('mobile_number') is not None:
                    employee.mobile_number = ci.get('mobile_number')
                if 'email' in ci and ci.get('email') is not None:
                    employee.email = ci.get('email')
                if 'current_address' in ci and ci.get('current_address') is not None:
                    employee.current_address = ci.get('current_address')
                if 'permanent_address' in ci and ci.get('permanent_address') is not None:
                    employee.permanent_address = ci.get('permanent_address')

            employee.save()

            # 3) Official information (OfficialDetails)
            oi = payload.get('official_information') or {}
            if oi:
                od_defaults = {}
                if 'date_of_joining' in oi and oi.get('date_of_joining'):
                    doj = _parse_date(oi.get('date_of_joining'))
                    if doj:
                        od_defaults['date_of_joining'] = doj
                for k in ('department', 'designation', 'location', 'supervisor_name', 'salary_type'):
                    if oi.get(k) is not None:
                        od_defaults[k] = oi.get(k)

                if od_defaults:
                    OfficialDetails.objects.update_or_create(employee=employee, defaults=od_defaults)

            # 4) Identity documents
            idd = payload.get('identity_documents') or {}
            if idd:
                id_defaults = {}
                for f in ('aadhaar_number', 'pan_number', 'esi_number', 'pf_uan_number'):
                    if idd.get(f) is not None:
                        # model uses aadhaar_number, pan_number, esi_number, pf_uan_number
                        id_defaults[f] = idd.get(f)

                if id_defaults:
                    # create or update IdentityDocument
                    try:
                        ident = IdentityDocument.objects.filter(employee=employee).first()
                        if ident:
                            for k, v in id_defaults.items():
                                setattr(ident, k, v)
                            ident.save()
                        else:
                            IdentityDocument.objects.create(employee=employee, **id_defaults)
                    except Exception:
                        # best-effort: ignore
                        pass

            # 5) Bank information
            bd = payload.get('bank_information') or {}
            if bd:
                bank_defaults = {}
                for f in ('bank_name', 'account_number', 'ifsc_code', 'branch_name'):
                    if bd.get(f) is not None:
                        bank_defaults[f] = bd.get(f)

                if bank_defaults:
                    try:
                        bank = BankDetails.objects.filter(employee=employee).first()
                        if bank:
                            for k, v in bank_defaults.items():
                                setattr(bank, k, v)
                            bank.save()
                        else:
                            BankDetails.objects.create(employee=employee, **bank_defaults)
                    except Exception:
                        pass

            # Build response summary
            resp = {
                'employee_id': employee.id,
                'employee_code': employee.employee_code,
                'full_name': employee.full_name,
                'email': employee.email,
            }

            return Response({'success': True, 'message': 'Employee updated', 'data': resp}, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({'success': False, 'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['get'], url_path='employee-list')
    def employee_list(self, request):
        """
        List all employees visible to this HR user.

        Query params:
        - company_id (optional): restrict to a company
        - status (optional): ACTIVE/LEFT/TERMINATED
        - search (optional): search by name, code or email

        Returns serialized list of employees.
        """
        try:
            company_id = request.query_params.get('company_id')
            status_filter = request.query_params.get('status')
            search = request.query_params.get('search')
            role_param = request.query_params.get('role')

            qs = Employee.objects.all()

            # Prefer restricting to the HR user's sub_company only (same subcompany employees)
            try:
                user_emp = getattr(request.user, 'employee', None)
            except Exception:
                user_emp = None

            if user_emp and getattr(user_emp, 'sub_company_id', None):
                qs = qs.filter(sub_company_id=user_emp.sub_company_id)
            elif company_id:
                # explicit override by company_id (main or sub)
                qs = qs.filter(Q(main_company_id=company_id) | Q(sub_company_id=company_id))
            else:
                # no HR sub_company found and no explicit company_id: default to active employees only
                qs = qs.filter(status='ACTIVE')

            # Status filter (optional)
            if status_filter:
                qs = qs.filter(status__iexact=status_filter)

            # Role filter: accept comma-separated values, case-insensitive
            if role_param:
                roles = [r.strip() for r in role_param.split(',') if r.strip()]
                if roles:
                    role_q = None
                    for r in roles:
                        q = Q(role__iexact=r)
                        role_q = q if role_q is None else (role_q | q)
                    if role_q is not None:
                        qs = qs.filter(role_q)

            # Search filter
            if search:
                qs = qs.filter(
                    Q(full_name__icontains=search) |
                    Q(employee_code__icontains=search) |
                    Q(email__icontains=search)
                )

            serializer = EmployeeSerializer(qs.select_related('officialdetails'), many=True)
            return Response({'success': True, 'count': qs.count(), 'data': serializer.data}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'success': False, 'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['get'], url_path=r'employee-list/(?P<emp_id>[^/.]+)')
    def employee_detail(self, request, emp_id=None):
        """
        Retrieve a single employee by id or employee_code.

        URL: /api/hr-dashboard/employee-list/<emp_id>/
        """
        try:
            emp = None
            # numeric -> try id
            if str(emp_id).isdigit():
                emp = Employee.objects.filter(id=int(emp_id)).first()
            # fallback to employee_code
            if not emp:
                emp = Employee.objects.filter(employee_code=str(emp_id)).first()

            if not emp:
                return Response({'success': False, 'error': 'Employee not found'}, status=status.HTTP_404_NOT_FOUND)

            serializer = EmployeeSerializer(emp)
            return Response({'success': True, 'data': serializer.data}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'success': False, 'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    # ==================== ANALYTICS & REPORTS ====================
    
    @action(detail=False, methods=['get'], url_path='analytics')
    def analytics(self, request):
        """
        Get comprehensive HR analytics
        
        Query Parameters:
        - company_id (optional): Filter by company
        - year (optional): Year for analysis (default: current year)
        """
        try:
            company_id = request.query_params.get('company_id')
            year = request.query_params.get('year', timezone.now().year)
            
            employees = Employee.objects.filter(status='ACTIVE')
            if company_id:
                employees = employees.filter(
                    Q(main_company_id=company_id) | Q(sub_company_id=company_id)
                )
            
            # Headcount analysis
            headcount_by_role = employees.values('role').annotate(count=Count('id'))
            headcount_by_gender = employees.values('gender').annotate(count=Count('id'))
            
            # Salary analysis
            salary_stats = SalaryStructure.objects.filter(
                employee__in=employees
            ).aggregate(
                min_ctc=Min('CTC'),
                max_ctc=Max('CTC'),
                avg_ctc=Avg('CTC'),
                total_payroll=Sum('CTC')
            )
            
            # Attendance trends (last 12 months)
            twelve_months_ago = timezone.now().date() - timedelta(days=365)
            attendance_trends = []
            
            for i in range(12):
                month_start = (timezone.now() - timedelta(days=30*i)).replace(day=1).date()
                if month_start.month == 12:
                    month_end = month_start.replace(year=month_start.year+1, month=1)
                else:
                    month_end = month_start.replace(month=month_start.month+1)
                
                attendance = Attendance.objects.filter(
                    employee__in=employees,
                    date__gte=month_start,
                    date__lt=month_end
                )
                
                attendance_trends.append({
                    'month': month_start.strftime('%B %Y'),
                    'present': attendance.filter(Q(shift_1_status='P') | Q(shift_2_status='P')).count(),
                    'absent': attendance.filter(Q(shift_1_status='A') | Q(shift_2_status='A')).count(),
                })
            
            # Turnover analysis
            joinings_this_year = employees.filter(
                officialdetails__date_of_joining__year=year
            ).count()
            
            leavings_this_year = Employee.objects.filter(
                Q(status='LEFT') | Q(status='TERMINATED')
            ).count()
            
            return Response({
                'success': True,
                'year': year,
                'headcount': {
                    'total_active': employees.count(),
                    'by_role': list(headcount_by_role),
                    'by_gender': list(headcount_by_gender),
                },
                'salary_analysis': {
                    'min_ctc': float(salary_stats.get('min_ctc') or 0),
                    'max_ctc': float(salary_stats.get('max_ctc') or 0),
                    'avg_ctc': float(salary_stats.get('avg_ctc') or 0),
                    'total_annual_payroll': float(salary_stats.get('total_payroll') or 0),
                },
                'attendance_trends': list(reversed(attendance_trends[:12])),
                'turnover': {
                    'joinings': joinings_this_year,
                    'leavings': leavings_this_year,
                    'turnover_rate': (leavings_this_year / employees.count() * 100) if employees.count() > 0 else 0,
                }
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
