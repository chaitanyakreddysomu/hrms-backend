from django.db import models
from django.contrib.auth.models import AbstractUser, Group, Permission
from django.utils import timezone
import secrets
import string
# In core/models.py or whatever app it belongs to
# from .approval_modals import ApprovalWorkflow

# Utility Functions
def generate_custom_user_id():
    chars = string.ascii_letters + string.digits + "-_.~!$'()*@"
    random_id = ''.join(secrets.choice(chars) for _ in range(10))
    return f"user_{random_id}"

def generate_custom_question_id():
    chars = string.ascii_letters + string.digits
    return f"user{''.join(secrets.choice(chars) for _ in range(10))}"

def generate_custom_schedule_id():
    chars = string.ascii_letters + string.digits
    return f"schdle{''.join(secrets.choice(chars) for _ in range(10))}"

# ------------------------------
# ExamSchedule Model
# ------------------------------
class ExamSchedule(models.Model):
    id = models.CharField(
        primary_key=True,
        default=generate_custom_schedule_id,
        editable=False,
        max_length=20,
        unique=True
    )

    exam_name = models.CharField(max_length=255, null=True, blank=True)
    exam_date = models.DateField(null=True, blank=True)
    exam_start_time = models.CharField(max_length=8, null=True, blank=True)  # Format: 'HH:MM:SS'
    exam_end_time = models.CharField(max_length=8, null=True, blank=True)   
    def __str__(self):
        return f"Schedule for {self.exam_name} on {self.exam_date} at {self.exam_time}"

    class Meta:
        db_table = 'Schedules'

# ------------------------------
# User   Model
# ------------------------------
class User(AbstractUser):
    id = models.CharField(
        primary_key=True,
        default=generate_custom_user_id,
        editable=False,
        max_length=20,
        unique=True
    )

    email = models.EmailField(unique=True)
    created_at = models.DateTimeField(default=timezone.now)

    groups = models.ManyToManyField(
        Group,
        related_name='user_groups',
        blank=True,
        help_text='The groups this user belongs to.',
        verbose_name='groups'
    )
    user_permissions = models.ManyToManyField(
        Permission,
        related_name='user_permissions_set',
        blank=True,
        help_text='Specific permissions for this user.',
        verbose_name='user permissions'
    )

    def __str__(self):
        return f"{self.username}"

    class Meta:
        db_table = 'users'

# ------------------------------
# Admins Model
# ------------------------------
class Admins(AbstractUser):
    id = models.CharField(
        primary_key=True,
        default=generate_custom_user_id,
        editable=False,
        max_length=20,
        unique=True
    )



    username = models.CharField(max_length=225)  # Remove the username field
    email = models.EmailField(unique=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    password = models.CharField(max_length=225)

    groups = models.ManyToManyField(
        Group,
        related_name='admin_groups',
        blank=True,
        help_text='The groups this admin belongs to.',
        verbose_name='groups'
    )
    user_permissions = models.ManyToManyField(
        Permission,
        related_name='admin_permissions_set',
        blank=True,
        help_text='Specific permissions for this admin.',
        verbose_name='user permissions'
    )

    def __str__(self):
        return f"{self.email}"

    class Meta:
        db_table = 'admin'

# ------------------------------
# ExamQuestion Model
# ------------------------------
class ExamQuestion(models.Model):
    id = models.CharField(
        primary_key=True,
        default=generate_custom_question_id,
        editable=False,
        max_length=20,
        unique=True
    )
    question = models.TextField()
    option_1 = models.CharField(max_length=255)
    option_2 = models.CharField(max_length=255)
    option_3 = models.CharField(max_length=255)
    option_4 = models.CharField(max_length=255)
    correct_answer = models.CharField(max_length=255)

    def __str__(self):
        return self.question

    class Meta:
        db_table = 'Questions'





class Company(models.Model):
    name = models.CharField(max_length=100)
    address = models.TextField(blank=True, null=True)
    gst_number = models.CharField(max_length=20, blank=True, null=True)
    is_main_company = models.BooleanField(default=False)  # True for RMS/IMS/KVS
    parent_company = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL, related_name='sub_companies')  # <-- Add this

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'company'


# Updated Employee Model - models.py
class Employee(models.Model):
    # Enums and Choices with Sub-Manager added
    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
    ]
    
    MARITAL_STATUS_CHOICES = [
        ('S', 'Single'),
        ('M', 'Married'),
        ('D', 'Divorced'),
        ('W', 'Widowed'),
    ]

    ROLE_CHOICES = [
        ('Admin', 'Admin'),
        ('HR', 'HR'),
        ('Supervisor', 'Supervisor'),
        ('Employee', 'Employee'),
    ]
    
    full_name = models.CharField(max_length=100)
    employee_code = models.CharField(max_length=20, unique=True)
    date_of_birth = models.DateField()
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    marital_status = models.CharField(max_length=1, choices=MARITAL_STATUS_CHOICES)

    mobile_number = models.CharField(max_length=15)
    email = models.EmailField()
    current_address = models.TextField()
    permanent_address = models.TextField()
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)

    main_company = models.ForeignKey(Company, null=True, blank=True, on_delete=models.SET_NULL, 
                                   related_name='main_employees', 
                                   limit_choices_to={'is_main_company': True})
    sub_company = models.ForeignKey(Company, null=True, blank=True, on_delete=models.SET_NULL, 
                                  related_name='sub_employees', 
                                  limit_choices_to={'is_main_company': False})
    # Supervisors can be linked to multiple companies
    supervised_companies = models.ManyToManyField(Company, blank=True, related_name='supervisors', help_text='Companies supervised by this supervisor')

    status = models.CharField(max_length=20, default='ACTIVE')  # ACTIVE, LEFT, TERMINATED
    photo = models.ImageField(upload_to='employee_photos/', blank=True, null=True)
    client_code = models.CharField(max_length=30, blank=True, null=True)
    
    # Approval Workflow Fields
    approval_status = models.CharField(
        max_length=20,
       
        default='active',
        help_text='Approval status for new accounts'
    )
    created_by = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_employees',
        help_text='Employee who created this account'
    )
    approved_by = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_employees',
        help_text='Employee who approved this account'
    )
    approval_workflow_id = models.IntegerField(
        null=True,
        blank=True,
        help_text='Associated approval workflow ID'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    approved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'employee'
        
    def __str__(self):
        return f"{self.full_name} ({self.employee_code}) - {self.role}"
        
    @property
    def company_name(self):
        """Get the company name based on role"""
        if self.main_company:
            return self.main_company.name
        elif self.sub_company:
            return self.sub_company.name
        return "No Company Assigned"
        
    @property 
    def is_manager_level(self):
        """Check if employee has management privileges"""
        return self.role in ['Admin', 'Manager', 'Sub-Manager']

class OfficialDetails(models.Model):
    employee = models.OneToOneField(Employee, on_delete=models.CASCADE)
    date_of_joining = models.DateField()
    department = models.CharField(max_length=100)
    designation = models.CharField(max_length=100)
    location = models.CharField(max_length=100)
    supervisor_name = models.CharField(max_length=100)
    salary_type = models.CharField(max_length=10, choices=[('MONTHLY', 'Monthly'), ('DAILY', 'Daily')])

    class Meta:
        db_table = 'OfficialDetails'

class IdentityDocument(models.Model):
    employee = models.OneToOneField(Employee, on_delete=models.CASCADE)
    aadhaar_number = models.CharField(max_length=12, blank=True)
    pan_number = models.CharField(max_length=10, blank=True)
    esi_number = models.CharField(max_length=20, blank=True, null=True)
    pf_uan_number = models.CharField(max_length=20, blank=True)
    passport_number = models.CharField(max_length=15, blank=True, null=True)

    class Meta:
        db_table = 'IdentityDocument'


class BankDetails(models.Model):
    employee = models.OneToOneField(Employee, on_delete=models.CASCADE)
    bank_name = models.CharField(max_length=100)
    account_number = models.CharField(max_length=30)
    ifsc_code = models.CharField(max_length=15)
    branch_name = models.CharField(max_length=35)

    class Meta:
        db_table = 'BankDetails'

class SalaryStructure(models.Model):
    employee = models.OneToOneField(Employee, on_delete=models.CASCADE)
    CTC = models.DecimalField(max_digits=10, decimal_places=2)
    basic = models.DecimalField(max_digits=10, decimal_places=2)
    da = models.DecimalField(max_digits=10, decimal_places=2)
    hra = models.DecimalField(max_digits=10, decimal_places=2)
    conveyance = models.DecimalField(max_digits=10, decimal_places=2)
    bonus = models.DecimalField(max_digits=10, decimal_places=2)
    other_allowances = models.DecimalField(max_digits=10, decimal_places=2)

    pf_deduction = models.DecimalField(max_digits=10, decimal_places=2)
    esi_deduction = models.DecimalField(max_digits=10, decimal_places=2)
    pt_deduction = models.DecimalField(max_digits=10, decimal_places=2)
    lwf_deduction = models.DecimalField(max_digits=10, decimal_places=2)
    insurance = models.DecimalField(max_digits=10, decimal_places=2)
    advance = models.DecimalField(max_digits=10, decimal_places=2)

    @property
    def net_salary(self):
        earnings = sum([
            self.basic, self.da, self.hra, self.conveyance,
            self.bonus, self.other_allowances
        ])
        deductions = sum([
            self.pf_deduction, self.esi_deduction, self.pt_deduction,
            self.lwf_deduction, self.insurance, self.advance
        ])
        return earnings - deductions

    class Meta:
        db_table = 'SalaryStructure'

class Payslip(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    month = models.IntegerField()
    year = models.IntegerField()
    gross_salary = models.DecimalField(max_digits=10, decimal_places=2)
    deductions = models.DecimalField(max_digits=10, decimal_places=2)
    net_salary = models.DecimalField(max_digits=10, decimal_places=2)
    pdf_file = models.FileField(upload_to='payslips/')

    class Meta:
        unique_together = ('employee', 'month', 'year')
        db_table = 'Payslip'


class IncrementHistory(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    effective_date = models.DateField()
    old_salary = models.DecimalField(max_digits=10, decimal_places=2)
    new_salary = models.DecimalField(max_digits=10, decimal_places=2)
    class Meta:
        db_table = 'IncrementHistory'


class Attendance(models.Model):
    STATUS_CHOICES = [
        ('P', 'Present'),
        ('A', 'Absent'),
        ('WO', 'Weekly Off'),
        ('H', 'Holiday'),
        ('HD', 'Half Day'),
    ]

    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    date = models.DateField()
    shift_1_status = models.CharField(max_length=2, choices=STATUS_CHOICES, default='A')
    shift_2_status = models.CharField(max_length=2, choices=STATUS_CHOICES, default='A')
    check_in_time = models.TimeField(null=True, blank=True)
    check_out_time = models.TimeField(null=True, blank=True)
    hours_worked = models.DurationField(null=True, blank=True)

    class Meta:
        unique_together = ('employee', 'date')
        db_table = 'Attendance'

class OvertimeRecord(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    date = models.DateField()
    hours = models.DecimalField(max_digits=5, decimal_places=2)
    class Meta:
        db_table = 'OvertimeRecord'


class Document(models.Model):
    DOCUMENT_TYPE_CHOICES = [
        ('APPOINTMENT', 'Appointment Order'),
        ('ESI_CARD', 'ESI Card'),
        ('ID_CARD', 'ID Card'),
        ('RELIEVING', 'Relieving Letter'),
    ]

    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    doc_type = models.CharField(max_length=20, choices=DOCUMENT_TYPE_CHOICES)
    file = models.FileField(upload_to='employee_documents/')
    issued_date = models.DateField()

    class Meta:
        db_table = 'Document'

class Report(models.Model):
    REPORT_TYPE_CHOICES = [
        ('SALARY_STATEMENT', 'Salary Statement'),
        ('DEDUCTION_STATEMENT', 'Deduction Statement'),
        ('EXPERIENCE_CERTIFICATE', 'Experience Certificate'),
    ]

    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    report_type = models.CharField(max_length=30, choices=REPORT_TYPE_CHOICES)
    file = models.FileField(upload_to='employee_reports/')
    generated_on = models.DateField(auto_now_add=True)

    class Meta:
        db_table = 'Report'


class ClientProfileSettings(models.Model):
    client = models.OneToOneField(Company, on_delete=models.CASCADE, limit_choices_to={'is_main_company': False})
    
    esi_applicable = models.BooleanField(default=False)
    esi_components = models.ManyToManyField('SalaryComponent', related_name='esi_components', blank=True)

    pf_applicable = models.BooleanField(default=False)
    pf_components = models.ManyToManyField('SalaryComponent', related_name='pf_components', blank=True)

    pt_applicable = models.BooleanField(default=False)
    pt_components = models.ManyToManyField('SalaryComponent', related_name='pt_components', blank=True)

    lwf_applicable = models.BooleanField(default=False)
    advance_applicable = models.BooleanField(default=False)
    insurance_applicable = models.BooleanField(default=False)

    service_charge_type = models.CharField(max_length=10, choices=[('FIXED', 'Fixed'), ('PERCENTAGE', 'Percentage')])
    service_charge_value = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        db_table = 'client_profile_settings'


class SalaryComponent(models.Model):
    name = models.CharField(max_length=100)  # e.g., Basic, DA, Special Allowance
    is_earning = models.BooleanField(default=True)  # Earning or Deduction

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'salary_component'




class ApprovalWorkflow(models.Model):
    """
    Tracks approval requests through hierarchical workflow stages
    """
    
    # Approval Types
    APPROVAL_TYPE_CHOICES = [
        ('employee', 'Employee Creation'),
        ('hr', 'HR Account Creation'),
        ('supervisor', 'Supervisor Account Creation'),
        ('sub_manager', 'Sub-Manager Account Creation'),
        ('manager', 'Manager Account Creation'),
        ('sub_company', 'Sub-Company Creation'),
    ]
    
    # Workflow Status
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('cancelled', 'Cancelled'),
    ]
    
    # Current Stage
    STAGE_CHOICES = [
        ('sub_manager', 'Awaiting Sub-Company Manager'),
        ('main_manager', 'Awaiting Main Company Manager'),
        ('admin', 'Awaiting Admin'),
        ('completed', 'Completed'),
    ]
    
    # Basic Info
    approval_type = models.CharField(
        max_length=30, 
        choices=APPROVAL_TYPE_CHOICES,
        default='employee',
        help_text="Type of approval request"
    )
    status = models.CharField(
        max_length=30, 
        choices=STATUS_CHOICES, 
        default='pending',
        help_text="Current status of the workflow"
    )
    current_stage = models.CharField(
        max_length=30, 
        choices=STAGE_CHOICES,
        default='sub_manager',
        help_text="Current approval stage in the workflow"
    )
    
    # Request Data (JSON)
    request_data = models.JSONField(
        default=dict,
        help_text="Data for the creation request"
    )
    
    # Company Context
    company = models.ForeignKey(
        'Company',
        on_delete=models.CASCADE,
        related_name='approval_workflows',
        help_text="Company where this request originated"
    )
    sub_company = models.ForeignKey(
        'Company',
        on_delete=models.CASCADE,
        related_name='sub_company_approvals',
        null=True,
        blank=True,
        help_text="Sub-company if applicable"
    )
    
    # Creator Info
    created_by = models.ForeignKey(
        'Employee',
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_approval_workflows',
        help_text="Employee who created this request"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Metadata
    rejection_reason = models.TextField(
        blank=True, 
        null=True,
        default='',
        help_text="Reason for rejection if applicable"
    )
    notes = models.TextField(
        blank=True, 
        null=True,
        default='',
        help_text="Additional notes or comments"
    )
    completed_at = models.DateTimeField(
        null=True, 
        blank=True,
        help_text="Timestamp when workflow was completed"
    )
    
    class Meta:
        db_table = 'approval_workflow'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'current_stage']),
            models.Index(fields=['approval_type', 'status']),
            models.Index(fields=['company', 'status']),
        ]
    
    def __str__(self):
        return f"{self.get_approval_type_display()} - {self.status} ({self.current_stage})"
    
    def get_next_approver_role(self):
        """
        Determine the next approver based on approval type and current stage
        """
        workflows = {
            'employee': {
                'sub_manager': 'sub_manager',
                'main_manager': 'main_manager',
            },
            'hr': {
                'sub_manager': 'sub_manager',
                'main_manager': 'main_manager',
                'admin': 'admin',
            },
            'supervisor': {
                'sub_manager': 'sub_manager',
                'main_manager': 'main_manager',
                'admin': 'admin',
            },
            'sub_manager': {
                'main_manager': 'main_manager',
                'admin': 'admin',
            },
            'manager': {
                'admin': 'admin',
            },
            'sub_company': {
                'admin': 'admin',
            },
        }
        
        workflow = workflows.get(self.approval_type, {})
        return workflow.get(self.current_stage)
    
    def get_next_stage(self):
        """
        Determine the next workflow stage after approval
        """
        stage_progression = {
            'employee': {
                'sub_manager': 'main_manager',
                'main_manager': 'completed',
            },
            'hr': {
                'sub_manager': 'main_manager',
                'main_manager': 'admin',
                'admin': 'completed',
            },
            'supervisor': {
                'sub_manager': 'main_manager',
                'main_manager': 'admin',
                'admin': 'completed',
            },
            'sub_manager': {
                'main_manager': 'admin',
                'admin': 'completed',
            },
            'manager': {
                'admin': 'completed',
            },
            'sub_company': {
                'admin': 'completed',
            },
        }
        
        progression = stage_progression.get(self.approval_type, {})
        return progression.get(self.current_stage, 'completed')
    
    def can_approve(self, employee):
        """
        Check if the given employee can approve at the current stage
        """
        # Admin can approve at admin stage
        if self.current_stage == 'admin' and employee.role == 'Admin':
            return True
        
        # Sub-company manager can approve at sub_manager stage
        if self.current_stage == 'sub_manager' and employee.role == 'Manager':
            # Check if manager belongs to the sub-company
            if self.sub_company and employee.company_id == self.sub_company.id:
                return True
        
        # Main company manager can approve at main_manager stage
        if self.current_stage == 'main_manager' and employee.role == 'Manager':
            # Check if manager belongs to the main company
            if employee.company_id == self.company.id:
                return True
        
        return False


class ApprovalHistory(models.Model):
    """
    Tracks each approval/rejection action in the workflow
    """
    
    ACTION_CHOICES = [
        ('created', 'Workflow Created'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('cancelled', 'Cancelled'),
    ]
    
    workflow = models.ForeignKey(
        ApprovalWorkflow,
        on_delete=models.CASCADE,
        related_name='history'
    )
    
    action = models.CharField(max_length=30, choices=ACTION_CHOICES)
    stage = models.CharField(max_length=30)
    
    # Approver Info
    actor = models.ForeignKey(
        'Employee',
        on_delete=models.SET_NULL,
        null=True,
        related_name='approval_actions',
        help_text="Employee who performed this action"
    )
    actor_role = models.CharField(max_length=50, help_text="Role at time of action")
    
    # Action Details
    comments = models.TextField(
        blank=True, 
        null=True,
        default='',
        help_text="Comments from the approver"
    )
    action_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Timestamp of this action"
    )
    
    # Metadata
    ip_address = models.GenericIPAddressField(
        null=True, 
        blank=True,
        help_text="IP address of the user who performed the action"
    )
    user_agent = models.CharField(
        max_length=500, 
        blank=True, 
        null=True,
        default='',
        help_text="Browser/client user agent string"
    )
    
    class Meta:
        db_table = 'approval_history'
        ordering = ['-action_at']
        verbose_name_plural = 'Approval Histories'
    
    def __str__(self):
        return f"{self.workflow.id} - {self.action} by {self.actor}"


class PendingUser(models.Model):
    """
    Temporary storage for user accounts pending approval
    """
    
    workflow = models.OneToOneField(
        ApprovalWorkflow,
        on_delete=models.CASCADE,
        related_name='pending_user'
    )
    
    # User Data (encrypted/secure)
    username = models.CharField(
        max_length=150, 
        unique=True,
        help_text="Temporary username for the pending user"
    )
    email = models.EmailField(
        unique=True,
        help_text="Email address for the pending user"
    )
    temporary_password = models.CharField(
        max_length=255, 
        help_text="Hashed password (stored securely)"
    )
    
    # Employee Data (JSON)
    employee_data = models.JSONField(
        default=dict,
        help_text="Employee details in JSON format"
    )
    
    # Official Details Data (JSON, if applicable)
    official_details_data = models.JSONField(
        null=True, 
        blank=True,
        default=dict,
        help_text="Official/organizational details if applicable"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(
        help_text="Approval request expires after 30 days",
        null=True,
        blank=True
    )
    
    class Meta:
        db_table = 'pending_user'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Pending: {self.username}"
    
    def is_expired(self):
        """Check if the approval request has expired"""
        if self.expires_at:
            return timezone.now() > self.expires_at
        return False


class ApprovalNotification(models.Model):
    """
    Notifications for pending approvals
    """
    
    workflow = models.ForeignKey(
        ApprovalWorkflow,
        on_delete=models.CASCADE,
        related_name='notifications'
    )
    
    recipient = models.ForeignKey(
        'Employee',
        on_delete=models.CASCADE,
        related_name='approval_notifications'
    )
    
    title = models.CharField(
        max_length=255,
        help_text="Notification title"
    )
    message = models.TextField(
        help_text="Notification message content"
    )
    
    is_read = models.BooleanField(
        default=False,
        help_text="Whether the notification has been read"
    )
    read_at = models.DateTimeField(
        null=True, 
        blank=True,
        help_text="Timestamp when notification was read"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Notification Type
    NOTIFICATION_TYPE_CHOICES = [
        ('pending_approval', 'Pending Approval'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('escalated', 'Escalated to Next Level'),
    ]
    notification_type = models.CharField(
        max_length=30,
        choices=NOTIFICATION_TYPE_CHOICES,
        default='pending_approval'
    )
    
    class Meta:
        db_table = 'approval_notification'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Notification for {self.recipient}: {self.title}"
    
    def mark_as_read(self):
        """Mark notification as read"""
        self.is_read = True
        self.read_at = timezone.now()
        self.save()
