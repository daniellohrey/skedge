from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from .forms import ScheduleForm, AvailabilityForm, EmployeeForm, Schedule_ParametersForm, DeleteEmployeeForm
from .models import Employee, Availability, Schedule, Schedule_Parameters
from axes.utils import reset
from ortools.sat.python import cp_model
import random

@login_required
def index(request):
	reset(username=request.user)
	data = {}
	employee_forms = []
	for employee in Employee.objects.all():
		form = AvailabilityForm(instance=employee.availability)
		employee_forms.append((employee, form))
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
	data['dform'] = DeleteEmployeeForm()
	try:
		if request.GET.get('error'):
			data['error'] = "Couldn't generate a valid timetable. Please try again with different parameters."
	except IndexError:
		pass
	return render(request, 'skedge/index.html', data)

@login_required
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

@login_required
def delete_employee(request):
	if request.method == 'POST':
		form = DeleteEmployeeForm(request.POST)
		if form.is_valid():
			form.cleaned_data['employee'].delete()
	return HttpResponseRedirect('/')

@login_required
def availability(request):
	if request.method == 'POST':
		a = Availability.objects.get(employee=request.POST['employee'])
		form = AvailabilityForm(request.POST, instance=a)
		if form.is_valid():
			form.save()
	return HttpResponse('OK', status=200)

wk = "B"
@login_required
def schedule(request):
	if request.method == 'POST':
		s = Schedule.objects.get(employee=request.POST['employee'])
		form = ScheduleForm(request.POST, instance=s)
		if form.is_valid():
			form.save()
		return HttpResponse('OK', status=200)
	data = {}
	schedule_forms = []
	working = {}
	for employee in Employee.objects.all():
		form = ScheduleForm(instance=employee.schedule)
		schedule_forms.append((employee, form))
		for s in range(4):
			for d in range(5):
				key = "w" + str(d) + "_" + str(s)
				exec("global wk; wk = employee.schedule." + key)
				if wk == "W":
					try:
						working[str(d) + "_" + str(s)].append(employee.name)
					except:
						working[str(d) + "_" + str(s)] = [employee.name]
	data['working'] = working
	data['forms'] = schedule_forms
	headers = ["Shift", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
	data['days'] = headers
	return render(request, 'skedge/schedule.html', data)

@login_required
def generate_schedule(request):
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
		status = generate()
		if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
			return HttpResponseRedirect('/schedule/')
		else:
			return HttpResponseRedirect('/?error=1')
	else:
		return HttpResponseRedirect('/')


av = "B"
def generate():
	global av
	employees = []
	for employee in Employee.objects.all():
		employees.append(employee.availability)
	params = Schedule_Parameters.objects.all()[0]
	num_employees = len(employees)
	num_days = 5
	num_shifts = 2

	#rather have people work more than ideal than be 1 short
	COVER_PENALTY = 10
	WEEKLY_SUM_PENALTY = 1
	CASUAL_PENALTY = 100

	int_vars = []
	int_coeffs = []
	model = cp_model.CpModel()

	#create morning/afternoon shift for each employee/day
	work = {}
	for e in range(num_employees):
		for d in range(num_days):
			for s in range(num_shifts):
				work[e, d, s] = model.NewBoolVar('work%i_%i_%i' % (e, d, s))

	#set availabilites from 2-230
	working_from_2 = [[], [], [], [], []] #for choosing workers to work from 2
	available_from_2 = [[], [], [], [], []]
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
					#check if working afternoon
					key = "a" + str(d) + "_2"
					exec("global av; av = w." + key)
					if av != 'N':
						#if working set working afternoon
						model.Add(work[e, d, 1] == 1)
						working_from_2[d].append(e)
				else:
					available_from_2[d].append(e)

	#set availabilites from 530-6, see from_2
	working_till_6 = [[], [], [], [], []]
	available_till_6 = [[], [], [], [], []]
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
					key = "a" + str(d) + "_2"
					exec("global av; av = w." + key)
					if av != 'N':
							model.Add(work[e, d, 1] == 1)
							working_till_6[d].append(e)
				else:
					available_till_6[d].append(e)
			
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
		model.Add(sum([till_6_check[e, d] for e in range(num_employees)]) >= av)

	#add ideal number of shifts for each employee
	for e in range(num_employees):
		w = employees[e]
		weekly_sum = model.NewIntVar(0, 10, "weekly_sum%i" % (e))
		model.Add(sum(work[e, d, s] for d in range(num_days) for s in range(num_shifts)) == weekly_sum)
		if w.weekly_ideal != 0:
			ideal = model.NewIntVar(0, 10, "weekly_ideal%i" % (e))
			model.Add(ideal == w.weekly_ideal)
			half_ideal = model.NewIntVar(0, 10, "half_ideal%i" % (e))
			model.AddDivisionEquality(half_ideal, ideal, 2)
			ideal_3 = model.NewIntVar(0, 10, "ideal_3_%i" % (e))
			model.Add(ideal_3 == ideal - 3)
			min_ideal = model.NewIntVar(0, 10, "min_ideal%i" % (e))
			model.AddMaxEquality(min_ideal, [half_ideal, ideal_3])
			model.Add(weekly_sum > min_ideal)
			#add calculate max_ideal
			#model.Add(weekly_sum <= max_ideal)
			delta = model.NewIntVar(-10, 10, "weekly_delta%i" % (e))
			model.Add(delta == ideal - weekly_sum)
			delta_penalty = model.NewIntVar(0, 10, 'weekly%i' % (e))
			model.AddAbsEquality(delta_penalty, delta)
			int_vars.append(delta_penalty)
			int_coeffs.append(WEEKLY_SUM_PENALTY)
		else:
			int_vars.append(weekly_sum)
			int_coeffs.append(CASUAL_PENALTY)

	#set objective
	model.Minimize(sum(int_vars[i] * int_coeffs[i] for i in range(len(int_vars))))

	#solve model
	solver = cp_model.CpSolver()
	#solver.parameters.num_search_workers = 8 #adjust for production server
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

				#set all not working from 2/till 6
				for s2 in [1, 3]:
					key = "w" + str(d) + "_" + str(s2)
					exec("w." + key + " = 'N'")
			#w.save()

		#set employees working from 2/till 6
		random.seed()
		for d in range(5):
			for e in working_from_2[d]:
					w = employee_schedules[e]
					key = "w" + str(d) + "_1"
					exec("w." + key + " = 'W'")
					#w.save()

			for e in working_till_6[d]:
					w = employee_schedules[e]
					key = "w" + str(d) + "_3"
					exec("w." + key + " = 'W'")
					#w.save()

			#choose from those available to start at 2
			key = "p" + str(d) + "_1"
			exec("global av; av = params." + key)
			if len(working_from_2[d]) < av:
				delta = av - len(working_from_2[d])
				available = []
				for e in available_from_2[d]:
					w = employee_schedules[e]
					key = "w" + str(d) + "_2"
					exec("global av; av = w." + key)
					if av == 'W':
						available.append(e)
				working = random.sample(available, delta)
				for e in working:
					w = employee_schedules[e]
					key = "w" + str(d) + "_1"
					exec("w." + key + " = 'W'")
					#w.save()

			key = "p" + str(d) + "_3"
			exec("global av; av = params." + key)
			if len(working_till_6[d]) < av:
				delta = av - len(working_till_6[d])
				available = []
				for e in available_till_6[d]:
					w = employee_schedules[e]
					key = "w" + str(d) + "_2"
					exec("global av; av = w." + key)
					if av == 'W':
						available.append(e)
				working = random.sample(available, delta)
				for e in working:
					w = employee_schedules[e]
					key = "w" + str(d) + "_3"
					exec("w." + key + " = 'W'")
					#w.save()

		for e in employee_schedules:
			e.save()
	return status
