from rest_framework import serializers
from AccountAdmin.models import User  # Importa User desde AccountAdmin

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = '__all__'
        extra_kwargs = {
            'password': {'write_only': True}  # oculta el password en la respuesta
        }

    def create(self, validated_data):
        # Usamos pop para sacar el password y pasarlo a set_password()
        password = validated_data.pop('password', None)
        user = User(**validated_data)
        if password:
            user.set_password(password)
        user.save()
        return user
