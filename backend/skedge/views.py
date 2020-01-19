from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from .forms import ScheduleForm, AvailabilityForm, EmployeeForm, Schedule_ParametersForm
from .models import Employee, Availability, Schedule, Schedule_Parameters
from ortools.sat.python import cp_model

@login_required
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
	try:
		p = Schedule_Parameters.objects.all()[0]
		form = Schedule_ParametersForm(instance=p)
	except IndexError:
		form = Schedule_ParametersForm()
	data['param_form'] = form
	data['avail'] = True
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

def schedule(request):
	if request.method == 'POST':
		s = Schedule.objects.get(employee=request.POST['employee'])
		form = ScheduleForm(request.POST, instance=s)
		if form.is_valid():
			form.save()
		return HttpResponseRedirect('/schedule/')
	data = {}
	schedule_forms = []
	for employee in Employee.objects.all():
		form = ScheduleForm(instance=employee.schedule)
		schedule_forms.append(form)
	data['forms'] = schedule_forms
	headers = ["Shift", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
	data['days'] = headers
	return render(request, 'skedge/schedule.html', data)

av = "B"
def generate_schedule(request):
	global av
	if request.method == 'POST':
		try:
			p = Schedule_Parameters.objects.all()[0]
			form = Schedule_ParametersForm(request.POST, instance=p)
		except IndexError:
			form = Schedule_ParametersForm(request.POST)
		if form.is_valid():
			form.save()
		else:
			return HttpResponseRedirect("/")

		employees = []
		for employee in Employee.objects.all():
			employees.append(employee.availability)
		params = Schedule_Parameters.objects.all()[0]
		num_employees = len(employees)
		num_days = 5
		num_shifts = 2

		#penalties should be such that you rather have someone work more than ideal than be one person short for a shift
		COVER_PENALTY = 10
		WEEKLY_SUM_PENALTY = 1

		int_vars = []
		int_coeffs = []
		model = cp_model.CpModel()

		#create morning/afternoon shift for each employee/day
		work = {}
		for e in range(num_employees):
			for d in range(num_days):
				for s in range(num_shifts):
					work[e, d, s] = model.NewBoolVar('work%i_%i_%i' % (e, d, s))

		#create dummy employee to find gaps

		#set availabilites from 2-230
		from_2 = {}
		for e in range(num_employees):
			for d in range(num_days):
				w = employees[e]
				from_2[e, d] = model.NewBoolVar('from_2_%i_%i' % (e, d))
				key = "a" + str(d) + "_1"
				exec("global av; av = w." + key)
				if av == 'N':
					#if not available set to not working
					model.Add(from_2[e, d] == 0)
				else:
					#if available/working set to available
					model.Add(from_2[e, d] == 1)
					if av == 'W':
						#if working set working afternoon
						model.Add(work[e, d, 1] == 1)

		#set availabilites from 530-6, see from_2
		till_6 = {}
		for e in range(num_employees):
			for d in range(num_days):
				w = employees[e]
				till_6[e, d] = model.NewBoolVar('till_6_%i_%i' % (e, d))
				key = "a" + str(d) + "_3"
				exec("global av; av = w." + key)
				if av == 'N':
					model.Add(till_6[e, d] == 0)
				else:
					model.Add(till_6[e, d] == 1)
					if av == 'W':
						model.Add(work[e, d, 1] == 1)
				
		#set working/not available shifts
		for e in range(num_employees):
			for d in range(num_days):
				for s, s2 in [(0, 0), (1, 2)]:
					w = employees[e]
					key = "a" + str(d) + "_" + str(s2)
					exec("global av; av = w." + key)
					if av == 'N':
						model.Add(work[e, d, s] == 0)
					elif av == 'W':
						model.Add(work[e, d, s] == 1)

		#add cover contraints
		for d in range(num_days):
			for s, s2 in [(0, 0), (1, 2)]:
				key = "p" + str(d) + "_" + str(s2)
				exec("global av; av = params." + key)
				working = model.NewIntVar(av - 1, av, "working%i_%i" % (d, s))
				model.Add(sum(work[e, d, s] for e in range(num_employees)) == working)
				ideal = model.NewIntVar(0, num_employees, "ideal%i_%i" % (d, s))
				model.Add(ideal == av)
				delta = model.NewIntVar(-1, 1, "delta%i_%i" % (d, s))
				model.Add(delta == ideal - working)
				delta_penalty = model.NewIntVar(0, 1, 'cover%i_%i' % (d, s))
				model.AddAbsEquality(delta_penalty, delta)
				int_vars.append(delta_penalty)
				int_coeffs.append(COVER_PENALTY)

		#add cover requirement from 2-230
		from_2_check = {}
		for e in range(num_employees):
			for d in range(num_days):
				from_2_check[e, d] = model.NewBoolVar('from_2_check%i_%i' % (e, d))
				#from_2_check is only true when work/from_2 are true
				model.Add(from_2_check[e, d] == 1).OnlyEnforceIf([work[e, d, 1], from_2[e, d]])
				model.Add(from_2_check[e, d] == 0).OnlyEnforceIf(work[e, d, 1].Not())
				model.Add(from_2_check[e, d] == 0).OnlyEnforceIf(from_2[e, d].Not())
		for d in range(num_days):
			key = "p" + str(d) + "_1"
			exec("global av; av = params." + key)
			model.Add(sum([from_2_check[e, d] for e in range(num_employees)]) >= av)

		#add cover requirement from 530-6
		till_6_check = {}
		for e in range(num_employees):
			for d in range(num_days):
				till_6_check[e, d] = model.NewBoolVar('till_6_check%i_%i' % (e, d))
				#from_2_check is only true when work/from_2 are true
				model.Add(till_6_check[e, d] == 1).OnlyEnforceIf([work[e, d, 1], till_6[e, d]])
				model.Add(till_6_check[e, d] == 0).OnlyEnforceIf(work[e, d, 1].Not())
				model.Add(till_6_check[e, d] == 0).OnlyEnforceIf(till_6[e, d].Not())
		for d in range(num_days):
			key = "p" + str(d) + "_3"
			exec("global av; av = params." + key)
			model.Add(sum([from_2_check[e, d] for e in range(num_employees)]) >= av)

		#add ideal number of shifts for each employee
		for e in range(num_employees):
			w = employees[e]
			weekly_sum = model.NewIntVar(0, 10, "weekly_sum%i" % (e))
			model.Add(sum(work[e, d, s] for d in range(num_days) for s in range(num_shifts)) == weekly_sum)
			ideal = model.NewIntVar(0, 10, "weekly_ideal%i" % (e))
			model.Add(ideal == w.weekly_ideal)
			delta = model.NewIntVar(-10, 10, "weekly_delta%i" % (e))
			model.Add(delta == ideal - weekly_sum)
			delta_penalty = model.NewIntVar(0, 10, 'weekly%i' % (e))
			model.AddAbsEquality(delta_penalty, delta)
			int_vars.append(delta_penalty)
			int_coeffs.append(WEEKLY_SUM_PENALTY)

		#set objective
		model.Minimize(sum(int_vars[i] * int_coeffs[i] for i in range(len(int_vars))))

		#solve model
		solver = cp_model.CpSolver()
		solver.parameters.num_search_workers = 8 #adjust for production server
		#printer = cp_model.ObjectiveSolutionPrinter()
		#status = solver.SolveWithSolutionCallback(model, printer)
		status = solver.Solve(model)

		if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
			employee_schedules = []
			for employee in Employee.objects.all():
				employee_schedules.append(employee.schedule)

			#set employees schedules
			for e in range(num_employees):
				w = employee_schedules[e]
				for d in range(num_days):
					#set whether working morning/afternoon
					for s, s2 in [(0, 0), (1, 2)]:
						key = "w" + str(d) + "_" + str(s2)
						av = solver.BooleanValue(work[e, d, s])
						if av:
							exec("w." + key + " = 'W'")
						else:
							exec("w." + key + " = 'N'")

					#set whether working from 2/till 6
					for s2 in [1, 3]:
						key = "w" + str(d) + "_" + str(s2)
						exec("w." + key + " = 'N'")
					#add actual 2-6 schedule

				w.save()

			return HttpResponseRedirect('/schedule/')

	return HttpResponseRedirect('/')

