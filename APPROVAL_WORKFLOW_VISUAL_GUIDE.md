# 🔄 Hierarchical Approval Workflow - Visual Summary

## 🎯 Core Principle: Smart Company-Specific Routing

> **"If HR creates an employee in Sub-Company 1, only Sub-Company 1 Manager gets notified - not all managers!"**

---

## 📊 Workflow Diagrams

### 1. Employee Creation (2-Level Approval)

```
┌─────────────────────────────────────────────────────────────────────┐
│                    EMPLOYEE CREATION WORKFLOW                       │
└─────────────────────────────────────────────────────────────────────┘

SCENARIO A: Employee in Sub-Company 1
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    ┌──────────────┐
    │   HR (Sub1)  │  Creates employee for Sub-Company 1
    │  Creates     │
    └──────┬───────┘
           │
           ▼
    ┌──────────────┐
    │ Sub-Co 1 Mgr │  ← ONLY Sub-Co 1 Manager notified
    │  Reviews     │    (Not Sub-Co 2, 3, etc.)
    └──────┬───────┘
           │
     ┌─────┴─────┐
     │ Approve?  │
     └─────┬─────┘
           │
     ┌─────┴─────┐
     │           │
     ▼           ▼
  ✅ Yes      ❌ No (Reject)
     │           │
     │           └──────────────┐
     ▼                          │
┌──────────────┐                │
│  Main Co Mgr │                │
│   Reviews    │                │
└──────┬───────┘                │
       │                        │
 ┌─────┴─────┐                  │
 │ Approve?  │                  │
 └─────┬─────┘                  │
       │                        │
   ┌───┴───┐                    │
   │       │                    │
   ▼       ▼                    ▼
 ✅ Yes  ❌ No           ┌────────────┐
   │       │            │  STOPPED   │
   │       └────────────► Rejected  │
   │                    │ Main Mgr  │
   ▼                    │  NOT      │
┌────────────┐          │ Notified  │
│ EMPLOYEE   │          └────────────┘
│  CREATED   │
│     ✓      │
└────────────┘


SCENARIO B: Employee in Main Company (Direct)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    ┌──────────────┐
    │   HR (Main)  │  Creates employee for Main Company
    │  Creates     │
    └──────┬───────┘
           │
           ▼
    ┌──────────────┐
    │  Main Co Mgr │  ← Skips Sub-Co Manager
    │   Reviews    │    (Direct to Main Manager)
    └──────┬───────┘
           │
     ┌─────┴─────┐
     │ Approve?  │
     └─────┬─────┘
           │
       ┌───┴───┐
       │       │
       ▼       ▼
     ✅ Yes  ❌ No
       │       │
       ▼       ▼
   ┌────────────┐  ┌────────────┐
   │ EMPLOYEE   │  │  STOPPED   │
   │  CREATED   │  │  Rejected  │
   └────────────┘  └────────────┘
```

---

### 2. HR/Supervisor Creation (3-Level Approval)

```
┌─────────────────────────────────────────────────────────────────────┐
│                 HR/SUPERVISOR CREATION WORKFLOW                     │
│            (Requires Admin approval - highest privilege)            │
└─────────────────────────────────────────────────────────────────────┘

    ┌──────────────┐
    │   Manager    │  Creates HR/Supervisor account
    │  Creates     │
    └──────┬───────┘
           │
           ▼
    ┌──────────────┐
    │ Sub-Co Mgr   │  ← First approval (if in sub-company)
    │  Reviews     │
    └──────┬───────┘
           │
     ┌─────┴─────┐
     │ Approve?  │
     └─────┬─────┘
           │
     ┌─────┴─────┐
     │           │
     ▼           ▼
  ✅ Yes      ❌ No ──────┐
     │                    │
     ▼                    │
┌──────────────┐          │
│  Main Co Mgr │          │
│   Reviews    │          │
└──────┬───────┘          │
       │                  │
 ┌─────┴─────┐            │
 │ Approve?  │            │
 └─────┬─────┘            │
       │                  │
   ┌───┴───┐              │
   │       │              │
   ▼       ▼              │
 ✅ Yes  ❌ No ────┐      │
   │       │       │      │
   ▼       │       │      │
┌──────────────┐   │      │
│    ADMIN     │   │      │
│   Reviews    │   │      │
└──────┬───────┘   │      │
       │           │      │
 ┌─────┴─────┐     │      │
 │ Approve?  │     │      │
 └─────┬─────┘     │      │
       │           │      │
   ┌───┴───┐       │      │
   │       │       │      │
   ▼       ▼       ▼      ▼
 ✅ Yes  ❌ No  ┌────────────┐
   │       │    │  STOPPED   │
   ▼       └────►  Rejected  │
┌────────────┐   └────────────┘
│ HR/SUPER   │
│  CREATED   │
│     ✓      │
└────────────┘

WHY 3 LEVELS?
• HR/Supervisor have elevated privileges
• Can access sensitive employee data
• Admin oversight required for security & compliance
```

---

### 3. Sub-Company Creation (Admin Only)

```
┌─────────────────────────────────────────────────────────────────────┐
│                  SUB-COMPANY CREATION WORKFLOW                      │
│                      (Admin approval only)                          │
└─────────────────────────────────────────────────────────────────────┘

    ┌──────────────┐
    │  Manager     │  Creates sub-company
    │  (Main Co)   │
    └──────┬───────┘
           │
           ▼
    ┌──────────────┐
    │    ADMIN     │  ← Direct to Admin (no sub-manager)
    │   Reviews    │
    └──────┬───────┘
           │
     ┌─────┴─────┐
     │ Approve?  │
     └─────┬─────┘
           │
       ┌───┴───┐
       │       │
       ▼       ▼
     ✅ Yes  ❌ No
       │       │
       ▼       ▼
   ┌────────────┐  ┌────────────┐
   │SUB-COMPANY │  │  STOPPED   │
   │  CREATED   │  │  Rejected  │
   │     ✓      │  └────────────┘
   └────────────┘

WHY ADMIN ONLY?
• Sub-companies are critical organizational units
• Impact system structure and data isolation
• Admin has system-wide visibility
```

---

## 🎭 Role-Based Access Matrix

```
┌──────────────────────────────────────────────────────────────────────┐
│                    WHO CAN DO WHAT?                                  │
└──────────────────────────────────────────────────────────────────────┘

╔═══════════════╦═══════════════╦═══════════════╦═══════════════╦═══════════════╗
║     Role      ║   Create      ║   Create      ║   Create      ║   Approve     ║
║               ║   Employee    ║   HR/Super    ║ Sub-Company   ║   Requests    ║
╠═══════════════╬═══════════════╬═══════════════╬═══════════════╬═══════════════╣
║ Admin         ║      ✅       ║      ✅       ║      ✅       ║  Admin stage  ║
╠═══════════════╬═══════════════╬═══════════════╬═══════════════╬═══════════════╣
║ Manager       ║      ✅       ║      ✅       ║      ✅       ║ Manager stage ║
║ (Main)        ║               ║               ║  (Main only)  ║  (own co)     ║
╠═══════════════╬═══════════════╬═══════════════╬═══════════════╬═══════════════╣
║ Manager       ║      ✅       ║      ✅       ║      ❌       ║ Sub-Mgr stage║
║ (Sub)         ║               ║               ║               ║  (own sub-co) ║
╠═══════════════╬═══════════════╬═══════════════╬═══════════════╬═══════════════╣
║ Sub-Manager   ║      ✅       ║      ✅       ║      ❌       ║ Sub-Mgr stage║
║               ║               ║               ║               ║  (own sub-co) ║
╠═══════════════╬═══════════════╬═══════════════╬═══════════════╬═══════════════╣
║ HR            ║      ✅       ║      ❌       ║      ❌       ║      ❌       ║
╠═══════════════╬═══════════════╬═══════════════╬═══════════════╬═══════════════╣
║ Supervisor    ║      ❌       ║      ❌       ║      ❌       ║      ❌       ║
╠═══════════════╬═══════════════╬═══════════════╬═══════════════╬═══════════════╣
║ Employee      ║      ❌       ║      ❌       ║      ❌       ║      ❌       ║
╚═══════════════╩═══════════════╩═══════════════╩═══════════════╩═══════════════╝
```

---

## 🌳 Company Hierarchy & Routing

```
┌─────────────────────────────────────────────────────────────────────┐
│                      COMPANY STRUCTURE                              │
└─────────────────────────────────────────────────────────────────────┘

                    ┌──────────────────┐
                    │   MAIN COMPANY   │
                    │   "TechCorp"     │
                    └────────┬─────────┘
                             │
              ┌──────────────┼──────────────┐
              │              │              │
              ▼              ▼              ▼
     ┌────────────────┐ ┌────────────────┐ ┌────────────────┐
     │ SUB-COMPANY 1  │ │ SUB-COMPANY 2  │ │ SUB-COMPANY 3  │
     │ "Engineering"  │ │ "Marketing"    │ │ "Sales"        │
     └────────────────┘ └────────────────┘ └────────────────┘


ROUTING EXAMPLES:
━━━━━━━━━━━━━━━━

Example 1: HR in Sub-Company 1 creates employee for Sub-Company 1
───────────────────────────────────────────────────────────────────
  Request goes to → Sub-Company 1 Manager ONLY
                   (NOT Sub-Company 2, 3, or Main Manager)

Example 2: HR in Sub-Company 1 creates employee for Sub-Company 2
───────────────────────────────────────────────────────────────────
  Request goes to → Sub-Company 2 Manager
                   (NOT Sub-Company 1 Manager)

Example 3: HR in Main Company creates employee for Main Company
─────────────────────────────────────────────────────────────────
  Request goes to → Main Company Manager directly
                   (Skips all sub-company managers)

Example 4: Manager in Sub-Company 1 creates HR for Sub-Company 1
──────────────────────────────────────────────────────────────────
  Request goes to → Main Company Manager (creator is sub-co manager)
                 → Then Admin
                   (Skips sub-company manager stage)
```

---

## 🚦 Approval Decision Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│                   APPROVER DECISION MATRIX                          │
└─────────────────────────────────────────────────────────────────────┘

When you receive an approval request:

    ┌─────────────────────┐
    │ Review Request      │
    │ - Employee details  │
    │ - Documents         │
    │ - Creator info      │
    └──────────┬──────────┘
               │
         ┌─────┴──────┐
         │ Decision?  │
         └─────┬──────┘
               │
       ┌───────┴────────┐
       │                │
       ▼                ▼
  ┌─────────┐      ┌──────────┐
  │ APPROVE │      │  REJECT  │
  └────┬────┘      └─────┬────┘
       │                 │
       │                 │
       ▼                 ▼
┌──────────────┐   ┌─────────────────┐
│ Add comment  │   │ Provide reason  │
│ (optional)   │   │ (REQUIRED)      │
└──────┬───────┘   └────────┬────────┘
       │                    │
       ▼                    ▼
┌──────────────┐   ┌─────────────────┐
│ Move to next │   │ Stop workflow   │
│ stage        │   │ immediately     │
│              │   │                 │
│ IF final:    │   │ Next approvers  │
│ Create acc   │   │ NOT notified    │
└──────────────┘   └─────────────────┘


REJECTION CONSEQUENCES:
━━━━━━━━━━━━━━━━━━━━━━
✗ Workflow permanently stopped
✗ Next level approvers NOT notified
✗ Creator gets rejection notification
✗ Request must be re-created to retry
✓ Rejection reason documented in audit log
```

---

## 📊 Database Schema Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                      DATABASE TABLES                                │
└─────────────────────────────────────────────────────────────────────┘

┌────────────────────────┐
│  approval_workflow     │  ← Main workflow tracking
├────────────────────────┤
│ id                     │
│ approval_type          │  employee, hr, supervisor, sub_company
│ status                 │  pending, approved, rejected
│ current_stage          │  sub_manager, main_manager, admin, completed
│ company_id             │  ← Main company reference
│ sub_company_id         │  ← Sub-company reference (if applicable)
│ created_by_id          │  ← Employee who created
│ request_data (JSON)    │  ← Employee/company data
│ rejection_reason       │
│ created_at             │
│ completed_at           │
└────────────────────────┘
           │
           │ 1:N
           ▼
┌────────────────────────┐
│  approval_history      │  ← Audit trail
├────────────────────────┤
│ id                     │
│ workflow_id            │
│ action                 │  created, approved, rejected
│ stage                  │  sub_manager, main_manager, admin
│ actor_id               │  ← Employee who acted
│ actor_role             │  Role at time of action
│ comments               │
│ action_at              │
│ ip_address             │
│ user_agent             │
└────────────────────────┘

┌────────────────────────┐
│  pending_user          │  ← Temporary storage
├────────────────────────┤
│ id                     │
│ workflow_id            │  1:1 with approval_workflow
│ username               │  ← UNIQUE (prevents duplicates)
│ email                  │  ← UNIQUE
│ temporary_password     │  ← Hashed
│ employee_data (JSON)   │
│ official_details (JSON)│
│ expires_at             │  ← 30 days expiration
└────────────────────────┘

┌────────────────────────┐
│ approval_notification  │  ← In-app notifications
├────────────────────────┤
│ id                     │
│ workflow_id            │
│ recipient_id           │  ← Employee to notify
│ title                  │
│ message                │
│ notification_type      │  pending, approved, rejected, escalated
│ is_read                │
│ read_at                │
│ created_at             │
└────────────────────────┘

┌────────────────────────┐
│  employee (updated)    │  ← Added approval fields
├────────────────────────┤
│ ... existing fields    │
│ approval_status        │  ← NEW: pending, approved, active
│ created_by_id          │  ← NEW: Who created this account
│ approved_by_id         │  ← NEW: Who approved
│ approval_workflow_id   │  ← NEW: Link to workflow
│ created_at             │  ← NEW
│ approved_at            │  ← NEW
└────────────────────────┘
```

---

## 🔔 Notification Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│                    NOTIFICATION SYSTEM                              │
└─────────────────────────────────────────────────────────────────────┘

STAGE 1: Request Created
━━━━━━━━━━━━━━━━━━━━━━━
    Creator (HR)
         │
         │ Creates request
         ▼
    ┌─────────────────┐
    │   Workflow      │
    │   Created       │
    └────────┬────────┘
             │
             ├──→ Notification sent to: Next Approver
             │    Type: "pending_approval"
             │    Title: "New Employee Creation Request"
             │
             └──→ Email notification (optional)


STAGE 2: First Approval
━━━━━━━━━━━━━━━━━━━━━━
    Sub-Company Manager
         │
         │ Approves
         ▼
    ┌─────────────────┐
    │   Stage         │
    │   Advanced      │
    └────────┬────────┘
             │
             ├──→ Notification sent to: Main Manager
             │    Type: "pending_approval"
             │
             └──→ Notification sent to: Creator (HR)
                  Type: "escalated"
                  Message: "Approved by Sub-Manager, pending Main Manager"


STAGE 3: Final Approval
━━━━━━━━━━━━━━━━━━━━━━━
    Main Manager
         │
         │ Approves (Final)
         ▼
    ┌─────────────────┐
    │   Employee      │
    │   Created!      │
    └────────┬────────┘
             │
             └──→ Notification sent to: Creator (HR)
                  Type: "approved"
                  Title: "Employee Created Successfully"
                  Message: "John Doe (EMP001) has been approved and created"


REJECTION SCENARIO
━━━━━━━━━━━━━━━━━
    Sub-Company Manager
         │
         │ Rejects
         ▼
    ┌─────────────────┐
    │   Workflow      │
    │   Rejected      │
    └────────┬────────┘
             │
             ├──→ Notification sent to: Creator (HR)
             │    Type: "rejected"
             │    Title: "Employee Request Rejected"
             │    Message: "Reason: Incomplete documentation"
             │
             └──→ NO notification to Main Manager
                  (Workflow stopped)
```

---

## 🎯 Real-World Example Timeline

```
┌─────────────────────────────────────────────────────────────────────┐
│                  COMPLETE WORKFLOW TIMELINE                         │
│          HR creates employee in Sub-Company 1                       │
└─────────────────────────────────────────────────────────────────────┘

10:00 AM  │ HR (Jane) creates employee request for "John Doe"
          │ Company: Sub-Company 1 (Engineering Division)
          │ Position: Software Engineer
          │
          ▼
          ┌────────────────────────────────────────────┐
          │ ✓ Workflow #100 created                    │
          │ ✓ PendingUser created (username: EMP001)   │
          │ ✓ Stage: sub_manager                       │
          │ ✓ Notification → Sub-Co 1 Manager          │
          └────────────────────────────────────────────┘

10:05 AM  │ Sub-Company 1 Manager (Mike) receives notification
          │ Checks email & in-app notification
          │
          ▼
          │ GET /api/approval-workflow/pending-approvals/
          │ Sees: 1 pending employee request
          │

11:30 AM  │ Sub-Company 1 Manager reviews request
          │ Verifies: Skills, experience, documents
          │ Decision: APPROVE
          │
          ▼
          │ POST /api/approval-workflow/100/approve/
          │ Comment: "Verified qualifications and documents"
          │
          ▼
          ┌────────────────────────────────────────────┐
          │ ✓ Stage changed: main_manager              │
          │ ✓ History logged: Mike approved            │
          │ ✓ Notification → Main Company Manager      │
          │ ✓ Notification → Jane (escalated)          │
          └────────────────────────────────────────────┘

11:35 AM  │ Main Company Manager (Sarah) receives notification
          │
          ▼
          │ GET /api/approval-workflow/pending-approvals/
          │ Sees: 1 pending employee request (from Sub-Co 1)
          │

02:00 PM  │ Main Company Manager reviews request
          │ Sees: Already approved by Sub-Co Manager
          │ Decision: APPROVE (Final)
          │
          ▼
          │ POST /api/approval-workflow/100/approve/
          │ Comment: "Final approval - Welcome to the team!"
          │
          ▼
          ┌────────────────────────────────────────────┐
          │ ✓ User account created (EMP001)            │
          │ ✓ Employee record created                  │
          │ ✓ Official details linked                  │
          │ ✓ PendingUser deleted                      │
          │ ✓ Workflow status: approved                │
          │ ✓ Stage: completed                         │
          │ ✓ Notification → Jane (approved)           │
          └────────────────────────────────────────────┘

02:01 PM  │ Jane (HR) receives "Approved" notification
          │ John Doe can now login with:
          │ Username: EMP001
          │ Password: (as provided in request)
          │
          ▼
          │ Success! Employee onboarded. 🎉

TOTAL TIME: 4 hours 1 minute
APPROVALS: 2 (Sub-Manager + Main Manager)
STATUS: ✅ Completed
```

---

## 🎓 Key Takeaways

```
┌─────────────────────────────────────────────────────────────────────┐
│                         REMEMBER                                    │
└─────────────────────────────────────────────────────────────────────┘

1. SMART ROUTING
   ══════════════
   ✓ Requests go ONLY to relevant company's manager
   ✓ Sub-Company 1 → Sub-Company 1 Manager ONLY
   ✓ Not all managers get notified

2. REJECTION = STOP
   ═════════════════
   ✓ If any approver rejects → Workflow stops
   ✓ Next level approvers are NOT notified
   ✓ Must create new request to retry

3. APPROVAL LEVELS
   ═══════════════
   ✓ Employee: 2 levels (Sub-Mgr → Main Mgr)
   ✓ HR/Supervisor: 3 levels (Sub-Mgr → Main Mgr → Admin)
   ✓ Sub-Company: 1 level (Admin only)

4. COMPANY CONTEXT
   ════════════════
   ✓ Each workflow linked to specific company
   ✓ Approvers only see their company's requests
   ✓ Company isolation enforced at database level

5. AUDIT TRAIL
   ════════════
   ✓ Every action logged with timestamp
   ✓ Actor information preserved
   ✓ Comments and reasons stored
   ✓ IP address and user agent tracked
```

---

**📚 Full Documentation:** `APPROVAL_WORKFLOW_IMPLEMENTATION.md`  
**🎨 API Docs:** `api/approval_workflow_apis.html`  
**⚡ Quick Ref:** `APPROVAL_WORKFLOW_QUICK_REFERENCE.md`

---

**Last Updated:** October 8, 2025  
**Version:** 1.0  
**Status:** ✅ Production Ready
