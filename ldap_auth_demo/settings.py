import os
import ldap
from django.contrib.messages import constants as messages
from django_auth_ldap.config import LDAPSearch, ActiveDirectoryGroupType
from dotenv import load_dotenv

load_dotenv()  # Đọc biến môi trường từ file .env

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# SECURITY WARNING: giữ secret key bí mật trong môi trường production
SECRET_KEY = 'django-insecure-ldap-demo-key-change-this-in-production'

# SECURITY WARNING: tắt debug trong môi trường production
DEBUG = True

ALLOWED_HOSTS = []

# Cấu hình ứng dụng
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'authentication',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'ldap_auth_demo.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'ldap_auth_demo.wsgi.application'

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}

# Cấu hình LDAP với thông tin đã cung cấp
ldap_host = os.getenv('LDAP_HOST')
ldap_port = int(os.getenv('LDAP_PORT', 389))
ldap_base_dn = os.getenv('LDAP_BASE_DN')
ldap_bind_dn = os.getenv('LDAP_BIND_DN')
ldap_bind_password = os.getenv('LDAP_BIND_PASSWORD')

# Tài khoản Bind để truy cập LDAP
AUTH_LDAP_BIND_DN = ldap_bind_dn
AUTH_LDAP_BIND_PASSWORD = ldap_bind_password

# Tìm kiếm người dùng - dựa vào sAMAccountName
AUTH_LDAP_USER_SEARCH = LDAPSearch(
    ldap_base_dn,
    ldap.SCOPE_SUBTREE,
    "(sAMAccountName=%(user)s)"
)

# Ánh xạ thuộc tính LDAP với Django user
AUTH_LDAP_USER_ATTR_MAP = {
    "username": "sAMAccountName",
    "first_name": "givenName",
    "last_name": "sn",
    "email": "mail",
}

# Các tùy chọn phân tích lỗi chi tiết của LDAP
AUTH_LDAP_CONNECTION_OPTIONS = {
    ldap.OPT_REFERRALS: 0,  # Tắt referrals để có thể phân tích lỗi tốt hơn
    ldap.OPT_X_TLS_REQUIRE_CERT: ldap.OPT_X_TLS_NEVER,  # Tùy chọn TLS nếu cần
    ldap.OPT_DEBUG_LEVEL: 255,  # Bật debug chi tiết
    ldap.OPT_NETWORK_TIMEOUT: 10,  # Timeout 10 giây
}

# Các thiết lập bổ sung cho django-auth-ldap
AUTH_LDAP_FIND_GROUP_PERMS = False  # Tắt tìm kiếm quyền của nhóm để tăng tốc độ
AUTH_LDAP_CACHE_TIMEOUT = 3600  # Cache LDAP 1 giờ
AUTH_LDAP_ALWAYS_UPDATE_USER = True  # Luôn cập nhật thông tin người dùng

# Các thuộc tính bổ sung muốn lấy từ LDAP
AUTH_LDAP_USER_FLAGS_BY_GROUP = {}

# Lấy thêm thuộc tính từ LDAP
AUTH_LDAP_PROFILE_ATTR_MAP = {
    "employee_id": "employeeID",  
    "title": "title",
    "mobile": "mobile",
    "manager": "manager"
}

# Cấu hình nhóm LDAP (nếu cần)
AUTH_LDAP_GROUP_SEARCH = LDAPSearch(
    "OU=GROUPS,DC=ttgroup,DC=com,DC=vn",  # Thay đổi đường dẫn nếu cần
    ldap.SCOPE_SUBTREE,
    "(objectClass=group)"
)
AUTH_LDAP_GROUP_TYPE = ActiveDirectoryGroupType()

# Các thiết lập LDAP bổ sung
# Kích hoạt log cho việc debug
import logging
logger = logging.getLogger('django_auth_ldap')
logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.DEBUG)

# Cấu hình xác thực
AUTHENTICATION_BACKENDS = [
    'django_auth_ldap.backend.LDAPBackend',
    'django.contrib.auth.backends.ModelBackend',
]

# Cấu hình đăng nhập/đăng xuất
LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/home/'
LOGOUT_REDIRECT_URL = '/login/'

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
LANGUAGE_CODE = 'vi'
TIME_ZONE = 'Asia/Ho_Chi_Minh'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static'),
]

# Cấu hình messages
MESSAGE_TAGS = {
    messages.DEBUG: 'alert-secondary',
    messages.INFO: 'alert-info',
    messages.SUCCESS: 'alert-success',
    messages.WARNING: 'alert-warning',
    messages.ERROR: 'alert-danger',
}

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'