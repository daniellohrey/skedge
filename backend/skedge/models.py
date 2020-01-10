from django.db import models

class Employee(models.Model):
	name = models.CharField(max_length=50, unique=True)
	#availability = models.OneToOneField(Availability, on_delete=models.CASCADE)
	#schedule = models.OneToOneField(Schedule, on_delete=models.CASCADE)

	def __str__(self):
		return self.name

class Availability(models.Model):
	employee = models.OneToOneField(Employee, on_delete=models.CASCADE)
	choices = [
		('N', 'Not Available'),
		('A', 'Available'),
		('W', 'Working')
	]
	for day in range(5):
		for shift in range(4):
			key = "a" + str(day) + "_" + str(shift)
			exec(key + " = models.CharField(choices=choices, max_length=1, default='N')")

class Schedule(models.Model):
	employee = models.OneToOneField(Employee, on_delete=models.CASCADE)
	choices = [
		('N', 'Not working'),
		('W', 'Working')
	]
	for day in range(5):
		for shift in range(4):
			key = "w" + str(day) + "_" + str(shift)
			exec(key + " = models.CharField(choices=choices, max_length=1, default='N')")
