from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction

User = get_user_model()

class PublicRegisterSerializer(serializers.ModelSerializer):
    """
    Registro público: solo email y password.
    username = email, rol = limMerchant, sucursal=""
    """
    email = serializers.EmailField(required=True)
    password = serializers.CharField(write_only=True, min_length=4)

    class Meta:
        model = User
        fields = ["email", "password"]

    def validate_email(self, value):
        # normalizamos y chequeamos existencia previa
        email = value.strip().lower()
        if User.objects.filter(username__iexact=email).exists() or User.objects.filter(email__iexact=email).exists():
            raise serializers.ValidationError("Este email ya está registrado.")
        return email

    def create(self, validated_data):
        email = validated_data["email"].strip().lower()
        password = validated_data["password"]

        user = User(
            username=email,
            email=email,
            rol="limMerchant",
            sucursal="",  # si tu modelo usa CharField, lo dejamos vacío
        )
        user.set_password(password)

        try:
            with transaction.atomic():
                user.save()
        except IntegrityError:
            # por si hay condición de carrera o datos inconsistentes
            raise serializers.ValidationError({"email": "Este email ya está registrado."})

        return user


class AdminCreateUserSerializer(serializers.ModelSerializer):
    """
    Creación por admin: username, email, password; opcionales rol y sucursal (texto).
    Si no se envía rol, queda limMerchant por defecto.
    """
    email = serializers.EmailField(required=True)
    password = serializers.CharField(write_only=True)
    rol = serializers.CharField(required=False)
    sucursal = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = User
        fields = ["username", "email", "password", "rol", "sucursal"]

    def validate_rol(self, value):
        if value and value not in ROL_CHOICES:
            raise serializers.ValidationError(f"Rol inválido. Use uno de: {', '.join(sorted(ROL_CHOICES))}")
        return value

    def create(self, validated_data):
        password = validated_data.pop("password")
        rol = validated_data.pop("rol", "limMerchant") or "limMerchant"
        sucursal = validated_data.pop("sucursal", "") or ""
        user = User(**validated_data, rol=rol, sucursal=sucursal)
        user.set_password(password)
        user.save()
        return user
