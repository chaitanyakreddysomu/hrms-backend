# HR Dashboard APIs - Complete List

## Overview
Comprehensive HR management system with 17 powerful endpoints for dashboard statistics, attendance management, salary management, payslip generation, overtime tracking, and advanced analytics.

**Base URL:** `http://localhost:8000/api/hr-dashboard/`

**Authentication:** JWT Bearer Token required for all endpoints

**Access Control:** Admin, Manager, Sub-Manager, HR, Supervisor

---

## API Endpoints Summary

### 📊 Dashboard Statistics (1 Endpoint)

| # | Method | Endpoint | Description | Params |
|---|--------|----------|-------------|--------|
| 1 | GET | `/dashboard-stats/` | Get comprehensive dashboard statistics | company_id, month, year |

**Returns:** Employee stats, attendance stats, salary stats, payslip stats, recent activities, overtime stats

---

### 👥 Attendance Management (3 Endpoints)

| # | Method | Endpoint | Description | Required Fields |
|---|--------|----------|-------------|-----------------|
| 2 | POST | `/mark-attendance/` | Mark attendance for single employee | employee_id, date, status |
| 3 | POST | `/bulk-mark-attendance/` | Mark attendance for multiple employees | date, attendance_records[] |
| 4 | GET | `/attendance-report/` | Get detailed attendance report | start_date, end_date |

**Status Values:** P (Present), A (Absent), WO (Weekly Off), H (Holiday), HD (Half Day)

---

### 💰 Salary Management (3 Endpoints)

| # | Method | Endpoint | Description | Key Features |
|---|--------|----------|-------------|--------------|
| 5 | POST | `/create-salary-structure/` | Create salary structure for employee | CTC, Basic, DA, HRA, Allowances, Deductions |
| 6 | PUT | `/update-salary-structure/` | Update salary structure | Auto-records increment in history |
| 7 | GET | `/get-salary-structure/` | Get employee salary details | Returns complete salary breakdown |

**Salary Components:**
- **Earnings:** Basic, DA, HRA, Conveyance, Bonus, Other Allowances
- **Deductions:** PF, ESI, PT, LWF, Insurance, Advance

---

### 📄 Payslip Management (2 Endpoints)

| # | Method | Endpoint | Description | Features |
|---|--------|----------|-------------|----------|
| 8 | POST | `/generate-payslip/` | Generate PDF payslip | Pro-rated salary calculation, PDF auto-generation |
| 9 | GET | `/get-payslips/` | Get payslips with filters | Filter by employee, month, year, company |

**Payslip Features:**
- Automatic pro-rated salary calculation based on attendance
- PDF generation with detailed breakdown
- Stores in `media/payslips/` directory
- Filename format: `payslip_EMP001_10_2024.pdf`

---

### ⏰ Overtime Management (2 Endpoints)

| # | Method | Endpoint | Description | Data |
|---|--------|----------|-------------|------|
| 10 | POST | `/record-overtime/` | Record overtime hours | employee_id, date, hours (decimal) |
| 11 | GET | `/overtime-report/` | Get overtime report | start_date, end_date, filters |

**Overtime Tracking:**
- Record hours in decimal format (e.g., 3.5 for 3 hours 30 minutes)
- Generate reports by employee or company
- Total hours aggregation
- Records count per employee

---

### 🔄 Employee Status Management (1 Endpoint)

| # | Method | Endpoint | Description | Status Values |
|---|--------|----------|-------------|---------------|
| 12 | PUT | `/update-employee-status/` | Update employee work status | ACTIVE, LEFT, TERMINATED |

**Use Cases:**
- Mark employee as resigned (LEFT)
- Terminate employee (TERMINATED)
- Reactivate employee (ACTIVE)

---

### 📊 Analytics & Reports (1 Endpoint)

| # | Method | Endpoint | Description | Analytics Provided |
|---|--------|----------|-------------|--------------------|
| 13 | GET | `/analytics/` | Get comprehensive HR analytics | Headcount, Salary, Attendance Trends, Turnover |

**Analytics Categories:**
1. **Headcount Analysis**
   - Total active employees
   - By role distribution
   - By gender distribution

2. **Salary Analysis**
   - Min/Max/Average CTC
   - Total annual payroll
   - Salary distribution

3. **Attendance Trends**
   - Last 12 months data
   - Present vs Absent trends
   - Monthly patterns

4. **Turnover Analysis**
   - New joinings count
   - Leavings count
   - Turnover rate percentage

---

## Quick Reference

### All 17 Endpoints at a Glance

```
Dashboard:
  GET  /api/hr-dashboard/dashboard-stats/

Attendance:
  POST /api/hr-dashboard/mark-attendance/
  POST /api/hr-dashboard/bulk-mark-attendance/
  GET  /api/hr-dashboard/attendance-report/

Salary:
  POST /api/hr-dashboard/create-salary-structure/
  PUT  /api/hr-dashboard/update-salary-structure/
  GET  /api/hr-dashboard/get-salary-structure/

Payslip:
  POST /api/hr-dashboard/generate-payslip/
  GET  /api/hr-dashboard/get-payslips/

Overtime:
  POST /api/hr-dashboard/record-overtime/
  GET  /api/hr-dashboard/overtime-report/

Employee Status:
  PUT  /api/hr-dashboard/update-employee-status/

Analytics:
  GET  /api/hr-dashboard/analytics/
```

---

## Request Methods Distribution

- **GET Requests:** 5 endpoints (Dashboard stats, Reports, Analytics)
- **POST Requests:** 5 endpoints (Create, Mark, Record operations)
- **PUT Requests:** 2 endpoints (Update operations)

---

## Common Query Parameters

### Filtering Parameters
- `employee_id` - Filter by specific employee
- `company_id` - Filter by company/sub-company
- `month` - Month number (1-12)
- `year` - Year (e.g., 2024)
- `start_date` - Start date (YYYY-MM-DD)
- `end_date` - End date (YYYY-MM-DD)

### Pagination (where applicable)
- `page` - Page number
- `page_size` - Items per page

---

## Response Format

All APIs return consistent response format:

**Success Response:**
```json
{
  "success": true,
  "message": "Operation completed successfully",
  "data": { ... }
}
```

**Error Response:**
```json
{
  "success": false,
  "error": "Error message description"
}
```

---

## Authentication Example

All requests must include JWT token in Authorization header:

```bash
# cURL Example
curl -X GET "http://localhost:8000/api/hr-dashboard/dashboard-stats/" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"

# Python Example
headers = {'Authorization': f'Bearer {jwt_token}'}
response = requests.get(url, headers=headers)

# JavaScript Example
fetch(url, {
  headers: { 'Authorization': `Bearer ${jwtToken}` }
})
```

---

## Key Features

### 🎯 Automated Calculations
- Pro-rated salary based on attendance
- Net salary after deductions
- Overtime hours aggregation
- Attendance percentages

### 📊 Real-time Analytics
- Live dashboard statistics
- Attendance trends (12 months)
- Salary distribution analysis
- Turnover rate calculation

### 📄 Document Generation
- Automatic PDF payslip generation
- Structured file naming convention
- Secure file storage

### 🔄 Bulk Operations
- Bulk attendance marking
- Multi-employee reports
- Company-wide analytics

### 📈 History Tracking
- Increment history on salary changes
- Attendance history
- Status change tracking

---

## Important Notes

1. **Date Format:** Always use `YYYY-MM-DD` format
2. **Decimal Hours:** Use decimal format (3.5 = 3 hours 30 minutes)
3. **Annual Figures:** All salary amounts are annual
4. **Pro-rated Calculations:** Payslips calculate based on actual attendance
5. **PDF Storage:** Payslips stored in `media/payslips/`
6. **Auto-increment:** Salary changes automatically recorded in history
7. **Company Filtering:** Use company_id for multi-company environments
8. **Bulk Processing:** Use bulk APIs for better performance

---

## Use Cases by Role

### Admin / Manager
- Full access to all 17 endpoints
- Dashboard overview for decision making
- Salary structure management
- Employee status updates
- Comprehensive analytics

### HR
- Attendance management (mark, bulk, reports)
- Salary structure creation/updates
- Payslip generation
- Document management
- Employee data management

### Supervisor
- Attendance marking for team
- View attendance reports
- View overtime reports
- Limited to supervised employees

---

## Integration Examples

### Python Integration
```python
import requests

class HRDashboardAPI:
    def __init__(self, base_url, token):
        self.base_url = base_url
        self.headers = {'Authorization': f'Bearer {token}'}
    
    def get_dashboard_stats(self, company_id=None):
        params = {'company_id': company_id} if company_id else {}
        response = requests.get(
            f'{self.base_url}/dashboard-stats/',
            headers=self.headers,
            params=params
        )
        return response.json()
    
    def mark_attendance(self, employee_id, date, status):
        data = {
            'employee_id': employee_id,
            'date': date,
            'status': status
        }
        response = requests.post(
            f'{self.base_url}/mark-attendance/',
            headers=self.headers,
            json=data
        )
        return response.json()

# Usage
api = HRDashboardAPI('http://localhost:8000/api/hr-dashboard', 'your_token')
stats = api.get_dashboard_stats(company_id=5)
print(stats)
```

### JavaScript Integration
```javascript
class HRDashboardAPI {
  constructor(baseUrl, token) {
    this.baseUrl = baseUrl;
    this.headers = {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    };
  }

  async getDashboardStats(companyId = null) {
    const params = companyId ? `?company_id=${companyId}` : '';
    const response = await fetch(
      `${this.baseUrl}/dashboard-stats/${params}`,
      { headers: this.headers }
    );
    return await response.json();
  }

  async markAttendance(employeeId, date, status) {
    const response = await fetch(
      `${this.baseUrl}/mark-attendance/`,
      {
        method: 'POST',
        headers: this.headers,
        body: JSON.stringify({
          employee_id: employeeId,
          date: date,
          status: status
        })
      }
    );
    return await response.json();
  }
}

// Usage
const api = new HRDashboardAPI('http://localhost:8000/api/hr-dashboard', 'your_token');
const stats = await api.getDashboardStats(5);
console.log(stats);
```

---

## Testing Checklist

- [ ] Dashboard stats load correctly with filters
- [ ] Single attendance marking works
- [ ] Bulk attendance marking processes multiple records
- [ ] Attendance reports generate with date range
- [ ] Salary structure creation with all components
- [ ] Salary structure updates record increment history
- [ ] Payslip generation creates PDF file
- [ ] Payslips list with filters
- [ ] Overtime recording accepts decimal hours
- [ ] Overtime reports aggregate correctly
- [ ] Employee status updates successfully
- [ ] Analytics return comprehensive data
- [ ] Authentication works with JWT token
- [ ] Permission checks enforce role-based access
- [ ] Error handling returns proper messages

---

## Performance Optimization Tips

1. **Use Bulk APIs:** For multiple records, use bulk endpoints instead of multiple single requests
2. **Filter Early:** Apply company_id and date filters to reduce data volume
3. **Pagination:** Implement pagination for large datasets
4. **Caching:** Consider caching dashboard stats for frequently accessed data
5. **Date Ranges:** Keep date ranges reasonable (max 1 year for reports)
6. **Async Processing:** Use background tasks for heavy operations like payslip generation

---

## Error Handling

Common error codes and messages:

| Code | Message | Cause |
|------|---------|-------|
| 400 | Bad Request | Missing required fields |
| 401 | Unauthorized | Invalid/expired JWT token |
| 403 | Forbidden | Insufficient permissions |
| 404 | Not Found | Employee/resource not found |
| 500 | Internal Server Error | Server-side error |

---

## Support & Documentation

- **HTML Documentation:** `hr_dashboard_apis.html`
- **Related APIs:** 
  - Employee Data Management APIs
  - Employee Dashboard APIs
  - Document Management APIs

---

**Version:** 1.0  
**Last Updated:** October 7, 2024  
**Total Endpoints:** 17  
**Authentication:** JWT Bearer Token  
**Access Roles:** Admin, Manager, Sub-Manager, HR, Supervisor
