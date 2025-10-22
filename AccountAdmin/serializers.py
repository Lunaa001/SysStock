from rest_framework import serializers
from django.contrib.auth import get_user_model
from SysstockApp.models import Branch

User = get_user_model()


# —— Campo anidado para el registro (solo escritura) ——
class SucursalInlineSerializer(serializers.Serializer):
    nombre = serializers.CharField(required=True)
    direccion = serializers.CharField(required=False, allow_blank=True, default="")


# —— REGISTRO: crea admin + sucursal inicial (owner = user) ——
class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True)
    # <- ¡Importante! anidado y SOLO escritura
    sucursal = SucursalInlineSerializer(write_only=True, required=True)

    class Meta:
        model = User
        fields = ["username", "email", "password", "sucursal"]
        extra_kwargs = {
            "email": {"required": True},
        }

    def create(self, validated_data):
        # 1) Sacar los datos anidados antes de crear el user
        sucursal_data = validated_data.pop("sucursal", None)
        if not sucursal_data:
            raise serializers.ValidationError({"sucursal": "Este campo es obligatorio."})

        # 2) Crear usuario como ADMIN (dueño)
        #    create_user ya hace el set_password interno
        user = User.objects.create_user(
            rol="admin",
            **validated_data,
        )

        # 3) Crear sucursal del usuario (aislada por owner)
        branch = Branch.objects.create(
            name=sucursal_data["nombre"],
            address=sucursal_data.get("direccion", ""),
            owner=user,
        )

        # 4) Asociar sucursal al usuario (si tu modelo la tiene)
        user.sucursal = branch
        user.save(update_fields=["sucursal"])

        return user


# —— ADMIN crea empleados (limMerchant) dentro de su empresa/sucursal ——
class AdminCreateUserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True)
    sucursal_id = serializers.IntegerField(required=True)

    class Meta:
        model = User
        fields = ["username", "email", "password", "rol", "sucursal_id"]
        extra_kwargs = {
            "email": {"required": True},
        }

    def create(self, validated_data):
        request = self.context["request"]          # admin autenticado
        admin_user = request.user

        # validar sucursal del admin
        try:
            branch = Branch.objects.get(
                id=validated_data["sucursal_id"],
                owner=admin_user
            )
        except Branch.DoesNotExist:
            raise serializers.ValidationError(
                {"sucursal_id": "La sucursal no te pertenece o no existe."}
            )

        # rol por defecto si no viene: limMerchant
        rol = validated_data.get("rol") or "limMerchant"

        # crear empleado (usuario normal ligado a sucursal)
        user = User.objects.create_user(
            username=validated_data["username"],
            email=validated_data["email"],
            password=validated_data["password"],
            rol=rol,
            sucursal=branch,
        )
        return user

User = get_user_model()

class ReassignBranchSerializer(serializers.Serializer):
    user_id = serializers.IntegerField()
    new_sucursal_id = serializers.IntegerField()

    def validate(self, attrs):
        request = self.context["request"]
        admin_user = request.user

        # Solo admin
        if getattr(admin_user, "rol", None) != "admin":
            raise serializers.ValidationError({"detail": "Solo el admin puede reasignar usuarios."})

        # Validar usuario destino
        try:
            target_user = User.objects.get(id=attrs["user_id"])
        except User.DoesNotExist:
            raise serializers.ValidationError({"user_id": "Usuario no encontrado."})

        if target_user.rol != "limMerchant":
            raise serializers.ValidationError({"user_id": "Solo se pueden reasignar limMerchant."})

        # Validar nueva sucursal (debe pertenecer al admin)
        try:
            new_branch = Branch.objects.get(id=attrs["new_sucursal_id"], owner=admin_user)
        except Branch.DoesNotExist:
            raise serializers.ValidationError({"new_sucursal_id": "La sucursal no existe o no te pertenece."})

        attrs["target_user"] = target_user
        attrs["new_branch"] = new_branch
        return attrs

    def save(self, **kwargs):
        target_user = self.validated_data["target_user"]
        new_branch = self.validated_data["new_branch"]
        target_user.sucursal = new_branch
        target_user.save(update_fields=["sucursal"])
        return target_user

User = get_user_model()

class WorkerSerializer(serializers.ModelSerializer):
    sucursal_name = serializers.CharField(source="sucursal.name", read_only=True)

    class Meta:
        model = User
        fields = ["id", "username", "email", "rol", "sucursal_id", "sucursal_name"]