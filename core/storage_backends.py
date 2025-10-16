# serializers.py
from rest_framework import serializers
from django.contrib.auth.models import User
from .models import *

class CompanySerializer(serializers.ModelSerializer):
    class Meta:
        model = Company
        fields = '__all__'

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