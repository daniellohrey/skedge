from django.db import models

class Employee(models.Model):
	name = models.CharField(max_length=50, unique=True)

	def __str__(self):
		return self.name

class Availability(models.Model):
	employee = models.OneToOneField(Employee, on_delete=models.CASCADE)
	weekly_ideal = models.IntegerField(default=0)
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

class Schedule_Parameters(models.Model):
	for day in range(5):
		for shift in range(4):
			key = "p" + str(day) + "_" + str(shift)
			exec(key + " = models.IntegerField()")
