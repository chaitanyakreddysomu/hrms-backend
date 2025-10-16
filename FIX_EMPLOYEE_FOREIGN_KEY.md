# Fix Applied: Employee Foreign Key Issue

## Problem
When calling the `add-bank-details` API, the following error occurred:
```
{
    "error": "null value in column \"employee_id\" of relation \"BankDetails\" violates not-null constraint\nDETAIL:  Failing row contains (1, State Bank of India, 1234567890123456, SBIN0001234, Main Branch, Bangalore, null).\n"
}
```

## Root Cause
The issue was in how we were passing the employee relationship to the serializers. The models use `OneToOneField` for the employee relationship:

```python
class BankDetails(models.Model):
    employee = models.OneToOneField(Employee, on_delete=models.CASCADE)
    bank_name = models.CharField(max_length=100)
    # ... other fields
```

And the serializer had `employee` as a read-only field:
```python
class BankDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = BankDetails
        fields = '__all__'
        read_only_fields = ['id', 'employee']
```

The code was trying to pass `employee_id` in the data dictionary:
```python
data['employee'] = employee.id  # ❌ Wrong - trying to pass ID
serializer.save()
```

This doesn't work because:
1. The serializer has `employee` as read-only, so it ignores it in the data
2. We need to pass the actual Employee instance, not the ID

## Solution Applied
Changed all add/update methods to pass the employee object directly to `serializer.save()`:

### Before (❌ Wrong):
```python
data = request.data.copy()
data['employee'] = employee.id

serializer = BankDetailsSerializer(data=data)

if serializer.is_valid():
    bank_details = serializer.save()  # employee_id ends up null!
```

### After (✅ Correct):
```python
data = request.data.copy()
data.pop('employee_id', None)  # Remove from data since it's read-only

serializer = BankDetailsSerializer(data=data)

if serializer.is_valid():
    bank_details = serializer.save(employee=employee)  # Pass as kwarg!
```

## Files Fixed
Updated the following methods in `core/hr_admin_views.py`:

1. ✅ **add_official_details** - Pass `employee=employee` to `serializer.save()`
2. ✅ **add_identity_documents** - Pass `employee=employee` to `serializer.save()`
3. ✅ **add_bank_details** - Pass `employee=employee` to `serializer.save()`

Note: Update methods (`update_official_details`, `update_identity_documents`, `update_bank_details`) don't need this change because they fetch existing records that already have the employee relationship set.

## Testing
Now you can successfully call the API:

```bash
POST http://127.0.0.1:8000/api/employee-data-management/add-bank-details/

{
    "employee_id": 19,
    "bank_name": "State Bank of India",
    "account_number": "1234567890123456",
    "ifsc_code": "SBIN0001234",
    "branch_name": "Main Branch, Bangalore"
}
```

**Expected Response:**
```json
{
    "message": "Bank details added successfully",
    "data": {
        "id": 1,
        "employee": 19,
        "bank_name": "State Bank of India",
        "account_number": "1234567890123456",
        "ifsc_code": "SBIN0001234",
        "branch_name": "Main Branch, Bangalore"
    }
}
```

## Server Status
✅ Server running successfully at http://127.0.0.1:8000/  
✅ System check: No issues (0 silenced)  
✅ All APIs ready for testing  

## Next Steps
Test all three add APIs:
1. `/api/employee-data-management/add-official-details/`
2. `/api/employee-data-management/add-identity-documents/`
3. `/api/employee-data-management/add-bank-details/`

All should now work correctly! 🚀
