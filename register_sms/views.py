from django.shortcuts import render

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import VerifyCodeSerializer, SendCodeSerializer
from drf_yasg.utils import swagger_auto_schema



class SendCodeView(APIView):
    @swagger_auto_schema(request_body=SendCodeSerializer)
    def post(self, request):
        serializer = SendCodeSerializer(data=request.data)
        if serializer.is_valid():
            phone = serializer.validated_data["phone"]
            return Response({"message": f"Code sent to {phone}"}, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



class VerifyCodeView(APIView):
    @swagger_auto_schema(request_body=VerifyCodeSerializer  )
    def post(self, request):
        serializer = VerifyCodeSerializer(data=request.data)
        if serializer.is_valid():
            return Response({"message": "Phone number verified successfully."}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

