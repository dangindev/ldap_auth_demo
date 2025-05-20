from django.db import models
from django.contrib.auth.models import User

class LDAPLoginLog(models.Model):
    """Model ghi lại lịch sử đăng nhập và lỗi LDAP"""
    username = models.CharField(max_length=255)
    timestamp = models.DateTimeField(auto_now_add=True)
    success = models.BooleanField(default=False)
    error_message = models.TextField(blank=True, null=True)
    error_code = models.CharField(max_length=50, blank=True, null=True)
    
    def __str__(self):
        status = "Thành công" if self.success else "Thất bại"
        return f"{self.username} - {status} - {self.timestamp}"

class UserProfile(models.Model):
    """Model lưu trữ thông tin bổ sung của người dùng từ LDAP"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    employee_id = models.CharField(max_length=50, blank=True, null=True, verbose_name="Mã nhân viên")
    title = models.CharField(max_length=100, blank=True, null=True, verbose_name="Chức danh")
    mobile = models.CharField(max_length=20, blank=True, null=True, verbose_name="Số điện thoại")
    manager = models.CharField(max_length=255, blank=True, null=True, verbose_name="Quản lý")
    department = models.CharField(max_length=255, blank=True, null=True, verbose_name="Phòng ban")
    last_ldap_sync = models.DateTimeField(auto_now=True, verbose_name="Lần đồng bộ cuối")
    
    def __str__(self):
        return f"Profile: {self.user.username}"