from rest_framework import serializers
from .models import User
from random import randint


from rest_framework import serializers
from django.core.validators import RegexValidator
from .models import User
import random

class SendCodeSerializer(serializers.Serializer):
    phone_regex = RegexValidator(regex=r'^\+?1?\d{9,14}$', message="Invalid phone number format.")
    phone = serializers.CharField(validators=[phone_regex], max_length=17)

    def validate_phone(self, value):
        """Check if the phone number exists and generate a verification code."""
        user, created = User.objects.get_or_create(phone=value, defaults={'is_active': False})
        verification_code = random.randint(100000, 999999)  
        user.verification_code = verification_code
        user.is_active = False
        user.save()

        
        print(f"Verification Code: {verification_code}") 

        return value

class VerifyCodeSerializer(serializers.Serializer):
    phone = serializers.CharField(max_length=17)
    code = serializers.IntegerField()

    def validate(self, data):
        """Check if the code matches the stored code."""
        phone = data.get("phone")
        code = data.get("code")

        try:
            user = User.objects.get(phone=phone)
        except User.DoesNotExist:
            raise serializers.ValidationError({"phone": "Phone number not found."})

        if str(user.verification_code) != str(code):
            raise serializers.ValidationError({"code": "Invalid verification code."})

        user.is_active = True
        user.verification_code = None 
        user.save()
        return data
