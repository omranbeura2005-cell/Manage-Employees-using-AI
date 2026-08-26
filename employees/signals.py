import json
from django.db.models.signals import post_save, pre_delete, pre_save
from django.contrib.auth.signals import user_logged_in
from django.dispatch import receiver
from django.utils import timezone
from datetime import timedelta
from .models import Employee, Attendance, AuditLog

def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

def serialize_model(instance):
    from django.core import serializers
    data = serializers.serialize('json', [instance])
    return json.loads(data)[0]['fields']

# Store the old state before save
@receiver(pre_save, sender=Employee)
@receiver(pre_save, sender=Attendance)
def capture_old_state(sender, instance, **kwargs):
    if instance.pk:
        old_instance = sender.objects.get(pk=instance.pk)
        instance._old_state = serialize_model(old_instance)
    else:
        instance._old_state = None

@receiver(post_save, sender=Employee)
@receiver(post_save, sender=Attendance)
def log_create_update(sender, instance, created, **kwargs):
    action = 'CREATE' if created else 'UPDATE'
    after_state = serialize_model(instance)
    before_state = getattr(instance, '_old_state', None)
    
    # We don't have the request user easily available in signals without middleware,
    # so user will be null unless we use thread locals.
    # For simplicity, we just save the states.
    AuditLog.objects.create(
        model_name=sender.__name__,
        object_id=instance.pk,
        action=action,
        before_state=before_state,
        after_state=after_state
    )

@receiver(pre_delete, sender=Employee)
@receiver(pre_delete, sender=Attendance)
def log_delete(sender, instance, **kwargs):
    before_state = serialize_model(instance)
    
    AuditLog.objects.create(
        model_name=sender.__name__,
        object_id=instance.pk,
        action='DELETE',
        before_state=before_state,
        after_state=None
    )

@receiver(user_logged_in)
def auto_increment_attendance(sender, request, user, **kwargs):
    if hasattr(user, 'employee'):
        emp = user.employee
        now = timezone.now()
        
        # If no previous login attendance or last login was >= 23 hours ago
        if not emp.last_login_attendance or (now - emp.last_login_attendance) >= timedelta(hours=23):
            emp.attendance_count += 1
            emp.last_login_attendance = now
            # update_fields to avoid triggering pre_save/post_save for AuditLog on every login
            emp.save(update_fields=['attendance_count', 'last_login_attendance'])
