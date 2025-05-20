from django import forms
from django.contrib.auth.forms import AuthenticationForm

class LDAPLoginForm(AuthenticationForm):
    """Form đăng nhập tùy chỉnh với các thông điệp lỗi cụ thể"""
    username = forms.CharField(
        label="Tên đăng nhập",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nhập tên đăng nhập'})
    )
    password = forms.CharField(
        label="Mật khẩu",
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Nhập mật khẩu'})
    )
    
    error_messages = {
        'invalid_login': "Tên đăng nhập hoặc mật khẩu không đúng. Vui lòng thử lại.",
        'inactive': "Tài khoản này đã bị vô hiệu hóa.",
    }