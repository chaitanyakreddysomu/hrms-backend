# Create a management command: management/commands/setup_initial_data.py
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User, Group
from myapp.models import Company, UserProfile

class Command(BaseCommand):
    help = 'Setup initial data for the system'
    
    def handle(self, *args, **options):
        # Create Groups
        admin_group, created = Group.objects.get_or_create(name='Admin')
        hr_group, created = Group.objects.get_or_create(name='HR')
        supervisor_group, created = Group.objects.get_or_create(name='Supervisor')
        employee_group, created = Group.objects.get_or_create(name='Employee')
        
        # Create Main Companies
        rms, created = Company.objects.get_or_create(
            name='RMS (RADIANT Manpower Services)',
            defaults={
                'address': 'Bangalore, Karnataka',
                'gst_number': '29AAGCI9587F1ZW',
                'is_main_company': True
            }
        )
        
        ims, created = Company.objects.get_or_create(
            name='IMS (InLine Manpower Services Pvt Ltd)',
            defaults={
                'address': 'Bangalore, Karnataka', 
                'gst_number': '29AAGCI9587F1ZX',
                'is_main_company': True
            }
        )
        
        kvs, created = Company.objects.get_or_create(
            name='KVS Manpower Solutions',
            defaults={
                'address': 'Bangalore, Karnataka',
                'gst_number': '29AAGCI9587F1ZY', 
                'is_main_company': True
            }
        )
        
        # Get admin user (assuming username 'admin')
        try:
            admin_user = User.objects.get(username='admin')
            
            # Create UserProfile for admin
            user_profile, created = UserProfile.objects.get_or_create(
                user=admin_user,
                defaults={
                    'role': 'ADMIN',
                    'phone_number': '9876543210',
                    'employee_code': 'ADMIN001'
                }
            )
            
            # Assign admin to admin group
            admin_user.groups.add(admin_group)
            
            # Assign all companies to admin
            user_profile.assigned_companies.add(rms, ims, kvs)
            
            self.stdout.write(
                self.style.SUCCESS('Successfully created initial data')
            )
            
        except User.DoesNotExist:
            self.stdout.write(
                self.style.ERROR('Admin user not found. Please create superuser first.')
            )