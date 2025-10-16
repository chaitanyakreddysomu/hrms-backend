"""
Supervisor Dashboard APIs for team management
Includes: Team overview, attendance tracking, performance monitoring, approvals
"""

from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Count, Sum, Avg, Q
from django.utils import timezone
from datetime import datetime, timedelta
from decimal import Decimal

from .models import (
    Employee, Attendance, OvertimeRecord, OfficialDetails,
    SalaryStructure, Payslip
)
from .serializers import (
    EmployeeSerializer, AttendanceSerializer, OvertimeRecordSerializer,
    OfficialDetailsSerializer
)
from rest_framework.permissions import IsAuthenticated


class IsSupervisor(permissions.BasePermission):
    """
    Custom permission for Supervisor role
    """
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        try:
            employee = Employee.objects.get(
                Q(employee_code=request.user.username) | Q(email=request.user.email)
            )
            return employee.role == 'Supervisor'
        except Employee.DoesNotExist:
            return False


class SupervisorDashboardViewSet(viewsets.ViewSet):
    """
    Supervisor Dashboard ViewSet for team management
    
    Features:
    - Team Overview & Statistics
    - Team Attendance Tracking
    - Team Performance Monitoring
    - Overtime Management
    - Team Reports
    - Quick Actions
    
    Access: Supervisor Role ONLY
    """
    permission_classes = [IsSupervisor]

    def _get_supervisor_employee(self, request):
        """Helper method to get supervisor's employee record"""
        try:
            return Employee.objects.get(
                Q(employee_code=request.user.username) | Q(email=request.user.email)
            )
        except Employee.DoesNotExist:
            return None

    def _get_team_members(self, supervisor):
        """Get all team members under this supervisor"""
        if not supervisor:
            return Employee.objects.none()
        
        # Get employees where supervisor_name matches this supervisor's name
        return Employee.objects.filter(
            officialdetails__supervisor_name=supervisor.full_name,
            status='ACTIVE'
        )

    # ==================== TEAM OVERVIEW ====================
    
    @action(detail=False, methods=['get'], url_path='team-overview')
    def team_overview(self, request):
        """
        Get comprehensive team overview statistics
        
        Query Parameters:
        - month (optional): Month number (1-12)
        - year (optional): Year (e.g., 2024)
        
        Returns:
        - Team member count
        - Attendance statistics
        - Performance metrics
        - Recent activities
        """
        try:
            supervisor = self._get_supervisor_employee(request)
            if not supervisor:
                return Response({
                    'success': False,
                    'error': 'Supervisor record not found'
                }, status=status.HTTP_404_NOT_FOUND)
            
            team_members = self._get_team_members(supervisor)
            
            month = request.query_params.get('month', timezone.now().month)
            year = request.query_params.get('year', timezone.now().year)
            
            # Team Statistics
            total_team = team_members.count()
            
            # Department-wise breakdown
            departments = team_members.values(
                'officialdetails__department'
            ).annotate(count=Count('id'))
            
            # Designation breakdown
            designations = team_members.values(
                'officialdetails__designation'
            ).annotate(count=Count('id'))
            
            # Attendance Statistics for current month
            start_date = datetime(int(year), int(month), 1).date()
            if int(month) == 12:
                end_date = datetime(int(year) + 1, 1, 1).date()
            else:
                end_date = datetime(int(year), int(month) + 1, 1).date()
            
            attendance_records = Attendance.objects.filter(
                employee__in=team_members,
                date__gte=start_date,
                date__lt=end_date
            )
            
            attendance_stats = {
                'present': attendance_records.filter(status='P').count(),
                'absent': attendance_records.filter(status='A').count(),
                'weekly_off': attendance_records.filter(status='WO').count(),
                'holiday': attendance_records.filter(status='H').count(),
                'half_day': attendance_records.filter(status='HD').count(),
            }
            
            # Calculate attendance percentage
            total_working_days = attendance_stats['present'] + attendance_stats['absent'] + attendance_stats['half_day']
            attendance_percentage = (attendance_stats['present'] / total_working_days * 100) if total_working_days > 0 else 0
            
            # Overtime Statistics
            overtime_records = OvertimeRecord.objects.filter(
                employee__in=team_members,
                date__gte=start_date,
                date__lt=end_date
            )
            total_overtime_hours = overtime_records.aggregate(total=Sum('hours'))['total'] or 0
            
            # Top performers (based on attendance)
            top_performers = []
            for member in team_members[:5]:
                member_attendance = attendance_records.filter(employee=member)
                present_count = member_attendance.filter(status='P').count()
                top_performers.append({
                    'employee_id': member.id,
                    'employee_code': member.employee_code,
                    'full_name': member.full_name,
                    'designation': getattr(member.officialdetails, 'designation', 'N/A') if hasattr(member, 'officialdetails') else 'N/A',
                    'present_days': present_count
                })
            
            # Sort by present days
            top_performers = sorted(top_performers, key=lambda x: x['present_days'], reverse=True)[:5]
            
            return Response({
                'success': True,
                'supervisor': {
                    'id': supervisor.id,
                    'name': supervisor.full_name,
                    'employee_code': supervisor.employee_code,
                    'department': getattr(supervisor.officialdetails, 'department', 'N/A') if hasattr(supervisor, 'officialdetails') else 'N/A'
                },
                'data': {
                    'team': {
                        'total_members': total_team,
                        'by_department': list(departments),
                        'by_designation': list(designations),
                    },
                    'attendance': {
                        'month': month,
                        'year': year,
                        'statistics': attendance_stats,
                        'attendance_percentage': round(attendance_percentage, 2),
                        'total_records': attendance_records.count(),
                    },
                    'overtime': {
                        'month': month,
                        'year': year,
                        'total_hours': float(total_overtime_hours),
                        'records_count': overtime_records.count(),
                    },
                    'top_performers': top_performers
                }
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    # ==================== TEAM MEMBERS ====================
    
    @action(detail=False, methods=['get'], url_path='team-members')
    def team_members(self, request):
        """
        Get list of all team members under this supervisor
        
        Query Parameters:
        - department (optional): Filter by department
        - designation (optional): Filter by designation
        
        Returns:
        - List of team members with details
        """
        try:
            supervisor = self._get_supervisor_employee(request)
            if not supervisor:
                return Response({
                    'success': False,
                    'error': 'Supervisor record not found'
                }, status=status.HTTP_404_NOT_FOUND)
            
            team_members = self._get_team_members(supervisor)
            
            # Apply filters
            department = request.query_params.get('department')
            designation = request.query_params.get('designation')
            
            if department:
                team_members = team_members.filter(officialdetails__department=department)
            
            if designation:
                team_members = team_members.filter(officialdetails__designation=designation)
            
            # Prepare team member data
            members_data = []
            for member in team_members:
                members_data.append({
                    'employee_id': member.id,
                    'employee_code': member.employee_code,
                    'full_name': member.full_name,
                    'email': member.email,
                    'mobile_number': member.mobile_number,
                    'role': member.role,
                    'department': getattr(member.officialdetails, 'department', 'N/A') if hasattr(member, 'officialdetails') else 'N/A',
                    'designation': getattr(member.officialdetails, 'designation', 'N/A') if hasattr(member, 'officialdetails') else 'N/A',
                    'date_of_joining': str(getattr(member.officialdetails, 'date_of_joining', 'N/A')) if hasattr(member, 'officialdetails') else 'N/A',
                    'status': member.status
                })
            
            return Response({
                'success': True,
                'supervisor': {
                    'id': supervisor.id,
                    'name': supervisor.full_name
                },
                'total_members': len(members_data),
                'team_members': members_data
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    # ==================== ATTENDANCE MANAGEMENT ====================
    
    @action(detail=False, methods=['post'], url_path='mark-team-attendance')
    def mark_team_attendance(self, request):
        """
        Mark attendance for team members
        
        Request Body:
        {
            "employee_id": 1,
            "date": "2024-10-07",
            "status": "P"
        }
        """
        try:
            supervisor = self._get_supervisor_employee(request)
            if not supervisor:
                return Response({
                    'success': False,
                    'error': 'Supervisor record not found'
                }, status=status.HTTP_404_NOT_FOUND)
            
            employee_id = request.data.get('employee_id')
            date_str = request.data.get('date')
            attendance_status = request.data.get('status')
            
            if not all([employee_id, date_str, attendance_status]):
                return Response({
                    'success': False,
                    'error': 'employee_id, date, and status are required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Verify employee is in supervisor's team
            team_members = self._get_team_members(supervisor)
            employee = team_members.filter(id=employee_id).first()
            
            if not employee:
                return Response({
                    'success': False,
                    'error': 'Employee not found in your team'
                }, status=status.HTTP_404_NOT_FOUND)
            
            # Parse date string to date object
            try:
                date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
            except ValueError:
                return Response({
                    'success': False,
                    'error': 'Invalid date format. Use YYYY-MM-DD'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Create or update attendance
            attendance, created = Attendance.objects.update_or_create(
                employee=employee,
                date=date_obj,
                defaults={'status': attendance_status}
            )
            
            serializer = AttendanceSerializer(attendance)
            
            return Response({
                'success': True,
                'message': 'Attendance marked successfully' if created else 'Attendance updated successfully',
                'data': serializer.data
            }, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['post'], url_path='bulk-mark-team-attendance')
    def bulk_mark_team_attendance(self, request):
        """
        Mark attendance for multiple team members at once
        
        Request Body:
        {
            "date": "2024-10-07",
            "attendance_records": [
                {"employee_id": 1, "status": "P"},
                {"employee_id": 2, "status": "A"}
            ]
        }
        """
        try:
            supervisor = self._get_supervisor_employee(request)
            if not supervisor:
                return Response({
                    'success': False,
                    'error': 'Supervisor record not found'
                }, status=status.HTTP_404_NOT_FOUND)
            
            date_str = request.data.get('date')
            attendance_records = request.data.get('attendance_records', [])
            
            if not date_str or not attendance_records:
                return Response({
                    'success': False,
                    'error': 'date and attendance_records are required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Parse date
            try:
                date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
            except ValueError:
                return Response({
                    'success': False,
                    'error': 'Invalid date format. Use YYYY-MM-DD'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            team_members = self._get_team_members(supervisor)
            created_count = 0
            updated_count = 0
            errors = []
            
            for record in attendance_records:
                try:
                    employee = team_members.filter(id=record['employee_id']).first()
                    if not employee:
                        errors.append({
                            'employee_id': record.get('employee_id'),
                            'error': 'Employee not found in your team'
                        })
                        continue
                    
                    attendance, created = Attendance.objects.update_or_create(
                        employee=employee,
                        date=date_obj,
                        defaults={'status': record['status']}
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

    @action(detail=False, methods=['get'], url_path='team-attendance-report')
    def team_attendance_report(self, request):
        """
        Get attendance report for team members
        
        Query Parameters:
        - employee_id (optional): Specific employee
        - start_date (required): Start date (YYYY-MM-DD)
        - end_date (required): End date (YYYY-MM-DD)
        """
        try:
            supervisor = self._get_supervisor_employee(request)
            if not supervisor:
                return Response({
                    'success': False,
                    'error': 'Supervisor record not found'
                }, status=status.HTTP_404_NOT_FOUND)
            
            employee_id = request.query_params.get('employee_id')
            start_date = request.query_params.get('start_date')
            end_date = request.query_params.get('end_date')
            
            if not start_date or not end_date:
                return Response({
                    'success': False,
                    'error': 'start_date and end_date are required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            team_members = self._get_team_members(supervisor)
            
            # Filter attendance records
            attendance_qs = Attendance.objects.filter(
                employee__in=team_members,
                date__gte=start_date,
                date__lte=end_date
            )
            
            if employee_id:
                attendance_qs = attendance_qs.filter(employee_id=employee_id)
            
            # Group by employee
            report_data = []
            employees = attendance_qs.values('employee').distinct()
            
            for emp in employees:
                emp_id = emp['employee']
                employee = Employee.objects.get(id=emp_id)
                emp_attendance = attendance_qs.filter(employee_id=emp_id)
                
                stats = {
                    'present': emp_attendance.filter(status='P').count(),
                    'absent': emp_attendance.filter(status='A').count(),
                    'weekly_off': emp_attendance.filter(status='WO').count(),
                    'holiday': emp_attendance.filter(status='H').count(),
                    'half_day': emp_attendance.filter(status='HD').count(),
                }
                
                total_working = stats['present'] + stats['absent'] + stats['half_day']
                attendance_percentage = (stats['present'] / total_working * 100) if total_working > 0 else 0
                
                report_data.append({
                    'employee_id': emp_id,
                    'employee_code': employee.employee_code,
                    'employee_name': employee.full_name,
                    'designation': getattr(employee.officialdetails, 'designation', 'N/A') if hasattr(employee, 'officialdetails') else 'N/A',
                    'statistics': stats,
                    'total_working_days': stats['present'] + stats['half_day'],
                    'attendance_percentage': round(attendance_percentage, 2)
                })
            
            return Response({
                'success': True,
                'supervisor': {
                    'id': supervisor.id,
                    'name': supervisor.full_name
                },
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

    # ==================== OVERTIME MANAGEMENT ====================
    
    @action(detail=False, methods=['post'], url_path='record-team-overtime')
    def record_team_overtime(self, request):
        """
        Record overtime hours for team member
        
        Request Body:
        {
            "employee_id": 1,
            "date": "2024-10-07",
            "hours": 3.5
        }
        """
        try:
            supervisor = self._get_supervisor_employee(request)
            if not supervisor:
                return Response({
                    'success': False,
                    'error': 'Supervisor record not found'
                }, status=status.HTTP_404_NOT_FOUND)
            
            employee_id = request.data.get('employee_id')
            date_str = request.data.get('date')
            hours = request.data.get('hours')
            
            if not all([employee_id, date_str, hours]):
                return Response({
                    'success': False,
                    'error': 'employee_id, date, and hours are required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Verify employee is in supervisor's team
            team_members = self._get_team_members(supervisor)
            employee = team_members.filter(id=employee_id).first()
            
            if not employee:
                return Response({
                    'success': False,
                    'error': 'Employee not found in your team'
                }, status=status.HTTP_404_NOT_FOUND)
            
            # Parse date
            try:
                date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
            except ValueError:
                return Response({
                    'success': False,
                    'error': 'Invalid date format. Use YYYY-MM-DD'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            overtime, created = OvertimeRecord.objects.update_or_create(
                employee=employee,
                date=date_obj,
                defaults={'hours': hours}
            )
            
            serializer = OvertimeRecordSerializer(overtime)
            
            return Response({
                'success': True,
                'message': 'Overtime recorded successfully',
                'data': serializer.data
            }, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['get'], url_path='team-overtime-report')
    def team_overtime_report(self, request):
        """
        Get overtime report for team
        
        Query Parameters:
        - employee_id (optional): Specific employee
        - start_date (required): Start date
        - end_date (required): End date
        """
        try:
            supervisor = self._get_supervisor_employee(request)
            if not supervisor:
                return Response({
                    'success': False,
                    'error': 'Supervisor record not found'
                }, status=status.HTTP_404_NOT_FOUND)
            
            employee_id = request.query_params.get('employee_id')
            start_date = request.query_params.get('start_date')
            end_date = request.query_params.get('end_date')
            
            if not start_date or not end_date:
                return Response({
                    'success': False,
                    'error': 'start_date and end_date are required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            team_members = self._get_team_members(supervisor)
            
            overtime_qs = OvertimeRecord.objects.filter(
                employee__in=team_members,
                date__gte=start_date,
                date__lte=end_date
            )
            
            if employee_id:
                overtime_qs = overtime_qs.filter(employee_id=employee_id)
            
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
                    'designation': getattr(employee.officialdetails, 'designation', 'N/A') if hasattr(employee, 'officialdetails') else 'N/A',
                    'total_overtime_hours': float(total_hours),
                    'records_count': emp_overtime.count(),
                })
            
            return Response({
                'success': True,
                'supervisor': {
                    'id': supervisor.id,
                    'name': supervisor.full_name
                },
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

    # ==================== TEAM PERFORMANCE ====================
    
    @action(detail=False, methods=['get'], url_path='team-performance')
    def team_performance(self, request):
        """
        Get team performance analytics
        
        Query Parameters:
        - month (optional): Month number
        - year (optional): Year
        """
        try:
            supervisor = self._get_supervisor_employee(request)
            if not supervisor:
                return Response({
                    'success': False,
                    'error': 'Supervisor record not found'
                }, status=status.HTTP_404_NOT_FOUND)
            
            month = request.query_params.get('month', timezone.now().month)
            year = request.query_params.get('year', timezone.now().year)
            
            team_members = self._get_team_members(supervisor)
            
            # Date range
            start_date = datetime(int(year), int(month), 1).date()
            if int(month) == 12:
                end_date = datetime(int(year) + 1, 1, 1).date()
            else:
                end_date = datetime(int(year), int(month) + 1, 1).date()
            
            performance_data = []
            
            for member in team_members:
                # Attendance stats
                attendance = Attendance.objects.filter(
                    employee=member,
                    date__gte=start_date,
                    date__lt=end_date
                )
                
                present = attendance.filter(status='P').count()
                absent = attendance.filter(status='A').count()
                total = present + absent
                attendance_rate = (present / total * 100) if total > 0 else 0
                
                # Overtime
                overtime = OvertimeRecord.objects.filter(
                    employee=member,
                    date__gte=start_date,
                    date__lt=end_date
                ).aggregate(total=Sum('hours'))['total'] or 0
                
                performance_data.append({
                    'employee_id': member.id,
                    'employee_code': member.employee_code,
                    'full_name': member.full_name,
                    'designation': getattr(member.officialdetails, 'designation', 'N/A') if hasattr(member, 'officialdetails') else 'N/A',
                    'attendance_rate': round(attendance_rate, 2),
                    'present_days': present,
                    'absent_days': absent,
                    'overtime_hours': float(overtime),
                    'performance_score': round(attendance_rate, 2)  # Simple score based on attendance
                })
            
            # Sort by performance score
            performance_data = sorted(performance_data, key=lambda x: x['performance_score'], reverse=True)
            
            return Response({
                'success': True,
                'supervisor': {
                    'id': supervisor.id,
                    'name': supervisor.full_name
                },
                'period': {
                    'month': month,
                    'year': year
                },
                'total_members': len(performance_data),
                'data': performance_data
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    # ==================== QUICK ACTIONS ====================
    
    @action(detail=False, methods=['get'], url_path='today-attendance-summary')
    def today_attendance_summary(self, request):
        """
        Get today's attendance summary for quick overview
        
        Returns:
        - Present count
        - Absent count
        - Not marked count
        - List of members with status
        """
        try:
            supervisor = self._get_supervisor_employee(request)
            if not supervisor:
                return Response({
                    'success': False,
                    'error': 'Supervisor record not found'
                }, status=status.HTTP_404_NOT_FOUND)
            
            team_members = self._get_team_members(supervisor)
            today = timezone.now().date()
            
            # Get today's attendance
            today_attendance = Attendance.objects.filter(
                employee__in=team_members,
                date=today
            )
            
            present_count = today_attendance.filter(status='P').count()
            absent_count = today_attendance.filter(status='A').count()
            marked_ids = today_attendance.values_list('employee_id', flat=True)
            not_marked_count = team_members.exclude(id__in=marked_ids).count()
            
            # Detailed list
            members_status = []
            for member in team_members:
                attendance = today_attendance.filter(employee=member).first()
                members_status.append({
                    'employee_id': member.id,
                    'employee_code': member.employee_code,
                    'full_name': member.full_name,
                    'status': attendance.get_status_display() if attendance else 'Not Marked',
                    'status_code': attendance.status if attendance else None
                })
            
            return Response({
                'success': True,
                'supervisor': {
                    'id': supervisor.id,
                    'name': supervisor.full_name
                },
                'date': str(today),
                'summary': {
                    'total_team': team_members.count(),
                    'present': present_count,
                    'absent': absent_count,
                    'not_marked': not_marked_count
                },
                'members_status': members_status
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
