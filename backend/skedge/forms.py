from django.forms import ModelForm, HiddenInput, ChoiceField
from .models import Employee, Schedule, Availability, Schedule_Parameters

class ScheduleForm(ModelForm):
	for s in range(4):
		for d in range(5):
			key = "a" + str(d) + "_" + str(s)
			exec(key + " = ChoiceField(widget=HiddenInput)")

	class Meta:
		model = Schedule
		fields = []
		for s in range(4):
			for d in range(5):
				key = "a" + str(d) + "_" + str(s)
				exec("fields.append('" + key + "')")

class AvailabilityForm(ModelForm):
	for s in range(4):
		for d in range(5):
			key = "a" + str(d) + "_" + str(s)
			exec(key + " = ChoiceField(widget=HiddenInput)")

	class Meta:
		model = Availability
		fields = ['employee']
		for s in range(4):
			for d in range(5):
				key = "a" + str(d) + "_" + str(s)
				exec("fields.append('" + key + "')")

class EmployeeForm(ModelForm):
	class Meta:
		model = Employee
		fields = '__all__'

class Schedule_ParametersForm(ModelForm):
	class Meta:
		model = Schedule_Parameters
		fields = '__all__'
