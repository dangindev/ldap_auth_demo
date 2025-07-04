# Generated by Django 5.0.1 on 2025-05-20 02:25

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="LDAPLoginLog",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("username", models.CharField(max_length=255)),
                ("timestamp", models.DateTimeField(auto_now_add=True)),
                ("success", models.BooleanField(default=False)),
                ("error_message", models.TextField(blank=True, null=True)),
                ("error_code", models.CharField(blank=True, max_length=50, null=True)),
            ],
        ),
        migrations.CreateModel(
            name="UserProfile",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "employee_id",
                    models.CharField(
                        blank=True,
                        max_length=50,
                        null=True,
                        verbose_name="Mã nhân viên",
                    ),
                ),
                (
                    "title",
                    models.CharField(
                        blank=True, max_length=100, null=True, verbose_name="Chức danh"
                    ),
                ),
                (
                    "mobile",
                    models.CharField(
                        blank=True,
                        max_length=20,
                        null=True,
                        verbose_name="Số điện thoại",
                    ),
                ),
                (
                    "manager",
                    models.CharField(
                        blank=True, max_length=255, null=True, verbose_name="Quản lý"
                    ),
                ),
                (
                    "department",
                    models.CharField(
                        blank=True, max_length=255, null=True, verbose_name="Phòng ban"
                    ),
                ),
                (
                    "last_ldap_sync",
                    models.DateTimeField(
                        auto_now=True, verbose_name="Lần đồng bộ cuối"
                    ),
                ),
                (
                    "user",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="profile",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
        ),
    ]
