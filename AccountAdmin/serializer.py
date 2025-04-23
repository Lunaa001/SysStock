from rest_framework import serializers
from AccountAdmin.models import User  # Importa User desde AccountAdmin

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = '__all__'
