"""
Hierarchical Approval Workflow API ViewSet
Created: October 8, 2025

This module handles approval workflow APIs for:
- Employee creation (Sub-Manager → Main Manager)
- HR/Supervisor creation (Sub-Manager → Main Manager → Admin)
- Sub-company creation (Admin approval only)

WORKFLOW ROUTING:
- Employee in Sub-company 1 → Sub-company 1 Manager → Main Company Manager
- HR in Sub-company 1 → Sub-company 1 Manager → Main Company Manager → Admin
- If Sub-Manager rejects → Stop (don't go to Main Manager)
- Only relevant company managers are notified
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q, Count, Case, When, CharField
from django.utils import timezone
from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import User as AuthUser
from datetime import timedelta
import json

from .models import (
    ApprovalWorkflow,
    ApprovalHistory,
    PendingUser,
    ApprovalNotification
)

from .models import Employee, Company, OfficialDetails
from .serializers import EmployeeSerializer  # Assuming you have this


class ApprovalWorkflowViewSet(viewsets.ViewSet):
    """
    ViewSet for handling hierarchical approval workflows
    """
    permission_classes = [IsAuthenticated]

    def _get_current_employee(self, request):
        """Get current employee from authenticated user"""
        try:
            return Employee.objects.get(
                Q(employee_code=request.user.username) | 
                Q(email=request.user.email)
            )
        except Employee.DoesNotExist:
            return None

    def _create_notification(self, workflow, recipient, notification_type, title, message):
        """Create a notification for an approver"""
        ApprovalNotification.objects.create(
            workflow=workflow,
            recipient=recipient,
            notification_type=notification_type,
            title=title,
            message=message
        )

    def _get_next_approvers(self, workflow):
        """
        Get the list of employees who can approve at the current stage
        Returns only the relevant company's manager, not all managers
        """
        approvers = []
        
        if workflow.current_stage == 'sub_manager':
            # Get manager of the specific sub-company
            if workflow.sub_company:
                approvers = Employee.objects.filter(
                    role='Manager',
                    sub_company=workflow.sub_company,
                    status='ACTIVE'
                )
            
        elif workflow.current_stage == 'main_manager':
            # Get manager of the main company
            approvers = Employee.objects.filter(
                role='Manager',
                main_company=workflow.company,
                status='ACTIVE'
            )
            
        elif workflow.current_stage == 'admin':
            # Get all active admins
            approvers = Employee.objects.filter(
                role='Admin',
                status='ACTIVE'
            )
        
        return approvers

    def _notify_next_approvers(self, workflow):
        """Send notifications to the next approvers"""
        approvers = self._get_next_approvers(workflow)
        
        for approver in approvers:
            title = f"New {workflow.get_approval_type_display()} Approval Request"
            message = f"A new {workflow.get_approval_type_display()} request requires your approval. Created by {workflow.created_by.full_name if workflow.created_by else 'System'}."
            
            self._create_notification(
                workflow=workflow,
                recipient=approver,
                notification_type='pending_approval',
                title=title,
                message=message
            )

    @action(detail=False, methods=['post'], url_path='create-employee-request')
    def create_employee_request(self, request):
        """
        Create an employee approval request
        Workflow: Sub-Manager → Main Manager
        
        POST /api/approval-workflow/create-employee-request/
        Body: {
            "employee_data": {...},
            "official_details_data": {...},
            "password": "temp_password"
        }
        """
        current_employee = self._get_current_employee(request)
        if not current_employee:
            return Response({
                'success': False,
                'error': 'Employee profile not found'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Only HR can create employee requests
        if current_employee.role not in ['HR']:
            return Response({
                'success': False,
                'error': 'Only HR can create employee accounts'
            }, status=status.HTTP_403_FORBIDDEN)
        
        employee_data = request.data.get('employee_data', {})
        official_details_data = request.data.get('official_details_data', {})
        password = request.data.get('password')
        
        if not employee_data or not password:
            return Response({
                'success': False,
                'error': 'Employee data and password are required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Determine company context
        company = None
        sub_company = None
        
        if current_employee.sub_company:
            # HR in sub-company
            sub_company = current_employee.sub_company
            company = sub_company.parent_company
        elif current_employee.main_company:
            # HR in main company
            company = current_employee.main_company
            # Check if creating for a sub-company
            sub_company_id = employee_data.get('sub_company_id')
            if sub_company_id:
                try:
                    sub_company = Company.objects.get(
                        id=sub_company_id,
                        parent_company=company
                    )
                except Company.DoesNotExist:
                    return Response({
                        'success': False,
                        'error': 'Invalid sub-company'
                    }, status=status.HTTP_400_BAD_REQUEST)
        
        # Determine initial stage
        if sub_company:
            # Employee in sub-company → starts at sub_manager stage
            initial_stage = 'sub_manager'
        else:
            # Employee in main company → starts at main_manager stage
            initial_stage = 'main_manager'
        
        # Create approval workflow
        workflow = ApprovalWorkflow.objects.create(
            approval_type='employee',
            status='pending',
            current_stage=initial_stage,
            request_data={
                'employee_data': employee_data,
                'official_details_data': official_details_data
            },
            company=company,
            sub_company=sub_company,
            created_by=current_employee
        )
        
        # Create pending user
        username = employee_data.get('employee_code')
        email = employee_data.get('email')
        
        PendingUser.objects.create(
            workflow=workflow,
            username=username,
            email=email,
            temporary_password=make_password(password),
            employee_data=employee_data,
            official_details_data=official_details_data,
            expires_at=timezone.now() + timedelta(days=30)
        )
        
        # Create history record
        ApprovalHistory.objects.create(
            workflow=workflow,
            action='created',
            stage=initial_stage,
            actor=current_employee,
            actor_role=current_employee.role,
            comments=f"Approval workflow created for new employee: {employee_data.get('full_name')}"
        )
        
        # Notify next approvers
        self._notify_next_approvers(workflow)
        
        return Response({
            'success': True,
            'message': f'Employee creation request submitted. Awaiting {workflow.get_current_stage_display()} approval.',
            'data': {
                'workflow_id': workflow.id,
                'approval_type': workflow.approval_type,
                'current_stage': workflow.current_stage,
                'status': workflow.status
            }
        }, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['post'], url_path='create-hr-supervisor-request')
    def create_hr_supervisor_request(self, request):
        """
        Create HR/Supervisor approval request
        Workflow: Sub-Manager → Main Manager → Admin
        
        POST /api/approval-workflow/create-hr-supervisor-request/
        Body: {
            "employee_data": {...},
            "official_details_data": {...},
            "password": "temp_password",
            "account_type": "hr" or "supervisor"
        }
        """
        current_employee = self._get_current_employee(request)
        if not current_employee:
            return Response({
                'success': False,
                'error': 'Employee profile not found'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Only Admin or HR can create HR/Supervisor accounts
        if current_employee.role not in ['Admin', 'HR']:
            return Response({
                'success': False,
                'error': 'Only Admin or HR can create HR/Supervisor accounts'
            }, status=status.HTTP_403_FORBIDDEN)
        
        employee_data = request.data.get('employee_data', {})
        official_details_data = request.data.get('official_details_data', {})
        password = request.data.get('password')
        account_type = request.data.get('account_type', 'hr')  # 'hr' or 'supervisor'
        
        if not employee_data or not password:
            return Response({
                'success': False,
                'error': 'Employee data and password are required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Set role based on account type
        employee_data['role'] = 'HR' if account_type == 'hr' else 'Supervisor'
        
        # Determine company context
        company = None
        sub_company = None
        
        if current_employee.sub_company:
            # Sub-Manager creating account
            sub_company = current_employee.sub_company
            company = sub_company.parent_company
            initial_stage = 'main_manager'  # Skip sub_manager, go directly to main manager
        elif current_employee.main_company:
            # Main Manager creating account
            company = current_employee.main_company
            # Check if creating for a sub-company
            sub_company_id = employee_data.get('sub_company_id')
            if sub_company_id:
                try:
                    sub_company = Company.objects.get(
                        id=sub_company_id,
                        parent_company=company
                    )
                    initial_stage = 'main_manager'
                except Company.DoesNotExist:
                    return Response({
                        'success': False,
                        'error': 'Invalid sub-company'
                    }, status=status.HTTP_400_BAD_REQUEST)
            else:
                initial_stage = 'admin'  # Main company HR/Supervisor → directly to admin
        
        # Create approval workflow
        workflow = ApprovalWorkflow.objects.create(
            approval_type='hr' if account_type == 'hr' else 'supervisor',
            status='pending',
            current_stage=initial_stage,
            request_data={
                'employee_data': employee_data,
                'official_details_data': official_details_data
            },
            company=company,
            sub_company=sub_company,
            created_by=current_employee
        )
        
        # Create pending user
        username = employee_data.get('employee_code')
        email = employee_data.get('email')
        
        PendingUser.objects.create(
            workflow=workflow,
            username=username,
            email=email,
            temporary_password=make_password(password),
            employee_data=employee_data,
            official_details_data=official_details_data,
            expires_at=timezone.now() + timedelta(days=30)
        )
        
        # Create history record
        ApprovalHistory.objects.create(
            workflow=workflow,
            action='created',
            stage=initial_stage,
            actor=current_employee,
            actor_role=current_employee.role,
            comments=f"Approval workflow created for new {account_type.upper()}: {employee_data.get('full_name')}"
        )
        
        # Notify next approvers
        self._notify_next_approvers(workflow)
        
        return Response({
            'success': True,
            'message': f'{account_type.upper()} creation request submitted. Awaiting {workflow.get_current_stage_display()} approval.',
            'data': {
                'workflow_id': workflow.id,
                'approval_type': workflow.approval_type,
                'current_stage': workflow.current_stage,
                'status': workflow.status
            }
        }, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['post'], url_path='create-sub-company-request')
    def create_sub_company_request(self, request):
        """
        Create sub-company approval request
        Workflow: Admin approval only
        
        POST /api/approval-workflow/create-sub-company-request/
        Body: {
            "company_data": {...}
        }
        """
        current_employee = self._get_current_employee(request)
        if not current_employee:
            return Response({
                'success': False,
                'error': 'Employee profile not found'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Only Manager can create sub-company requests
        if current_employee.role != 'Manager':
            return Response({
                'success': False,
                'error': 'Only Manager can create sub-companies'
            }, status=status.HTTP_403_FORBIDDEN)
        
        company_data = request.data.get('company_data', {})
        
        if not company_data:
            return Response({
                'success': False,
                'error': 'Company data is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Ensure parent company is set
        company_data['parent_company_id'] = current_employee.main_company.id
        company_data['is_main_company'] = False
        
        # Create approval workflow
        workflow = ApprovalWorkflow.objects.create(
            approval_type='sub_company',
            status='pending',
            current_stage='admin',  # Directly to admin
            request_data={'company_data': company_data},
            company=current_employee.main_company,
            created_by=current_employee
        )
        
        # Create history record
        ApprovalHistory.objects.create(
            workflow=workflow,
            action='created',
            stage='admin',
            actor=current_employee,
            actor_role=current_employee.role,
            comments=f"Approval workflow created for new sub-company: {company_data.get('name')}"
        )
        
        # Notify admins
        self._notify_next_approvers(workflow)
        
        return Response({
            'success': True,
            'message': 'Sub-company creation request submitted. Awaiting Admin approval.',
            'data': {
                'workflow_id': workflow.id,
                'approval_type': workflow.approval_type,
                'current_stage': workflow.current_stage,
                'status': workflow.status
            }
        }, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['get'], url_path='pending-approvals')
    def pending_approvals(self, request):
        """
        Get pending approval requests for the current user
        Only shows requests that the current user can approve
        
        GET /api/approval-workflow/pending-approvals/
        Query params: ?type=employee&stage=sub_manager&page=1&page_size=20
        """
        current_employee = self._get_current_employee(request)
        if not current_employee:
            return Response({
                'success': False,
                'error': 'Employee profile not found'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Filter workflows that the current employee can approve
        workflows = ApprovalWorkflow.objects.filter(status='pending')
        
        # Filter based on role and company
        if current_employee.role == 'Admin':
            # Admin can see all workflows at admin stage
            workflows = workflows.filter(current_stage='admin')
        elif current_employee.role == 'Manager':
            if current_employee.main_company:
                # Main company manager
                workflows = workflows.filter(
                    current_stage='main_manager',
                    company=current_employee.main_company
                )
            elif current_employee.sub_company:
                # Sub-company manager
                workflows = workflows.filter(
                    current_stage='sub_manager',
                    sub_company=current_employee.sub_company
                )
        else:
            # Other roles cannot approve
            workflows = ApprovalWorkflow.objects.none()
        
        # Apply filters
        approval_type = request.query_params.get('type')
        if approval_type:
            workflows = workflows.filter(approval_type=approval_type)
        
        # Pagination
        page_size = int(request.query_params.get('page_size', 20))
        page = int(request.query_params.get('page', 1))
        start = (page - 1) * page_size
        end = start + page_size
        
        total_count = workflows.count()
        workflows = workflows[start:end]
        
        # Serialize data
        data = []
        for workflow in workflows:
            data.append({
                'id': workflow.id,
                'approval_type': workflow.approval_type,
                'approval_type_display': workflow.get_approval_type_display(),
                'status': workflow.status,
                'current_stage': workflow.current_stage,
                'current_stage_display': workflow.get_current_stage_display(),
                'company': workflow.company.name if workflow.company else None,
                'sub_company': workflow.sub_company.name if workflow.sub_company else None,
                'created_by': {
                    'employee_code': workflow.created_by.employee_code,
                    'full_name': workflow.created_by.full_name,
                    'role': workflow.created_by.role
                } if workflow.created_by else None,
                'created_at': workflow.created_at.isoformat(),
                'request_data': workflow.request_data
            })
        
        return Response({
            'success': True,
            'data': data,
            'pagination': {
                'page': page,
                'page_size': page_size,
                'total_count': total_count,
                'total_pages': (total_count + page_size - 1) // page_size
            }
        })

    @action(detail=True, methods=['post'], url_path='approve')
    def approve(self, request, pk=None):
        """
        Approve a workflow request
        
        POST /api/approval-workflow/{id}/approve/
        Body: {
            "comments": "Optional approval comments"
        }
        """
        current_employee = self._get_current_employee(request)
        if not current_employee:
            return Response({
                'success': False,
                'error': 'Employee profile not found'
            }, status=status.HTTP_403_FORBIDDEN)
        
        try:
            workflow = ApprovalWorkflow.objects.get(id=pk)
        except ApprovalWorkflow.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Workflow not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Check if workflow is pending
        if workflow.status != 'pending':
            return Response({
                'success': False,
                'error': 'Workflow is not pending'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Check if current employee can approve
        if not workflow.can_approve(current_employee):
            return Response({
                'success': False,
                'error': 'You do not have permission to approve this request'
            }, status=status.HTTP_403_FORBIDDEN)
        
        comments = request.data.get('comments', '')
        
        # Create approval history
        ApprovalHistory.objects.create(
            workflow=workflow,
            action='approved',
            stage=workflow.current_stage,
            actor=current_employee,
            actor_role=current_employee.role,
            comments=comments
        )
        
        # Get next stage
        next_stage = workflow.get_next_stage()
        
        if next_stage == 'completed':
            # Final approval - create the actual record
            workflow.status = 'approved'
            workflow.current_stage = 'completed'
            workflow.completed_at = timezone.now()
            workflow.save()
            
            # Create the actual employee/company
            if workflow.approval_type in ['employee', 'hr', 'supervisor']:
                self._create_employee_account(workflow)
            elif workflow.approval_type == 'sub_company':
                self._create_sub_company(workflow)
            
            # Notify creator
            self._create_notification(
                workflow=workflow,
                recipient=workflow.created_by,
                notification_type='approved',
                title=f'{workflow.get_approval_type_display()} Approved',
                message=f'Your {workflow.get_approval_type_display()} request has been fully approved and created.'
            )
            
            message = f'{workflow.get_approval_type_display()} has been approved and created successfully.'
        else:
            # Move to next stage
            workflow.current_stage = next_stage
            workflow.save()
            
            # Notify next approvers
            self._notify_next_approvers(workflow)
            
            message = f'Approved. Request moved to {workflow.get_current_stage_display()} stage.'
        
        return Response({
            'success': True,
            'message': message,
            'data': {
                'workflow_id': workflow.id,
                'status': workflow.status,
                'current_stage': workflow.current_stage
            }
        })

    @action(detail=True, methods=['post'], url_path='reject')
    def reject(self, request, pk=None):
        """
        Reject a workflow request
        Stops the workflow - does not proceed to next stage
        
        POST /api/approval-workflow/{id}/reject/
        Body: {
            "reason": "Rejection reason (required)"
        }
        """
        current_employee = self._get_current_employee(request)
        if not current_employee:
            return Response({
                'success': False,
                'error': 'Employee profile not found'
            }, status=status.HTTP_403_FORBIDDEN)
        
        try:
            workflow = ApprovalWorkflow.objects.get(id=pk)
        except ApprovalWorkflow.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Workflow not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Check if workflow is pending
        if workflow.status != 'pending':
            return Response({
                'success': False,
                'error': 'Workflow is not pending'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Check if current employee can reject
        if not workflow.can_approve(current_employee):
            return Response({
                'success': False,
                'error': 'You do not have permission to reject this request'
            }, status=status.HTTP_403_FORBIDDEN)
        
        reason = request.data.get('reason', '')
        if not reason:
            return Response({
                'success': False,
                'error': 'Rejection reason is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Update workflow
        workflow.status = 'rejected'
        workflow.rejection_reason = reason
        workflow.completed_at = timezone.now()
        workflow.save()
        
        # Create rejection history
        ApprovalHistory.objects.create(
            workflow=workflow,
            action='rejected',
            stage=workflow.current_stage,
            actor=current_employee,
            actor_role=current_employee.role,
            comments=reason
        )
        
        # Notify creator
        self._create_notification(
            workflow=workflow,
            recipient=workflow.created_by,
            notification_type='rejected',
            title=f'{workflow.get_approval_type_display()} Rejected',
            message=f'Your {workflow.get_approval_type_display()} request has been rejected. Reason: {reason}'
        )
        
        return Response({
            'success': True,
            'message': 'Request rejected successfully. Workflow stopped.',
            'data': {
                'workflow_id': workflow.id,
                'status': workflow.status,
                'rejection_reason': reason
            }
        })

    @action(detail=True, methods=['get'], url_path='history')
    def workflow_history(self, request, pk=None):
        """
        Get approval history for a workflow
        
        GET /api/approval-workflow/{id}/history/
        """
        try:
            workflow = ApprovalWorkflow.objects.get(id=pk)
        except ApprovalWorkflow.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Workflow not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        history = ApprovalHistory.objects.filter(workflow=workflow)
        
        data = []
        for entry in history:
            data.append({
                'action': entry.action,
                'action_display': entry.get_action_display(),
                'stage': entry.stage,
                'actor': {
                    'employee_code': entry.actor.employee_code,
                    'full_name': entry.actor.full_name,
                    'role': entry.actor_role
                } if entry.actor else None,
                'comments': entry.comments,
                'action_at': entry.action_at.isoformat()
            })
        
        return Response({
            'success': True,
            'data': {
                'workflow_id': workflow.id,
                'approval_type': workflow.get_approval_type_display(),
                'status': workflow.status,
                'history': data
            }
        })

    @action(detail=False, methods=['get'], url_path='notifications')
    def notifications(self, request):
        """
        Get notifications for the current user
        
        GET /api/approval-workflow/notifications/
        Query params: ?unread_only=true&page=1&page_size=20
        """
        current_employee = self._get_current_employee(request)
        if not current_employee:
            return Response({
                'success': False,
                'error': 'Employee profile not found'
            }, status=status.HTTP_403_FORBIDDEN)
        
        notifications = ApprovalNotification.objects.filter(recipient=current_employee)
        
        # Filter unread only
        unread_only = request.query_params.get('unread_only', 'false').lower() == 'true'
        if unread_only:
            notifications = notifications.filter(is_read=False)
        
        # Pagination
        page_size = int(request.query_params.get('page_size', 20))
        page = int(request.query_params.get('page', 1))
        start = (page - 1) * page_size
        end = start + page_size
        
        total_count = notifications.count()
        notifications = notifications[start:end]
        
        data = []
        for notif in notifications:
            data.append({
                'id': notif.id,
                'workflow_id': notif.workflow.id,
                'title': notif.title,
                'message': notif.message,
                'notification_type': notif.notification_type,
                'is_read': notif.is_read,
                'created_at': notif.created_at.isoformat(),
                'read_at': notif.read_at.isoformat() if notif.read_at else None
            })
        
        return Response({
            'success': True,
            'data': data,
            'pagination': {
                'page': page,
                'page_size': page_size,
                'total_count': total_count,
                'total_pages': (total_count + page_size - 1) // page_size
            }
        })

    @action(detail=False, methods=['post'], url_path='mark-notification-read')
    def mark_notification_read(self, request):
        """
        Mark notification as read
        
        POST /api/approval-workflow/mark-notification-read/
        Body: {
            "notification_id": 123
        }
        """
        notification_id = request.data.get('notification_id')
        if not notification_id:
            return Response({
                'success': False,
                'error': 'notification_id is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            notification = ApprovalNotification.objects.get(id=notification_id)
            notification.mark_as_read()
            
            return Response({
                'success': True,
                'message': 'Notification marked as read'
            })
        except ApprovalNotification.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Notification not found'
            }, status=status.HTTP_404_NOT_FOUND)

    @action(detail=False, methods=['get'], url_path='statistics')
    def statistics(self, request):
        """
        Get approval workflow statistics for the current user
        
        GET /api/approval-workflow/statistics/
        """
        current_employee = self._get_current_employee(request)
        if not current_employee:
            return Response({
                'success': False,
                'error': 'Employee profile not found'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Get workflows relevant to current user
        if current_employee.role == 'Admin':
            workflows = ApprovalWorkflow.objects.filter(current_stage='admin', status='pending')
        elif current_employee.role == 'Manager':
            if current_employee.main_company:
                workflows = ApprovalWorkflow.objects.filter(
                    current_stage='main_manager',
                    company=current_employee.main_company,
                    status='pending'
                )
            elif current_employee.sub_company:
                workflows = ApprovalWorkflow.objects.filter(
                    current_stage='sub_manager',
                    sub_company=current_employee.sub_company,
                    status='pending'
                )
        else:
            workflows = ApprovalWorkflow.objects.none()
        
        # Get counts by type
        stats = {
            'pending_count': workflows.count(),
            'by_type': {
                'employee': workflows.filter(approval_type='employee').count(),
                'hr': workflows.filter(approval_type='hr').count(),
                'supervisor': workflows.filter(approval_type='supervisor').count(),
                'sub_company': workflows.filter(approval_type='sub_company').count(),
            },
            'unread_notifications': ApprovalNotification.objects.filter(
                recipient=current_employee,
                is_read=False
            ).count()
        }
        
        return Response({
            'success': True,
            'data': stats
        })

    def _create_employee_account(self, workflow):
        """Create actual employee account after approval"""
        pending_user = PendingUser.objects.get(workflow=workflow)
        employee_data = pending_user.employee_data
        official_details_data = pending_user.official_details_data
        
        # Create User account
        user = AuthUser.objects.create(
            username=pending_user.username,
            email=pending_user.email,
            password=pending_user.temporary_password,
            is_active=True
        )
        
        # Create Employee record
        employee = Employee.objects.create(
            **employee_data,
            approval_status='approved',
            created_by=workflow.created_by,
            approved_by=self._get_last_approver(workflow),
            approval_workflow_id=workflow.id,
            approved_at=timezone.now()
        )
        
        # Create Official Details
        if official_details_data:
            OfficialDetails.objects.create(
                employee=employee,
                **official_details_data
            )
        
        return employee

    def _create_sub_company(self, workflow):
        """Create actual sub-company after approval"""
        company_data = workflow.request_data.get('company_data', {})
        
        # Create Company record
        company = Company.objects.create(**company_data)
        
        return company

    def _get_last_approver(self, workflow):
        """Get the last employee who approved the workflow"""
        last_approval = ApprovalHistory.objects.filter(
            workflow=workflow,
            action='approved'
        ).order_by('-action_at').first()
        
        return last_approval.actor if last_approval else None
