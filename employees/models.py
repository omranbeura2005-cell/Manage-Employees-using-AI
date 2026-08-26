from django.db import models
from django.contrib.auth.models import User

class Employee(models.Model):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=15, blank=True)
    age = models.IntegerField(null=True, blank=True)
    department = models.CharField(max_length=100)
    designation = models.CharField(max_length=100)
    salary = models.DecimalField(max_digits=10, decimal_places=2)
    profile_picture = models.ImageField(upload_to='employee_profiles/', null=True, blank=True)
    join_date = models.DateField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    
    attendance_count = models.IntegerField(default=0)
    last_login_attendance = models.DateTimeField(null=True, blank=True)
    
    @property
    def current_month_attendance_count(self):
        from django.utils import timezone
        today = timezone.localdate()
        return self.attendance_set.filter(date__year=today.year, date__month=today.month).count()
        
    def __str__(self):
        return f"{self.first_name} {self.last_name}"

class Attendance(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    date = models.DateField(auto_now_add=True)
    check_in_time = models.TimeField(null=True, blank=True)
    check_out_time = models.TimeField(null=True, blank=True)
    check_in_photo = models.ImageField(upload_to='attendance_photos/', null=True, blank=True)
    
    def __str__(self):
        return f"{self.employee} - {self.date}"

class AuditLog(models.Model):
    model_name = models.CharField(max_length=100)
    object_id = models.IntegerField(null=True, blank=True)
    action = models.CharField(max_length=50) # CREATE, UPDATE, DELETE
    timestamp = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    before_state = models.TextField(blank=True, null=True)
    after_state = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return f"{self.action} on {self.model_name} (ID: {self.object_id})"

class AdminChatMessage(models.Model):
    admin = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.TextField()
    response = models.TextField(blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Q: {self.message[:20]}..."
