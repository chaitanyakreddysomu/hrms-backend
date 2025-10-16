# Manager Dashboard - Role-Based Access Control (RBAC)

## 🔒 Security Implementation

### Access Control Summary
The Manager Dashboard APIs are **strictly protected** and can ONLY be accessed by users with the **Manager role**.

## How It Works

### 1. Custom Permission Class: `IsManager`

```python
class IsManager(permissions.BasePermission):
    """
    Custom permission for Manager role
    """
    def has_permission(self, request, view):
        # Step 1: Check if user is authenticated
        if not request.user.is_authenticated:
            return False
        
        try:
            # Step 2: Get employee record
            employee = Employee.objects.get(
                Q(employee_code=request.user.username) | Q(email=request.user.email)
            )
            
            # Step 3: Verify role is 'Manager'
            return employee.role == 'Manager'
            
        except Employee.DoesNotExist:
            # Step 4: Deny if employee not found
            return False
```

### 2. Applied to ViewSet

```python
class ManagerDashboardViewSet(viewsets.ViewSet):
    """
    Access: Manager Role ONLY
    """
    permission_classes = [IsManager]  # ← Security enforced here
    
    # All endpoints inherit this permission
```

## 🚫 What Happens if Non-Manager Tries to Access?

### Request Flow:

```
┌─────────────────────────────────────────────────────────────┐
│  1. User sends request to Manager Dashboard API             │
│     GET /api/manager-dashboard/company-overview/            │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│  2. Django checks Authentication                             │
│     ✓ Is JWT token valid?                                   │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│  3. IsManager Permission Check                               │
│     ✓ Is user authenticated?                                │
│     ✓ Does employee record exist?                           │
│     ✓ Is employee.role == 'Manager'?                        │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
        ┌────────────┴───────────┐
        │                        │
        ▼                        ▼
┌───────────────┐      ┌─────────────────┐
│  ✅ ALLOWED   │      │  ❌ DENIED      │
│  Access API   │      │  403 Forbidden  │
└───────────────┘      └─────────────────┘
```

### Example Responses:

#### ❌ No Token / Invalid Token
```json
HTTP 401 Unauthorized
{
  "detail": "Authentication credentials were not provided."
}
```

#### ❌ User is Not a Manager (e.g., Employee, HR, Supervisor)
```json
HTTP 403 Forbidden
{
  "detail": "You do not have permission to perform this action."
}
```

#### ✅ User is Manager
```json
HTTP 200 OK
{
  "success": true,
  "data": { ... }
}
```

## 📋 Role Hierarchy in HRMS

```
┌─────────────────────────────────────────────────────────┐
│  ROLE HIERARCHY                                         │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  Admin            → Full system access                  │
│  ├─ Manager       → Main company management ✓          │
│  ├─ Sub-Manager   → Sub-company management             │
│  ├─ HR            → HR operations                      │
│  ├─ Supervisor    → Team supervision                   │
│  └─ Employee      → Personal dashboard only            │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

## 🎯 Who Can Access Manager Dashboard?

| Role | Can Access? | Reason |
|------|------------|---------|
| **Manager** | ✅ YES | Primary role - Main company management |
| Admin | ❌ NO | Has separate admin dashboard |
| Sub-Manager | ❌ NO | Has separate sub-manager dashboard |
| HR | ❌ NO | Has separate HR dashboard |
| Supervisor | ❌ NO | Has separate supervisor dashboard |
| Employee | ❌ NO | Has separate employee dashboard |

## 🔐 Security Features

### 1. **Authentication Required**
- Valid JWT token must be provided
- Token must not be expired
- Token must be associated with a valid user

### 2. **Role Verification**
- System checks employee record exists
- Verifies `role` field equals 'Manager'
- Case-sensitive role matching

### 3. **Data Isolation**
- Manager can only see their main company data
- Cannot access other companies' data
- Sub-companies under their main company only

### 4. **Request Validation**
- Every request is validated
- Permission checked before any data is accessed
- Automatic error responses for unauthorized access

## 🧪 Testing Access Control

### Test 1: Manager Access (Should Work ✅)
```bash
# Login as Manager
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "MGR001",
    "password": "manager_password"
  }'

# Get token from response
TOKEN="eyJ0eXAiOiJKV1QiLCJhbGc..."

# Access Manager Dashboard
curl -X GET http://localhost:8000/api/manager-dashboard/company-overview/ \
  -H "Authorization: Bearer $TOKEN"

# Expected: 200 OK with data
```

### Test 2: Employee Access (Should Fail ❌)
```bash
# Login as Employee
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "EMP001",
    "password": "employee_password"
  }'

# Get token from response
TOKEN="eyJ0eXAiOiJKV1QiLCJhbGc..."

# Try to access Manager Dashboard
curl -X GET http://localhost:8000/api/manager-dashboard/company-overview/ \
  -H "Authorization: Bearer $TOKEN"

# Expected: 403 Forbidden
```

### Test 3: No Authentication (Should Fail ❌)
```bash
# Try to access without token
curl -X GET http://localhost:8000/api/manager-dashboard/company-overview/

# Expected: 401 Unauthorized
```

## 🛡️ Additional Security Recommendations

### 1. **Token Expiration**
```python
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=1),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
}
```

### 2. **Rate Limiting**
```python
REST_FRAMEWORK = {
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/day',
        'user': '1000/day',
        'manager': '5000/day'
    }
}
```

### 3. **HTTPS Only**
```python
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
```

### 4. **Logging & Monitoring**
```python
# Log all manager dashboard access
import logging
logger = logging.getLogger(__name__)

logger.info(f"Manager {manager.employee_code} accessed company overview")
```

## 📝 Code Example: Adding Role Check to New Endpoint

```python
from rest_framework.decorators import action
from rest_framework.response import Response

class ManagerDashboardViewSet(viewsets.ViewSet):
    permission_classes = [IsManager]  # Applied to ALL actions
    
    @action(detail=False, methods=['get'], url_path='new-endpoint')
    def new_endpoint(self, request):
        """
        This endpoint is automatically protected by IsManager permission
        No additional permission checks needed!
        """
        manager = self._get_manager_employee(request)
        # Manager role is already verified at this point
        return Response({'success': True})
```

## 🎓 Key Takeaways

1. ✅ **All Manager Dashboard APIs require Manager role**
2. ✅ **Permission is enforced at ViewSet level**
3. ✅ **Automatic 403 Forbidden for non-managers**
4. ✅ **Role verification happens before any data access**
5. ✅ **Each endpoint inherits the permission automatically**
6. ✅ **No additional permission checks needed in individual endpoints**

## 🔍 Verifying Your Setup

Check your employee record has correct role:

```python
# In Django shell
python manage.py shell

from core.models import Employee
manager = Employee.objects.get(employee_code='MGR001')
print(f"Role: {manager.role}")  # Should print: Role: Manager
```

---

**Security Status**: 🔒 **PROTECTED**
- Only Manager role can access
- Authentication required
- Role verification on every request
- Data isolation enforced
