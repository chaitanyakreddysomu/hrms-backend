# HR/Admin Employee Data Management API Documentation

## Overview
These APIs allow HR, Admin, Manager, Sub-Manager, and Supervisor roles to add and update employee official information, identity documents, and bank details.

---

## Authentication
All endpoints require JWT token authentication.

**Header Required:**
```
Authorization: Bearer <your_jwt_token>
```

---

## Role-Based Access Control

### Role Permissions

| Role | Access Scope |
|------|--------------|
| **Admin** | Can manage all employees across all companies |
| **Manager** | Can manage employees in their main company and all sub-companies |
| **Sub-Manager** | Can manage employees only in their sub-company |
| **HR** | Can manage employees in their company (main or sub) |
| **Supervisor** | Can manage employees in their company (main or sub) |

---

## API Endpoints

### 1. Add Official Details

**Endpoint:** `POST /api/employee-data-management/add-official-details/`

**Description:** Add official details for an employee (DOJ, department, designation, etc.)

**Allowed Roles:** Admin, Manager, Sub-Manager, HR, Supervisor

**Request Body:**
```json
{
  "employee_id": 1,
  "date_of_joining": "2024-01-15",
  "department": "IT Department",
  "designation": "Senior Developer",
  "location": "Bangalore Office",
  "supervisor_name": "Jane Smith",
  "salary_type": "MONTHLY"
}
```

**Salary Type Options:**
- `MONTHLY` - Monthly salary
- `DAILY` - Daily wage

**Success Response (201 Created):**
```json
{
  "message": "Official details added successfully",
  "data": {
    "id": 1,
    "employee": 1,
    "date_of_joining": "2024-01-15",
    "department": "IT Department",
    "designation": "Senior Developer",
    "location": "Bangalore Office",
    "supervisor_name": "Jane Smith",
    "salary_type": "MONTHLY"
  }
}
```

**Error Responses:**
- `400 Bad Request` - Missing employee_id or validation error
- `403 Forbidden` - User doesn't have permission to manage this employee
- `404 Not Found` - Employee not found

---

### 2. Update Official Details

**Endpoint:** `PUT /api/employee-data-management/update-official-details/`

**Description:** Update existing official details for an employee

**Allowed Roles:** Admin, Manager, Sub-Manager, HR, Supervisor

**Request Body:**
```json
{
  "employee_id": 1,
  "department": "Software Development",
  "designation": "Lead Developer",
  "location": "Mumbai Office"
}
```

**Note:** You can send partial updates (only the fields you want to change)

**Success Response (200 OK):**
```json
{
  "message": "Official details updated successfully",
  "data": {
    "id": 1,
    "employee": 1,
    "date_of_joining": "2024-01-15",
    "department": "Software Development",
    "designation": "Lead Developer",
    "location": "Mumbai Office",
    "supervisor_name": "Jane Smith",
    "salary_type": "MONTHLY"
  }
}
```

---

### 3. Add Identity Documents

**Endpoint:** `POST /api/employee-data-management/add-identity-documents/`

**Description:** Add identity documents for an employee (Aadhaar, PAN, ESI, PF, etc.)

**Allowed Roles:** Admin, Manager, Sub-Manager, HR, Supervisor

**Request Body:**
```json
{
  "employee_id": 1,
  "aadhaar_number": "1234 5678 9012",
  "pan_number": "ABCDE1234F",
  "esi_number": "1234567890",
  "pf_uan_number": "100123456789",
  "passport_number": "A12345678"
}
```

**Field Notes:**
- `aadhaar_number` - 12 digits (can include spaces)
- `pan_number` - 10 characters alphanumeric
- `esi_number` - Optional, 10-17 digits
- `pf_uan_number` - 12 digits
- `passport_number` - Optional

**Success Response (201 Created):**
```json
{
  "message": "Identity documents added successfully",
  "data": {
    "id": 1,
    "employee": 1,
    "aadhaar_number": "1234 5678 9012",
    "pan_number": "ABCDE1234F",
    "esi_number": "1234567890",
    "pf_uan_number": "100123456789",
    "passport_number": "A12345678"
  }
}
```

---

### 4. Update Identity Documents

**Endpoint:** `PUT /api/employee-data-management/update-identity-documents/`

**Description:** Update existing identity documents for an employee

**Allowed Roles:** Admin, Manager, Sub-Manager, HR, Supervisor

**Request Body:**
```json
{
  "employee_id": 1,
  "aadhaar_number": "9876 5432 1098",
  "pan_number": "ZYXWV9876E"
}
```

**Success Response (200 OK):**
```json
{
  "message": "Identity documents updated successfully",
  "data": {
    "id": 1,
    "employee": 1,
    "aadhaar_number": "9876 5432 1098",
    "pan_number": "ZYXWV9876E",
    "esi_number": "1234567890",
    "pf_uan_number": "100123456789",
    "passport_number": "A12345678"
  }
}
```

---

### 5. Add Bank Details

**Endpoint:** `POST /api/employee-data-management/add-bank-details/`

**Description:** Add bank account details for an employee

**Allowed Roles:** Admin, Manager, Sub-Manager, HR, Supervisor

**Request Body:**
```json
{
  "employee_id": 1,
  "bank_name": "State Bank of India",
  "account_number": "1234567890123456",
  "ifsc_code": "SBIN0001234",
  "branch_name": "Main Branch, Bangalore"
}
```

**Field Notes:**
- `bank_name` - Full name of the bank
- `account_number` - Bank account number (usually 9-18 digits)
- `ifsc_code` - 11 character IFSC code (format: XXXX0YYYYYY)
- `branch_name` - Bank branch name and location

**Success Response (201 Created):**
```json
{
  "message": "Bank details added successfully",
  "data": {
    "id": 1,
    "employee": 1,
    "bank_name": "State Bank of India",
    "account_number": "1234567890123456",
    "ifsc_code": "SBIN0001234",
    "branch_name": "Main Branch, Bangalore"
  }
}
```

---

### 6. Update Bank Details

**Endpoint:** `PUT /api/employee-data-management/update-bank-details/`

**Description:** Update existing bank account details for an employee

**Allowed Roles:** Admin, Manager, Sub-Manager, HR, Supervisor

**Request Body:**
```json
{
  "employee_id": 1,
  "account_number": "9876543210987654",
  "ifsc_code": "SBIN0005678"
}
```

**Success Response (200 OK):**
```json
{
  "message": "Bank details updated successfully",
  "data": {
    "id": 1,
    "employee": 1,
    "bank_name": "State Bank of India",
    "account_number": "9876543210987654",
    "ifsc_code": "SBIN0005678",
    "branch_name": "Main Branch, Bangalore"
  }
}
```

---

### 7. Get Employee Details

**Endpoint:** `GET /api/employee-data-management/get-employee-details/?employee_id=1`

**Description:** Get complete employee details including official info, identity docs, and bank details

**Allowed Roles:** Admin, Manager, Sub-Manager, HR, Supervisor

**Query Parameters:**
- `employee_id` (required) - ID of the employee

**Success Response (200 OK):**
```json
{
  "employee": {
    "id": 1,
    "full_name": "John Doe",
    "employee_code": "EMP001",
    "date_of_birth": "1990-05-15",
    "gender": "M",
    "marital_status": "M",
    "mobile_number": "9876543210",
    "email": "john.doe@example.com",
    "current_address": "123 Main St, City",
    "permanent_address": "456 Home St, Town",
    "role": "Employee",
    "status": "ACTIVE",
    "photo": "/media/employee_photos/john.jpg"
  },
  "official_details": {
    "id": 1,
    "employee": 1,
    "date_of_joining": "2024-01-15",
    "department": "IT Department",
    "designation": "Senior Developer",
    "location": "Bangalore Office",
    "supervisor_name": "Jane Smith",
    "salary_type": "MONTHLY"
  },
  "identity_documents": {
    "id": 1,
    "employee": 1,
    "aadhaar_number": "1234 5678 9012",
    "pan_number": "ABCDE1234F",
    "esi_number": "1234567890",
    "pf_uan_number": "100123456789",
    "passport_number": "A12345678"
  },
  "bank_details": {
    "id": 1,
    "employee": 1,
    "bank_name": "State Bank of India",
    "account_number": "1234567890123456",
    "ifsc_code": "SBIN0001234",
    "branch_name": "Main Branch, Bangalore"
  }
}
```

**Note:** If any section (official_details, identity_documents, bank_details) doesn't exist for the employee, it will return `null`.

---

### 8. List Employees

**Endpoint:** `GET /api/employee-data-management/list-employees/`

**Description:** List all employees based on role permissions

**Allowed Roles:** Admin, Manager, Sub-Manager, HR, Supervisor

**Query Parameters (all optional):**
- `company_id` - Filter by company (main_company or sub_company)
- `role` - Filter by employee role (Admin, Manager, HR, Supervisor, Employee)
- `status` - Filter by status (ACTIVE, LEFT, TERMINATED)

**Example Requests:**
```
GET /api/employee-data-management/list-employees/
GET /api/employee-data-management/list-employees/?role=Employee
GET /api/employee-data-management/list-employees/?status=ACTIVE
GET /api/employee-data-management/list-employees/?company_id=5&role=HR
```

**Success Response (200 OK):**
```json
{
  "count": 25,
  "employees": [
    {
      "id": 1,
      "full_name": "John Doe",
      "employee_code": "EMP001",
      "date_of_birth": "1990-05-15",
      "gender": "M",
      "marital_status": "M",
      "mobile_number": "9876543210",
      "email": "john.doe@example.com",
      "role": "Employee",
      "status": "ACTIVE"
    },
    {
      "id": 2,
      "full_name": "Jane Smith",
      "employee_code": "EMP002",
      "date_of_birth": "1992-08-20",
      "gender": "F",
      "marital_status": "S",
      "mobile_number": "9876543211",
      "email": "jane.smith@example.com",
      "role": "HR",
      "status": "ACTIVE"
    }
  ]
}
```

---

## Common Error Responses

### 400 Bad Request
```json
{
  "error": "employee_id is required"
}
```

```json
{
  "error": "Official details already exist for this employee. Use update API instead."
}
```

```json
{
  "error": {
    "pan_number": ["This field is required."],
    "ifsc_code": ["This field must be exactly 11 characters."]
  }
}
```

### 403 Forbidden
```json
{
  "error": "You can only manage employees in your sub-company"
}
```

```json
{
  "error": "You can only manage employees in your company"
}
```

### 404 Not Found
```json
{
  "error": "Employee not found"
}
```

```json
{
  "error": "Requester employee profile not found"
}
```

### 500 Internal Server Error
```json
{
  "error": "Detailed error message"
}
```

---

## Usage Examples

### Python Example (using requests)

```python
import requests

# Login to get JWT token
login_url = "http://localhost:8000/api/auth/login/"
login_data = {"username": "hr_user", "password": "password123"}
response = requests.post(login_url, json=login_data)
token = response.json()['access']

headers = {"Authorization": f"Bearer {token}"}

# Add official details
official_data = {
    "employee_id": 1,
    "date_of_joining": "2024-01-15",
    "department": "IT Department",
    "designation": "Senior Developer",
    "location": "Bangalore Office",
    "supervisor_name": "Jane Smith",
    "salary_type": "MONTHLY"
}

response = requests.post(
    "http://localhost:8000/api/employee-data-management/add-official-details/",
    json=official_data,
    headers=headers
)
print(response.json())

# Add identity documents
identity_data = {
    "employee_id": 1,
    "aadhaar_number": "1234 5678 9012",
    "pan_number": "ABCDE1234F",
    "esi_number": "1234567890",
    "pf_uan_number": "100123456789"
}

response = requests.post(
    "http://localhost:8000/api/employee-data-management/add-identity-documents/",
    json=identity_data,
    headers=headers
)
print(response.json())

# Add bank details
bank_data = {
    "employee_id": 1,
    "bank_name": "State Bank of India",
    "account_number": "1234567890123456",
    "ifsc_code": "SBIN0001234",
    "branch_name": "Main Branch"
}

response = requests.post(
    "http://localhost:8000/api/employee-data-management/add-bank-details/",
    json=bank_data,
    headers=headers
)
print(response.json())

# Get complete employee details
response = requests.get(
    "http://localhost:8000/api/employee-data-management/get-employee-details/?employee_id=1",
    headers=headers
)
print(response.json())

# List all active employees
response = requests.get(
    "http://localhost:8000/api/employee-data-management/list-employees/?status=ACTIVE",
    headers=headers
)
print(response.json())
```

### JavaScript Example (using fetch)

```javascript
const API_BASE = 'http://localhost:8000/api';
const token = localStorage.getItem('jwt_token');

const headers = {
  'Authorization': `Bearer ${token}`,
  'Content-Type': 'application/json'
};

// Add official details
const addOfficialDetails = async (employeeId) => {
  const data = {
    employee_id: employeeId,
    date_of_joining: "2024-01-15",
    department: "IT Department",
    designation: "Senior Developer",
    location: "Bangalore Office",
    supervisor_name: "Jane Smith",
    salary_type: "MONTHLY"
  };

  const response = await fetch(
    `${API_BASE}/employee-data-management/add-official-details/`,
    {
      method: 'POST',
      headers: headers,
      body: JSON.stringify(data)
    }
  );

  const result = await response.json();
  console.log(result);
};

// Update identity documents
const updateIdentityDocs = async (employeeId) => {
  const data = {
    employee_id: employeeId,
    aadhaar_number: "9876 5432 1098",
    pan_number: "ZYXWV9876E"
  };

  const response = await fetch(
    `${API_BASE}/employee-data-management/update-identity-documents/`,
    {
      method: 'PUT',
      headers: headers,
      body: JSON.stringify(data)
    }
  );

  const result = await response.json();
  console.log(result);
};

// Get employee details
const getEmployeeDetails = async (employeeId) => {
  const response = await fetch(
    `${API_BASE}/employee-data-management/get-employee-details/?employee_id=${employeeId}`,
    { headers: headers }
  );

  const result = await response.json();
  console.log(result);
};

// List employees
const listEmployees = async (filters = {}) => {
  const params = new URLSearchParams(filters);
  const response = await fetch(
    `${API_BASE}/employee-data-management/list-employees/?${params}`,
    { headers: headers }
  );

  const result = await response.json();
  console.log(result);
};
```

---

## Workflow Example

### Complete Employee Onboarding Process

1. **Create Employee Record** (use existing employee creation API)
2. **Add Official Details** (this API)
3. **Add Identity Documents** (this API)
4. **Add Bank Details** (this API)
5. **Verify Complete Profile** (get-employee-details API)

```python
# Step 1: Employee already created
employee_id = 1

# Step 2: Add official details
add_official_details(employee_id, {
    "date_of_joining": "2024-01-15",
    "department": "IT",
    "designation": "Developer",
    "location": "Office",
    "supervisor_name": "Manager",
    "salary_type": "MONTHLY"
})

# Step 3: Add identity documents
add_identity_documents(employee_id, {
    "aadhaar_number": "1234 5678 9012",
    "pan_number": "ABCDE1234F",
    "pf_uan_number": "100123456789"
})

# Step 4: Add bank details
add_bank_details(employee_id, {
    "bank_name": "SBI",
    "account_number": "1234567890",
    "ifsc_code": "SBIN0001234",
    "branch_name": "Main Branch"
})

# Step 5: Verify
employee_details = get_employee_details(employee_id)
print(employee_details)
```

---

## Best Practices

1. **Always validate data** before sending to API
2. **Use partial updates** when updating (only send changed fields)
3. **Handle errors gracefully** - Check role permissions before attempting operations
4. **Secure sensitive data** - Identity documents and bank details should be encrypted in transit
5. **Audit logging** - Track who added/updated employee data and when
6. **Validate ID numbers** - Ensure Aadhaar (12 digits), PAN (10 chars), IFSC (11 chars) formats

---

## Security Notes

- All endpoints require authentication
- Role-based access control is enforced
- Sub-Managers can only manage their sub-company employees
- HR and Supervisors can only manage employees in their company
- Managers can manage all employees in their main company and sub-companies
- Admins have full access to all employees

---

## Support

For issues or questions, contact the system administrator.
