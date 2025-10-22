# AccountAdmin/serializers.py
from rest_framework import serializers
from django.contrib.auth import get_user_model
from SysstockApp.models import Branch

User = get_user_model()

class SucursalInlineSerializer(serializers.Serializer):
    nombre = serializers.CharField(required=True)
    direccion = serializers.CharField(required=False, allow_blank=True)

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True)
    password2 = serializers.CharField(write_only=True, required=True)
    # sucursal anidada: se crea en paralelo
    sucursal = SucursalInlineSerializer(write_only=True)

    class Meta:
        model = User
        fields = ["username", "email", "password", "password2", "sucursal"]
        extra_kwargs = {"email": {"required": True}}

    def validate(self, attrs):
        if attrs["password"] != attrs["password2"]:
            raise serializers.ValidationError({"password": "Las contraseñas no coinciden."})
        return attrs

    def create(self, validated_data):
        # 1) separar sucursal
        sucursal_data = validated_data.pop("sucursal")
        password2 = validated_data.pop("password2")

        nombre = sucursal_data.get("nombre")
        direccion = sucursal_data.get("direccion", "")

        # 2) crear / obtener sucursal
        # Solo usamos "name"; si Branch tiene address lo guardamos, si no lo ignoramos
        branch, created = Branch.objects.get_or_create(name=nombre)
        # intentar setear address si existe en el modelo
        if direccion and hasattr(branch, "address"):
            branch.address = direccion
            branch.save()

        # 3) crear usuario con rol admin y sucursal asignada
        user = User.objects.create_user(
            **validated_data,
        )
        user.rol = getattr(User, "ADMIN", "admin")  # por defecto admin
        user.sucursal = branch
        user.set_password(validated_data["password"])
        user.save()
        return user


class AdminCreateUserSerializer(serializers.ModelSerializer):
    """
    Serializer para que un ADMIN cree empleados (o más admins) dentro de su empresa.
    Si no envían sucursal explícita, se asigna la del admin por defecto.
    """
    password = serializers.CharField(write_only=True, required=True)
    sucursal_id = serializers.IntegerField(required=False)  # opcional: asignar sucursal por id
    rol = serializers.ChoiceField(
        choices=[("admin", "Administrador"), ("limMerchant", "Limmerchant")],
        default="limMerchant"
    )

    class Meta:
        model = User
        fields = ["username", "email", "password", "rol", "sucursal_id"]

    # AccountAdmin/serializers.py (solo el método create)
    def create(self, validated_data):
        sucursal_data = validated_data.pop("sucursal")
        validated_data.pop("password2")

        nombre = sucursal_data.get("nombre")
        direccion = sucursal_data.get("direccion", "")

        branch, created = Branch.objects.get_or_create(name=nombre)
        if direccion and hasattr(branch, "address"):
            branch.address = direccion
            branch.save()

        # PASA sucursal y rol DENTRO de create_user (primer INSERT ya con valores)
        user = User.objects.create_user(
            **validated_data,              # username, email, password
            sucursal=branch,
            rol=getattr(User, "ADMIN", "admin")
        )
        return user
