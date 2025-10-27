from django.contrib.auth import get_user_model
from rest_framework import serializers
from SysstockApp.models import Branch

User = get_user_model()

# --------------------------
# 1) REGISTER PÚBLICO (ADMIN INICIAL) con body.company anidado
# --------------------------
class RegisterSerializer(serializers.ModelSerializer):
  
    password2 = serializers.CharField(write_only=True)
    company = serializers.DictField(child=serializers.CharField(allow_blank=True), write_only=True)

    class Meta:
        model = User
        fields = ["username", "email", "password", "password2", "company"]
        extra_kwargs = {
            "password": {"write_only": True},
            "email": {"required": True}
        }

    def validate(self, attrs):
        if attrs["password"] != attrs["password2"]:
            raise serializers.ValidationError({"password": "Las contraseñas no coinciden."})

        if User.objects.filter(username=attrs["username"]).exists():
            raise serializers.ValidationError({"username": "Ya existe un usuario con ese username."})
        if User.objects.filter(email=attrs["email"]).exists():
            raise serializers.ValidationError({"email": "Ya existe un usuario con ese email."})

        comp = attrs.get("company") or {}
        if not comp.get("name"):
            raise serializers.ValidationError({"company.name": "El nombre de la empresa es obligatorio."})
        return attrs

    def create(self, validated_data):
        company = validated_data.pop("company", {}) or {}
        password = validated_data.pop("password")
        validated_data.pop("password2", None)

        # Crear usuario con create_user (esto ya hashea el password)
        user = User.objects.create_user(password=password, **validated_data)

        # Rol admin para el que se registra por publico
        if hasattr(user, "rol"):
            user.rol = "admin"

        # Mapear campos de company si existen en el modelo
        mapping = {
            "company_name": company.get("name"),
            "phone": company.get("phone"),
            "address": company.get("address"),
        }
        for field, value in mapping.items():
            if value is not None and hasattr(user, field):
                setattr(user, field, value)

        user.save()
        return user


# --------------------------
# 2) SOLO LECTURA (listar/detallar)
# --------------------------
class AdminUserReadSerializer(serializers.ModelSerializer):
    sucursal = serializers.SerializerMethodField()

    class Meta:
        model = User
        # Sacamos first_name y last_name tal como pediste
        fields = ["id", "username", "email", "rol", "is_active", "sucursal"]

    def get_sucursal(self, obj):
        branch = getattr(obj, "sucursal", None)  # tu FK se llama 'sucursal'
        if branch:
            return {"id": branch.id, "name": getattr(branch, "name", None)}
        return None


# --------------------------
# 3) CREAR EMPLEADO (limMerchant) por ADMIN
# --------------------------
class AdminCreateUserSerializer(serializers.ModelSerializer):
    password2 = serializers.CharField(write_only=True)
    sucursal_id = serializers.IntegerField(write_only=True, required=True)

    # Hacemos nombres opcionales (si vienen, se guardan; si no, no pasa nada)
    first_name = serializers.CharField(required=False, allow_blank=True)
    last_name  = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = User
        fields = [
            "username", "email",
            "password", "password2",
            "sucursal_id",
            "first_name", "last_name",   # opcionales
        ]
        extra_kwargs = {"password": {"write_only": True}}

    def validate(self, attrs):
        request = self.context.get("request")
        admin = getattr(request, "user", None)
        if not admin or getattr(admin, "rol", None) != "admin":
            raise serializers.ValidationError({"detail": "Solo un admin puede crear empleados."})

        if attrs["password"] != attrs["password2"]:
            raise serializers.ValidationError({"password": "Las contraseñas no coinciden."})

        if User.objects.filter(username=attrs["username"]).exists():
            raise serializers.ValidationError({"username": "Ya existe un usuario con ese username."})
        if User.objects.filter(email=attrs["email"]).exists():
            raise serializers.ValidationError({"email": "Ya existe un usuario con ese email."})

        try:
            branch = Branch.objects.get(pk=attrs["sucursal_id"])
        except Branch.DoesNotExist:
            raise serializers.ValidationError({"sucursal_id": "Sucursal inexistente."})

        if branch.owner_id != admin.id and not getattr(admin, "is_superuser", False):
            raise serializers.ValidationError({"sucursal_id": "No puedes asignar sucursales de otro admin."})

        attrs["_branch_obj"] = branch
        return attrs

    def create(self, validated_data):
        validated_data.pop("password2", None)
        branch = validated_data.pop("_branch_obj")
        password = validated_data.pop("password")
        validated_data.pop("sucursal_id", None)

        # create_user ya hashea el password
        user = User.objects.create_user(password=password, **validated_data)

        if hasattr(user, "rol"):
            user.rol = "limMerchant"
        if hasattr(user, "sucursal"):
            user.sucursal = branch

        user.save()
        return user

# --------------------------
# 4) TRANSFERIR SUCURSAL (solo admin)
# --------------------------
class ChangeUserBranchSerializer(serializers.Serializer):
    sucursal_id = serializers.IntegerField()

    def validate(self, attrs):
        request = self.context.get("request")
        admin = getattr(request, "user", None)
        if not admin or getattr(admin, "rol", None) != "admin":
            raise serializers.ValidationError({"detail": "Solo un admin puede transferir usuarios."})

        sid = attrs.get("sucursal_id")
        try:
            branch = Branch.objects.get(pk=sid)
        except Branch.DoesNotExist:
            raise serializers.ValidationError({"sucursal_id": "Sucursal inexistente."})

        if branch.owner_id != admin.id and not getattr(admin, "is_superuser", False):
            raise serializers.ValidationError({"sucursal_id": "No puedes asignar sucursales de otro admin."})

        attrs["_branch_obj"] = branch
        return attrs
