# Salary Structure API Documentation

## Base URL
`http://127.0.0.1:8000/api/salary-structures/`

## Authentication
All endpoints require authentication using JWT token:
```
Authorization: Bearer <your_token>
```

---

## Endpoints

### 1. List All Salary Structures
**GET** `/api/salary-structures/`

Get a list of all salary structures.

**Query Parameters:**
- `client_id` (optional) - Filter by company/client ID
- `employee_id` (optional) - Filter by employee ID

**Example Request:**
```bash
GET /api/salary-structures/
GET /api/salary-structures/?client_id=1
GET /api/salary-structures/?employee_id=5
```

**Response:**
```json
[
    {
        "id": 1,
        "employee": 1,
        "CTC": "500000.00",
        "basic": "200000.00",
        "da": "50000.00",
        "hra": "100000.00",
        "conveyance": "20000.00",
        "bonus": "30000.00",
        "other_allowances": "10000.00",
        "pf_deduction": "24000.00",
        "esi_deduction": "0.00",
        "pt_deduction": "2400.00",
        "lwf_deduction": "100.00",
        "insurance": "5000.00",
        "advance": "0.00"
    }
]
```

---

### 2. Get Salary Structure by ID
**GET** `/api/salary-structures/{id}/`

Get details of a specific salary structure.

**Example Request:**
```bash
GET /api/salary-structures/1/
```

**Response:**
```json
{
    "id": 1,
    "employee": 1,
    "CTC": "500000.00",
    "basic": "200000.00",
    "da": "50000.00",
    "hra": "100000.00",
    "conveyance": "20000.00",
    "bonus": "30000.00",
    "other_allowances": "10000.00",
    "pf_deduction": "24000.00",
    "esi_deduction": "0.00",
    "pt_deduction": "2400.00",
    "lwf_deduction": "100.00",
    "insurance": "5000.00",
    "advance": "0.00"
}
```

---

### 3. Get Salary Structure by Employee
**GET** `/api/salary-structures/by_employee/?employee_id={employee_id}`

Get salary structure for a specific employee.

**Query Parameters:**
- `employee_id` (required) - Employee ID

**Example Request:**
```bash
GET /api/salary-structures/by_employee/?employee_id=5
```

**Response:**
```json
{
    "id": 5,
    "employee": 5,
    "CTC": "600000.00",
    "basic": "250000.00",
    "da": "60000.00",
    "hra": "120000.00",
    "conveyance": "25000.00",
    "bonus": "35000.00",
    "other_allowances": "15000.00",
    "pf_deduction": "30000.00",
    "esi_deduction": "0.00",
    "pt_deduction": "2400.00",
    "lwf_deduction": "100.00",
    "insurance": "6000.00",
    "advance": "0.00"
}
```

**Error Response:**
```json
{
    "error": "Salary structure not found for this employee"
}
```

---

### 4. Create Salary Structure
**POST** `/api/salary-structures/`

Create a new salary structure for an employee.

**Request Body:**
```json
{
    "employee": 10,
    "CTC": "500000.00",
    "basic": "200000.00",
    "da": "50000.00",
    "hra": "100000.00",
    "conveyance": "20000.00",
    "bonus": "30000.00",
    "other_allowances": "10000.00",
    "pf_deduction": "24000.00",
    "esi_deduction": "0.00",
    "pt_deduction": "2400.00",
    "lwf_deduction": "100.00",
    "insurance": "5000.00",
    "advance": "0.00"
}
```

**Success Response:**
```json
{
    "id": 10,
    "employee": 10,
    "CTC": "500000.00",
    "basic": "200000.00",
    "da": "50000.00",
    "hra": "100000.00",
    "conveyance": "20000.00",
    "bonus": "30000.00",
    "other_allowances": "10000.00",
    "pf_deduction": "24000.00",
    "esi_deduction": "0.00",
    "pt_deduction": "2400.00",
    "lwf_deduction": "100.00",
    "insurance": "5000.00",
    "advance": "0.00"
}
```

**Error Responses:**
```json
{
    "error": "Employee not found"
}
```
```json
{
    "error": "Salary structure already exists for this employee",
    "message": "Use PUT/PATCH to update existing salary structure"
}
```

---

### 5. Update Salary Structure (Full Update)
**PUT** `/api/salary-structures/{id}/`

Update an existing salary structure (all fields required).

**Request Body:**
```json
{
    "employee": 1,
    "CTC": "550000.00",
    "basic": "220000.00",
    "da": "55000.00",
    "hra": "110000.00",
    "conveyance": "22000.00",
    "bonus": "33000.00",
    "other_allowances": "11000.00",
    "pf_deduction": "26400.00",
    "esi_deduction": "0.00",
    "pt_deduction": "2400.00",
    "lwf_deduction": "100.00",
    "insurance": "5500.00",
    "advance": "0.00"
}
```

**Response:**
```json
{
    "id": 1,
    "employee": 1,
    "CTC": "550000.00",
    "basic": "220000.00",
    "da": "55000.00",
    "hra": "110000.00",
    "conveyance": "22000.00",
    "bonus": "33000.00",
    "other_allowances": "11000.00",
    "pf_deduction": "26400.00",
    "esi_deduction": "0.00",
    "pt_deduction": "2400.00",
    "lwf_deduction": "100.00",
    "insurance": "5500.00",
    "advance": "0.00"
}
```

---

### 6. Partial Update Salary Structure
**PATCH** `/api/salary-structures/{id}/`

Update specific fields of a salary structure.

**Request Body (only include fields to update):**
```json
{
    "basic": "230000.00",
    "da": "60000.00",
    "hra": "115000.00"
}
```

**Response:**
```json
{
    "id": 1,
    "employee": 1,
    "CTC": "550000.00",
    "basic": "230000.00",
    "da": "60000.00",
    "hra": "115000.00",
    "conveyance": "22000.00",
    "bonus": "33000.00",
    "other_allowances": "11000.00",
    "pf_deduction": "26400.00",
    "esi_deduction": "0.00",
    "pt_deduction": "2400.00",
    "lwf_deduction": "100.00",
    "insurance": "5500.00",
    "advance": "0.00"
}
```

---

### 7. Delete Salary Structure
**DELETE** `/api/salary-structures/{id}/`

Delete a salary structure.

**Example Request:**
```bash
DELETE /api/salary-structures/1/
```

**Response:**
```
Status: 204 No Content
```

---

## Field Descriptions

| Field | Type | Description |
|-------|------|-------------|
| `id` | Integer | Auto-generated ID |
| `employee` | Integer | Employee ID (Foreign Key) |
| `CTC` | Decimal | Cost to Company (Annual) |
| `basic` | Decimal | Basic Salary (Annual) |
| `da` | Decimal | Dearness Allowance (Annual) |
| `hra` | Decimal | House Rent Allowance (Annual) |
| `conveyance` | Decimal | Conveyance Allowance (Annual) |
| `bonus` | Decimal | Annual Bonus |
| `other_allowances` | Decimal | Other Allowances (Annual) |
| `pf_deduction` | Decimal | Provident Fund Deduction (Annual) |
| `esi_deduction` | Decimal | ESI Deduction (Annual) |
| `pt_deduction` | Decimal | Professional Tax Deduction (Annual) |
| `lwf_deduction` | Decimal | Labour Welfare Fund Deduction (Annual) |
| `insurance` | Decimal | Insurance Deduction (Annual) |
| `advance` | Decimal | Advance Deduction (Annual) |

---

## Complete Usage Example (Python)

```python
import requests

# Base URL
BASE_URL = "http://127.0.0.1:8000/api"

# Login and get token (example)
login_response = requests.post(f"{BASE_URL}/auth/login/", json={
    "username": "admin",
    "password": "password123"
})
token = login_response.json()['access']

# Set headers
headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
}

# 1. Create salary structure
new_salary = {
    "employee": 10,
    "CTC": "500000.00",
    "basic": "200000.00",
    "da": "50000.00",
    "hra": "100000.00",
    "conveyance": "20000.00",
    "bonus": "30000.00",
    "other_allowances": "10000.00",
    "pf_deduction": "24000.00",
    "esi_deduction": "0.00",
    "pt_deduction": "2400.00",
    "lwf_deduction": "100.00",
    "insurance": "5000.00",
    "advance": "0.00"
}

response = requests.post(
    f"{BASE_URL}/salary-structures/",
    json=new_salary,
    headers=headers
)
print("Created:", response.json())

# 2. Get salary structure by employee
response = requests.get(
    f"{BASE_URL}/salary-structures/by_employee/?employee_id=10",
    headers=headers
)
print("By Employee:", response.json())

# 3. Update salary structure (partial)
update_data = {
    "basic": "220000.00",
    "hra": "110000.00"
}
response = requests.patch(
    f"{BASE_URL}/salary-structures/1/",
    json=update_data,
    headers=headers
)
print("Updated:", response.json())

# 4. List all salary structures for a client
response = requests.get(
    f"{BASE_URL}/salary-structures/?client_id=1",
    headers=headers
)
print("List:", response.json())
```

---

## Notes

1. **One-to-One Relationship**: Each employee can have only ONE salary structure
2. **Annual Values**: All salary components are annual values
3. **Decimals**: Use decimal values with 2 decimal places (e.g., "50000.00")
4. **Employee Must Exist**: The employee ID must exist before creating a salary structure
5. **Update vs Create**: Use PUT/PATCH to update existing structures, not POST
6. **Net Salary Calculation**: The model has a `net_salary` property that automatically calculates: 
   - Net Salary = (basic + da + hra + conveyance + bonus + other_allowances) - (pf_deduction + esi_deduction + pt_deduction + lwf_deduction + insurance + advance)

---

## Error Codes

| Status Code | Description |
|-------------|-------------|
| 200 | Success |
| 201 | Created successfully |
| 204 | Deleted successfully |
| 400 | Bad request (validation error) |
| 401 | Unauthorized (missing/invalid token) |
| 403 | Forbidden (no permission) |
| 404 | Not found |
| 500 | Server error |
