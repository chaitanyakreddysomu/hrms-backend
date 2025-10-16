# Employee Document Management APIs

## Overview
Complete document management system with two sets of APIs:
1. **Employee APIs** - For viewing and downloading documents (read-only)
2. **HR/Admin/Manager/Supervisor APIs** - For uploading, updating, and deleting documents (full CRUD)

---

## 📂 Employee Document APIs (Read-Only)

### Base URL: `/api/employee-documents/`

These APIs allow employees to view and download their own documents uploaded by HR/Admin/Manager/Supervisor.

### 1. List All Documents
**GET** `/api/employee-documents/list/`

Get list of all documents for the authenticated employee.

**Authentication:** Required (Employee)

**Response:**
```json
[
  {
    "id": 1,
    "doc_type": "APPOINTMENT",
    "doc_type_display": "Appointment Order",
    "file": "employee_documents/appointment_emp1.pdf",
    "file_url": "http://localhost:8000/media/employee_documents/appointment_emp1.pdf",
    "issued_date": "2024-01-15"
  },
  {
    "id": 2,
    "doc_type": "ESI_CARD",
    "doc_type_display": "ESI Card",
    "file": "employee_documents/esi_card_emp1.pdf",
    "file_url": "http://localhost:8000/media/employee_documents/esi_card_emp1.pdf",
    "issued_date": "2024-02-01"
  }
]
```

---

### 2. Get Appointment Order
**GET** `/api/employee-documents/appointment-order/`

Get appointment order document details for the authenticated employee.

**Authentication:** Required (Employee)

**Response:**
```json
{
  "id": 1,
  "doc_type": "APPOINTMENT",
  "doc_type_display": "Appointment Order",
  "file": "employee_documents/appointment_emp1.pdf",
  "file_url": "http://localhost:8000/media/employee_documents/appointment_emp1.pdf",
  "issued_date": "2024-01-15"
}
```

**Error Response (404):**
```json
{
  "error": "Appointment order not found"
}
```

---

### 3. Get ESI Card
**GET** `/api/employee-documents/esi-card/`

Get ESI card document (if applicable) for the authenticated employee.

**Authentication:** Required (Employee)

**Response:**
```json
{
  "id": 2,
  "doc_type": "ESI_CARD",
  "doc_type_display": "ESI Card",
  "file": "employee_documents/esi_card_emp1.pdf",
  "file_url": "http://localhost:8000/media/employee_documents/esi_card_emp1.pdf",
  "issued_date": "2024-02-01"
}
```

---

### 4. Get ID Card
**GET** `/api/employee-documents/id-card/`

Get ID card document for download/print for the authenticated employee.

**Authentication:** Required (Employee)

**Response:**
```json
{
  "id": 3,
  "doc_type": "ID_CARD",
  "doc_type_display": "ID Card",
  "file": "employee_documents/id_card_emp1.pdf",
  "file_url": "http://localhost:8000/media/employee_documents/id_card_emp1.pdf",
  "issued_date": "2024-01-20"
}
```

---

### 5. Get Relieving Letter
**GET** `/api/employee-documents/relieving-letter/`

Get relieving letter (for resigned/terminated employees).

**Authentication:** Required (Employee)

**Response:**
```json
{
  "id": 4,
  "doc_type": "RELIEVING",
  "doc_type_display": "Relieving Letter",
  "file": "employee_documents/relieving_emp1.pdf",
  "file_url": "http://localhost:8000/media/employee_documents/relieving_emp1.pdf",
  "issued_date": "2024-12-31"
}
```

---

### 6. Download Document
**GET** `/api/employee-documents/{document_id}/download/`

Download any document by its ID as PDF/file.

**Authentication:** Required (Employee - must own the document)

**Path Parameters:**
- `document_id` - ID of the document to download

**Response:** File download (PDF/Image)

**Error Response (403):**
```json
{
  "error": "Unauthorized"
}
```

---

## 🔧 HR/Admin/Manager/Supervisor Document Management APIs

### Base URL: `/api/employee-document-management/`

These APIs allow HR, Admin, Manager, Sub-Manager, and Supervisor roles to upload, update, and delete employee documents.

### Permission Matrix

| Role | Can Manage |
|------|------------|
| **Admin** | All employees across all companies |
| **Manager** | Employees in their main company + all sub-companies |
| **Sub-Manager** | Only employees in their specific sub-company |
| **HR** | Employees in their company (main or sub) |
| **Supervisor** | Employees in their company (main or sub) |

---

### 1. Upload Document
**POST** `/api/employee-document-management/upload-document/`

Upload a document for an employee.

**Authentication:** Required (Admin, Manager, Sub-Manager, HR, Supervisor)

**Request (Form Data):**
```
employee_id: 19
doc_type: APPOINTMENT
file: [Binary file data]
issued_date: 2024-01-15
```

**Document Types:**
- `APPOINTMENT` - Appointment Order
- `ESI_CARD` - ESI Card
- `ID_CARD` - ID Card
- `RELIEVING` - Relieving Letter

**Response (201 Created):**
```json
{
  "message": "Document uploaded successfully",
  "data": {
    "id": 1,
    "doc_type": "APPOINTMENT",
    "doc_type_display": "Appointment Order",
    "file": "employee_documents/appointment_emp19.pdf",
    "file_url": "http://localhost:8000/media/employee_documents/appointment_emp19.pdf",
    "issued_date": "2024-01-15"
  }
}
```

**Error Responses:**

**400 Bad Request** - Missing required fields:
```json
{
  "error": "employee_id, doc_type, file, and issued_date are required"
}
```

**400 Bad Request** - Invalid doc_type:
```json
{
  "error": "doc_type must be one of ['APPOINTMENT', 'ESI_CARD', 'ID_CARD', 'RELIEVING']"
}
```

**403 Forbidden** - Permission denied:
```json
{
  "error": "You can only manage employees in your sub-company"
}
```

---

### 2. Update Document
**PUT** `/api/employee-document-management/update-document/`

Update an existing document (replace file or update issued date).

**Authentication:** Required (Admin, Manager, Sub-Manager, HR, Supervisor)

**Request (Form Data):**
```
document_id: 1
file: [Binary file data] (optional)
issued_date: 2024-01-20 (optional)
```

**Response (200 OK):**
```json
{
  "message": "Document updated successfully",
  "data": {
    "id": 1,
    "doc_type": "APPOINTMENT",
    "doc_type_display": "Appointment Order",
    "file": "employee_documents/appointment_emp19_new.pdf",
    "file_url": "http://localhost:8000/media/employee_documents/appointment_emp19_new.pdf",
    "issued_date": "2024-01-20"
  }
}
```

---

### 3. Delete Document
**DELETE** `/api/employee-document-management/delete-document/?document_id=1`

Delete a document.

**Authentication:** Required (Admin, Manager, Sub-Manager, HR, Supervisor)

**Query Parameters:**
- `document_id` - ID of the document to delete

**Response (200 OK):**
```json
{
  "message": "Appointment Order deleted successfully"
}
```

**Error Response (400):**
```json
{
  "error": "document_id is required"
}
```

---

### 4. List Employee Documents
**GET** `/api/employee-document-management/list-employee-documents/?employee_id=19&doc_type=APPOINTMENT`

List all documents for a specific employee.

**Authentication:** Required (Admin, Manager, Sub-Manager, HR, Supervisor)

**Query Parameters:**
- `employee_id` (required) - ID of the employee
- `doc_type` (optional) - Filter by document type

**Response (200 OK):**
```json
{
  "employee_id": 19,
  "employee_name": "John Doe",
  "count": 3,
  "documents": [
    {
      "id": 1,
      "doc_type": "APPOINTMENT",
      "doc_type_display": "Appointment Order",
      "file": "employee_documents/appointment_emp19.pdf",
      "file_url": "http://localhost:8000/media/employee_documents/appointment_emp19.pdf",
      "issued_date": "2024-01-15"
    },
    {
      "id": 2,
      "doc_type": "ESI_CARD",
      "doc_type_display": "ESI Card",
      "file": "employee_documents/esi_card_emp19.pdf",
      "file_url": "http://localhost:8000/media/employee_documents/esi_card_emp19.pdf",
      "issued_date": "2024-02-01"
    },
    {
      "id": 3,
      "doc_type": "ID_CARD",
      "doc_type_display": "ID Card",
      "file": "employee_documents/id_card_emp19.pdf",
      "file_url": "http://localhost:8000/media/employee_documents/id_card_emp19.pdf",
      "issued_date": "2024-01-20"
    }
  ]
}
```

---

## 🔄 Complete Workflow Example

### Scenario: HR uploads appointment order for new employee

**Step 1: HR uploads appointment order**
```bash
curl -X POST http://localhost:8000/api/employee-document-management/upload-document/ \
  -H "Authorization: Bearer <hr_jwt_token>" \
  -F "employee_id=19" \
  -F "doc_type=APPOINTMENT" \
  -F "file=@appointment_order.pdf" \
  -F "issued_date=2024-01-15"
```

**Step 2: Employee views their documents**
```bash
curl -X GET http://localhost:8000/api/employee-documents/list/ \
  -H "Authorization: Bearer <employee_jwt_token>"
```

**Step 3: Employee downloads appointment order**
```bash
curl -X GET http://localhost:8000/api/employee-documents/1/download/ \
  -H "Authorization: Bearer <employee_jwt_token>" \
  --output appointment_order.pdf
```

---

## 🐍 Python Examples

### Employee Side - View Documents
```python
import requests

API_BASE = 'http://localhost:8000/api'
employee_token = 'your_employee_jwt_token'
headers = {'Authorization': f'Bearer {employee_token}'}

# List all documents
response = requests.get(f'{API_BASE}/employee-documents/list/', headers=headers)
documents = response.json()
print(f"Total documents: {len(documents)}")

# Get appointment order
response = requests.get(f'{API_BASE}/employee-documents/appointment-order/', headers=headers)
appointment = response.json()
print(f"Appointment Order URL: {appointment['file_url']}")

# Download document
document_id = 1
response = requests.get(
    f'{API_BASE}/employee-documents/{document_id}/download/',
    headers=headers,
    stream=True
)
with open('appointment_order.pdf', 'wb') as f:
    f.write(response.content)
print("Document downloaded successfully")
```

### HR Side - Upload Documents
```python
import requests

API_BASE = 'http://localhost:8000/api'
hr_token = 'your_hr_jwt_token'
headers = {'Authorization': f'Bearer {hr_token}'}

# Upload appointment order
with open('appointment_order.pdf', 'rb') as file:
    files = {'file': file}
    data = {
        'employee_id': 19,
        'doc_type': 'APPOINTMENT',
        'issued_date': '2024-01-15'
    }
    response = requests.post(
        f'{API_BASE}/employee-document-management/upload-document/',
        headers=headers,
        files=files,
        data=data
    )
    result = response.json()
    print(result['message'])
    print(f"Document ID: {result['data']['id']}")

# List employee documents
response = requests.get(
    f'{API_BASE}/employee-document-management/list-employee-documents/',
    headers=headers,
    params={'employee_id': 19}
)
docs = response.json()
print(f"Employee {docs['employee_name']} has {docs['count']} documents")

# Update document
with open('new_appointment_order.pdf', 'rb') as file:
    files = {'file': file}
    data = {
        'document_id': 1,
        'issued_date': '2024-01-20'
    }
    response = requests.put(
        f'{API_BASE}/employee-document-management/update-document/',
        headers=headers,
        files=files,
        data=data
    )
    print(response.json()['message'])

# Delete document
response = requests.delete(
    f'{API_BASE}/employee-document-management/delete-document/',
    headers=headers,
    params={'document_id': 1}
)
print(response.json()['message'])
```

---

## 📱 JavaScript/React Examples

### Employee Side - View Documents
```javascript
const API_BASE = 'http://localhost:8000/api';
const employeeToken = localStorage.getItem('employee_jwt_token');

const headers = {
  'Authorization': `Bearer ${employeeToken}`
};

// List all documents
const listDocuments = async () => {
  const response = await fetch(`${API_BASE}/employee-documents/list/`, {
    headers
  });
  const documents = await response.json();
  console.log(`Total documents: ${documents.length}`);
  return documents;
};

// Get appointment order
const getAppointmentOrder = async () => {
  const response = await fetch(
    `${API_BASE}/employee-documents/appointment-order/`,
    { headers }
  );
  const appointment = await response.json();
  return appointment;
};

// Download document
const downloadDocument = async (documentId) => {
  const response = await fetch(
    `${API_BASE}/employee-documents/${documentId}/download/`,
    { headers }
  );
  const blob = await response.blob();
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = 'document.pdf';
  a.click();
};
```

### HR Side - Upload Documents
```javascript
const API_BASE = 'http://localhost:8000/api';
const hrToken = localStorage.getItem('hr_jwt_token');

const headers = {
  'Authorization': `Bearer ${hrToken}`
};

// Upload document
const uploadDocument = async (employeeId, docType, file, issuedDate) => {
  const formData = new FormData();
  formData.append('employee_id', employeeId);
  formData.append('doc_type', docType);
  formData.append('file', file);
  formData.append('issued_date', issuedDate);

  const response = await fetch(
    `${API_BASE}/employee-document-management/upload-document/`,
    {
      method: 'POST',
      headers,
      body: formData
    }
  );
  const result = await response.json();
  console.log(result.message);
  return result.data;
};

// List employee documents
const listEmployeeDocuments = async (employeeId, docType = null) => {
  const params = new URLSearchParams({ employee_id: employeeId });
  if (docType) params.append('doc_type', docType);

  const response = await fetch(
    `${API_BASE}/employee-document-management/list-employee-documents/?${params}`,
    { headers }
  );
  const docs = await response.json();
  console.log(`${docs.employee_name} has ${docs.count} documents`);
  return docs;
};

// Update document
const updateDocument = async (documentId, file = null, issuedDate = null) => {
  const formData = new FormData();
  formData.append('document_id', documentId);
  if (file) formData.append('file', file);
  if (issuedDate) formData.append('issued_date', issuedDate);

  const response = await fetch(
    `${API_BASE}/employee-document-management/update-document/`,
    {
      method: 'PUT',
      headers,
      body: formData
    }
  );
  const result = await response.json();
  console.log(result.message);
  return result.data;
};

// Delete document
const deleteDocument = async (documentId) => {
  const response = await fetch(
    `${API_BASE}/employee-document-management/delete-document/?document_id=${documentId}`,
    {
      method: 'DELETE',
      headers
    }
  );
  const result = await response.json();
  console.log(result.message);
};
```

---

## 🎯 Best Practices

### 1. File Upload
- Accept PDF files for formal documents
- Accept images (JPEG, PNG) for cards
- Validate file size (max 5MB recommended)
- Sanitize filenames before upload
- Use unique filenames to avoid conflicts

### 2. Security
- Always verify employee ownership for downloads
- Implement role-based access control for uploads
- Log all document access and modifications
- Use HTTPS in production
- Encrypt sensitive documents at rest

### 3. User Experience
- Show upload progress for large files
- Provide preview before download
- Cache document lists for better performance
- Show document status (available, pending, expired)
- Send notifications when new documents are uploaded

### 4. Error Handling
- Handle file upload failures gracefully
- Validate file types on both client and server
- Show user-friendly error messages
- Implement retry mechanism for failed uploads
- Clean up incomplete uploads

---

## 🚀 Deployment Status

✅ Employee Document APIs implemented  
✅ HR/Admin Document Management APIs implemented  
✅ Role-based permissions configured  
✅ File upload handling in place  
✅ URL routes registered  
✅ Error handling implemented  
✅ Documentation complete  

**Server Status:** Ready for testing at `http://localhost:8000`

---

## 📊 API Summary

### Employee APIs (6 endpoints)
1. `GET /api/employee-documents/list/` - List all documents
2. `GET /api/employee-documents/appointment-order/` - Get appointment order
3. `GET /api/employee-documents/esi-card/` - Get ESI card
4. `GET /api/employee-documents/id-card/` - Get ID card
5. `GET /api/employee-documents/relieving-letter/` - Get relieving letter
6. `GET /api/employee-documents/{id}/download/` - Download document

### HR/Admin APIs (4 endpoints)
1. `POST /api/employee-document-management/upload-document/` - Upload document
2. `PUT /api/employee-document-management/update-document/` - Update document
3. `DELETE /api/employee-document-management/delete-document/` - Delete document
4. `GET /api/employee-document-management/list-employee-documents/` - List employee documents

**Total:** 10 comprehensive document management APIs! 🎉
