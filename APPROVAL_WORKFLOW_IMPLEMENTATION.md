# 🔄 Hierarchical Approval Workflow System - Complete Implementation Guide

## 📋 Overview

This document provides a complete guide to the **Hierarchical Approval Workflow System** implemented in the HRMS platform. This system ensures that new employee and account creations go through proper approval chains based on company hierarchy and account type.

---

## ✨ Key Features

### 1. **Smart Company-Specific Routing**
- Approval requests go **only to the relevant company's manager**
- If HR creates employee in **Sub-Company 1** → Notification goes to **Sub-Company 1 Manager only**
- Not all managers are notified - only the responsible one

### 2. **Auto-Stop on Rejection**
- If Sub-Company Manager rejects → Workflow stops immediately
- Main Company Manager is **NOT notified**
- Creator receives rejection notification with reason

### 3. **Multi-Level Approval Chains**
- **Employee Creation**: Sub-Manager → Main Manager (2 levels)
- **HR/Supervisor Creation**: Sub-Manager → Main Manager → Admin (3 levels)
- **Sub-Company Creation**: Admin only (1 level)

### 4. **Complete Audit Trail**
- Every action logged with timestamp
- Actor information preserved
- Comments and rejection reasons stored
- Full compliance with audit requirements

---

## 🔄 Approval Workflows

### Workflow 1: Employee Creation (2 Levels)

```
┌─────────────────┐      ┌──────────────────┐      ┌──────────────────┐      ┌──────────┐
│  HR Creates     │  →   │  Sub-Company     │  →   │  Main Company    │  →   │ Employee │
│  Request        │      │  Manager         │      │  Manager         │      │ Created  │
└─────────────────┘      └──────────────────┘      └──────────────────┘      └──────────┘
                              Approves/              Approves/                 ✓ Active
                              Rejects                Rejects
```

**Workflow Logic:**
- If employee is for **Sub-Company** → Starts at `sub_manager` stage
- If employee is for **Main Company** → Starts at `main_manager` stage (skips sub-manager)
- Each manager sees only **their company's** requests

**Who Can Create:** HR, Manager, Sub-Manager

**Approval Required From:**
1. Sub-Company Manager (if in sub-company)
2. Main Company Manager (final)

---

### Workflow 2: HR/Supervisor Creation (3 Levels)

```
┌─────────────────┐      ┌──────────────────┐      ┌──────────────────┐      ┌─────────┐      ┌──────────┐
│  Manager        │  →   │  Sub-Company     │  →   │  Main Company    │  →   │  Admin  │  →   │ Account  │
│  Creates        │      │  Manager         │      │  Manager         │      │         │      │ Created  │
└─────────────────┘      └──────────────────┘      └──────────────────┘      └─────────┘      └──────────┘
                              (if sub-co)            Approves/                Approves/         ✓ Active
                                                     Rejects                  Rejects
```

**Who Can Create:** Manager, Sub-Manager

**Approval Required From:**
1. Sub-Company Manager (if created in sub-company)
2. Main Company Manager
3. Admin (final)

**Why 3 Levels?**
- HR and Supervisor roles have elevated privileges
- Admin oversight required for security and compliance
- Ensures proper authorization for sensitive accounts

---

### Workflow 3: Sub-Company Creation (1 Level)

```
┌─────────────────┐      ┌─────────┐      ┌──────────────┐
│  Manager        │  →   │  Admin  │  →   │ Sub-Company  │
│  Creates        │      │         │      │ Created      │
└─────────────────┘      └─────────┘      └──────────────┘
                          Approves/         ✓ Active
                          Rejects
```

**Who Can Create:** Manager (main company only)

**Approval Required From:**
1. Admin (only)

**Why Admin Only?**
- Sub-companies are critical organizational structures
- Admin has system-wide visibility
- Prevents unauthorized company creation

---

## 📊 Database Models

### 1. ApprovalWorkflow Model

Tracks approval requests through their lifecycle.

```python
class ApprovalWorkflow(models.Model):
    # Type: employee, hr, supervisor, sub_company
    approval_type = models.CharField(max_length=20)
    
    # Status: pending, approved, rejected, cancelled
    status = models.CharField(max_length=20, default='pending')
    
    # Current Stage: sub_manager, main_manager, admin, completed
    current_stage = models.CharField(max_length=20)
    
    # Request data (JSON)
    request_data = models.JSONField()
    
    # Company Context
    company = models.ForeignKey(Company)  # Main company
    sub_company = models.ForeignKey(Company, null=True)  # Sub-company if applicable
    
    # Creator
    created_by = models.ForeignKey(Employee)
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Rejection
    rejection_reason = models.TextField(blank=True)
    completed_at = models.DateTimeField(null=True)
```

**Key Methods:**
- `can_approve(employee)` - Check if employee can approve at current stage
- `get_next_stage()` - Determine next workflow stage
- `get_next_approver_role()` - Get required role for next approval

---

### 2. ApprovalHistory Model

Logs every action in the workflow.

```python
class ApprovalHistory(models.Model):
    workflow = models.ForeignKey(ApprovalWorkflow)
    
    # Action: created, approved, rejected, cancelled
    action = models.CharField(max_length=20)
    stage = models.CharField(max_length=20)
    
    # Actor
    actor = models.ForeignKey(Employee)
    actor_role = models.CharField(max_length=50)
    
    # Details
    comments = models.TextField(blank=True)
    action_at = models.DateTimeField(auto_now_add=True)
    
    # Audit
    ip_address = models.GenericIPAddressField(null=True)
    user_agent = models.CharField(max_length=500, blank=True)
```

---

### 3. PendingUser Model

Temporary storage for user accounts awaiting approval.

```python
class PendingUser(models.Model):
    workflow = models.OneToOneField(ApprovalWorkflow)
    
    # User credentials (encrypted)
    username = models.CharField(max_length=150, unique=True)
    email = models.EmailField(unique=True)
    temporary_password = models.CharField(max_length=255)  # Hashed
    
    # Employee data (JSON)
    employee_data = models.JSONField()
    official_details_data = models.JSONField(null=True)
    
    # Expiration
    expires_at = models.DateTimeField()  # 30 days from creation
```

**Purpose:**
- Stores account details during approval process
- Prevents duplicate usernames/emails
- Auto-expires after 30 days if not approved
- Deleted after successful creation

---

### 4. ApprovalNotification Model

Notifications for approvers and creators.

```python
class ApprovalNotification(models.Model):
    workflow = models.ForeignKey(ApprovalWorkflow)
    recipient = models.ForeignKey(Employee)
    
    title = models.CharField(max_length=255)
    message = models.TextField()
    
    # Type: pending_approval, approved, rejected, escalated
    notification_type = models.CharField(max_length=20)
    
    # Read tracking
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)
```

---

### 5. Employee Model Updates

Added approval-related fields:

```python
class Employee(models.Model):
    # ... existing fields ...
    
    # Approval fields
    approval_status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending Approval'),
            ('approved', 'Approved'),
            ('rejected', 'Rejected'),
            ('active', 'Active'),
        ],
        default='active'
    )
    created_by = models.ForeignKey('self', null=True, blank=True)
    approved_by = models.ForeignKey('self', null=True, blank=True)
    approval_workflow_id = models.IntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    approved_at = models.DateTimeField(null=True, blank=True)
```

---

## 🔌 API Endpoints

### Base URL
```
/api/approval-workflow/
```

### All Endpoints

| Method | Endpoint | Description | Who Can Use |
|--------|----------|-------------|-------------|
| POST | `/create-employee-request/` | Create employee approval request | HR, Manager, Sub-Manager |
| POST | `/create-hr-supervisor-request/` | Create HR/Supervisor request | Manager, Sub-Manager |
| POST | `/create-sub-company-request/` | Create sub-company request | Manager (main) |
| GET | `/pending-approvals/` | Get pending requests to approve | Manager, Admin |
| POST | `/{id}/approve/` | Approve a workflow | Authorized approver |
| POST | `/{id}/reject/` | Reject a workflow | Authorized approver |
| GET | `/{id}/history/` | Get workflow history | Any authenticated user |
| GET | `/notifications/` | Get my notifications | Any authenticated user |
| POST | `/mark-notification-read/` | Mark notification as read | Any authenticated user |
| GET | `/statistics/` | Get approval statistics | Manager, Admin |

---

## 💡 Complete Usage Examples

### Example 1: HR Creates Employee in Sub-Company 1

**Scenario:** HR in Sub-Company 1 wants to create a new employee.

#### Step 1: HR Creates Request

```bash
POST /api/approval-workflow/create-employee-request/
Authorization: Bearer {hr_token}
Content-Type: application/json

{
  "employee_data": {
    "full_name": "John Doe",
    "employee_code": "EMP001",
    "date_of_birth": "1990-01-15",
    "gender": "M",
    "marital_status": "S",
    "mobile_number": "+1234567890",
    "email": "john.doe@company.com",
    "current_address": "123 Main St",
    "permanent_address": "123 Main St",
    "role": "Employee",
    "sub_company_id": 1  // Sub-Company 1
  },
  "official_details_data": {
    "date_of_joining": "2025-01-01",
    "department": "Engineering",
    "designation": "Software Engineer",
    "location": "New York",
    "supervisor_name": "Jane Manager",
    "salary_type": "MONTHLY"
  },
  "password": "TempPassword123"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Employee creation request submitted. Awaiting Sub-Company Manager approval.",
  "data": {
    "workflow_id": 100,
    "approval_type": "employee",
    "current_stage": "sub_manager",
    "status": "pending"
  }
}
```

**What Happens:**
- ✅ Workflow created with ID 100
- ✅ Notification sent to **Sub-Company 1 Manager ONLY**
- ✅ Other managers are NOT notified
- ✅ PendingUser record created
- ✅ Expires in 30 days if not approved

---

#### Step 2: Sub-Company 1 Manager Views Pending Approvals

```bash
GET /api/approval-workflow/pending-approvals/
Authorization: Bearer {sub_company_1_manager_token}
```

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "id": 100,
      "approval_type": "employee",
      "approval_type_display": "Employee Creation",
      "status": "pending",
      "current_stage": "sub_manager",
      "current_stage_display": "Awaiting Sub-Company Manager",
      "company": "TechCorp Inc",
      "sub_company": "Engineering Division",
      "created_by": {
        "employee_code": "HR001",
        "full_name": "Jane HR",
        "role": "HR"
      },
      "created_at": "2025-10-08T10:30:00Z",
      "request_data": {
        "employee_data": {
          "full_name": "John Doe",
          "employee_code": "EMP001"
        }
      }
    }
  ],
  "pagination": {
    "page": 1,
    "page_size": 20,
    "total_count": 1,
    "total_pages": 1
  }
}
```

**Note:** Only sees requests for **their sub-company**.

---

#### Step 3: Sub-Company 1 Manager Approves

```bash
POST /api/approval-workflow/100/approve/
Authorization: Bearer {sub_company_1_manager_token}
Content-Type: application/json

{
  "comments": "Approved. All details verified by Sub-Company Manager."
}
```

**Response:**
```json
{
  "success": true,
  "message": "Approved. Request moved to Main Company Manager stage.",
  "data": {
    "workflow_id": 100,
    "status": "pending",
    "current_stage": "main_manager"
  }
}
```

**What Happens:**
- ✅ Workflow stage changed from `sub_manager` to `main_manager`
- ✅ Approval history logged
- ✅ Notification sent to **Main Company Manager**
- ✅ Sub-Company Manager's notification marked as escalated

---

#### Step 4: Main Company Manager Approves (Final)

```bash
POST /api/approval-workflow/100/approve/
Authorization: Bearer {main_manager_token}
Content-Type: application/json

{
  "comments": "Final approval granted. Welcome aboard!"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Employee Creation has been approved and created successfully.",
  "data": {
    "workflow_id": 100,
    "status": "approved",
    "current_stage": "completed"
  }
}
```

**What Happens:**
- ✅ User account created: username = `EMP001`, email = `john.doe@company.com`
- ✅ Employee record created with approval status = `approved`
- ✅ OfficialDetails record created and linked
- ✅ PendingUser record deleted
- ✅ Workflow status = `approved`, stage = `completed`
- ✅ Notification sent to creator (HR) confirming success
- ✅ Employee can now log in with provided credentials

---

### Example 2: Sub-Company Manager Rejects Employee

**Scenario:** Sub-Company Manager finds issues and rejects the request.

#### Steps 1-2: Same as Example 1

#### Step 3: Sub-Company Manager Rejects

```bash
POST /api/approval-workflow/100/reject/
Authorization: Bearer {sub_company_1_manager_token}
Content-Type: application/json

{
  "reason": "Incomplete documentation. Missing identity proofs."
}
```

**Response:**
```json
{
  "success": true,
  "message": "Request rejected successfully. Workflow stopped.",
  "data": {
    "workflow_id": 100,
    "status": "rejected",
    "rejection_reason": "Incomplete documentation. Missing identity proofs."
  }
}
```

**What Happens:**
- ✅ Workflow status changed to `rejected`
- ✅ Rejection reason stored
- ✅ Workflow **STOPPED** - no further approvals
- ✅ Main Company Manager is **NOT notified**
- ✅ Creator (HR) receives rejection notification
- ✅ PendingUser retained for 30 days (for reference)
- ✅ Employee account is **NOT created**

---

### Example 3: Manager Creates HR Account (3-Level)

**Scenario:** Main Company Manager wants to create an HR account in Sub-Company 1.

#### Step 1: Manager Creates HR Request

```bash
POST /api/approval-workflow/create-hr-supervisor-request/
Authorization: Bearer {main_manager_token}
Content-Type: application/json

{
  "employee_data": {
    "full_name": "Sarah HR",
    "employee_code": "HR002",
    "date_of_birth": "1988-05-20",
    "gender": "F",
    "marital_status": "M",
    "mobile_number": "+1234567891",
    "email": "sarah.hr@company.com",
    "current_address": "456 Oak Ave",
    "permanent_address": "456 Oak Ave",
    "sub_company_id": 1
  },
  "official_details_data": {
    "date_of_joining": "2025-02-01",
    "department": "Human Resources",
    "designation": "HR Manager",
    "location": "Chicago",
    "supervisor_name": "Director Name",
    "salary_type": "MONTHLY"
  },
  "password": "TempHRPass123",
  "account_type": "hr"
}
```

**Response:**
```json
{
  "success": true,
  "message": "HR creation request submitted. Awaiting Main Company Manager approval.",
  "data": {
    "workflow_id": 101,
    "approval_type": "hr",
    "current_stage": "main_manager",
    "status": "pending"
  }
}
```

**Note:** Since creator is Main Manager, skips sub_manager stage and goes directly to main_manager.

---

#### Step 2: Main Company Manager Approves

```bash
POST /api/approval-workflow/101/approve/
Authorization: Bearer {main_manager_token}

{
  "comments": "Main Manager approval - escalating to Admin"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Approved. Request moved to Admin stage.",
  "data": {
    "workflow_id": 101,
    "status": "pending",
    "current_stage": "admin"
  }
}
```

---

#### Step 3: Admin Approves (Final)

```bash
POST /api/approval-workflow/101/approve/
Authorization: Bearer {admin_token}

{
  "comments": "Admin final approval - HR account created"
}
```

**Response:**
```json
{
  "success": true,
  "message": "HR Account Creation has been approved and created successfully.",
  "data": {
    "workflow_id": 101,
    "status": "approved",
    "current_stage": "completed"
  }
}
```

**What Happens:**
- ✅ HR account created with elevated privileges
- ✅ Admin oversight logged for compliance
- ✅ 3-level approval chain completed

---

## 🔔 Notification System

### Notification Types

1. **pending_approval** - When a request needs your approval
2. **approved** - When your request was approved
3. **rejected** - When your request was rejected
4. **escalated** - When request moved to next level

### Get Notifications

```bash
GET /api/approval-workflow/notifications/?unread_only=true
Authorization: Bearer {token}
```

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "id": 456,
      "workflow_id": 100,
      "title": "New Employee Creation Approval Request",
      "message": "A new Employee Creation request requires your approval. Created by Jane HR.",
      "notification_type": "pending_approval",
      "is_read": false,
      "created_at": "2025-10-08T11:00:00Z",
      "read_at": null
    }
  ],
  "pagination": {...}
}
```

### Mark as Read

```bash
POST /api/approval-workflow/mark-notification-read/
Authorization: Bearer {token}
Content-Type: application/json

{
  "notification_id": 456
}
```

---

## 📊 Statistics & Monitoring

### Get Approval Statistics

```bash
GET /api/approval-workflow/statistics/
Authorization: Bearer {manager_token}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "pending_count": 8,
    "by_type": {
      "employee": 5,
      "hr": 2,
      "supervisor": 1,
      "sub_company": 0
    },
    "unread_notifications": 3
  }
}
```

**Use Cases:**
- Dashboard widgets showing pending approval count
- Real-time notification badges
- Manager workload monitoring

---

## 📜 Audit Trail & History

### View Workflow History

```bash
GET /api/approval-workflow/100/history/
Authorization: Bearer {token}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "workflow_id": 100,
    "approval_type": "Employee Creation",
    "status": "approved",
    "history": [
      {
        "action": "created",
        "action_display": "Workflow Created",
        "stage": "sub_manager",
        "actor": {
          "employee_code": "HR001",
          "full_name": "Jane HR",
          "role": "HR"
        },
        "comments": "Approval workflow created for new employee: John Doe",
        "action_at": "2025-10-08T10:30:00Z"
      },
      {
        "action": "approved",
        "action_display": "Approved",
        "stage": "sub_manager",
        "actor": {
          "employee_code": "MGR005",
          "full_name": "Sub Manager Name",
          "role": "Manager"
        },
        "comments": "Approved. All details verified.",
        "action_at": "2025-10-08T11:15:00Z"
      },
      {
        "action": "approved",
        "action_display": "Approved",
        "stage": "main_manager",
        "actor": {
          "employee_code": "MGR001",
          "full_name": "Main Manager Name",
          "role": "Manager"
        },
        "comments": "Final approval granted.",
        "action_at": "2025-10-08T14:30:00Z"
      }
    ]
  }
}
```

**Compliance Benefits:**
- Complete audit trail for regulatory requirements
- Track who approved what and when
- Rejection reasons documented
- Timestamps for all actions

---

## 🚀 Installation & Setup

### Step 1: Run Migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

This will create the following tables:
- `approval_workflow`
- `approval_history`
- `pending_user`
- `approval_notification`

And update the `employee` table with approval fields.

---

### Step 2: Update URLs (Already Done)

The URLs are already registered in `core/urls.py`:

```python
from . import approval_workflow_views
router.register(r'approval-workflow', approval_workflow_views.ApprovalWorkflowViewSet, basename='approval-workflow')
```

---

### Step 3: Test with Sample Data

#### Create Test Users:

```python
# Create Admin
admin = Employee.objects.create(
    full_name="Admin User",
    employee_code="ADM001",
    email="admin@company.com",
    role="Admin",
    status="ACTIVE"
)

# Create Main Company Manager
main_manager = Employee.objects.create(
    full_name="Main Manager",
    employee_code="MGR001",
    email="manager@company.com",
    role="Manager",
    main_company=main_company,
    status="ACTIVE"
)

# Create Sub-Company Manager
sub_manager = Employee.objects.create(
    full_name="Sub Manager",
    employee_code="MGR002",
    email="submanager@company.com",
    role="Manager",
    sub_company=sub_company,
    status="ACTIVE"
)

# Create HR
hr = Employee.objects.create(
    full_name="HR Person",
    employee_code="HR001",
    email="hr@company.com",
    role="HR",
    sub_company=sub_company,
    status="ACTIVE"
)
```

#### Test Workflow:

```bash
# 1. HR creates employee request
POST /api/approval-workflow/create-employee-request/
# Login as HR001

# 2. Sub-Manager approves
POST /api/approval-workflow/{id}/approve/
# Login as MGR002

# 3. Main Manager approves
POST /api/approval-workflow/{id}/approve/
# Login as MGR001

# 4. Check that employee was created
GET /api/employees/
```

---

## 🔒 Security Considerations

### 1. **Permission Validation**

Every action validates:
- User is authenticated
- User has employee profile
- User has required role for the action
- User has access to the specific company

### 2. **Company Isolation**

```python
# Sub-Company Manager only sees their sub-company's requests
workflows = ApprovalWorkflow.objects.filter(
    current_stage='sub_manager',
    sub_company=current_employee.sub_company,
    status='pending'
)

# Main Company Manager only sees their main company's requests
workflows = ApprovalWorkflow.objects.filter(
    current_stage='main_manager',
    company=current_employee.main_company,
    status='pending'
)
```

### 3. **Prevent Unauthorized Approval**

```python
def can_approve(self, employee):
    # Check stage and role match
    if self.current_stage == 'admin' and employee.role != 'Admin':
        return False
    
    # Check company context
    if self.current_stage == 'sub_manager':
        if employee.sub_company_id != self.sub_company_id:
            return False
    
    return True
```

### 4. **Data Encryption**

- Passwords stored hashed using Django's `make_password()`
- Sensitive data in JSON fields can be encrypted
- Use HTTPS in production

---

## ⚠️ Important Notes

### 1. **Rejection is Permanent**

Once rejected, the workflow cannot be resumed. Creator must:
- Fix the issues
- Create a new approval request

### 2. **Expiration Management**

- Pending requests expire after **30 days**
- Run cleanup job to delete expired pending users:

```python
# management/commands/cleanup_expired_approvals.py
from django.core.management.base import BaseCommand
from django.utils import timezone
from core.approval_models import PendingUser

class Command(BaseCommand):
    def handle(self, *args, **options):
        expired = PendingUser.objects.filter(
            expires_at__lt=timezone.now()
        )
        count = expired.count()
        expired.delete()
        self.stdout.write(f"Deleted {count} expired pending users")
```

Run daily via cron:
```bash
python manage.py cleanup_expired_approvals
```

### 3. **Email Notifications (Optional Enhancement)**

Add email notifications alongside in-app notifications:

```python
def _notify_next_approvers(self, workflow):
    approvers = self._get_next_approvers(workflow)
    
    for approver in approvers:
        # In-app notification
        self._create_notification(...)
        
        # Email notification (optional)
        send_mail(
            subject=f"New Approval Request: {workflow.get_approval_type_display()}",
            message=f"You have a new approval request from {workflow.created_by.full_name}",
            from_email='noreply@company.com',
            recipient_list=[approver.email]
        )
```

### 4. **Performance Optimization**

For large organizations with many approvals:

- Add database indexes (already defined in Meta class)
- Use `select_related()` and `prefetch_related()` in queries
- Implement caching for statistics
- Consider pagination for all list endpoints

---

## 📈 Monitoring & Analytics

### Metrics to Track:

1. **Average Approval Time**
   - Time from creation to completion
   - Time spent at each stage

2. **Rejection Rate**
   - Percentage of requests rejected
   - Common rejection reasons

3. **Pending Backlog**
   - Number of pending requests
   - Age of pending requests

4. **Approver Performance**
   - Average response time per approver
   - Number of approvals per approver

### Example Analytics Query:

```python
from django.db.models import Avg, Count
from datetime import timedelta

# Average approval time
avg_time = ApprovalWorkflow.objects.filter(
    status='approved',
    completed_at__isnull=False
).aggregate(
    avg_duration=Avg(
        models.F('completed_at') - models.F('created_at')
    )
)

# Rejection rate
total = ApprovalWorkflow.objects.count()
rejected = ApprovalWorkflow.objects.filter(status='rejected').count()
rejection_rate = (rejected / total * 100) if total > 0 else 0
```

---

## 🎓 Best Practices

### 1. **Clear Rejection Reasons**

Always provide detailed rejection reasons:
```json
{
  "reason": "Incomplete documentation. Missing: 1) Aadhaar card copy, 2) Previous employment letter"
}
```

### 2. **Informative Approval Comments**

Add context to approvals:
```json
{
  "comments": "Approved after verification of identity documents and background check completion."
}
```

### 3. **Regular Cleanup**

- Run expiration cleanup daily
- Archive completed workflows older than 1 year
- Monitor pending backlog

### 4. **User Training**

Train users on:
- How to create proper approval requests
- What documents are required
- Expected approval timelines
- How to handle rejections

---

## 📚 Related Documentation

- **API Documentation**: `api/approval_workflow_apis.html`
- **Manager Dashboard**: `MANAGER_DASHBOARD_IMPLEMENTATION.md`
- **Admin Dashboard**: `ADMIN_DASHBOARD_IMPLEMENTATION.md`
- **HR Dashboard**: `HR_DASHBOARD_IMPLEMENTATION.md`

---

## 🆘 Troubleshooting

### Problem: Manager not seeing pending approvals

**Check:**
1. Is manager's company correctly set in Employee model?
2. Is workflow's company/sub_company correctly set?
3. Is workflow at the correct stage?

```python
# Debug query
workflow = ApprovalWorkflow.objects.get(id=100)
print(f"Current stage: {workflow.current_stage}")
print(f"Company: {workflow.company}")
print(f"Sub-company: {workflow.sub_company}")

manager = Employee.objects.get(employee_code='MGR001')
print(f"Manager company: {manager.main_company}")
print(f"Manager sub-company: {manager.sub_company}")
```

### Problem: Approval not moving to next stage

**Check:**
1. Is `get_next_stage()` returning correct value?
2. Are notifications being created?
3. Check ApprovalHistory for logged actions

### Problem: Employee not created after final approval

**Check:**
1. Is PendingUser record present?
2. Are there any exceptions in server logs?
3. Verify employee_data has all required fields

---

## ✅ Checklist for Production

- [ ] Run migrations on production database
- [ ] Create initial Admin, Manager, HR test accounts
- [ ] Test complete workflows for each account type
- [ ] Set up email notifications
- [ ] Configure expiration cleanup cron job
- [ ] Add monitoring and alerting
- [ ] Train users on the system
- [ ] Document company-specific approval policies
- [ ] Set up backup for approval_workflow tables
- [ ] Configure audit log retention policy

---

**Last Updated:** October 8, 2025  
**Version:** 1.0  
**Status:** ✅ Production Ready

---

**🎉 System is now ready for hierarchical multi-level approvals with smart company-specific routing!**
