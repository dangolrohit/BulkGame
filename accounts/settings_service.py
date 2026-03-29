from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.db import transaction

from accounts.models import CustomUser, UserProfile


def process_account_settings_post(request, user) -> list[tuple[str, str]]:
    """
    Validate POST and update full_name / password. Email and phone are not editable;
    crafted POST attempts are rejected with specific messages.

    Returns a list of (level, message) where level is "success" or "error".
    On validation errors, nothing is saved.
    """
    post = request.POST
    profile = user.profile
    errors: list[tuple[str, str]] = []

    full_name = post.get("full_name", "").strip()
    if not full_name:
        errors.append(("error", "Full name is required."))

    if "email" in post:
        raw = (post.get("email") or "").strip()
        if raw:
            norm = CustomUser.objects.normalize_email(raw)
            if norm.lower() != user.email.lower():
                if CustomUser.objects.filter(email__iexact=norm).exclude(pk=user.pk).exists():
                    errors.append(("error", "Email already exists."))
                else:
                    errors.append(("error", "Email cannot be changed."))

    if "phone" in post:
        raw = (post.get("phone") or "").strip()
        current = profile.phone or ""
        if raw != current:
            if raw and UserProfile.objects.filter(phone=raw).exclude(user=user).exists():
                errors.append(("error", "Phone number already exists."))
            else:
                errors.append(("error", "Phone number cannot be changed."))

    pw1 = (post.get("new_password") or "").strip()
    pw2 = (post.get("confirm_password") or "").strip()
    changing_pw = bool(pw1 or pw2)
    if changing_pw:
        if pw1 != pw2:
            errors.append(("error", "Passwords do not match."))
        else:
            try:
                validate_password(pw1, user)
            except ValidationError as e:
                for msg in e.messages:
                    errors.append(("error", msg))

    if errors:
        return errors

    with transaction.atomic():
        user.full_name = full_name
        update_fields = ["full_name"]
        if changing_pw:
            user.set_password(pw1)
            update_fields.append("password")
        user.save(update_fields=update_fields)

    if changing_pw:
        update_session_auth_hash(request, user)

    return [("success", "Settings saved.")]


def flash_settings_messages(request, tuples: list[tuple[str, str]]) -> None:
    from django.contrib import messages

    for level, msg in tuples:
        if level == "success":
            messages.success(request, msg)
        elif level == "warning":
            messages.warning(request, msg)
        else:
            messages.error(request, msg)
