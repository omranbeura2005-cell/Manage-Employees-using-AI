from django.contrib import admin
from .models import Employee, Attendance, AuditLog, AdminChatMessage

@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'last_name', 'email', 'department', 'designation')
    search_fields = ('first_name', 'last_name', 'email', 'department')
    list_filter = ('department', 'designation')

@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ('employee', 'date', 'check_in_time', 'check_out_time')
    search_fields = ('employee__first_name', 'employee__last_name')
    list_filter = ('date',)

@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('model_name', 'action', 'timestamp', 'user')
    search_fields = ('model_name', 'action')
    list_filter = ('action', 'model_name')
    readonly_fields = ('model_name', 'object_id', 'action', 'timestamp', 'user', 'before_state', 'after_state')

@admin.register(AdminChatMessage)
class AdminChatMessageAdmin(admin.ModelAdmin):
    list_display = ('admin', 'timestamp')
    search_fields = ('admin__username', 'message')
