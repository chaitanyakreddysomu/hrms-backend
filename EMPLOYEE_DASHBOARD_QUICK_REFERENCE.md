# Employee Dashboard API - Quick Reference

## Base URL
```
http://your-domain.com/api
```

## Authentication
All endpoints require JWT token in header:
```
Authorization: Bearer YOUR_JWT_TOKEN
```

---

## 📊 Dashboard Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/employee-dashboard/stats/` | GET | Dashboard statistics (present days, absent days, OT hours, salary) |
| `/employee-dashboard/notifications/` | GET | Recent notifications (supports `?limit=10&unread_only=true`) |
| `/employee-dashboard/{id}/mark-read/` | POST | Mark notification as read |
| `/employee-dashboard/mark-all-read/` | POST | Mark all notifications as read |

---

## 👤 Profile Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/employee-profile/personal-info/` | GET | Name, employee code, DOB, gender, marital status |
| `/employee-profile/contact-info/` | GET | Mobile, email, addresses |
| `/employee-profile/official-info/` | GET | DOJ, department, designation, location, supervisor |
| `/employee-profile/identity-docs/` | GET | Aadhaar, PAN, ESI, PF UAN |
| `/employee-profile/bank-info/` | GET | Bank details |
| `/employee-profile/complete/` | GET | Complete profile in one call |
| `/employee-profile/request-update/` | POST | Request profile field update (needs HR approval) |
| `/employee-profile/update-requests/` | GET | View all update requests |

**Update Request Body:**
```json
{
  "field_name": "mobile_number",
  "requested_value": "9999999999",
  "reason": "Changed mobile number"
}
```

---

## 📄 Documents Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/employee-documents/list/` | GET | All documents |
| `/employee-documents/appointment-order/` | GET | Appointment order |
| `/employee-documents/esi-card/` | GET | ESI card |
| `/employee-documents/id-card/` | GET | ID card |
| `/employee-documents/relieving-letter/` | GET | Relieving letter |
| `/employee-documents/{id}/download/` | GET | Download document PDF |

---

## 💰 Salary Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/employee-salary/structure/` | GET | Salary components (earnings & deductions) |
| `/employee-salary/payslips/` | GET | Payslip history (supports `?year=2024&month=12`) |
| `/employee-salary/{id}/download/` | GET | Download payslip PDF |
| `/employee-salary/increments/` | GET | Increment history |

---

## 📅 Attendance Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/employee-attendance/calendar/` | GET | Monthly calendar (supports `?year=2024&month=12`) |
| `/employee-attendance/summary/` | GET | Attendance summary (supports `?year=2024&month=12`) |
| `/employee-attendance/overtime/` | GET | Overtime details (supports `?year=2024&month=12`) |

**Attendance Status Codes:**
- `P` = Present
- `A` = Absent
- `WO` = Weekly Off
- `H` = Holiday
- `HD` = Half Day

---

## 📊 Reports Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/employee-reports/list/` | GET | All generated reports |
| `/employee-reports/salary-statement/` | GET | Salary statement |
| `/employee-reports/deduction-statement/` | GET | Deduction statement (PF/ESI/PT/LWF) |
| `/employee-reports/{id}/download/` | GET | Download report PDF |

---

## Response Examples

### Dashboard Stats
```json
{
  "employee_name": "John Doe",
  "employee_code": "EMP001",
  "present_days": 20,
  "absent_days": 2,
  "ot_hours": 10.5,
  "take_home_salary": 45000.00
}
```

### Notifications
```json
{
  "notifications": [
    {
      "id": 1,
      "notification_type": "PAYSLIP",
      "title": "Payslip Uploaded",
      "message": "Your payslip for December 2024 has been uploaded",
      "is_read": false,
      "created_at": "2025-01-05T10:30:00Z"
    }
  ],
  "unread_count": 5
}
```

### Salary Structure
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
  "net_salary": 45500.00
}
```

### Attendance Calendar
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
    }
  ]
}
```

---

## Error Response
```json
{
  "error": "Error message description"
}
```

---

## HTTP Status Codes

| Code | Description |
|------|-------------|
| 200 | Success |
| 201 | Created |
| 400 | Bad Request |
| 401 | Unauthorized (no token) |
| 403 | Forbidden (not your data) |
| 404 | Not Found |
| 500 | Server Error |

---

## Quick Test Commands

### Get Dashboard Stats
```bash
curl -H "Authorization: Bearer TOKEN" \
  http://localhost:8000/api/employee-dashboard/stats/
```

### Get Notifications
```bash
curl -H "Authorization: Bearer TOKEN" \
  "http://localhost:8000/api/employee-dashboard/notifications/?limit=5"
```

### Get Complete Profile
```bash
curl -H "Authorization: Bearer TOKEN" \
  http://localhost:8000/api/employee-profile/complete/
```

### Get Payslips for 2024
```bash
curl -H "Authorization: Bearer TOKEN" \
  "http://localhost:8000/api/employee-salary/payslips/?year=2024"
```

### Get Attendance for January 2025
```bash
curl -H "Authorization: Bearer TOKEN" \
  "http://localhost:8000/api/employee-attendance/calendar/?year=2025&month=1"
```

### Download Payslip
```bash
curl -H "Authorization: Bearer TOKEN" \
  -o payslip.pdf \
  http://localhost:8000/api/employee-salary/1/download/
```

### Request Profile Update
```bash
curl -X POST \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"field_name":"mobile_number","requested_value":"9999999999","reason":"Changed"}' \
  http://localhost:8000/api/employee-profile/request-update/
```

---

## Frontend Integration Snippet

```javascript
const API_BASE = 'http://localhost:8000/api';
const token = localStorage.getItem('jwt_token');

const headers = {
  'Authorization': `Bearer ${token}`,
  'Content-Type': 'application/json'
};

// Get dashboard stats
fetch(`${API_BASE}/employee-dashboard/stats/`, { headers })
  .then(res => res.json())
  .then(data => console.log(data));

// Get notifications
fetch(`${API_BASE}/employee-dashboard/notifications/?limit=10`, { headers })
  .then(res => res.json())
  .then(data => console.log(data));

// Download payslip
fetch(`${API_BASE}/employee-salary/${payslipId}/download/`, { headers })
  .then(res => res.blob())
  .then(blob => {
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'payslip.pdf';
    a.click();
  });
```

---

## Need Help?

See full documentation:
- **EMPLOYEE_DASHBOARD_API.md** - Complete API documentation
- **EMPLOYEE_DASHBOARD_IMPLEMENTATION.md** - Implementation details
