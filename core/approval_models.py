"""
Hierarchical Approval Workflow Models
Created: October 8, 2025

This module handles multi-level approval workflows for:
- Employee creation (Sub-Manager → Main Manager)
- HR/Supervisor creation (Sub-Manager → Main Manager → Admin)
- Sub-company creation (Admin approval only)
"""

from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
import json
