from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Client, EmployeeClientDetails

User = get_user_model()

# ✅ Serializer for User Registration
class UserRegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ["id", "username", "email", "phone_number", "dob", "role", "password"]

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data["username"],
            email=validated_data["email"],
            phone_number=validated_data["phone_number"],
            dob=validated_data["dob"],
            role=validated_data["role"],
            password=validated_data["password"]
        )
        return user


# ✅ Serializer for User Login
class UserLoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    phone_number = serializers.CharField()
    dob = serializers.DateField()
    role = serializers.ChoiceField(choices=User.ROLE_CHOICES)
    password = serializers.CharField(write_only=True)


# ✅ Serializer for Viewing User Data
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "email", "role", "phone_number", "dob"]


# ✅ Serializer for Clients (Direct & Employee-Registered)
class ClientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Client
        fields = "__all__"


# ✅ Serializer for Employee-Registered Clients (Sensitive Data)
class EmployeeClientDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmployeeClientDetails
        fields = "__all__"
