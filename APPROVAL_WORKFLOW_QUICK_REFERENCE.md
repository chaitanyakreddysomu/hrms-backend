# 🔄 Approval Workflow System - Quick Reference

## 🎯 Key Concept

**Smart Routing:** Approval requests go **only to the relevant company's manager**, not all managers.

---

## 📊 Workflow Summary

| Account Type | Creator | Approval Chain | Levels |
|-------------|---------|----------------|---------|
| **Employee** | HR, Manager, Sub-Manager | Sub-Manager → Main Manager | 2 |
| **HR** | Manager, Sub-Manager | Sub-Manager → Main Manager → Admin | 3 |
| **Supervisor** | Manager, Sub-Manager | Sub-Manager → Main Manager → Admin | 3 |
| **Sub-Company** | Manager (main) | Admin | 1 |

---

## 🔄 Employee Creation Flow

```
HR creates employee in Sub-Company 1
         ↓
Sub-Company 1 Manager (ONLY Sub-Co 1, not all managers)
         ↓ (approves)
Main Company Manager
         ↓ (approves)
Employee Created ✅
```

**If Sub-Manager Rejects:**
```
HR creates employee in Sub-Company 1
         ↓
Sub-Company 1 Manager
         ↓ (rejects)
STOPS HERE ❌
Main Manager NOT notified
Creator receives rejection notice
```

---

## 📋 API Quick Reference

### Create Requests

```bash
# Employee
POST /api/approval-workflow/create-employee-request/
Body: { employee_data, official_details_data, password }

# HR/Supervisor
POST /api/approval-workflow/create-hr-supervisor-request/
Body: { employee_data, official_details_data, password, account_type }

# Sub-Company
POST /api/approval-workflow/create-sub-company-request/
Body: { company_data }
```

### View & Approve

```bash
# Get my pending approvals
GET /api/approval-workflow/pending-approvals/

# Approve
POST /api/approval-workflow/{id}/approve/
Body: { comments }

# Reject
POST /api/approval-workflow/{id}/reject/
Body: { reason }
```

### Notifications

```bash
# Get notifications
GET /api/approval-workflow/notifications/?unread_only=true

# Get statistics
GET /api/approval-workflow/statistics/

# View history
GET /api/approval-workflow/{id}/history/
```

---

## 🎭 Who Sees What?

### Admin
- Sees: All workflows at **admin** stage
- Can approve: HR, Supervisor, Sub-Manager accounts

### Main Company Manager
- Sees: Workflows at **main_manager** stage for **their company only**
- Can approve: Employees (final), HR/Supervisor (middle stage)

### Sub-Company Manager
- Sees: Workflows at **sub_manager** stage for **their sub-company only**
- Can approve: Employees (first stage), HR/Supervisor (first stage)

### HR
- Can create: Employee approval requests
- Cannot approve anything

---

## ✅ Complete Example

### Scenario: HR creates employee in Sub-Company 1

```bash
# Step 1: HR creates request
POST /api/approval-workflow/create-employee-request/
{
  "employee_data": {
    "full_name": "John Doe",
    "employee_code": "EMP001",
    "email": "john@company.com",
    "role": "Employee",
    "sub_company_id": 1  // Sub-Company 1
  },
  "password": "temp123"
}
# Response: workflow_id = 100, stage = sub_manager

# Step 2: Sub-Company 1 Manager approves
POST /api/approval-workflow/100/approve/
# Response: stage = main_manager

# Step 3: Main Company Manager approves
POST /api/approval-workflow/100/approve/
# Response: status = approved, Employee created!
```

---

## 🚨 Key Rules

1. **Company-Specific Routing**
   - Sub-Company 1 requests → Sub-Company 1 Manager ONLY
   - Sub-Company 2 requests → Sub-Company 2 Manager ONLY

2. **Rejection Stops Workflow**
   - If Sub-Manager rejects → Main Manager NOT notified
   - Workflow permanently rejected
   - Must create new request to retry

3. **Expiration**
   - Pending requests expire after 30 days
   - Run cleanup: `python manage.py cleanup_expired_approvals`

4. **Security**
   - JWT authentication required
   - Role-based access control
   - Company isolation enforced

---

## 📁 Files Created

- `core/approval_models.py` - Database models
- `core/approval_workflow_views.py` - API endpoints
- `api/approval_workflow_apis.html` - HTML documentation
- `APPROVAL_WORKFLOW_IMPLEMENTATION.md` - Complete guide

---

## 🎓 Testing Checklist

- [ ] Create test Admin, Managers, HR
- [ ] Test employee creation workflow
- [ ] Test HR/Supervisor creation workflow
- [ ] Test sub-company creation workflow
- [ ] Test rejection flow
- [ ] Test company-specific routing
- [ ] Verify notifications work
- [ ] Check approval history logging

---

## 📞 Common Issues

**Problem:** Manager not seeing pending approvals  
**Solution:** Check company assignment in Employee model

**Problem:** Approval not moving to next stage  
**Solution:** Check workflow stage and approver role match

**Problem:** All managers getting notified  
**Solution:** Verify sub_company field is set correctly

---

## 🔗 Related Docs

- Full guide: `APPROVAL_WORKFLOW_IMPLEMENTATION.md`
- API docs: `api/approval_workflow_apis.html`
- Database schema: `core/approval_models.py`

---

**Last Updated:** October 8, 2025  
**Version:** 1.0  
**Status:** ✅ Ready to Use
