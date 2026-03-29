from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm

from accounts.models import CustomUser


class AppLoginForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault("class", "form-control")


class SignupForm(UserCreationForm):
    full_name = forms.CharField(
        max_length=255,
        required=True,
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )

    class Meta:
        model = CustomUser
        fields = ("email", "full_name", "password1", "password2")
        widgets = {
            "email": forms.EmailInput(attrs={"class": "form-control"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name in ("password1", "password2"):
            self.fields[name].widget.attrs.setdefault("class", "form-control")

    def save(self, commit=True):
        user = super().save(commit=False)
        user.full_name = self.cleaned_data["full_name"]
        user.role = "user"
        if commit:
            user.save()
        return user
