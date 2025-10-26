from django.db import models

class StaffID(models.Model):
    ROLE_CHOICES = [
        ("doctor", "Doctor"),
        ("reception", "Reception"),
        ("pharmacy", "Pharmacy"),
    ]

    staff_login_id = models.CharField(max_length=50, unique=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)

    def __str__(self):
        return f"{self.staff_login_id} ({self.role})"
