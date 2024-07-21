from rest_framework import generics
from rest_framework.response import Response
from .serializers import RegistrationSerializer, CustomAuthTokenSerializer, CustomTokenObtainPairSerializer, ChangePasswordSerializer, ActivationResendSerializer
from django.contrib.auth.models import User
from rest_framework import status 
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.authtoken.models import Token
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.views import TokenObtainPairView
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from mail_templated import send_mail, EmailMessage
from ..utils import EmailThread
from rest_framework_simplejwt.tokens import RefreshToken
import jwt
from jwt.exceptions import ExpiredSignatureError, InvalidSignatureError
from django.conf import settings

# Registration
class RegistrationApiView(generics.GenericAPIView):
    serializer_class = RegistrationSerializer

    def post(self, request, *args, **kwargs):
        serializer = RegistrationSerializer(data= request.data)
        # checks if user's data is valid
        if serializer.is_valid():
            serializer.save()
            email = serializer.validated_data['email']
            username = serializer.validated_data['username']
            data = {
                'username' : username,
                'email' : email,

            }
            # create user object to make an jwt token after registration so it could be used for activation
            user_obj = get_object_or_404(User, email=email)
            token = self.get_tokens_for_user(user_obj)
            # sends a mail containing the activation token
            email_obj = EmailMessage('email/activation_email.tpl', {'token': token}, 'admin@admin.com', to=[email])
            EmailThread(email_obj).start()  
            return Response(data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    # make an jwt refresh token
    def get_tokens_for_user(self, user):
        refresh = RefreshToken.for_user(user)
        return str(refresh.access_token)
    
# Login
class CustomObtainAuthToken(ObtainAuthToken):
    serializer_class = CustomAuthTokenSerializer
    def post(self, request, *args, **kwargs): 
        serializer = self.serializer_class(data=request.data,
                                           context={'request': request})
        # checks if user's data is valid, and if not, it raises an error
        serializer.is_valid(raise_exception=True)
        # creates a token for the user
        user = serializer.validated_data['user']
        token, created = Token.objects.get_or_create(user=user)
        return Response({
            'token': token.key,
            'user_id': user.pk,
            'username': user.username
        })
    

class CustomDiscardAuthToken(APIView):
    permission_classes = [IsAuthenticated]

    def post (self, request, *args, **kwargs):
        request.user.auth_token.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    

class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer


class ChangePasswordApiView(generics.GenericAPIView):
    serializer_class = ChangePasswordSerializer
    model = User
    permission_classes = [IsAuthenticated]

    def get_object(self, queryset=None):
        obj = self.request.user
        return obj
    
    def put(self, request, *args, **kwargs):
        self.object = self.get_object()
        serializer = self.get_serializer(data = request.data)
        if serializer.is_valid():
            # Check old password
            if not self.object.check_password(serializer.data.get("old_password")):
                return Response({"old_password": ["Wrong password."]}, status=status.HTTP_400_BAD_REQUEST)
            # set_password also hashes the password that the user will get
            self.object.set_password(serializer.data.get("new_password"))
            self.object.save()
            response = {
                'status': 'success',
                'code': status.HTTP_200_OK,
                'message': 'Password updated successfully',
                'data': []
            }        
            return Response({'details':'password changed successfully'}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    

class ActivationApiView(APIView):
    def get(self, request, token, *args, **kwargs): 
        try:
            # decode the jwt token
            token = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
            # getting user id from jwt token
            user_id = token.get('user_id')
        except ExpiredSignatureError:
            return Response({'details':"token has been expired"}, status=status.HTTP_400_BAD_REQUEST)
        except InvalidSignatureError:
            return Response({'details':"token is not valid"}, status=status.HTTP_400_BAD_REQUEST)
        # getting the user and make it verified and then save it
        user_obj = User.objects.get(pk = user_id)
        # check if the user is already verified
        if user_obj.is_verified:
            return Response({"detail":"Your account has already been verified"})
        user_obj.is_verified = True
        user_obj.save()
        return Response({"detail":"Your account has been verified and activated successfully"})


class ActivationResendApiView(generics.GenericAPIView):
    serializer_class = ActivationResendSerializer

    def post(self, request, *args, **kwargs):  
        serializer = self.serializer_class(data=request.data)   
        serializer.is_valid(raise_exception=True)
        user_obj = serializer.validated_data['user']
        token = self.get_tokens_for_user(user_obj)
        email_obj = EmailMessage('email/activation_email.tpl', {'token': token}, 'admin@admin.com', to=[user_obj.email])
        EmailThread(email_obj).start()  
        return Response({"details":"User activation resend successfully"}, status=status.HTTP_200_OK)       
    
    def get_tokens_for_user(self, user):
        refresh = RefreshToken.for_user(user)
        return str(refresh.access_token)
    