from django.forms import ModelForm
from .models import Employee, Schedule, Availability, Schedule_Parameters

class ScheduleForm(ModelForm):
	class Meta:
		model = Schedule
		fields = '__all__'

class AvailabilityForm(ModelForm):
	class Meta:
		model = Availability
		fields = '__all__'

class EmployeeForm(ModelForm):
	class Meta:
		model = Employee
		fields = '__all__'

class Schedule_ParametersForm(ModelForm):
	class Meta:
		model = Schedule_Parameters
		fields = '__all__'
