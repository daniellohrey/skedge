from django.urls import path
from . import views

app_name = 'skedge'
urlpatterns = [
	path('', views.index, name='index'),
	path('employee/', views.employee, name='employee'),
	path('availability/', views.availability, name='availability'),
]
