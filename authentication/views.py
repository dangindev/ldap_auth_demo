import ldap
import ldap.dn
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.conf import settings
from django.contrib.auth.models import User

from .forms import LDAPLoginForm
from .models import LDAPLoginLog, UserProfile

def login_view(request):
    """Xử lý đăng nhập và phân tích cụ thể các lỗi LDAP"""
    if request.method == 'POST':
        form = LDAPLoginForm(request, data=request.POST)
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        # Dùng để ghi log
        log_entry = LDAPLoginLog(username=username)
        
        # Kiểm tra nếu có mô phỏng lỗi
        error_type = request.POST.get('error_simulation', '')
        if error_type:
            if error_type == 'account_expired':
                messages.error(request, 'Tài khoản của bạn đã hết hạn. Vui lòng liên hệ quản trị viên.')
                log_entry.error_message = 'Tài khoản hết hạn (mô phỏng)'
                log_entry.error_code = 'ACCOUNT_EXPIRED'
                log_entry.save()
                return render(request, 'authentication/login.html', {'form': form})
            elif error_type == 'invalid_credentials':
                messages.error(request, 'Tên đăng nhập hoặc mật khẩu không đúng.')
                log_entry.error_message = 'Thông tin đăng nhập không hợp lệ (mô phỏng)'
                log_entry.error_code = 'INVALID_CREDENTIALS'
                log_entry.save()
                return render(request, 'authentication/login.html', {'form': form})
            elif error_type == 'account_locked':
                messages.error(request, 'Tài khoản của bạn đã bị khóa do đăng nhập sai nhiều lần. Vui lòng liên hệ quản trị viên.')
                log_entry.error_message = 'Tài khoản bị khóa (mô phỏng)'
                log_entry.error_code = 'ACCOUNT_LOCKED'
                log_entry.save()
                return render(request, 'authentication/login.html', {'form': form})
            elif error_type == 'password_expired':
                messages.error(request, 'Mật khẩu của bạn đã hết hạn. Vui lòng đổi mật khẩu mới.')
                log_entry.error_message = 'Mật khẩu hết hạn (mô phỏng)'
                log_entry.error_code = 'PASSWORD_EXPIRED'
                log_entry.save()
                return render(request, 'authentication/login.html', {'form': form})
            elif error_type == 'server_down':
                messages.error(request, 'Không thể kết nối đến máy chủ LDAP. Vui lòng thử lại sau.')
                log_entry.error_message = 'Máy chủ LDAP không khả dụng (mô phỏng)'
                log_entry.error_code = 'SERVER_DOWN'
                log_entry.save()
                return render(request, 'authentication/login.html', {'form': form})
        
        try:
            # Thử xác thực qua LDAP
            user = authenticate(request, username=username, password=password)
            
            if user is not None:
                login(request, user)
                log_entry.success = True
                log_entry.save()
                
                # Lấy thông tin chi tiết từ LDAP và lưu vào UserProfile
                try:
                    # Tạo hoặc cập nhật profile
                    profile, created = UserProfile.objects.get_or_create(user=user)
                    
                    # Kết nối LDAP để lấy thông tin chi tiết hơn
                    conn = ldap.initialize(settings.AUTH_LDAP_SERVER_URI)
                    conn.simple_bind_s(settings.AUTH_LDAP_BIND_DN, settings.AUTH_LDAP_BIND_PASSWORD)
                    
                    # Tìm kiếm người dùng trong LDAP
                    search_filter = f"(sAMAccountName={username})"
                    base_dn = "OU=USERS,OU=HO,OU=HANOI,DC=ttgroup,DC=com,DC=vn"
                    attrs = ['employeeID', 'title', 'mobile', 'manager', 'department', 'mail', 'givenName', 'sn']
                    
                    results = conn.search_s(base_dn, ldap.SCOPE_SUBTREE, search_filter, attrs)
                    
                    if results and len(results) > 0:
                        dn, attrs = results[0]
                        
                        # Cập nhật thông tin profile
                        if b'employeeID' in attrs:
                            profile.employee_id = attrs[b'employeeID'][0].decode('utf-8')
                        
                        if b'title' in attrs:
                            profile.title = attrs[b'title'][0].decode('utf-8')
                        
                        if b'mobile' in attrs:
                            profile.mobile = attrs[b'mobile'][0].decode('utf-8')
                        
                        if b'manager' in attrs:
                            profile.manager = attrs[b'manager'][0].decode('utf-8')
                        
                        if b'department' in attrs and attrs[b'department']:
                            profile.department = attrs[b'department'][0].decode('utf-8')
                        
                        # Cập nhật thông tin user từ LDAP nếu cần
                        if b'mail' in attrs and attrs[b'mail'] and not user.email:
                            user.email = attrs[b'mail'][0].decode('utf-8')
                        
                        if b'givenName' in attrs and attrs[b'givenName'] and not user.first_name:
                            user.first_name = attrs[b'givenName'][0].decode('utf-8')
                        
                        if b'sn' in attrs and attrs[b'sn'] and not user.last_name:
                            user.last_name = attrs[b'sn'][0].decode('utf-8')
                        
                        # Lưu các thay đổi
                        user.save()
                        profile.save()
                except Exception as e:
                    # Lỗi khi cập nhật profile không nên ngăn người dùng đăng nhập
                    print(f"Lỗi khi cập nhật profile: {str(e)}")
                
                messages.success(request, f'Đăng nhập thành công! Xin chào {user.username}')
                return redirect('home')
            else:
                # Xác thực thất bại - thực hiện kết nối trực tiếp để phân tích chi tiết lỗi
                
                # Kết nối trực tiếp đến LDAP để phân tích chi tiết lỗi
                try:
                    # Khởi tạo kết nối LDAP
                    ldap_conn = ldap.initialize(settings.AUTH_LDAP_SERVER_URI)
                    
                    # Bước 1: Bind với tài khoản service để tìm DN của user
                    try:
                        ldap_conn.simple_bind_s(settings.AUTH_LDAP_BIND_DN, settings.AUTH_LDAP_BIND_PASSWORD)
                    except ldap.SERVER_DOWN:
                        messages.error(request, 'Không thể kết nối đến máy chủ LDAP. Vui lòng thử lại sau hoặc liên hệ IT.')
                        log_entry.error_message = 'Máy chủ LDAP không khả dụng'
                        log_entry.error_code = 'SERVER_DOWN'
                        log_entry.save()
                        return render(request, 'authentication/login.html', {'form': form})
                    except ldap.INVALID_CREDENTIALS:
                        messages.error(request, 'Tài khoản service LDAP không hợp lệ. Vui lòng liên hệ IT.')
                        log_entry.error_message = 'Tài khoản service không hợp lệ'
                        log_entry.error_code = 'SERVICE_ACCOUNT_INVALID'
                        log_entry.save()
                        return render(request, 'authentication/login.html', {'form': form})
                    
                    # Bước 2: Tìm kiếm DN của user
                    search_filter = f"(sAMAccountName={username})"
                    base_dn = "OU=USERS,OU=HO,OU=HANOI,DC=ttgroup,DC=com,DC=vn"
                    
                    try:
                        result = ldap_conn.search_s(base_dn, ldap.SCOPE_SUBTREE, search_filter, ['cn'])
                    except ldap.NO_SUCH_OBJECT:
                        messages.error(request, 'Đường dẫn LDAP không hợp lệ. Vui lòng liên hệ IT.')
                        log_entry.error_message = 'Base DN không tồn tại'
                        log_entry.error_code = 'NO_SUCH_OBJECT'
                        log_entry.save()
                        return render(request, 'authentication/login.html', {'form': form})
                    
                    if not result:
                        messages.error(request, 'Tài khoản không tồn tại trong hệ thống.')
                        log_entry.error_message = 'Tài khoản không tồn tại'
                        log_entry.error_code = 'USER_NOT_FOUND'
                        log_entry.save()
                        return render(request, 'authentication/login.html', {'form': form})
                    
                    # Bước 3: Thử bind với tài khoản người dùng để phát hiện lỗi chính xác
                    user_dn = result[0][0]
                    ldap_conn = ldap.initialize(settings.AUTH_LDAP_SERVER_URI)  # Khởi tạo kết nối mới
                    
                    try:
                        ldap_conn.simple_bind_s(user_dn, password)
                        # Nếu tới đây nghĩa là bind thành công, nhưng authenticate() thất bại vì lý do khác
                        messages.error(request, 'Tài khoản không có quyền truy cập ứng dụng này.')
                        log_entry.error_message = 'Không có quyền truy cập'
                        log_entry.error_code = 'ACCESS_DENIED'
                    except ldap.INVALID_CREDENTIALS:
                        # Phân tích chi tiết mã lỗi để xác định loại lỗi cụ thể hơn
                        try:
                            conn = ldap.initialize(settings.AUTH_LDAP_SERVER_URI)
                            conn.set_option(ldap.OPT_REFERRALS, 0)
                            result = conn.simple_bind_s(user_dn, "wrong_password_to_check_error_code")
                        except ldap.INVALID_CREDENTIALS as e:
                            error_str = str(e)
                            
                            # Phân tích mã lỗi chi tiết
                            if "data 532" in error_str or "PASSWORD_EXPIRED" in error_str:
                                messages.error(request, 'Mật khẩu của bạn đã hết hạn. Vui lòng đổi mật khẩu mới.')
                                log_entry.error_message = 'Mật khẩu hết hạn'
                                log_entry.error_code = 'PASSWORD_EXPIRED'
                            elif "data 533" in error_str or "ACCOUNT_DISABLED" in error_str:
                                messages.error(request, 'Tài khoản của bạn đã bị vô hiệu hóa. Vui lòng liên hệ quản trị viên.')
                                log_entry.error_message = 'Tài khoản bị vô hiệu hóa'
                                log_entry.error_code = 'ACCOUNT_DISABLED'
                            elif "data 775" in error_str or "ACCOUNT_LOCKED" in error_str:
                                messages.error(request, 'Tài khoản của bạn đã bị khóa do đăng nhập sai nhiều lần. Vui lòng liên hệ quản trị viên.')
                                log_entry.error_message = 'Tài khoản bị khóa'
                                log_entry.error_code = 'ACCOUNT_LOCKED'
                            elif "data 701" in error_str or "ACCOUNT_EXPIRED" in error_str:
                                messages.error(request, 'Tài khoản của bạn đã hết hạn. Vui lòng liên hệ quản trị viên.')
                                log_entry.error_message = 'Tài khoản hết hạn'
                                log_entry.error_code = 'ACCOUNT_EXPIRED'
                            else:
                                messages.error(request, 'Tên đăng nhập hoặc mật khẩu không đúng.')
                                log_entry.error_message = 'Thông tin đăng nhập không hợp lệ'
                                log_entry.error_code = 'INVALID_CREDENTIALS'
                        except Exception:
                            # Nếu không lấy được mã lỗi chi tiết, hiển thị thông báo chung
                            messages.error(request, 'Tên đăng nhập hoặc mật khẩu không đúng.')
                            log_entry.error_message = 'Thông tin đăng nhập không hợp lệ'
                            log_entry.error_code = 'INVALID_CREDENTIALS'
                    except ldap.UNWILLING_TO_PERFORM:
                        messages.error(request, 'Máy chủ LDAP từ chối thực hiện thao tác. Có thể cần đổi mật khẩu.')
                        log_entry.error_message = 'Máy chủ từ chối thực hiện'
                        log_entry.error_code = 'UNWILLING_TO_PERFORM'
                    except ldap.PASSWORD_EXPIRED:
                        messages.error(request, 'Mật khẩu của bạn đã hết hạn. Vui lòng đổi mật khẩu mới.')
                        log_entry.error_message = 'Mật khẩu hết hạn'
                        log_entry.error_code = 'PASSWORD_EXPIRED'
                    except ldap.ACCOUNT_EXPIRED:
                        messages.error(request, 'Tài khoản của bạn đã hết hạn. Vui lòng liên hệ quản trị viên.')
                        log_entry.error_message = 'Tài khoản hết hạn'
                        log_entry.error_code = 'ACCOUNT_EXPIRED'
                    except ldap.TIMEOUT:
                        messages.error(request, 'Kết nối đến máy chủ LDAP bị hết thời gian chờ. Vui lòng thử lại sau.')
                        log_entry.error_message = 'Hết thời gian chờ kết nối'
                        log_entry.error_code = 'TIMEOUT'
                    except Exception as e:
                        messages.error(request, f'Lỗi khi xác thực: {str(e)}')
                        log_entry.error_message = f'Lỗi khác: {str(e)}'
                        log_entry.error_code = 'OTHER'
                except Exception as e:
                    messages.error(request, f'Lỗi kết nối LDAP: {str(e)}')
                    log_entry.error_message = f'Lỗi kết nối: {str(e)}'
                    log_entry.error_code = 'CONNECTION_ERROR'
                
                log_entry.save()
        except Exception as e:
            messages.error(request, f'Lỗi hệ thống: {str(e)}')
            log_entry.error_message = f'Lỗi hệ thống: {str(e)}'
            log_entry.error_code = 'SYSTEM_ERROR'
            log_entry.save()
    else:
        form = LDAPLoginForm()
    
    return render(request, 'authentication/login.html', {'form': form})

@login_required
def home_view(request):
    """Trang chính sau khi đăng nhập thành công hiển thị thông tin đầy đủ"""
    # Lấy thông tin profile của người dùng
    try:
        profile = request.user.profile
    except UserProfile.DoesNotExist:
        # Nếu chưa có profile, tạo mới
        profile = UserProfile.objects.create(user=request.user)
    
    context = {
        'user': request.user,
        'profile': profile
    }
    
    return render(request, 'authentication/home.html', context)

def logout_view(request):
    """Xử lý đăng xuất"""
    logout(request)
    messages.info(request, 'Bạn đã đăng xuất thành công.')
    return redirect('login')

def error_simulation_view(request):
    """Trang mô phỏng các lỗi LDAP khác nhau để kiểm tra"""
    return render(request, 'authentication/error_messages.html')