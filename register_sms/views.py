# views.py
from asyncio import timeout
from random import randint

from django.core.cache import cache
from drf_yasg.utils import swagger_auto_schema
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, viewsets, permissions
from rest_framework_simplejwt.tokens import RefreshToken
from .models import User
from .serializers import *
from rest_framework.exceptions import PermissionDenied

class PhoneAPIView(APIView):
    @swagger_auto_schema(request_body=PhoneSerializer)
    def post(self, request):
        serializer = PhoneSerializer(data=request.data)
        if serializer.is_valid():
            phone = serializer.validated_data['phone']

            otp_code = str(randint(1000, 9999))
            print("Code:", otp_code)

            cache.set(phone, {"otp": otp_code, "phone_number": phone}, timeout=900)

            return Response(
                {"success":True,"detail":"Code send to you!"},
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class VerifyOTPAPIView(APIView):
        @swagger_auto_schema(request_body=VerifyOTPSerializer)
        def post(self, request):
            serializer = VerifyOTPSerializer(data=request.data)
            if serializer.is_valid():
                phone = serializer.validated_data['phone']
                verification_code = serializer.validated_data['verification_code']
                cached_otp = cache.get(phone)

                if str(cached_otp.get("otp")) == str(verification_code):

                    return Response(
                        {"success":True,"detail":"Phone nomber verfyed"},
                        status=status.HTTP_200_OK
                    )

                return Response(
                    {"success":False,"detail":"invalid code or number."},
                     status=status.HTTP_400_BAD_REQUEST
                )

            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class RegisterAPIView(APIView):
    @swagger_auto_schema(request_body=RegisterSerializer)
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():

            phone = serializer.validated_data['phone']
            cached_data = cache.get(phone)

            if not cached_data:
                return Response(
                    {"success": False, "detail": "phone number is not verfyed"}
                )

            phone_number = cached_data.get("phone_number")

            if str(phone_number) == str(phone):
                serializer.save()
                return Response(
                    {"success": True, "detail": "account created succsessfully"},
                    status=status.HTTP_201_CREATED
                )


        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class LoginAPIView(APIView):
    @swagger_auto_schema(request_body=LoginSerializer)
    def post(self, request):
        phone = request.data.get("phone")
        password = request.data.get("password")

        user = User.objects.filter(phone=phone).first()

        if user and user.check_password(password):
            refresh = RefreshToken.for_user(user)
            return Response({
                "refresh": str(refresh),
                "access": str(refresh.access_token),
                "is_admin": user.is_admin,
                "is_user": user.is_user,
                "is_staff": user.is_staff,
            })
        return Response({"error": "phone or password is incorrect"}, status=status.HTTP_401_UNAUTHORIZED)

class ProfileAPIView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        serializer = RegisterSerializer(request.user)
        return Response(
            {"success":True,"data":serializer.data},
            status=status.HTTP_200_OK
        )

    def patch(self, request):
        serializer = RegisterSerializer(request.user, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(
                {"success":True,"data":serializer.data},
                status=status.HTTP_201_CREATEDOK
            )



from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status, permissions
from .models import Movie, Actor


class MovieViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    queryset = Movie.objects.all()
    serializer_class = MovieSerializer

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def add_actors(self, request, pk=None):
        movie = self.get_object()
        actor_ids = request.data.get('actor_ids', [])

        if not actor_ids:
            return Response({"error": "Provide at least one actor ID"}, status=status.HTTP_400_BAD_REQUEST)

        actors = Actor.objects.filter(id__in=actor_ids)
        if not actors:
            return Response({"error": "No valid actors found"}, status=status.HTTP_404_NOT_FOUND)

        movie.actors.add(*actors)
        return Response({"success": "Actors added successfully"}, status=status.HTTP_200_OK)
    
class ActorViewSet(viewsets.ModelViewSet):
    serializer_class = ActorSerializer
    permission_classes = [IsAuthenticated]
    queryset = Actor.objects.all()
    def get_permissions(self):
        if self.request.user.is_admin:
            return [permissions.AllowAny()]  
        return super().get_permissions()


class CommentViewSet(viewsets.ModelViewSet):
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticated]
    queryset = Comment.objects.all()

    def perform_create(self, serializer):
        serializer.save(user_id=self.request.user)

    def get_permissions(self):
        if self.request.user.is_admin:
            return [permissions.AllowAny()] 
        return super().get_permissions()

    def perform_destroy(self, instance):
        user = self.request.user
        if user.is_admin or instance.user == user:
            instance.delete()  
        else:
            raise PermissionDenied("You do not have permission to delete this comment.")
