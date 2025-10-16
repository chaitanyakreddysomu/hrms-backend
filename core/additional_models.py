# additional_models.py - Additional models based on requirements

from django.db import models
from django.conf import settings
from django.utils import timezone
from .models import Employee, Company

class ActivityLog(models.Model):
    """Track all user activities for audit trail"""
    ACTION_CHOICES = [
        ('CREATE', 'Create'),
        ('UPDATE', 'Update'),
        ('DELETE', 'Delete'),
        ('VIEW', 'View'),
        ('LOGIN', 'Login'),
        ('LOGOUT', 'Logout'),
        ('EXPORT', 'Export'),
        ('IMPORT', 'Import'),
        ('APPROVE', 'Approve'),
        ('REJECT', 'Reject'),
        ('LOCK', 'Lock'),
        ('UNLOCK', 'Unlock'),
    ]
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    description = models.TextField()
    model_name = models.CharField(max_length=100, blank=True, null=True)
    object_id = models.PositiveIntegerField(blank=True, null=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.TextField(blank=True, null=True)
    timestamp = models.DateTimeField(default=timezone.now)
    additional_data = models.JSONField(default=dict, blank=True)
    
    class Meta:
        db_table = 'activity_log'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['user', 'timestamp']),
            models.Index(fields=['action', 'timestamp']),
        ]

class UserProfile(models.Model):
    """Extended user profile for role-based access"""
    ROLE_CHOICES = [
        ('ADMIN', 'Admin'),
        ('HR', 'HR'),
        ('SUPERVISOR', 'Supervisor'),
        ('EMPLOYEE', 'Employee'),
    ]
    
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    assigned_companies = models.ManyToManyField(Company, blank=True)
    current_client = models.ForeignKey(
        Company, on_delete=models.SET_NULL, 
        null=True, blank=True, 
        related_name='current_users',
        limit_choices_to={'is_main_company': False}
    )
    phone_number = models.CharField(max_length=15, blank=True)
    employee_code = models.CharField(max_length=20, blank=True, unique=True)
    last_client_switch = models.DateTimeField(null=True, blank=True)
    session_timeout_minutes = models.PositiveIntegerField(default=30)
    
    class Meta:
        db_table = 'user_profile'

class SystemConfiguration(models.Model):
    """System-wide configuration settings"""
    key = models.CharField(max_length=100, unique=True)
    value = models.TextField()
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    
    class Meta:
        db_table = 'system_configuration'

class Holiday(models.Model):
    """Company holidays configuration"""
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    date = models.DateField()
    name = models.CharField(max_length=100)
    is_optional = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'holiday'
        unique_together = ('company', 'date')

class EmployeeLeave(models.Model):
    """Employee leave management"""
    LEAVE_TYPE_CHOICES = [
        ('CASUAL', 'Casual Leave'),
        ('SICK', 'Sick Leave'),
        ('EARNED', 'Earned Leave'),
        ('MATERNITY', 'Maternity Leave'),
        ('PATERNITY', 'Paternity Leave'),
        ('COMP_OFF', 'Compensatory Off'),
    ]
    
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
        ('CANCELLED', 'Cancelled'),
    ]
    
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    leave_type = models.CharField(max_length=20, choices=LEAVE_TYPE_CHOICES)
    from_date = models.DateField()
    to_date = models.DateField()
    days_requested = models.DecimalField(max_digits=4, decimal_places=1)
    reason = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    applied_date = models.DateTimeField(auto_now_add=True)
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, 
        null=True, blank=True,
        related_name='approved_leaves'
    )
    approved_date = models.DateTimeField(null=True, blank=True)
    remarks = models.TextField(blank=True)
    
    class Meta:
        db_table = 'employee_leave'

class EmployeeDisciplinary(models.Model):
    """Employee disciplinary actions"""
    ACTION_CHOICES = [
        ('WARNING', 'Warning'),
        ('SHOW_CAUSE', 'Show Cause Notice'),
        ('SUSPENSION', 'Suspension'),
        ('TERMINATION', 'Termination'),
        ('FINE', 'Fine'),
    ]
    
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    action_type = models.CharField(max_length=20, choices=ACTION_CHOICES)
    reason = models.TextField()
    action_date = models.DateField()
    amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)  # For fines
    document = models.FileField(upload_to='disciplinary_documents/', null=True, blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'employee_disciplinary'

class PayrollLock(models.Model):
    """Payroll locking mechanism"""
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    month = models.IntegerField()
    year = models.IntegerField()
    locked_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='locked_payrolls')
    locked_at = models.DateTimeField(auto_now_add=True)
    unlocked_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, 
        null=True, blank=True,
        related_name='unlocked_payrolls'
    )
    unlocked_at = models.DateTimeField(null=True, blank=True)
    is_locked = models.BooleanField(default=True)
    remarks = models.TextField(blank=True)
    
    class Meta:
        db_table = 'payroll_lock'
        unique_together = ('company', 'month', 'year')

# Note: ApprovalWorkflow model is defined in approval_models.py
# Removed duplicate to prevent conflicts

class Notification(models.Model):
    """Employee notifications"""
    TYPE_CHOICES = [
        ('APPOINTMENT', 'Appointment Order Issued'),
        ('PAYSLIP', 'Payslip Uploaded'),
        ('SALARY', 'Salary Credited'),
        ('DOCUMENT', 'Document Uploaded'),
        ('LEAVE', 'Leave Status Update'),
        ('ATTENDANCE', 'Attendance Update'),
        ('GENERAL', 'General Notification'),
    ]
    
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    title = models.CharField(max_length=200)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    link = models.CharField(max_length=255, blank=True, null=True)
    
    class Meta:
        db_table = 'notification'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['employee', 'is_read', 'created_at']),
        ]
    
    def __str__(self):
        return f"{self.employee.full_name} - {self.title}"


class ProfileUpdateRequest(models.Model):
    """Track employee profile update requests"""
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
    ]
    
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='update_requests')
    field_name = models.CharField(max_length=100)
    current_value = models.TextField()
    requested_value = models.TextField()
    reason = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    requested_at = models.DateTimeField(auto_now_add=True)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, 
        null=True, blank=True,
        related_name='reviewed_update_requests'
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    remarks = models.TextField(blank=True)
    
    class Meta:
        db_table = 'profile_update_request'
        ordering = ['-requested_at']


class EmailTemplate(models.Model):
    """Email templates for various notifications"""
    TEMPLATE_TYPE_CHOICES = [
        ('APPOINTMENT_ORDER', 'Appointment Order'),
        ('PAYSLIP', 'Payslip'),
        ('RELIEVING_LETTER', 'Relieving Letter'),
        ('ESI_CARD', 'ESI Card'),
        ('LEAVE_APPROVAL', 'Leave Approval'),
        ('LEAVE_REJECTION', 'Leave Rejection'),
    ]
    
    template_type = models.CharField(max_length=30, choices=TEMPLATE_TYPE_CHOICES)
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    subject = models.CharField(max_length=200)
    body = models.TextField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'email_template'
        unique_together = ('template_type', 'company')

class NotificationQueue(models.Model):
    """Queue for email/WhatsApp notifications"""
    NOTIFICATION_TYPE_CHOICES = [
        ('EMAIL', 'Email'),
        ('WHATSAPP', 'WhatsApp'),
        ('SMS', 'SMS'),
    ]
    
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('SENT', 'Sent'),
        ('FAILED', 'Failed'),
        ('RETRY', 'Retry'),
    ]
    
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPE_CHOICES)
    recipient = models.CharField(max_length=100)  # Email or phone number
    subject = models.CharField(max_length=200, blank=True)
    message = models.TextField()
    attachment_path = models.CharField(max_length=500, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    attempts = models.PositiveIntegerField(default=0)
    max_attempts = models.PositiveIntegerField(default=3)
    created_at = models.DateTimeField(auto_now_add=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(blank=True)
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, null=True, blank=True)
    
    class Meta:
        db_table = 'notification_queue'

class EmployeeContract(models.Model):
    """Employee contract details"""
    CONTRACT_TYPE_CHOICES = [
        ('PERMANENT', 'Permanent'),
        ('CONTRACT', 'Contract'),
        ('TEMPORARY', 'Temporary'),
        ('PROBATION', 'Probation'),
    ]
    
    employee = models.OneToOneField(Employee, on_delete=models.CASCADE)
    contract_type = models.CharField(max_length=20, choices=CONTRACT_TYPE_CHOICES)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    probation_period_months = models.PositiveIntegerField(default=6)
    notice_period_days = models.PositiveIntegerField(default=30)
    contract_document = models.FileField(upload_to='contracts/', null=True, blank=True)
    terms_and_conditions = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'employee_contract'

class Shift(models.Model):
    """Shift management"""
    name = models.CharField(max_length=50)
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    start_time = models.TimeField()
    end_time = models.TimeField()
    break_duration_minutes = models.PositiveIntegerField(default=60)
    overtime_threshold_minutes = models.PositiveIntegerField(default=480)  # 8 hours
    night_shift_allowance = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'shift'

class EmployeeShift(models.Model):
    """Employee shift assignments"""
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    shift = models.ForeignKey(Shift, on_delete=models.CASCADE)
    effective_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    is_current = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'employee_shift'

class ReimbursementCategory(models.Model):
    """Reimbursement categories"""
    name = models.CharField(max_length=100)
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    max_amount_per_month = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    requires_approval = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'reimbursement_category'

class EmployeeReimbursement(models.Model):
    """Employee reimbursement requests"""
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
        ('PAID', 'Paid'),
    ]
    
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    category = models.ForeignKey(ReimbursementCategory, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField()
    bill_date = models.DateField()
    receipt = models.FileField(upload_to='reimbursement_receipts/')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    applied_date = models.DateTimeField(auto_now_add=True)
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, 
        null=True, blank=True
    )
    approved_date = models.DateTimeField(null=True, blank=True)
    paid_date = models.DateTimeField(null=True, blank=True)
    remarks = models.TextField(blank=True)
    
    class Meta:
        db_table = 'employee_reimbursement'

class CompanyBankAccount(models.Model):
    """Company bank account details"""
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    bank_name = models.CharField(max_length=100)
    account_number = models.CharField(max_length=30)
    ifsc_code = models.CharField(max_length=15)
    branch_name = models.CharField(max_length=100)
    account_type = models.CharField(max_length=20, default='Current')
    is_primary = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'company_bank_account'

class ReportSchedule(models.Model):
    """Scheduled report generation"""
    FREQUENCY_CHOICES = [
        ('DAILY', 'Daily'),
        ('WEEKLY', 'Weekly'),
        ('MONTHLY', 'Monthly'),
        ('QUARTERLY', 'Quarterly'),
    ]
    
    REPORT_TYPE_CHOICES = [
        ('ATTENDANCE', 'Attendance Report'),
        ('SALARY', 'Salary Report'),
        ('ESI', 'ESI Report'),
        ('PF', 'PF Report'),
        ('PT', 'PT Report'),
        ('LWF', 'LWF Report'),
    ]
    
    name = models.CharField(max_length=100)
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    report_type = models.CharField(max_length=20, choices=REPORT_TYPE_CHOICES)
    frequency = models.CharField(max_length=20, choices=FREQUENCY_CHOICES)
    recipients = models.TextField()  # Comma-separated email addresses
    next_run_date = models.DateTimeField()
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'report_schedule'

class DataBackup(models.Model):
    """Data backup tracking"""
    BACKUP_TYPE_CHOICES = [
        ('MANUAL', 'Manual'),
        ('SCHEDULED', 'Scheduled'),
        ('AUTOMATED', 'Automated'),
    ]
    
    STATUS_CHOICES = [
        ('IN_PROGRESS', 'In Progress'),
        ('COMPLETED', 'Completed'),
        ('FAILED', 'Failed'),
    ]
    
    backup_type = models.CharField(max_length=20, choices=BACKUP_TYPE_CHOICES)
    file_path = models.CharField(max_length=500)
    file_size_mb = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(blank=True)
    
    class Meta:
        db_table = 'data_backup'