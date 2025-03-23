from django.shortcuts import render
from rest_framework.permissions import BasePermission
# Create your views here.
from rest_framework import generics, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication
from .models import Client, EmployeeClientDetails
from .serializers import ClientSerializer, EmployeeClientDetailsSerializer
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from .models import User
from .serializers import UserRegisterSerializer, UserLoginSerializer, UserSerializer
import random
from .serializers import EmployeeClientDetailsSerializer
from django.core.exceptions import ObjectDoesNotExist




# ✅ Generate JWT Token
def get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)
    return {
        "refresh": str(refresh),
        "access": str(refresh.access_token),
    }


# ✅ Employee & Manager Registration API
class RegisterEmployeeView(APIView):
    def post(self, request):
        serializer = UserRegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            tokens = get_tokens_for_user(user)
            return Response(
                {"message": "Registration successful", "tokens": tokens, "user": UserSerializer(user).data},
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ✅ Employee & Manager Login API
class LoginEmployeeView(APIView):
    def post(self, request):
        serializer = UserLoginSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data["email"]
            phone_number = serializer.validated_data["phone_number"]
            dob = serializer.validated_data["dob"]
            role = serializer.validated_data["role"]
            password = serializer.validated_data["password"]

            user = User.objects.filter(email=email, phone_number=phone_number, dob=dob, role=role).first()

            if user and user.check_password(password):
                tokens = get_tokens_for_user(user)
                return Response(
                    {"message": "Login successful", "tokens": tokens, "user": UserSerializer(user).data},
                    status=status.HTTP_200_OK
                )
            return Response({"error": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)





class IsEmployee(BasePermission):
    """
    Custom permission: Only employees can access.
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'employee'

class IsManager(BasePermission):
    """
    Custom permission: Only managers can access.
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'manager'


# ✅ Create & View Clients (Employees & Managers)
class ClientListCreateView(generics.ListCreateAPIView):
    queryset = Client.objects.all()
    serializer_class = ClientSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        """ Assign an employee dynamically in API View """
        if serializer.validated_data['client_type'] == 'direct':
            # Logic to assign employee dynamically
            serializer.save()
        else:
            serializer.save(assigned_employee=self.request.user)

# ✅ Employee: View & Update Only Their Clients
class EmployeeClientUpdateView(generics.RetrieveUpdateAPIView):
    serializer_class = ClientSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsEmployee]

    def get_queryset(self):
        return Client.objects.filter(assigned_employee=self.request.user)

# ✅ Manager: View & Update Any Client
class ManagerClientUpdateView(generics.RetrieveUpdateAPIView):
    queryset = Client.objects.all()
    serializer_class = ClientSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsManager]

# ✅ Employee & Manager: Update Employee Client Details (CIBIL, Aadhaar, PAN, etc.)
class EmployeeClientDetailsUpdateView(generics.RetrieveUpdateAPIView):
    queryset = EmployeeClientDetails.objects.all()
    serializer_class = EmployeeClientDetailsSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [permissions.IsAuthenticated]  # Both Employees & Managers can update




class EmployeeClientManageView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        """Retrieve all clients assigned to the logged-in employee."""
        if request.user.role != 'employee':
            return Response({"error": "Access denied"}, status=status.HTTP_403_FORBIDDEN)

        clients = Client.objects.filter(assigned_employee=request.user)
        serializer = ClientSerializer(clients, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        """Create a new employee-registered client."""
        if request.user.role != 'employee':
            return Response({"error": "Access denied"}, status=status.HTTP_403_FORBIDDEN)

        data = request.data.copy()
        data["client_type"] = "employee_registered"
        data["assigned_employee"] = request.user.id  # Assign to the logged-in employee

        serializer = ClientSerializer(data=data)
        if serializer.is_valid():
            serializer.save(assigned_employee=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, pk):
        """Update details of an assigned client (except approval status)."""
        if request.user.role != 'employee':
            return Response({"error": "Access denied"}, status=status.HTTP_403_FORBIDDEN)

        try:
            client = Client.objects.get(id=pk, assigned_employee=request.user)
        except Client.DoesNotExist:
            return Response({"error": "Client not found or unauthorized"}, status=status.HTTP_404_NOT_FOUND)

        serializer = ClientSerializer(client, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    


class ClientApplicationView(APIView):
    permission_classes = [permissions.AllowAny]  # No authentication required

    def post(self, request):
        """Client can apply without login. The system will auto-assign an employee."""
        required_fields = [
            "name", "contact_number", "father_name", "mother_name",
            "qualifications", "married_status", "current_address",
            "landmark", "years_at_address", "gmail", "office_name",
            "office_address", "designation", "department",
            "current_experience", "overall_experience",
            "reference_name_1", "reference_number_1",
            "reference_name_2", "reference_number_2",
            "expected_loan_amount", "loan_purpose"
        ]

        # ✅ Validate request data (Only accept required fields)
        data = {key: request.data.get(key) for key in required_fields if key in request.data}

        if len(data) != len(required_fields):
            return Response({"error": "Missing required fields"}, status=status.HTTP_400_BAD_REQUEST)

        # ✅ Auto-assign to a registered employee
        employees = User.objects.filter(role="employee")
        assigned_employee = random.choice(employees) if employees.exists() else None

        data["client_type"] = "direct"
        data["assigned_employee"] = assigned_employee.id if assigned_employee else None

        serializer = ClientSerializer(data=data)
        if serializer.is_valid():
            serializer.save(assigned_employee=assigned_employee)
            return Response(
                {
                    "message": "Client application submitted successfully",
                    "client": serializer.data,
                    "assigned_employee": assigned_employee.email if assigned_employee else "Not assigned yet"
                },
                status=status.HTTP_201_CREATED
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    

class SendApprovalRequestView(APIView):
    """
    Employee sends client details to Manager (MD) for loan approval.
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsEmployee]  # Only employees can send requests

    def post(self, request, client_id):
        try:
            client = Client.objects.get(id=client_id, assigned_employee=request.user)

            # Ensure only employee-registered clients are sent for approval
            if client.client_type != "employee_registered":
                return Response({"error": "Only employee-registered clients can be sent for approval."}, status=status.HTTP_400_BAD_REQUEST)

            # Fetch additional client details
            try:
                extra_details = client.extra_details
            except ObjectDoesNotExist:
                return Response({"error": "Client details not found. Please complete all fields before sending approval."}, status=status.HTTP_400_BAD_REQUEST)

            # ✅ Check Required Fields
            required_fields = ["cibil_score", "aadhaar_front", "aadhaar_back", "cibil_report", "pan_card"]
            missing_fields = [field for field in required_fields if not getattr(extra_details, field)]

            if missing_fields:
                return Response({"error": f"Missing fields: {', '.join(missing_fields)}"}, status=status.HTTP_400_BAD_REQUEST)

            # ✅ Mark client as pending approval
            client.approval_status = "pending"
            client.save()

            # ✅ Get Employee (Sender) Details
            employee = request.user  # Employee sending the request

            return Response(
                {
                    "message": "Approval request sent to Manager (MD).",
                    "client_details": {
                        "client_id": client.id,
                        "client_name": client.name,
                        "contact_number": client.contact_number,
                        "email": client.gmail,
                        "address": client.current_address,
                        "loan_amount": client.expected_loan_amount,
                        "loan_purpose": client.loan_purpose,
                        "status": client.approval_status
                    },
                    "employee_details": {
                        "employee_id": employee.id,
                        "employee_name": employee.name,
                        "email": employee.email,
                        "phone_number": employee.phone_number,
                        "role": employee.role
                    }
                },
                status=status.HTTP_200_OK
            )

        except Client.DoesNotExist:
            return Response({"error": "Client not found or not assigned to you."}, status=status.HTTP_404_NOT_FOUND)