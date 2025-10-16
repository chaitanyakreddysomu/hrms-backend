from django.urls import path, include,re_path
from rest_framework.routers import DefaultRouter
from . import views


router = DefaultRouter()
router.register(r'users', views.UserViewSet)

urlpatterns = [
    
    


    
    
    # path('contact', views.contact_view, name='contact'),
    path('add-admin/', views.AddAdminView.as_view(), name='add-admin'),
    path('admin-login/', views.AdminLoginView.as_view(), name='admin-login'),
    path('add-question/', views.AddExamQuestionView.as_view(), name='add-question'),
    path('add-schedule/', views.AddExamScheduleView.as_view(), name='add-schedule'),

    path('start-exam/', views.StartExamView.as_view(), name='start-exam'),
    path('submit-score/<str:session_id>/', views.SubmitScoreView.as_view(), name='submit-score'),

    path('exam-questions/', views.ExamQuestionListView.as_view(), name='exam-questions'),
    path('exam-schedules/', views.ExamScheduleListView.as_view(), name='exam-schedules'),
    path('admins/', views.AdminListView.as_view(), name='admins-list'),
    path('users/', views.UserListView.as_view(), name='users-list'),
    path('delete-user/<str:id>/', views.delete_user_view, name='delete-user'),

    path('edit-question/<str:id>/', views.edit_exam_question, name='edit-question'),
    path('delete-question/<str:id>/', views.delete_exam_question, name='delete-question'),
    path('edit-schedule/<str:id>/', views.edit_exam_schedule, name='edit-schedule'),
    path('delete-schedule/<str:id>/', views.delete_exam_schedule, name='delete-schedule'),

    # API routes
    path('', include(router.urls)),
]

# Updated urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView
from . import views

router = DefaultRouter()
router.register(r'auth', views.AuthViewSet, basename='auth')
router.register(r'companies', views.CompanyViewSet, basename='company')
router.register(r'client-settings', views.ClientProfileSettingsViewSet, basename='client-settings')
router.register(r'employees', views.EmployeeViewSet, basename='employees')
router.register(r'salary-structures', views.SalaryStructureViewSet, basename='salary-structures')
router.register(r'attendance', views.AttendanceViewSet, basename='attendance')
router.register(r'payroll', views.PayrollViewSet, basename='payroll')
router.register(r'reports', views.ReportsViewSet, basename='reports')
router.register(r'documents', views.DocumentViewSet, basename='documents')
router.register(r'supervisor', views.SupervisorViewSet, basename='supervisor')
router.register(r'hr', views.HRViewSet, basename='hr')
router.register(r'admin', views.AdminViewSet, basename='admin')

# Employee Dashboard ViewSets
from . import employee_dashboard_views
router.register(r'employee-dashboard', employee_dashboard_views.EmployeeDashboardViewSet, basename='employee-dashboard')
router.register(r'employee-profile', employee_dashboard_views.EmployeeProfileViewSet, basename='employee-profile')
router.register(r'employee-documents', employee_dashboard_views.EmployeeDocumentsViewSet, basename='employee-documents')
router.register(r'employee-salary', employee_dashboard_views.EmployeeSalaryViewSet, basename='employee-salary')
router.register(r'employee-attendance', employee_dashboard_views.EmployeeAttendanceViewSet, basename='employee-attendance')
router.register(r'employee-reports', employee_dashboard_views.EmployeeReportsViewSet, basename='employee-reports')

# HR/Admin/Manager/Supervisor ViewSets for Employee Data Management
from . import hr_admin_views
router.register(r'employee-data-management', hr_admin_views.EmployeeDataManagementViewSet, basename='employee-data-management')
router.register(r'employee-document-management', hr_admin_views.EmployeeDocumentManagementViewSet, basename='employee-document-management')

# Admin Dashboard ViewSet for Complete System Management
from . import admin_dashboard_views
router.register(r'admin-dashboard', admin_dashboard_views.AdminDashboardViewSet, basename='admin-dashboard')

# HR Dashboard ViewSet for Comprehensive HR Management
from . import hr_dashboard_views
router.register(r'hr-dashboard', hr_dashboard_views.HRDashboardViewSet, basename='hr-dashboard')

# Approval Workflow ViewSet for Hierarchical Approvals
from . import approval_workflow_views
router.register(r'approval-workflow', approval_workflow_views.ApprovalWorkflowViewSet, basename='approval-workflow')

# Supervisor Dashboard ViewSet for Team Management
from . import supervisor_dashboard_views
router.register(r'supervisor-dashboard', supervisor_dashboard_views.SupervisorDashboardViewSet, basename='supervisor-dashboard')

# Manager Dashboard ViewSet for Main Company Management
from . import manager_dashboard_views
router.register(r'manager-dashboard', manager_dashboard_views.ManagerDashboardViewSet, basename='manager-dashboard')

# Sub-Manager Dashboard ViewSet for Sub-Company Management
from . import submanager_dashboard_views
router.register(r'sub-manager-dashboard', submanager_dashboard_views.SubManagerDashboardViewSet, basename='sub-manager-dashboard')

admin_setup_urlpatterns = [
    path('api/admin/status/', views.check_system_status, name='admin-status'),
    path('api/admin/setup/', views.create_admin_setup, name='admin-setup'),
    path('api/admin/quick-setup/', views.quick_admin_setup, name='admin-quick-setup'),
    path('api/admin/sample-data/', views.create_sample_data, name='admin-sample-data'),
]

urlpatterns = [
    path('api/', include(router.urls)),
    
    # Authentication
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # Company management (NEW ENDPOINTS)
    path('api/main-companies/', views.get_main_companies, name='get-main-companies'),
    path('api/transfer-company/', views.transfer_company, name='transfer-company'),
    
    # Utility endpoints
    path('api/dashboard-stats/', views.dashboard_stats, name='dashboard-stats'),
    path('api/switch-client/', views.switch_client_profile, name='switch-client'),
    path('api/master-data/', views.master_data, name='master-data'),
    path('api/employee-search/', views.employee_search, name='employee-search'),
    path('api/client-info/', views.get_user_client_info, name='get-user-client-info'),
    
    # Document operations
    path('api/generate-appointment/', views.generate_appointment_order, name='generate-appointment'),
    path('api/bulk-document-send/', views.bulk_document_send, name='bulk-document-send'),
    
    # Attendance operations
    path('api/attendance-template/', views.attendance_template, name='attendance-template'),
    path('api/lock-salary-statement/', views.lock_salary_statement, name='lock-salary-statement'),
    
    # File downloads
    path('api/download-payslip/<int:payslip_id>/', views.download_payslip, name='download-payslip'),
    path('api/export-report/', views.export_report, name='export-report'),
    
    # Client user creation
    path('api/create-client-user/', views.create_client_user, name='create-client-user'),

    path('api/create-employee/', views.create_employee_for_subcompany, name='create-employee'),
    path('api/accessible-subcompanies/', views.get_accessible_subcompanies, name='accessible-subcompanies'),
    path('api/subcompany-employees/', views.get_employees_by_subcompany, name='subcompany-employees'),
    path('api/creatable-roles/', views.get_creatable_roles, name='creatable-roles'),

] + admin_setup_urlpatterns

"""
=======================
API ENDPOINT EXAMPLES
=======================

1. LOGIN (Anyone can access)
POST /api/auth/login/
{
    "username": "admin",
    "password": "your_password"
}

2. GET ALL COMPANIES (Admin/Manager only)
GET /api/companies/
Headers: Authorization: Bearer <your_token>

3. CREATE MAIN COMPANY WITH MANAGER (Admin only)
POST /api/companies/create_main_company/
Headers: Authorization: Bearer <admin_token>
{
    "company_data": {
        "name": "New Main Company Ltd",
        "address": "123 Main St, City, State, Country",
        "gst_number": "29AAGCI9587F1ZZ"
    },
    "user_data": {
        "username": "main_company_manager",
        "email": "manager@maincompany.com",
        "password": "secure_password_123",
        "first_name": "John",
        "last_name": "Manager",
        "mobile_number": "9876543210",
        "date_of_birth": "1985-06-15",
        "gender": "M",
        "marital_status": "M"
    }
}

Response:
{
    "success": true,
    "message": "Main company created successfully",
    "company": {
        "id": 1,
        "name": "New Main Company Ltd",
        "address": "123 Main St, City, State, Country",
        "gst_number": "29AAGCI9587F1ZZ",
        "is_main_company": true,
        "parent_company": null
    },
    "user_account": {
        "id": 5,
        "username": "main_company_manager",
        "email": "manager@maincompany.com",
        "role": "Manager",
        "message": "Manager account created for main company"
    }
}

4. CREATE SUB-COMPANY WITH MANAGER (Admin/Manager)
POST /api/companies/create_sub_company/
Headers: Authorization: Bearer <your_token>
{
    "parent_company_id": 1,
    "company_data": {
        "name": "Client Sub Company Pvt Ltd",
        "address": "456 Client St, Client City",
        "gst_number": "29BBGCI9587F1ZZ"
    },
    "settings_data": {
        "esi_applicable": true,
        "pf_applicable": true,
        "pt_applicable": true,
        "lwf_applicable": false,
        "advance_applicable": true,
        "insurance_applicable": true,
        "service_charge_type": "PERCENTAGE",
        "service_charge_value": 6.0
    },
    "user_data": {
        "username": "client_manager",
        "email": "manager@clientcompany.com",
        "password": "client_secure_123",
        "first_name": "Jane",
        "last_name": "ClientManager",
        "mobile_number": "9876543211",
        "date_of_birth": "1988-03-20",
        "gender": "F",
        "marital_status": "S"
    }
}

Response:
{
    "success": true,
    "message": "Sub-company created successfully",
    "company": {
        "id": 2,
        "name": "Client Sub Company Pvt Ltd",
        "address": "456 Client St, Client City",
        "gst_number": "29BBGCI9587F1ZZ",
        "is_main_company": false,
        "parent_company": 1
    },
    "settings": {
        "id": 1,
        "client": 2,
        "esi_applicable": true,
        "pf_applicable": true,
        "pt_applicable": true,
        "service_charge_type": "PERCENTAGE",
        "service_charge_value": "6.00"
    },
    "parent_company": {
        "id": 1,
        "name": "New Main Company Ltd"
    },
    "user_account": {
        "id": 6,
        "username": "client_manager",
        "email": "manager@clientcompany.com",
        "role": "Sub-Manager",
        "message": "Sub-Manager account created for sub-company"
    }
}

5. GET SUB-COMPANIES UNDER MAIN COMPANY
GET /api/companies/1/sub_companies/
Headers: Authorization: Bearer <your_token>

Response:
{
    "main_company": {
        "id": 1,
        "name": "New Main Company Ltd",
        "is_main_company": true
    },
    "sub_companies": [
        {
            "id": 2,
            "name": "Client Sub Company Pvt Ltd",
            "parent_company": 1,
            "is_main_company": false
        }
    ],
    "count": 1
}

6. GET COMPANY HIERARCHY
GET /api/companies/hierarchy/
Headers: Authorization: Bearer <your_token>

7. GET MAIN COMPANIES FOR DROPDOWN
GET /api/main-companies/
Headers: Authorization: Bearer <your_token>

8. TRANSFER SUB-COMPANY TO DIFFERENT MAIN COMPANY
POST /api/transfer-company/
Headers: Authorization: Bearer <your_token>
{
    "sub_company_id": 2,
    "new_parent_company_id": 3
}

======================
ROLE ASSIGNMENT LOGIC:
======================

MAIN COMPANY CREATION:
- Creates Company with is_main_company=True
- Creates User account with Manager role (Django Group)
- Creates Employee record with role='Manager'
- Associates Employee with main_company (not sub_company)

SUB-COMPANY CREATION:
- Creates Company with is_main_company=False and parent_company set
- Creates ClientProfileSettings for the sub-company
- Creates User account with Sub-Manager role (Django Group)
- Creates Employee record with role='Sub-Manager'  
- Associates Employee with sub_company (not main_company)

ROLE HIERARCHY:
1. Admin (Django Group) - Can create main companies, manage everything
2. Manager (Django Group) - Main company managers, can create sub-companies, manage their domain
3. Sub-Manager (Django Group) - Sub-company managers, can manage their sub-company only
4. HR (Django Group) - Employee management, payroll, reports
5. Supervisor (Django Group) - Limited employee operations
6. Employee (Django Group) - View own data only

======================
PERMISSION STRUCTURE:
======================

COMPANY OPERATIONS:
✓ create_main_company: Admin only
✓ create_sub_company: Admin or Manager
✓ get companies: Admin or Manager
✓ get hierarchy: Admin or Manager
✓ transfer company: Admin or Manager

EMPLOYEE OPERATIONS:
✓ create/edit employees: Admin, Manager, or HR
✓ view employees: Admin, Manager, HR, or Supervisor
✓ delete employees: Admin or Manager only

PAYROLL OPERATIONS:
✓ generate payslips: Admin, Manager, or HR
✓ approve payroll: Manager only
✓ view payroll: Admin, Manager, or HR

======================
USER DATA STRUCTURE:
======================

Required Fields:
- username (must be unique)
- email (must be unique)
- password (minimum 6 characters recommended)

Optional Fields:
- first_name (defaults to company name first word)
- last_name (defaults to "Administrator")
- mobile_number (defaults to "0000000000")
- date_of_birth (defaults to "1990-01-01")
- gender (M/F/O, defaults to "M")
- marital_status (S/M/D/W, defaults to "S")

Auto-Generated Fields:
- employee_code: MAIN_<company_id>_ADMIN or SUB_<company_id>_ADMIN
- role: Always "Manager" for company administrators
- status: Always "ACTIVE"

======================
ERROR HANDLING:
======================

Common Errors:
1. "Permission denied" - User doesn't have required role
2. "Username already exists" - Choose different username
3. "Email already exists" - Choose different email  
4. "Invalid parent company ID" - Parent company doesn't exist or isn't main company
5. "GST number already exists" - Use unique GST number

To Debug:
1. Check user token validity: GET /api/auth/profile/ (if available)
2. Check user groups: Verify user is in Admin or Manager group
3. Check company structure: GET /api/companies/hierarchy/
4. Check employee records: GET /api/employees/ with client_id filter
"""