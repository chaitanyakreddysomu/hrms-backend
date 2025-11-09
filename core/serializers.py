from rest_framework import serializers
from django.contrib.auth import authenticate
from .models import User,ExamQuestion,Admins,ExamSchedule
from django.db import models
from django.contrib.auth import get_user_model
from rest_framework.validators import UniqueValidator
from .utils import generate_presigned_url
from django.contrib.auth.hashers import make_password  
   
# serializers.py
from rest_framework import serializers
from .models import User

import uuid

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'full_name', 'roll_number', 'email', 'college_code', 'exam', 'created_at', 'score']
        read_only_fields = ['id', 'created_at', 'score']

    def create(self, validated_data):
        # Generate a dummy username since AbstractUser requires it
        validated_data['username'] = f"user_{uuid.uuid4().hex[:10]}"
        user = User(**validated_data)
        user.set_unusable_password()  # Disable login
        user.save()
        return user

class AdminSerializer(serializers.ModelSerializer):
    class Meta:
        model = Admins
        fields = ['id','username', 'email', 'password']
        extra_kwargs = {
            'password': {'write_only': True}
        }

    def create(self, validated_data):
        validated_data['password'] = make_password(validated_data['password'])  # Hash password
        return super().create(validated_data)


class AdminLoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

class ExamQuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExamQuestion
        fields = '__all__'
        read_only_fields = ['id']

class ExamScheduleSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExamSchedule
        fields = ['id', 'exam_name', 'exam_date', 'exam_start_time', 'exam_end_time']




# serializers.py
from rest_framework import serializers
from django.contrib.auth.models import User
from .models import *
# In your serializers.py

class CompanySerializer(serializers.ModelSerializer):
    parent_company_name = serializers.CharField(source='parent_company.name', read_only=True)
    sub_companies_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Company
        fields = '__all__'
    
    def get_sub_companies_count(self, obj):
        if obj.is_main_company:
            return obj.sub_companies.count()
        return 0

class SalaryComponentSerializer(serializers.ModelSerializer):
    class Meta:
        model = SalaryComponent
        fields = '__all__'

class ClientProfileSettingsSerializer(serializers.ModelSerializer):
    esi_components = SalaryComponentSerializer(many=True, read_only=True)
    pf_components = SalaryComponentSerializer(many=True, read_only=True)
    pt_components = SalaryComponentSerializer(many=True, read_only=True)
    
    class Meta:
        model = ClientProfileSettings
        fields = '__all__'

class EmployeeSerializer(serializers.ModelSerializer):
    main_company_name = serializers.CharField(source='main_company.name', read_only=True)
    sub_company_name = serializers.CharField(source='sub_company.name', read_only=True)
    
    class Meta:
        model = Employee
        fields = '__all__'

class OfficialDetailsSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source='employee.full_name', read_only=True)
    
    class Meta:
        model = OfficialDetails
        fields = '__all__'

class IdentityDocumentSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source='employee.full_name', read_only=True)
    
    class Meta:
        model = IdentityDocument
        fields = '__all__'

class BankDetailsSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source='employee.full_name', read_only=True)
    
    class Meta:
        model = BankDetails
        fields = '__all__'

class SalaryStructureSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source='employee.full_name', read_only=True)
    net_salary = serializers.ReadOnlyField()
    
    class Meta:
        model = SalaryStructure
        fields = '__all__'

class AttendanceSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source='employee.full_name', read_only=True)
    employee_code = serializers.CharField(source='employee.employee_code', read_only=True)
    
    class Meta:
        model = Attendance
        fields = '__all__'

class OvertimeRecordSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source='employee.full_name', read_only=True)
    employee_code = serializers.CharField(source='employee.employee_code', read_only=True)
    
    class Meta:
        model = OvertimeRecord
        fields = '__all__'

class DocumentSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source='employee.full_name', read_only=True)
    
    class Meta:
        model = Document
        fields = '__all__'

class PayslipSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source='employee.full_name', read_only=True)
    employee_code = serializers.CharField(source='employee.employee_code', read_only=True)
    
    class Meta:
        model = Payslip
        fields = '__all__'

class IncrementHistorySerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source='employee.full_name', read_only=True)
    employee_code = serializers.CharField(source='employee.employee_code', read_only=True)
    
    class Meta:
        model = IncrementHistory
        fields = '__all__'

class ReportSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source='employee.full_name', read_only=True)
    
    class Meta:
        model = Report
        fields = '__all__'


class ComplaintSerializer(serializers.ModelSerializer):
    """Serializer for Complaint model"""
    # These fields are filled from the authenticated user / view and should not be required in the request body
    employee = serializers.PrimaryKeyRelatedField(read_only=True)
    employee_name = serializers.CharField(read_only=True)
    employee_email = serializers.EmailField(read_only=True)
    employee_id_text = serializers.CharField(read_only=True)

    class Meta:
        model = Complaint
        fields = ['id', 'subject', 'details', 'employee', 'employee_name', 'employee_email', 'employee_id_text', 'date_of_complaint', 'status', 'updated_at']
        read_only_fields = ['id', 'date_of_complaint', 'updated_at', 'employee', 'employee_name', 'employee_email', 'employee_id_text']

# Detailed Employee Serializer with all related data
class EmployeeDetailSerializer(serializers.ModelSerializer):
    official_details = OfficialDetailsSerializer(source='officialdetails', read_only=True)
    identity_document = IdentityDocumentSerializer(source='identitydocument', read_only=True)
    bank_details = BankDetailsSerializer(source='bankdetails', read_only=True)
    salary_structure = SalaryStructureSerializer(source='salarystructure', read_only=True)
    documents = DocumentSerializer(many=True, read_only=True)
    main_company_name = serializers.CharField(source='main_company.name', read_only=True)
    sub_company_name = serializers.CharField(source='sub_company.name', read_only=True)
    
    class Meta:
        model = Employee
        fields = '__all__'

# Bulk Attendance Upload Serializer
class BulkAttendanceSerializer(serializers.Serializer):
    month = serializers.IntegerField(min_value=1, max_value=12)
    year = serializers.IntegerField(min_value=2020)
    company_id = serializers.IntegerField()
    attendance_data = serializers.ListField(
        child=serializers.DictField()
    )

# Salary Statement Serializer
class SalaryStatementSerializer(serializers.Serializer):
    employee_id = serializers.IntegerField()
    month = serializers.IntegerField(min_value=1, max_value=12)
    year = serializers.IntegerField(min_value=2020)
    days_in_month = serializers.IntegerField()
    days_payable = serializers.IntegerField()
    overtime_hours = serializers.DecimalField(max_digits=5, decimal_places=2, default=0)

# Invoice Generation Serializer
class InvoiceGenerationSerializer(serializers.Serializer):
    client_id = serializers.IntegerField()
    month = serializers.IntegerField(min_value=1, max_value=12)
    year = serializers.IntegerField(min_value=2020)
    
# Monthly Report Serializer
class MonthlyReportSerializer(serializers.Serializer):
    company_id = serializers.IntegerField()
    month = serializers.IntegerField(min_value=1, max_value=12)
    year = serializers.IntegerField(min_value=2020)
    report_type = serializers.ChoiceField(choices=[
        ('ESI', 'ESI Statement'),
        ('PF', 'PF Statement'),
        ('PT', 'PT Statement'),
        ('LWF', 'LWF Statement'),
        ('INSURANCE', 'Insurance Statement')
    ])

# Employee Creation with all details
class EmployeeCreateSerializer(serializers.ModelSerializer):
    official_details = OfficialDetailsSerializer(required=False)
    identity_document = IdentityDocumentSerializer(required=False)
    bank_details = BankDetailsSerializer(required=False)
    salary_structure = SalaryStructureSerializer(required=False)
    
    class Meta:
        model = Employee
        fields = '__all__'
    
    def create(self, validated_data):
        official_details_data = validated_data.pop('official_details', None)
        identity_document_data = validated_data.pop('identity_document', None)
        bank_details_data = validated_data.pop('bank_details', None)
        salary_structure_data = validated_data.pop('salary_structure', None)
        
        employee = Employee.objects.create(**validated_data)
        
        if official_details_data:
            OfficialDetails.objects.create(employee=employee, **official_details_data)
        
        if identity_document_data:
            IdentityDocument.objects.create(employee=employee, **identity_document_data)
            
        if bank_details_data:
            BankDetails.objects.create(employee=employee, **bank_details_data)
            
        if salary_structure_data:
            SalaryStructure.objects.create(employee=employee, **salary_structure_data)
        
        return employee

# Login Response Serializer
class LoginResponseSerializer(serializers.Serializer):
    access_token = serializers.CharField()
    refresh_token = serializers.CharField()
    user = serializers.DictField()
    main_companies = CompanySerializer(many=True)
    current_client = CompanySerializer(allow_null=True)

# Attendance Summary Serializer  
class AttendanceSummarySerializer(serializers.Serializer):
    employee_id = serializers.IntegerField()
    employee_name = serializers.CharField()
    employee_code = serializers.CharField()
    total_days = serializers.IntegerField()
    present_days = serializers.IntegerField()
    absent_days = serializers.IntegerField()
    holidays = serializers.IntegerField()
    weekly_offs = serializers.IntegerField()
    overtime_hours = serializers.DecimalField(max_digits=5, decimal_places=2)


# ==================== Employee Dashboard Serializers ====================

from .additional_models import Notification, ProfileUpdateRequest

class NotificationSerializer(serializers.ModelSerializer):
    """Serializer for employee notifications"""
    class Meta:
        model = Notification
        fields = ['id', 'notification_type', 'title', 'message', 'is_read', 'created_at', 'link']
        read_only_fields = ['id', 'created_at']


class ProfileUpdateRequestSerializer(serializers.ModelSerializer):
    """Serializer for profile update requests"""
    employee_name = serializers.CharField(source='employee.full_name', read_only=True)
    employee_code = serializers.CharField(source='employee.employee_code', read_only=True)
    reviewed_by_name = serializers.CharField(source='reviewed_by.username', read_only=True)
    
    class Meta:
        model = ProfileUpdateRequest
        fields = [
            'id', 'employee', 'employee_name', 'employee_code',
            'field_name', 'current_value', 'requested_value', 'reason',
            'status', 'requested_at', 'reviewed_by', 'reviewed_by_name',
            'reviewed_at', 'remarks'
        ]
        read_only_fields = ['id', 'requested_at', 'reviewed_by', 'reviewed_at']


class OfficialDetailsSerializer(serializers.ModelSerializer):
    """Serializer for employee official details"""
    class Meta:
        model = OfficialDetails
        fields = '__all__'
        read_only_fields = ['id', 'employee']


class IdentityDocumentSerializer(serializers.ModelSerializer):
    """Serializer for employee identity documents"""
    class Meta:
        model = IdentityDocument
        fields = '__all__'
        read_only_fields = ['id', 'employee']


class BankDetailsSerializer(serializers.ModelSerializer):
    """Serializer for employee bank details"""
    class Meta:
        model = BankDetails
        fields = '__all__'
        read_only_fields = ['id', 'employee']


class SalaryStructureSerializer(serializers.ModelSerializer):
    """Serializer for employee salary structure"""
    net_salary = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    
    class Meta:
        model = SalaryStructure
        fields = '__all__'
        read_only_fields = ['id', 'employee', 'net_salary']


class PayslipSerializer(serializers.ModelSerializer):
    """Serializer for employee payslips"""
    month_name = serializers.SerializerMethodField()
    pdf_url = serializers.SerializerMethodField()
    
    class Meta:
        model = Payslip
        fields = ['id', 'month', 'year', 'month_name', 'gross_salary', 
                  'deductions', 'net_salary', 'pdf_file', 'pdf_url']
        read_only_fields = ['id', 'employee']
    
    def get_month_name(self, obj):
        import calendar
        return calendar.month_name[obj.month]
    
    def get_pdf_url(self, obj):
        if obj.pdf_file:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.pdf_file.url)
            return obj.pdf_file.url
        return None


class IncrementHistorySerializer(serializers.ModelSerializer):
    """Serializer for employee increment history"""
    increment_amount = serializers.SerializerMethodField()
    increment_percentage = serializers.SerializerMethodField()
    
    class Meta:
        model = IncrementHistory
        fields = ['id', 'effective_date', 'old_salary', 'new_salary', 
                  'increment_amount', 'increment_percentage']
        read_only_fields = ['id', 'employee']
    
    def get_increment_amount(self, obj):
        return float(obj.new_salary - obj.old_salary)
    
    def get_increment_percentage(self, obj):
        if obj.old_salary > 0:
            return round(((obj.new_salary - obj.old_salary) / obj.old_salary) * 100, 2)
        return 0


class AttendanceSerializer(serializers.ModelSerializer):
    """Serializer for employee attendance"""
    shift_1 = serializers.CharField(source='shift_1_status')
    shift_2 = serializers.CharField(source='shift_2_status')
    status_display = serializers.SerializerMethodField()
    day = serializers.SerializerMethodField()

    class Meta:
        model = Attendance
        fields = [
            'id', 'date', 'day', 'shift_1', 'shift_2', 'status_display',
            'check_in_time', 'check_out_time', 'hours_worked'
        ]
        read_only_fields = ['id', 'employee']

    def get_day(self, obj):
        # obj.date may sometimes be a string (from API input) or a date object — normalize both
        try:
            d = obj.date
            if isinstance(d, str):
                from datetime import datetime
                d = datetime.fromisoformat(d).date()
        except Exception:
            return None
        return d.strftime("%A")

    def get_status_display(self, obj):
        try:
            d = obj.date
            if isinstance(d, str):
                from datetime import datetime
                d = datetime.fromisoformat(d).date()
            day_name = d.strftime("%A")
        except Exception:
            day_name = ''
        s1 = obj.shift_1_status
        s2 = obj.shift_2_status
        if day_name.lower() == 'sunday':
            return 'sunday'
        if s1 == 'P' and s2 == 'P':
            return 'present'
        if s1 == 'A' and s2 == 'A':
            return ''
        if (s1 == 'P' and s2 == 'A') or (s1 == 'A' and s2 == 'P'):
            return 'half day'
        return ''


class OvertimeRecordSerializer(serializers.ModelSerializer):
    """Serializer for employee overtime records"""
    class Meta:
        model = OvertimeRecord
        fields = ['id', 'date', 'hours']
        read_only_fields = ['id', 'employee']


class DocumentSerializer(serializers.ModelSerializer):
    """Serializer for employee documents"""
    doc_type_display = serializers.CharField(source='get_doc_type_display', read_only=True)
    file_url = serializers.SerializerMethodField()
    
    class Meta:
        model = Document
        fields = ['id', 'doc_type', 'doc_type_display', 'file', 'file_url', 'issued_date']
        read_only_fields = ['id', 'employee']
    
    def get_file_url(self, obj):
        if obj.file:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.file.url)
            return obj.file.url
        return None


class ReportSerializer(serializers.ModelSerializer):
    """Serializer for employee reports"""
    report_type_display = serializers.CharField(source='get_report_type_display', read_only=True)
    file_url = serializers.SerializerMethodField()
    
    class Meta:
        model = Report
        fields = ['id', 'report_type', 'report_type_display', 'file', 'file_url', 'generated_on']
        read_only_fields = ['id', 'employee', 'generated_on']
    
    def get_file_url(self, obj):
        if obj.file:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.file.url)
            return obj.file.url
        return None


class EmployeeProfileSerializer(serializers.ModelSerializer):
    """Complete employee profile serializer"""
    official_details = OfficialDetailsSerializer(source='officialdetails', read_only=True)
    identity_document = IdentityDocumentSerializer(source='identitydocument', read_only=True)
    bank_details = BankDetailsSerializer(source='bankdetails', read_only=True)
    salary_structure = SalaryStructureSerializer(source='salarystructure', read_only=True)
    gender_display = serializers.CharField(source='get_gender_display', read_only=True)
    marital_status_display = serializers.CharField(source='get_marital_status_display', read_only=True)
    
    class Meta:
        model = Employee
        fields = [
            'id', 'full_name', 'employee_code', 'date_of_birth', 
            'gender', 'gender_display', 'marital_status', 'marital_status_display',
            'mobile_number', 'email', 'current_address', 'permanent_address',
            'role', 'status', 'photo', 'official_details', 'identity_document',
            'bank_details', 'salary_structure'
        ]
        read_only_fields = ['id']


class EmployeeDashboardSerializer(serializers.Serializer):
    """Dashboard summary serializer"""
    employee_name = serializers.CharField()
    employee_code = serializers.CharField()
    profile_photo = serializers.URLField(allow_null=True)
    present_days = serializers.IntegerField()
    absent_days = serializers.IntegerField()
    half_days = serializers.IntegerField()
    ot_hours = serializers.FloatField()
    take_home_salary = serializers.DecimalField(max_digits=10, decimal_places=2)
    current_month = serializers.CharField()