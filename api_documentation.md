# Manpower Services Management System - API Documentation

## Overview
This Django REST API backend provides comprehensive manpower services management for contract labor providers. The system supports multi-tenant architecture with role-based access control.

## Base URL
```
https://your-domain.com/api/
```

## Authentication
All endpoints require JWT authentication except login.

### Headers Required
```
Authorization: Bearer <access_token>
Content-Type: application/json
```

## Main Endpoints

### 1. Authentication

#### Login
```http
POST /api/auth/login/
```

**Request Body:**
```json
{
    "username": "admin",
    "password": "password"
}
```

**Response:**
```json
{
    "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "user": {
        "id": 1,
        "username": "admin",
        "email": "admin@example.com",
        "first_name": "Admin",
        "last_name": "User"
    },
    "main_companies": [
        {
            "id": 1,
            "name": "RMS (RADIANT Manpower Services)",
            "is_main_company": true
        }
    ],
    "current_client": null
}
```

#### Token Refresh
```http
POST /api/token/refresh/
```

### 2. Company Management

#### Get Main Companies (RMS, IMS, KVS)
```http
GET /api/companies/main_companies/
```

#### Get Clients under Main Company
```http
GET /api/companies/{main_company_id}/clients/
```

#### Create New Client with Settings
```http
POST /api/companies/create_client/
```

**Request Body:**
```json
{
    "client_data": {
        "name": "Brand Studio Lifestyle Pvt Ltd",
        "address": "Bangalore",
        "gst_number": "29AAACO8088P1ZH",
        "is_main_company": false
    },
    "settings_data": {
        "esi_applicable": true,
        "pf_applicable": true,
        "pt_applicable": true,
        "lwf_applicable": false,
        "advance_applicable": true,
        "insurance_applicable": true,
        "service_charge_type": "PERCENTAGE",
        "service_charge_value": 6.00
    }
}
```

### 3. Employee Management

#### List Employees
```http
GET /api/employees/?client_id=1&status=ACTIVE
```

#### Create Employee
```http
POST /api/employees/
```

**Request Body:**
```json
{
    "full_name": "John Doe",
    "employee_code": "IMS-001",
    "date_of_birth": "1990-01-01",
    "gender": "M",
    "marital_status": "S",
    "mobile_number": "9876543210",
    "email": "john@example.com",
    "current_address": "Bangalore",
    "permanent_address": "Bangalore",
    "role": "EMPLOYEE",
    "main_company": 1,
    "sub_company": 2,
    "official_details": {
        "date_of_joining": "2025-01-01",
        "department": "Production",
        "designation": "Operator",
        "location": "Bangalore",
        "supervisor_name": "Manager",
        "salary_type": "MONTHLY"
    },
    "identity_document": {
        "aadhaar_number": "123456789012",
        "pan_number": "ABCDE1234F",
        "pf_uan_number": "123456789012"
    },
    "bank_details": {
        "bank_name": "SBI",
        "account_number": "12345678901",
        "ifsc_code": "SBIN0001234",
        "branch_name": "Main Branch"
    },
    "salary_structure": {
        "CTC": "300000",
        "basic": 12000.00,
        "da": 2400.00,
        "hra": 3600.00,
        "conveyance": 1600.00,
        "bonus": 1000.00,
        "other_allowances": 400.00,
        "pf_deduction": 1440.00,
        "esi_deduction": 367.50,
        "pt_deduction": 200.00,
        "lwf_deduction": 0.75,
        "insurance": 500.00,
        "advance": 0.00
    }
}
```

#### Get Employee Details
```http
GET /api/employees/{employee_id}/
```

#### Salary Increment
```http
POST /api/employees/{employee_id}/increment_salary/
```

**Request Body:**
```json
{
    "effective_date": "2025-04-01",
    "salary_data": {
        "basic": 15000.00,
        "da": 3000.00,
        "hra": 4500.00
    }
}
```

### 4. Attendance Management

#### Bulk Attendance Upload
```http
POST /api/attendance/bulk_upload/
```

**Request Body:**
```json
{
    "month": 1,
    "year": 2025,
    "company_id": 1,
    "attendance_data": [
        {
            "employee_id": 1,
            "date": "2025-01-01",
            "status": "P"
        },
        {
            "employee_id": 1,
            "date": "2025-01-02",
            "status": "A"
        }
    ]
}
```

#### Monthly Attendance Summary
```http
GET /api/attendance/monthly_summary/?client_id=1&month=1&year=2025
```

#### Get Attendance Template
```http
GET /api/attendance-template/?client_id=1&month=1&year=2025
```

### 5. Payroll Management

#### Generate Salary Statement
```http
POST /api/payroll/generate_salary_statement/
```

**Request Body:**
```json
{
    "employee_id": 1,
    "month": 1,
    "year": 2025,
    "days_in_month": 31,
    "days_payable": 30,
    "overtime_hours": 5.0
}
```

#### Generate Invoice
```http
POST /api/payroll/generate_invoice/
```

**Request Body:**
```json
{
    "client_id": 1,
    "month": 1,
    "year": 2025
}
```

### 6. Reports

#### Statutory Reports (ESI, PF, PT, LWF)
```http
POST /api/reports/statutory_report/
```

**Request Body:**
```json
{
    "company_id": 1,
    "month": 1,
    "year": 2025,
    "report_type": "ESI"
}
```

### 7. Document Management

#### Upload Document
```http
POST /api/documents/
```

**Request Body (multipart/form-data):**
```
employee: 1
doc_type: APPOINTMENT
file: [file upload]
issued_date: 2025-01-01
```

#### Send Document via Email
```http
POST /api/documents/{document_id}/send_email/
```

**Request Body:**
```json
{
    "email": "employee@example.com"
}
```

### 8. Utility Endpoints

#### Dashboard Statistics
```http
GET /api/dashboard-stats/?client_id=1
```

#### Switch Client Profile
```http
POST /api/switch-client/
```

**Request Body:**
```json
{
    "client_id": 2
}
```

#### Master Data for Dropdowns
```http
GET /api/master-data/
```

#### Employee Search
```http
GET /api/employee-search/?q=john&client_id=1
```

#### Lock Salary Statement
```http
POST /api/lock-salary-statement/
```

**Request Body:**
```json
{
    "month": 1,
    "year": 2025,
    "client_id": 1
}
```

### 9. Role-Specific Endpoints

#### Supervisor Endpoints
```http
GET /api/supervisor/assigned_employees/
POST /api/supervisor/submit_attendance/
```

#### HR Endpoints
```http
GET /api/hr/pending_approvals/
POST /api/hr/approve_attendance/
```

#### Admin Endpoints
```http
GET /api/admin/activity_log/
POST /api/admin/unlock_statement/
```

### 10. File Downloads

#### Download Payslip
```http
GET /api/download-payslip/{payslip_id}/
```

#### Export Report
```http
GET /api/export-report/?report_type=ATTENDANCE&format=excel&client_id=1&month=1&year=2025
```

## Response Formats

### Success Response
```json
{
    "status": "success",
    "data": { ... },
    "message": "Operation completed successfully"
}
```

### Error Response
```json
{
    "status": "error",
    "errors": {
        "field_name": ["Error message"]
    },
    "message": "Validation failed"
}
```

### Pagination Response
```json
{
    "count": 100,
    "next": "http://api.example.com/employees/?page=3",
    "previous": "http://api.example.com/employees/?page=1",
    "results": [...]
}
```

## Query Parameters

### Common Query Parameters
- `page`: Page number for pagination
- `page_size`: Number of items per page (max 100)
- `ordering`: Field name to sort by (prefix with - for descending)
- `search`: Search term for text fields

### Employee Filtering
- `client_id`: Filter by client company
- `status`: ACTIVE, LEFT, TERMINATED
- `department`: Filter by department
- `designation`: Filter by designation

### Attendance Filtering  
- `month`: Month (1-12)
- `year`: Year (YYYY)
- `employee_id`: Specific employee
- `date_from`: Start date (YYYY-MM-DD)
- `date_to`: End date (YYYY-MM-DD)

## Status Codes

- `200 OK`: Successful GET, PUT, PATCH
- `201 Created`: Successful POST
- `204 No Content`: Successful DELETE
- `400 Bad Request`: Invalid request data
- `401 Unauthorized`: Authentication required
- `403 Forbidden`: Permission denied
- `404 Not Found`: Resource not found
- `422 Unprocessable Entity`: Validation error
- `500 Internal Server Error`: Server error

## Rate Limiting

- 1000 requests per hour per user
- 100 requests per minute per user
- File upload: 10 uploads per minute

## Data Models

### Employee Model
```json
{
    "id": 1,
    "full_name": "John Doe",
    "employee_code": "IMS-001",
    "date_of_birth": "1990-01-01",
    "gender": "M",
    "marital_status": "S",
    "mobile_number": "9876543210",
    "email": "john@example.com",
    "current_address": "Address",
    "permanent_address": "Address",
    "role": "EMPLOYEE",
    "main_company": 1,
    "sub_company": 2,
    "status": "ACTIVE",
    "photo": "/media/photos/photo.jpg",
    "client_code": "CLIENT001"
}
```

### Attendance Model
```json
{
    "id": 1,
    "employee": 1,
    "date": "2025-01-01",
    "status": "P",
    "employee_name": "John Doe",
    "employee_code": "IMS-001"
}
```

### Payslip Model
```json
{
    "id": 1,
    "employee": 1,
    "month": 1,
    "year": 2025,
    "gross_salary": 21000.00,
    "deductions": 2507.25,
    "net_salary": 18492.75,
    "pdf_file": "/media/payslips/payslip.pdf",
    "employee_name": "John Doe",
    "employee_code": "IMS-001"
}
```

## Validation Rules

### Employee Creation
- `full_name`: Required, max 100 characters
- `employee_code`: Required, unique, max 20 characters
- `date_of_birth`: Required, date format
- `mobile_number`: Required, 10 digits
- `email`: Required, valid email format

### Attendance
- `status`: Required, choices: P, A, WO, H, HD
- `date`: Required, cannot be future date
- `employee`: Must be active employee

### Salary Structure
- All amount fields: Must be positive numbers
- `basic`: Required, minimum wage compliance
- Net salary calculation: earnings - deductions

## Business Rules

### Attendance Rules
- Can only mark attendance for past 5 days
- Weekly off defaults to Saturday
- Overtime calculated at 2x rate after 8 hours
- Half day = 0.5 attendance count

### Payroll Rules
- ESI applicable only if gross salary ≤ ₹25,000
- PF deduction: 12% of basic salary
- ESI deduction: 1.75% of gross salary
- PT deduction based on salary slabs
- Service charge: Fixed amount or percentage of gross

### Document Rules
- Maximum file size: 5MB
- Supported formats: PDF, JPG, JPEG, PNG, DOC, DOCX
- Auto-generate appointment orders, ID cards, payslips
- Email documents directly to employees

## Security Features

### Authentication
- JWT tokens with 8-hour expiry
- Refresh token rotation
- Session timeout after 30 minutes idle

### Authorization
- Role-based access control (Admin, HR, Supervisor, Employee)
- Client profile isolation
- Permission checks on all endpoints

### Data Protection
- Input validation and sanitization
- SQL injection prevention
- XSS protection
- File upload validation
- Activity logging for audit trail

## Integration Points

### Email Integration
- SMTP configuration for notifications
- Template-based emails
- Attachment support for documents

### WhatsApp Integration
- WhatsApp Business API integration
- Document sharing via WhatsApp
- Status notifications

### External APIs
- Bank API for salary disbursement
- Government portals for statutory compliance
- SMS gateway for notifications

## Performance Considerations

### Caching
- Redis caching for frequently accessed data
- Session caching
- Query result caching

### Database Optimization
- Indexed fields for fast lookups
- Query optimization
- Connection pooling

### File Handling
- Async file processing
- Compressed file storage
- CDN integration for media files

## Error Handling

### Common Error Scenarios
1. **Invalid Client Profile**: User tries to access data from unauthorized client
2. **Duplicate Employee Code**: Attempting to create employee with existing code
3. **Invalid Attendance Date**: Marking attendance for future date or locked period
4. **Insufficient Permissions**: User lacks required role permissions
5. **File Upload Errors**: Invalid file type, size exceeded, corrupted file

### Error Response Examples
```json
{
    "error": "INVALID_CLIENT_ACCESS",
    "message": "You don't have permission to access this client's data",
    "code": 403
}
```

```json
{
    "error": "VALIDATION_ERROR",
    "message": "Validation failed",
    "details": {
        "employee_code": ["Employee with this code already exists"],
        "email": ["Enter a valid email address"]
    },
    "code": 400
}
```

## Deployment Notes

### Environment Variables
```env
SECRET_KEY=your-secret-key
DEBUG=False
DATABASE_URL=postgresql://user:pass@localhost/db
REDIS_URL=redis://localhost:6379/0
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
AWS_ACCESS_KEY_ID=your-aws-key
AWS_SECRET_ACCESS_KEY=your-aws-secret
WHATSAPP_API_TOKEN=your-whatsapp-token
```

### Production Checklist
- [ ] Set DEBUG=False
- [ ] Configure proper database
- [ ] Set up Redis for caching
- [ ] Configure email settings
- [ ] Set up file storage (AWS S3)
- [ ] Configure CORS for frontend
- [ ] Set up SSL certificates
- [ ] Configure log rotation
- [ ] Set up monitoring (Sentry)
- [ ] Configure backup strategy

## Testing

### API Testing
```bash
# Install test dependencies
pip install pytest pytest-django

# Run tests
pytest

# Run with coverage
pytest --cov=manpower
```

### Sample Test Cases
- User authentication and authorization
- Employee CRUD operations
- Attendance bulk upload
- Payroll calculation accuracy
- Document generation and email sending
- Role-based access control
- Data validation and error handling