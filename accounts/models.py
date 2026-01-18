from django.db import models

class StaffID(models.Model):
    ROLE_CHOICES = [
        ("doctor", "Doctor"),
        ("reception", "Reception"),
        ("pharmacy", "Pharmacy"),
    ]

    staff_login_id = models.CharField(max_length=50, unique=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    password = models.CharField(max_length=100, default="1234", help_text="Password for sidebar menu access")

    def __str__(self):
        return f"{self.staff_login_id} ({self.role})"
