import base64
from datetime import datetime, date
from django.shortcuts import render, redirect, get_object_or_404
from django.core.files.base import ContentFile
from django.contrib import messages
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from .models import Employee, Attendance, AuditLog, AdminChatMessage
from .forms import EmployeeForm, AttendanceForm
from django.conf import settings
import google.generativeai as genai


@login_required
def dashboard(request):
    if request.user.is_superuser:
        total_employees = Employee.objects.count()
        today = timezone.localdate()
        present_today = Attendance.objects.filter(date=today, check_in_time__isnull=False).count()
        recent_audits = AuditLog.objects.order_by('-timestamp')[:5]
    else:
        # Employee view
        try:
            employee = request.user.employee
            total_employees = 1
            today = timezone.localdate()
            present_today = 1 if Attendance.objects.filter(employee=employee, date=today, check_in_time__isnull=False).exists() else 0
            recent_audits = None # Normal users don't see audits
        except Employee.DoesNotExist:
            total_employees = 0
            present_today = 0
            recent_audits = None

    context = {
        'total_employees': total_employees,
        'present_today': present_today,
        'recent_audits': recent_audits,
    }
    return render(request, 'dashboard.html', context)

@login_required
def employee_list(request):
    if request.user.is_superuser:
        employees = Employee.objects.all()
    else:
        try:
            employees = Employee.objects.filter(user=request.user)
        except Employee.DoesNotExist:
            employees = Employee.objects.none()
            
    return render(request, 'employee_list.html', {'employees': employees})

@login_required
def employee_detail(request, pk):
    employee = get_object_or_404(Employee, pk=pk)
    
    # Admins can view anyone. Normal employees can only view themselves.
    if not request.user.is_superuser and getattr(request.user, 'employee', None) != employee:
        return HttpResponseForbidden("You can only view your own profile.")
        
    return render(request, 'employee_detail.html', {'target_employee': employee})

@login_required
def employee_create(request):
    if not request.user.is_superuser:
        return HttpResponseForbidden("Only administrators can add employees.")
        
    if request.method == 'POST':
        form = EmployeeForm(request.POST, request.FILES)
        if form.is_valid():
            employee = form.save(commit=False)
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            
            if username and password:
                from django.contrib.auth.models import User
                from django.db import IntegrityError
                
                if User.objects.filter(username__iexact=username).exists():
                    messages.error(request, 'Username already exists. Employee created without login account.')
                else:
                    try:
                        user = User.objects.create_user(username=username, password=password, email=employee.email)
                        employee.user = user
                    except IntegrityError:
                        messages.error(request, 'Username already exists. Employee created without login account.')
                    
            employee.save()
            messages.success(request, 'Employee created successfully.')
            return redirect('employee_list')
    else:
        form = EmployeeForm()
    return render(request, 'employee_form.html', {'form': form, 'title': 'Add Employee'})

@login_required
def employee_update(request, pk):
    employee = get_object_or_404(Employee, pk=pk)
    
    if not request.user.is_superuser and getattr(request.user, 'employee', None) != employee:
        return HttpResponseForbidden("You can only edit your own profile.")
        
    if request.method == 'POST':
        form = EmployeeForm(request.POST, request.FILES, instance=employee)
        if form.is_valid():
            employee = form.save(commit=False)
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            
            if username:
                from django.contrib.auth.models import User
                from django.db import IntegrityError
                
                if not employee.user:
                    # Creating a new user for existing employee
                    if User.objects.filter(username__iexact=username).exists():
                        messages.error(request, 'Username already exists. Could not attach login account.')
                    else:
                        try:
                            user = User.objects.create_user(username=username, password=password, email=employee.email)
                            employee.user = user
                        except IntegrityError:
                            messages.error(request, 'Username already exists. Could not attach login account.')
                else:
                    # Updating existing user
                    if employee.user.username != username and User.objects.filter(username__iexact=username).exists():
                        messages.error(request, 'Username already exists. Username was not changed.')
                    else:
                        try:
                            employee.user.username = username
                            password_changed = False
                            if password:
                                employee.user.set_password(password)
                                password_changed = True
                            employee.user.save()
                            
                            # Keep the user logged in if they just changed their own password
                            if password_changed and request.user == employee.user:
                                from django.contrib.auth import update_session_auth_hash
                                update_session_auth_hash(request, employee.user)
                        except IntegrityError:
                            messages.error(request, 'Username already exists. Username was not changed.')
                        
            employee.save()
            messages.success(request, 'Employee updated successfully.')
            return redirect('employee_list')
    else:
        initial_data = {}
        if employee.user:
            initial_data['username'] = employee.user.username
        form = EmployeeForm(instance=employee, initial=initial_data)
    return render(request, 'employee_form.html', {'form': form, 'title': 'Edit Employee'})

@login_required
def employee_delete(request, pk):
    if not request.user.is_superuser:
        return HttpResponseForbidden("Only administrators can delete employees.")
        
    employee = get_object_or_404(Employee, pk=pk)
    if request.method == 'POST':
        employee.delete()
        messages.success(request, 'Employee deleted successfully.')
        return redirect('employee_list')
    return render(request, 'employee_confirm_delete.html', {'employee': employee})

@login_required
def attendance_view(request):
    if request.method == 'POST':
        form = AttendanceForm(request.POST)
        action_type = request.POST.get('action_type')
        
        if form.is_valid():
            # If normal user, force employee to be them
            if not request.user.is_superuser:
                try:
                    employee = request.user.employee
                except Employee.DoesNotExist:
                    return HttpResponseForbidden("You do not have an associated employee record.")
            else:
                employee = form.cleaned_data['employee']
                
            photo_data = form.cleaned_data.get('check_in_photo_data')
            
            today = timezone.localdate()
            now = timezone.localtime().time()
            
            attendance, created = Attendance.objects.get_or_create(
                employee=employee,
                date=today,
                defaults={'check_in_time': now}
            )
            
            if action_type == 'check_in':
                if not created:
                    messages.warning(request, f'{employee.first_name} has already checked in today.')
                else:
                    if photo_data:
                        format, imgstr = photo_data.split(';base64,')
                        ext = format.split('/')[-1]
                        file_name = f"{employee.id}_{today.strftime('%Y%m%d')}.{ext}"
                        attendance.check_in_photo = ContentFile(base64.b64decode(imgstr), name=file_name)
                    attendance.save()
                    messages.success(request, f'Check-in successful for {employee.first_name}.')
                    
            elif action_type == 'check_out':
                if attendance.check_out_time:
                    messages.warning(request, f'{employee.first_name} has already checked out today.')
                else:
                    attendance.check_out_time = now
                    attendance.save()
                    messages.success(request, f'Check-out successful for {employee.first_name}.')
            
            return redirect('attendance_view')
    else:
        form = AttendanceForm()
        
    return render(request, 'attendance.html', {'form': form})

@login_required
def attendance_report(request):
    if request.user.is_superuser:
        attendances = Attendance.objects.all().order_by('-date')
    else:
        try:
            attendances = Attendance.objects.filter(employee=request.user.employee).order_by('-date')
        except Employee.DoesNotExist:
            attendances = Attendance.objects.none()
            
    return render(request, 'attendance_report.html', {'attendances': attendances})

@login_required
def ai_assistant_view(request):
    if not request.user.is_superuser:
        return HttpResponseForbidden("Only administrators can access the AI Assistant.")
        
    if request.method == 'POST':
        message = request.POST.get('message')
        
        try:
            # Configure Gemini API
            genai.configure(api_key=settings.GEMINI_API_KEY)
            # Use gemini-1.5-flash as default model
            model = genai.GenerativeModel('gemini-1.5-flash')
            # Add a bit of context so the AI knows its role
            system_prompt = "You are a helpful AI assistant for an Employee Management System. "
            full_prompt = system_prompt + message
            
            ai_response = model.generate_content(full_prompt)
            response_text = ai_response.text
        except Exception as e:
            response_text = f"Error generating response: {str(e)}. Please check if your GEMINI_API_KEY is configured correctly."
            
        return render(request, 'ai_assistant.html', {'response': response_text, 'message': message})
    
    return render(request, 'ai_assistant.html')
