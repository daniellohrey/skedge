from django.db import models

class Availability(models.Model):
	available = {}
	for day in range(5):
		for shift in range(4):
			available[day, shift] = models.BooleanField(default=False)

class Schedule(models.Model):
	working = {}
	for day in range(5):
		for shift in range(4):
			working[day, shift] = models.BooleanField(default=False)

class Employee(models.Model):
	name = models.CharField(max_length=50, primary_key=True)
	availability = models.OneToOneField(Availability, on_delete=models.CASCADE)
	schedule = models.OneToOneField(Schedule, on_delete=models.CASCADE)

	def __str__(self):
		return self.name
