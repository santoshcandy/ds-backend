from django.urls import path
from .views import (
    ClientListCreateView, EmployeeClientUpdateView, ManagerClientUpdateView,
    EmployeeClientDetailsUpdateView,ClientApplicationView
)
from .views import RegisterEmployeeView, LoginEmployeeView,EmployeeClientManageView
urlpatterns = [
    path('clients/', ClientListCreateView.as_view(), name='client-list-create'),
    path('clients/<int:pk>/update/', EmployeeClientUpdateView.as_view(), name='employee-client-update'),
    path('clients/<int:pk>/manager-update/', ManagerClientUpdateView.as_view(), name='manager-client-update'),
    path('clients/<int:pk>/details-update/', EmployeeClientDetailsUpdateView.as_view(), name='employee-client-details-update'),
    path("register/", RegisterEmployeeView.as_view(), name="register"),
    path("login/", LoginEmployeeView.as_view(), name="login"),
    path("employee/clients/", EmployeeClientManageView.as_view(), name="employee-clients"),
    path("employee/clients/<int:pk>/", EmployeeClientManageView.as_view(), name="employee-client-update"),
    path("client/apply/", ClientApplicationView.as_view(), name="client-apply"),






]

