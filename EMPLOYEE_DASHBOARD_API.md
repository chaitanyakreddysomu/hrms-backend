# Employee Dashboard API Documentation

## Overview
This document describes the Employee Dashboard APIs for the HRMS system. These APIs provide employees with self-service access to their personal information, documents, salary, attendance, and reports.

---

## Authentication
All employee dashboard APIs require authentication using JWT tokens.

**Header Required:**
```
Authorization: Bearer <your_jwt_token>
```

---

## API Endpoints

### 1. Dashboard APIs

#### 1.1 Get Dashboard Stats
**Endpoint:** `GET /api/employee-dashboard/stats/`

**Description:** Returns employee dashboard statistics including present days, absent days, OT hours, and take-home salary for the current month.

**Response:**
```json
{
  "employee_name": "John Doe",
  "employee_code": "EMP001",
  "profile_photo": "http://example.com/media/employee_photos/john.jpg",
  "present_days": 20,
  "absent_days": 2,
  "half_days": 1,
  "ot_hours": 10.5,
  "take_home_salary": 45000.00,
  "current_month": "January 2025"
}
```

#### 1.2 Get Recent Notifications
**Endpoint:** `GET /api/employee-dashboard/notifications/`

**Query Parameters:**
- `limit` (optional, default: 10) - Number of notifications to return
- `unread_only` (optional, default: false) - Return only unread notifications

**Response:**
```json
{
  "notifications": [
    {
      "id": 1,
      "notification_type": "PAYSLIP",
      "title": "Payslip Uploaded",
      "message": "Your payslip for December 2024 has been uploaded",
      "is_read": false,
      "created_at": "2025-01-05T10:30:00Z",
      "link": "/api/employee-salary/payslips/?month=12&year=2024"
    },
    {
      "id": 2,
      "notification_type": "SALARY",
      "title": "Salary Credited",
      "message": "Your salary for December 2024 has been credited",
      "is_read": false,
      "created_at": "2025-01-01T09:00:00Z",
      "link": null
    }
  ],
  "unread_count": 5
}
```

#### 1.3 Mark Notification as Read
**Endpoint:** `POST /api/employee-dashboard/{notification_id}/mark-read/`

**Response:**
```json
{
  "message": "Notification marked as read"
}
```

#### 1.4 Mark All Notifications as Read
**Endpoint:** `POST /api/employee-dashboard/mark-all-read/`

**Response:**
```json
{
  "message": "5 notifications marked as read"
}
```

---

### 2. Profile APIs

#### 2.1 Get Personal Information
**Endpoint:** `GET /api/employee-profile/personal-info/`

**Response:**
```json
{
  "full_name": "John Doe",
  "employee_code": "EMP001",
  "date_of_birth": "1990-05-15",
  "gender": "Male",
  "gender_code": "M",
  "marital_status": "Married",
  "marital_status_code": "M",
  "photo": "http://example.com/media/employee_photos/john.jpg"
}
```

#### 2.2 Get Contact Information
**Endpoint:** `GET /api/employee-profile/contact-info/`

**Response:**
```json
{
  "mobile_number": "9876543210",
  "email": "john.doe@example.com",
  "current_address": "123 Main St, City, State, 12345",
  "permanent_address": "456 Home St, Town, State, 67890"
}
```

#### 2.3 Get Official Information
**Endpoint:** `GET /api/employee-profile/official-info/`

**Response:**
```json
{
  "date_of_joining": "2020-01-15",
  "department": "IT Department",
  "designation": "Senior Developer",
  "location": "Bangalore Office",
  "supervisor_name": "Jane Smith",
  "salary_type": "MONTHLY"
}
```

#### 2.4 Get Identity Documents
**Endpoint:** `GET /api/employee-profile/identity-docs/`

**Response:**
```json
{
  "aadhaar_number": "1234 5678 9012",
  "pan_number": "ABCDE1234F",
  "esi_number": "1234567890",
  "pf_uan_number": "100123456789",
  "passport_number": "A12345678"
}
```

#### 2.5 Get Bank Information
**Endpoint:** `GET /api/employee-profile/bank-info/`

**Response:**
```json
{
  "bank_name": "State Bank of India",
  "account_number": "1234567890123456",
  "ifsc_code": "SBIN0001234",
  "branch_name": "Main Branch"
}
```

#### 2.6 Get Complete Profile
**Endpoint:** `GET /api/employee-profile/complete/`

**Response:**
```json
{
  "personal_information": {
    "full_name": "John Doe",
    "employee_code": "EMP001",
    "date_of_birth": "1990-05-15",
    "gender": "Male",
    "marital_status": "Married",
    "photo": "http://example.com/media/employee_photos/john.jpg"
  },
  "contact_information": {
    "mobile_number": "9876543210",
    "email": "john.doe@example.com",
    "current_address": "123 Main St, City, State, 12345",
    "permanent_address": "456 Home St, Town, State, 67890"
  },
  "official_information": {
    "date_of_joining": "2020-01-15",
    "department": "IT Department",
    "designation": "Senior Developer",
    "location": "Bangalore Office",
    "supervisor_name": "Jane Smith",
    "salary_type": "MONTHLY"
  },
  "identity_documents": {
    "aadhaar_number": "1234 5678 9012",
    "pan_number": "ABCDE1234F",
    "esi_number": "1234567890",
    "pf_uan_number": "100123456789"
  },
  "bank_information": {
    "bank_name": "State Bank of India",
    "account_number": "1234567890123456",
    "ifsc_code": "SBIN0001234",
    "branch_name": "Main Branch"
  }
}
```

#### 2.7 Request Profile Update
**Endpoint:** `POST /api/employee-profile/request-update/`

**Request Body:**
```json
{
  "field_name": "mobile_number",
  "requested_value": "9999999999",
  "reason": "Changed mobile number"
}
```

**Response:**
```json
{
  "message": "Update request submitted successfully",
  "request": {
    "id": 1,
    "employee": 1,
    "employee_name": "John Doe",
    "employee_code": "EMP001",
    "field_name": "mobile_number",
    "current_value": "9876543210",
    "requested_value": "9999999999",
    "reason": "Changed mobile number",
    "status": "PENDING",
    "requested_at": "2025-01-07T10:00:00Z",
    "reviewed_by": null,
    "reviewed_by_name": null,
    "reviewed_at": null,
    "remarks": ""
  }
}
```

#### 2.8 Get Profile Update Requests
**Endpoint:** `GET /api/employee-profile/update-requests/`

**Response:**
```json
[
  {
    "id": 1,
    "employee": 1,
    "employee_name": "John Doe",
    "employee_code": "EMP001",
    "field_name": "mobile_number",
    "current_value": "9876543210",
    "requested_value": "9999999999",
    "reason": "Changed mobile number",
    "status": "PENDING",
    "requested_at": "2025-01-07T10:00:00Z",
    "reviewed_by": null,
    "reviewed_by_name": null,
    "reviewed_at": null,
    "remarks": ""
  }
]
```

---

### 3. Documents APIs

#### 3.1 List All Documents
**Endpoint:** `GET /api/employee-documents/list/`

**Response:**
```json
[
  {
    "id": 1,
    "doc_type": "APPOINTMENT",
    "doc_type_display": "Appointment Order",
    "file": "/media/employee_documents/appointment_order.pdf",
    "file_url": "http://example.com/media/employee_documents/appointment_order.pdf",
    "issued_date": "2020-01-15"
  },
  {
    "id": 2,
    "doc_type": "ID_CARD",
    "doc_type_display": "ID Card",
    "file": "/media/employee_documents/id_card.pdf",
    "file_url": "http://example.com/media/employee_documents/id_card.pdf",
    "issued_date": "2020-01-20"
  }
]
```

#### 3.2 Get Appointment Order
**Endpoint:** `GET /api/employee-documents/appointment-order/`

**Response:**
```json
{
  "id": 1,
  "doc_type": "APPOINTMENT",
  "doc_type_display": "Appointment Order",
  "file": "/media/employee_documents/appointment_order.pdf",
  "file_url": "http://example.com/media/employee_documents/appointment_order.pdf",
  "issued_date": "2020-01-15"
}
```

#### 3.3 Get ESI Card
**Endpoint:** `GET /api/employee-documents/esi-card/`

#### 3.4 Get ID Card
**Endpoint:** `GET /api/employee-documents/id-card/`

#### 3.5 Get Relieving Letter
**Endpoint:** `GET /api/employee-documents/relieving-letter/`

#### 3.6 Download Document
**Endpoint:** `GET /api/employee-documents/{document_id}/download/`

**Response:** Binary file download

---

### 4. Salary APIs

#### 4.1 Get Salary Structure
**Endpoint:** `GET /api/employee-salary/structure/`

**Response:**
```json
{
  "earnings": {
    "basic": 25000.00,
    "da": 5000.00,
    "hra": 10000.00,
    "conveyance": 2000.00,
    "bonus": 3000.00,
    "other_allowances": 5000.00
  },
  "deductions": {
    "pf": 3000.00,
    "esi": 750.00,
    "pt": 200.00,
    "lwf": 50.00,
    "insurance": 500.00,
    "advance": 0.00
  },
  "net_salary": 45500.00,
  "ctc": 600000.00
}
```

#### 4.2 Get Payslip History
**Endpoint:** `GET /api/employee-salary/payslips/`

**Query Parameters:**
- `year` (optional) - Filter by year
- `month` (optional) - Filter by month

**Response:**
```json
[
  {
    "id": 1,
    "month": 12,
    "year": 2024,
    "month_name": "December",
    "gross_salary": 50000.00,
    "deductions": 4500.00,
    "net_salary": 45500.00,
    "pdf_url": "http://example.com/media/payslips/payslip_12_2024.pdf"
  },
  {
    "id": 2,
    "month": 11,
    "year": 2024,
    "month_name": "November",
    "gross_salary": 50000.00,
    "deductions": 4500.00,
    "net_salary": 45500.00,
    "pdf_url": "http://example.com/media/payslips/payslip_11_2024.pdf"
  }
]
```

#### 4.3 Download Payslip
**Endpoint:** `GET /api/employee-salary/{payslip_id}/download/`

**Response:** Binary PDF file download

#### 4.4 Get Increment History
**Endpoint:** `GET /api/employee-salary/increments/`

**Response:**
```json
[
  {
    "id": 1,
    "effective_date": "2024-01-01",
    "old_salary": 500000.00,
    "new_salary": 600000.00,
    "increment_amount": 100000.00,
    "increment_percentage": 20.00
  },
  {
    "id": 2,
    "effective_date": "2023-01-01",
    "old_salary": 400000.00,
    "new_salary": 500000.00,
    "increment_amount": 100000.00,
    "increment_percentage": 25.00
  }
]
```

---

### 5. Attendance APIs

#### 5.1 Get Attendance Calendar
**Endpoint:** `GET /api/employee-attendance/calendar/`

**Query Parameters:**
- `year` (optional, default: current year)
- `month` (optional, default: current month)

**Response:**
```json
{
  "year": 2025,
  "month": 1,
  "month_name": "January",
  "attendance": [
    {
      "date": "2025-01-01",
      "day": "Wednesday",
      "status": "H",
      "status_display": "Holiday"
    },
    {
      "date": "2025-01-02",
      "day": "Thursday",
      "status": "P",
      "status_display": "Present"
    },
    {
      "date": "2025-01-03",
      "day": "Friday",
      "status": "P",
      "status_display": "Present"
    },
    {
      "date": "2025-01-04",
      "day": "Saturday",
      "status": "WO",
      "status_display": "Weekly Off"
    },
    {
      "date": "2025-01-05",
      "day": "Sunday",
      "status": "WO",
      "status_display": "Weekly Off"
    }
  ]
}
```

**Status Codes:**
- `P` - Present
- `A` - Absent
- `WO` - Weekly Off
- `H` - Holiday
- `HD` - Half Day

#### 5.2 Get Attendance Summary
**Endpoint:** `GET /api/employee-attendance/summary/`

**Query Parameters:**
- `year` (optional, default: current year)
- `month` (optional, default: current month)

**Response:**
```json
{
  "year": 2025,
  "month": 1,
  "month_name": "January",
  "total_working_days": 22,
  "days_present": 20,
  "days_absent": 2,
  "weekly_offs": 4,
  "holidays": 2,
  "half_days": 1,
  "overtime_hours": 10.5
}
```

#### 5.3 Get Overtime Details
**Endpoint:** `GET /api/employee-attendance/overtime/`

**Query Parameters:**
- `year` (optional, default: current year)
- `month` (optional, default: current month)

**Response:**
```json
{
  "year": 2025,
  "month": 1,
  "month_name": "January",
  "overtime_records": [
    {
      "date": "2025-01-15",
      "hours": 3.5
    },
    {
      "date": "2025-01-20",
      "hours": 4.0
    },
    {
      "date": "2025-01-25",
      "hours": 3.0
    }
  ],
  "total_hours": 10.5
}
```

---

### 6. Reports APIs

#### 6.1 List All Reports
**Endpoint:** `GET /api/employee-reports/list/`

**Response:**
```json
[
  {
    "id": 1,
    "report_type": "SALARY_STATEMENT",
    "report_type_display": "Salary Statement",
    "file": "/media/employee_reports/salary_statement_2024.pdf",
    "file_url": "http://example.com/media/employee_reports/salary_statement_2024.pdf",
    "generated_on": "2025-01-01"
  },
  {
    "id": 2,
    "report_type": "DEDUCTION_STATEMENT",
    "report_type_display": "Deduction Statement",
    "file": "/media/employee_reports/deduction_statement_2024.pdf",
    "file_url": "http://example.com/media/employee_reports/deduction_statement_2024.pdf",
    "generated_on": "2025-01-01"
  }
]
```

#### 6.2 Get Salary Statement
**Endpoint:** `GET /api/employee-reports/salary-statement/`

**Query Parameters:**
- `period` (optional) - yearly or quarterly
- `year` (optional)

**Response:**
```json
{
  "id": 1,
  "report_type": "SALARY_STATEMENT",
  "report_type_display": "Salary Statement",
  "file": "/media/employee_reports/salary_statement_2024.pdf",
  "file_url": "http://example.com/media/employee_reports/salary_statement_2024.pdf",
  "generated_on": "2025-01-01"
}
```

#### 6.3 Get Deduction Statement
**Endpoint:** `GET /api/employee-reports/deduction-statement/`

**Response:**
```json
{
  "id": 2,
  "report_type": "DEDUCTION_STATEMENT",
  "report_type_display": "Deduction Statement",
  "file": "/media/employee_reports/deduction_statement_2024.pdf",
  "file_url": "http://example.com/media/employee_reports/deduction_statement_2024.pdf",
  "generated_on": "2025-01-01"
}
```

#### 6.4 Download Report
**Endpoint:** `GET /api/employee-reports/{report_id}/download/`

**Response:** Binary file download

---

## Error Responses

All APIs return standard error responses:

```json
{
  "error": "Error message description"
}
```

**Common HTTP Status Codes:**
- `200 OK` - Request successful
- `201 Created` - Resource created successfully
- `400 Bad Request` - Invalid request data
- `401 Unauthorized` - Authentication required
- `403 Forbidden` - Insufficient permissions
- `404 Not Found` - Resource not found
- `500 Internal Server Error` - Server error

---

## Usage Examples

### Python Example (using requests library)

```python
import requests

# Login to get JWT token
login_url = "http://example.com/api/auth/login/"
login_data = {
    "username": "john.doe",
    "password": "password123"
}
response = requests.post(login_url, json=login_data)
token = response.json()['access']

# Get dashboard stats
headers = {"Authorization": f"Bearer {token}"}
stats_url = "http://example.com/api/employee-dashboard/stats/"
response = requests.get(stats_url, headers=headers)
print(response.json())

# Get payslip history
payslips_url = "http://example.com/api/employee-salary/payslips/?year=2024"
response = requests.get(payslips_url, headers=headers)
print(response.json())

# Download payslip
payslip_id = 1
download_url = f"http://example.com/api/employee-salary/{payslip_id}/download/"
response = requests.get(download_url, headers=headers)
with open(f"payslip_{payslip_id}.pdf", "wb") as f:
    f.write(response.content)
```

### JavaScript Example (using fetch)

```javascript
// Login to get JWT token
const loginUrl = "http://example.com/api/auth/login/";
const loginData = {
  username: "john.doe",
  password: "password123"
};

fetch(loginUrl, {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify(loginData)
})
.then(response => response.json())
.then(data => {
  const token = data.access;
  
  // Get dashboard stats
  const statsUrl = "http://example.com/api/employee-dashboard/stats/";
  return fetch(statsUrl, {
    headers: {'Authorization': `Bearer ${token}`}
  });
})
.then(response => response.json())
.then(stats => console.log(stats))
.catch(error => console.error('Error:', error));
```

---

## Notes

1. All date fields are in `YYYY-MM-DD` format
2. All datetime fields are in ISO 8601 format with timezone
3. Decimal fields have 2 decimal places
4. File URLs are absolute URLs when `request` context is available
5. Employees can only access their own data
6. Profile update requests require HR approval
7. Some fields are read-only and cannot be updated directly

---

## Support

For issues or questions, please contact the system administrator.
