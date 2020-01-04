#Constraint programming to schedule BAASC shifts

import random
from ortools.sat.python import cp_model

class Employee():
	def __init__(self, name, from_2 = 0, till_6 = 0):
		self._name = name
		self._not_available = []
		if from_2:
			self._from_2 = 1
		else:
			self._from_2 = 0
		if till_6:
			self._till_6 = 1
		else:
			self._till_6 = 0
		
		return

	@property
	def name(self):
		return self._name

	def set_name(self, name):
		self._name = name

	@property
	def not_available(self):
		return self._not_available

	#availabilities is a list of shifts employee is available for
	#shift is (day, time) - day 0-4, m-f, time is 0-1, morning-afternoon
	def set_availabilities(self, availabilities):
		self._not_available = []
		for i in range(5):
			for j in range(2):
				if (i, j) not in availabilities:
					self._not_available.append((i, j))

	@property
	def from_2(self):
		return self._from_2

	def set_from_2(self, from_2):
		if from_2:
			self._from_2 = 1
		else:
			self._from_2 = 0

	@property
	def till_6(self):
		return self._till_6

	def set_till_6(self, till_6):
		if till_6:
			self._till_6 = 1
		else:
			self._till_6 = 0

def find_schedule(employees, cover):
	num_employees = len(employees)
	num_days = 5
	num_shifts = 2
	model = cp_model.CpModel()

	work = {}
	for e in range(num_employees):
		for d in range(num_days):
			for s in range(num_shifts):
				work[e, d, s] = model.NewBoolVar('work%i_%i_%i' % (e, d, s))

	from_2 = []
	for e in range(num_employees):
		w = employees[e]
		from_2.append(model.NewBoolVar('from_2_%i' % (e)))
		model.Add(from_2[e] == w.from_2)

	till_6 = []
	for e in range(num_employees):
		w = employees[e]
		till_6.append(model.NewBoolVar('till_6_%i' % (e)))
		model.Add(till_6[e] == w.till_6)

	#int_vars = []
	#int_coeffs = []
	#bool_vars = []
	#bool_coeffs = []

	#set shifts not available
	for e in range(num_employees):
		w = employees[e]
		for d, s in w.not_available:
			model.Add(work[e, d, s] == 0)

	#set cover contraints
	for d in range(num_days):
		for s in range(num_shifts):
			model.Add(sum(work[e, d, s] for e in range(num_employees)) == cover[d][s])

	#at least 1 employee available to start at 2 per afternoon shift
	from_2_check = []
	for e in range(num_employees):
		for d in range(num_days):
				from_2_check.append(model.NewBoolVar('from_2_check%i' % (e)))
				model.AddBoolAnd((work[e, d, 1], from_2[e])).OnlyEnforceIf(work[e, d, 1])

	#at least 2 employees available to finish at 6 per afternoon shift

	#weekly sum of shifts at least half of available shifts
	for e in range(num_employees):
		weekly_min = (10 - len(employees[e].not_available)) // 3 * 2
		weekly_sum = model.NewIntVar(weekly_min, 10, '')
		model.Add(sum(work[e, d, s] for d in range(num_days) for s in range(num_shifts)) == weekly_sum)

	#solve model
	solver = cp_model.CpSolver()
	solver.parameters.num_search_workers = 8
	status = solver.Solve(model)

	if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
		print("Skedge")
		print("         M T W T F")
		for e in range(num_employees):
			schedule = ''
			schedule += employees[e].name + " " * (9 - len(employees[e].name))
			for d in range(num_days):
				for s in range(num_shifts):
					if solver.BooleanValue(work[e, d, s]):
						schedule += "1"
					else:
						schedule += "0"
			print(schedule)

		print()
		print("Availabilities")
		for e in range(num_employees):
			print(employees[e].name)
			print(employees[e].not_available)

		print()

	print(solver.ResponseStats())

def main():
	employees = []
	shifts = []
	random.seed(1)

	for i in range(5):
		for j in range(2):
			shifts.append((i, j))

	e = Employee("Daniel")
	e.set_availabilities(random.sample(shifts, 5))
	employees.append(e)

	e = Employee("Evelyn")
	e.set_availabilities(random.sample(shifts, 7))
	employees.append(e)

	e = Employee("Emily L")
	e.set_availabilities(random.sample(shifts, 4))
	employees.append(e)

	e = Employee("Emily T")
	e.set_availabilities(random.sample(shifts, 6))
	employees.append(e)

	e = Employee("Matt")
	e.set_availabilities(random.sample(shifts, 8))
	employees.append(e)

	e = Employee("Luke")
	e.set_availabilities(random.sample(shifts, 5))
	employees.append(e)

	e = Employee("Murray")
	e.set_availabilities(random.sample(shifts, 4))
	employees.append(e)

	e = Employee("Sam")
	e.set_availabilities(random.sample(shifts, 6))
	employees.append(e)

	e = Employee("Simon")
	e.set_availabilities(random.sample(shifts, 7))
	employees.append(e)

	e = Employee("Rio")
	e.set_availabilities(random.sample(shifts, 6))
	employees.append(e)

	e = Employee("Sophie L")
	e.set_availabilities(random.sample(shifts, 4))
	employees.append(e)

	e = Employee("Sophie A")
	e.set_availabilities(random.sample(shifts, 5))
	employees.append(e)

	e = Employee("Vanessa")
	e.set_availabilities(random.sample(shifts, 8))
	employees.append(e)

	e = Employee("Dale")
	e.set_availabilities(random.sample(shifts, 8))
	employees.append(e)

	cover = []
	for i in range(5):
		cover.append((4, 5))

	find_schedule(employees, cover)

if __name__ == "__main__":
	main()
