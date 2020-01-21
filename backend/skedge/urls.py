from django.urls import path
from . import views

app_name = 'skedge'
urlpatterns = [
	path('', views.index, name='index'),
	path('employee/', views.employee, name='employee'),
	path('availability/', views.availability, name='availability'),
	path('schedule/', views.schedule, name='schedule'),
	path('generate/', views.generate_schedule, name='generate'),
	path('employee/delete/', views.delete_employee, name='delete'),
]
