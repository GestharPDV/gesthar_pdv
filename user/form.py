from django.contrib.auth.forms import UserChangeForm
from .models import UserGesthar


class UserGestharChangeForm(UserChangeForm):
    password = None

    class Meta:
        model = UserGesthar
        fields = [
            "first_name",
            "last_name",
            "email",
            "cpf",
            "phone_number",
            "hire_date",
        ]
