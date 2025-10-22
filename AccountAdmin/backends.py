# AccountAdmin/backends.py
from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model
from django.db.models import Q

class EmailOrUsernameModelBackend(ModelBackend):
    """
    Permite autenticar con username O email usando el mismo campo 'username' del payload.
    Compatible con TokenObtainPairView (SimpleJWT).
    """
    def authenticate(self, request, username=None, password=None, **kwargs):
        User = get_user_model()

        # Si SimpleJWT envía el nombre del campo USERNAME_FIELD distinto, tomalo de kwargs
        if username is None:
            username = kwargs.get(User.USERNAME_FIELD)

        if not username or not password:
            return None

        try:
            # Busca por username O email
            user = User.objects.get(Q(username=username) | Q(email=username))
        except User.DoesNotExist:
            return None

        if user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None
