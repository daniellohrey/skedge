from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from .forms import ScheduleForm, AvailabilityForm, EmployeeForm
from .models import Employee, Availability, Schedule

#@login_required
def index(request):
	data = {}
	employee_forms = []
	for employee in Employee.objects.all():
		form = AvailabilityForm(instance=employee.availability)
		employee_forms.append(form)
	data['forms'] = employee_forms
	headers = ["Shift", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
	data['days'] = headers
	new_employee = EmployeeForm()
	data['eform'] = new_employee
	return render(request, 'skedge/index.html', data)

def employee(request):
	if request.method == 'POST':
		form = EmployeeForm(request.POST)
		if form.is_valid():
			e = form.save()
			a = Availability(employee=e)
			a.save()
			s = Schedule(employee=e)
			s.save()
	return HttpResponseRedirect('/')

def availability(request):
	if request.method == 'POST':
		a = Availability.objects.get(employee=request.POST['employee'])
		form = AvailabilityForm(request.POST, instance=a)
		if form.is_valid():
			form.save()
	return HttpResponseRedirect('/')
