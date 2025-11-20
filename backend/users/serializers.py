from rest_framework import serializers
from django.contrib.auth import get_user_model,authenticate
from django.contrib.auth.password_validation import validate_password
from django.utils.translation import gettext_lazy as _
from .models import CustomUser

class UserRegistrationSerializer(serializers.ModelSerializer):
     password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
     password2 = serializers.CharField(write_only=True, required=True)

     class Meta:
          model = CustomUser
          fields = ['firstname', 'lastname', 'email', 'date_of_birth', 'password', 'password2']
          extra_kwargs = {
               'password': {'write_only': True},
               'password2': {'write_only': True},
          }

     def validate(self, attrs):
          if attrs['password'] != attrs['password2']:
               raise serializers.ValidationError({"password": "Password fileds didn't match"})
          return attrs
          
     def validate_email(self, value):
          if CustomUser.objects.filter(email=value).exists():
               raise serializers.ValidationError("Email already in use")
          return value
          
     def create(self, validated_data):
          validated_data.pop('password2')
          user = CustomUser.objects.create_user(**validated_data)

class UserLoginSerializer(serializers.ModelSerializer):
     email = serializers.EmailField(required=True)
     password = serializers.CharField(write_only=True, required=True)
     class Meta:
          model = CustomUser
          fields = ['email', 'password']

     def validate(self, attrs):
          email = attrs.get('email')
          password = attrs.get('password')
          
          if email and password:
               user = authenticate(request=self.context.get('request'), email=email, password=password)
               if not user:
                    msg = _('Credential Provided are Invalid')
                    raise serializers.ValidationError(msg, code ='authorization')
          else:
               msg = _('Provide both email and password')
               raise serializers.ValidationError(msg, code='authorization')
          attrs['user'] = user
          return attrs
     
class UserProfileSerializer(serializers.ModelSerializer):
     full_name = serializers.SerializerMethodField()

     class Meta:
          model = CustomUser
          fields = ['id', 'first_name', 'last_name', 'full_name', 'email', 'date_of_birth', 'date_joined', 'last_login']
          read_only_fields = ['id', 'date_joined', 'last_login']

     def get_full_name(self, obj):
          return f"{obj.first_name} {obj.last_name}"
          
class ChangePasswordSerializer(serializers.Serializer):
     old_password = serializers.CharField(write_only=True, required=True)
     new_password = serializers.CharField(write_only=True, required=True, validators = [validate_password])
     new_password2 = serializers.CharField(write_only=True, required=True)

     def validate_old_password(self, value):
          user = self.context['request'].user
          if not user.check_password(value):
               raise serializers.ValidationError("Old Password is not correct")
          return value
     
     def validate(self, attrs):
          if attrs['new_password'] != attrs['new_password2']:
               raise serializers.ValidationError({"new_password": "Password fields didn't match."})
          return attrs
     
     def save(self, **kwargs):
          user = self.context['request'].user
          user.set_password(self.validated_data['new_password'])
          user.save()
          return user
     