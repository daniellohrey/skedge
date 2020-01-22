from django.forms import ModelForm, Form, HiddenInput, ChoiceField, ModelChoiceField
from .models import Employee, Schedule, Availability, Schedule_Parameters

class ScheduleForm(ModelForm):
	choices = [
                ('N', 'Not Working'),
                ('W', 'Working')
        ]
	for s in range(4):
		for d in range(5):
			key = "w" + str(d) + "_" + str(s)
			exec(key + " = ChoiceField(widget=HiddenInput, choices=choices)")

	class Meta:
		model = Schedule
		fields = ['employee']
		for s in range(4):
			for d in range(5):
				key = "w" + str(d) + "_" + str(s)
				exec("fields.append('" + key + "')")

class AvailabilityForm(ModelForm):
	choices = [
                ('N', 'Not Available'),
                ('A', 'Available'),
                ('W', 'Working')
        ]
	for s in range(4):
		for d in range(5):
			key = "a" + str(d) + "_" + str(s)
			exec(key + " = ChoiceField(widget=HiddenInput, choices=choices)")

	class Meta:
		model = Availability
		fields = ['employee', 'weekly_ideal']
		for s in range(4):
			for d in range(5):
				key = "a" + str(d) + "_" + str(s)
				exec("fields.append('" + key + "')")

class EmployeeForm(ModelForm):
	class Meta:
		model = Employee
		fields = ['name']

class Schedule_ParametersForm(ModelForm):
	class Meta:
		model = Schedule_Parameters
		fields = []
		for s in range(4):
			for d in range(5):
				key = "p" + str(d) + "_" + str(s)
				exec("fields.append('" + key + "')")

class DeleteEmployeeForm(Form):
	employee = ModelChoiceField(queryset=Employee.objects.all())
