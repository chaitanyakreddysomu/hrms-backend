"""
HR Dashboard APIs for comprehensive HR management system
Includes: Dashboard stats, Attendance, Salary, Payslips, Reports, Analytics
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Count, Sum, Avg, Min, Max, Q
from django.utils import timezone
from datetime import datetime, timedelta
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
                'present': attendance_records.filter(status='P').count(),
                'absent': attendance_records.filter(status='A').count(),
                'weekly_off': attendance_records.filter(status='WO').count(),
                'holiday': attendance_records.filter(status='H').count(),
                'half_day': attendance_records.filter(status='HD').count(),
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
            attendance_status = request.data.get('status')
            
            if not all([employee_id, date, attendance_status]):
                return Response({
                    'success': False,
                    'error': 'employee_id, date, and status are required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            employee = Employee.objects.get(id=employee_id)
            
            # Create or update attendance
            attendance, created = Attendance.objects.update_or_create(
                employee=employee,
                date=date,
                defaults={'status': attendance_status}
            )
            
            serializer = AttendanceSerializer(attendance)
            
            return Response({
                'success': True,
                'message': 'Attendance marked successfully' if created else 'Attendance updated successfully',
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
                    attendance, created = Attendance.objects.update_or_create(
                        employee=employee,
                        date=date,
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
                    'present': emp_attendance.filter(status='P').count(),
                    'absent': emp_attendance.filter(status='A').count(),
                    'weekly_off': emp_attendance.filter(status='WO').count(),
                    'holiday': emp_attendance.filter(status='H').count(),
                    'half_day': emp_attendance.filter(status='HD').count(),
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
                    'present': attendance.filter(status='P').count(),
                    'absent': attendance.filter(status='A').count(),
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
