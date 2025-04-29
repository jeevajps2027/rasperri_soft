from django.db import models
from datetime import datetime

# Create your models here.
class Parameter_Settings(models.Model):
    sr_no = models.CharField(max_length=10)
    part_model = models.CharField(max_length=100)
    part_name = models.CharField(max_length=100)
    char_lock = models.CharField(max_length=100)
    char_lock_limit = models.CharField(max_length=100)
    punch_no = models.BooleanField(default=False)

    def __str__(self):
        return f"ParameterSettings for {self.part_model}"

class paraTableData(models.Model):
    parameter_settings = models.ForeignKey(Parameter_Settings, related_name='table_data', on_delete=models.CASCADE)
    sr_no = models.CharField(max_length=10)
    parameter_name = models.CharField(max_length=100, blank=True)
    channel_no = models.CharField(max_length=10, blank=True)
    low_master = models.CharField(max_length=100, blank=True)
    high_master = models.CharField(max_length=100, blank=True)
    nominal = models.CharField(max_length=100, blank=True)
    lsl = models.CharField(max_length=100, blank=True)
    usl = models.CharField(max_length=100, blank=True)
    ltl = models.CharField(max_length=100, blank=True)
    utl = models.CharField(max_length=100, blank=True)
    master_grp = models.CharField(max_length=10, blank=True)
    step_no = models.CharField(max_length=10, blank=True)
    auto_man = models.BooleanField(default=False)
    timer = models.CharField(max_length=100, blank=True)
    digits = models.CharField(max_length=10, blank=True)
    id_od = models.CharField(max_length=10, blank=True)

    def __str__(self):
        return f"TableData for {self.parameter_name} ({self.sr_no})"
    






class Operator_setting(models.Model):
    operator_no = models.CharField(max_length=10)
    operator_name = models.CharField(max_length=100)


class master_data(models.Model):
    a = models.FloatField()
    a1 = models.IntegerField()
    b = models.FloatField()
    b1 = models.IntegerField()
    e = models.CharField(max_length=10)
    d = models.FloatField()
    o1 = models.FloatField()
    part_model = models.CharField(max_length=100)
    date_time = models.DateTimeField()
    mastering = models.CharField(max_length=10)
    probe_number = models.IntegerField()  # Add probeNumber as a field


    def __str__(self):
        return f"{self.parameter_name} - {self.part_model}"
    

class User_Data(models.Model):
    id = models.AutoField(primary_key=True)  # Auto-incrementing ID
    username = models.CharField(max_length=255, unique=True)  # Username with a unique constraint

    def __str__(self):
        return self.username    
    

class ComportSetting(models.Model):
    com_port = models.CharField(max_length=255)
    baud_rate = models.CharField(max_length=255)
    parity = models.CharField(max_length=255)
    stop_bit = models.CharField(max_length=255)
    data_bit = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.com_port} - {self.baud_rate}"    
    


class Data_Shift(models.Model):
    shift = models.CharField(max_length=50)
    shift_time = models.CharField(max_length=20) 

    def __str__(self):
        return f"{self.shift} - {self.shift_time}"

    def save(self, *args, **kwargs):
        if self.shift_time:  # Convert the string to a datetime object
            try:
                parsed_time = datetime.strptime(self.shift_time, "%I:%M:%S %p")
                self.shift_time = parsed_time.strftime(" %I:%M:%S %p")
            except ValueError:
                # Handle the case where the string is not in the expected format
                pass
        super().save(*args, **kwargs)


class MeasurementData(models.Model):
    date = models.DateTimeField()
    comp_sr_no = models.CharField(max_length=100)
    part_model = models.CharField(max_length=100)
    part_name = models.CharField(max_length=100)
    operator = models.CharField(max_length=100)
    shift = models.CharField(max_length=10)
    parameter_name = models.CharField(max_length=100)
    lsl = models.FloatField()
    usl = models.FloatField()
    ltl = models.FloatField()
    utl = models.FloatField()
    nominal = models.FloatField()
    output = models.FloatField()
    max_value = models.FloatField()
    min_value = models.FloatField()
    tir_value = models.FloatField()
    statusCell = models.CharField(max_length=100)
    overall_status = models.CharField(max_length=100)

    def __str__(self):
        return f"Measurement for {self.part_name} on {self.date_time}"




class part_retrived(models.Model):
    part_name = models.CharField(max_length=255)  # Field to store the part name



class BackupSettings(models.Model):
    backup_date = models.CharField(max_length=100)  # You can use DateTimeField if needed
    confirm_backup = models.BooleanField(default=False)  # New field to store checkbox value


    def __str__(self):
        return str(self.backup_date)


class ParameterFactor(models.Model):
    part_model = models.CharField(max_length=255)
    parameter_name = models.CharField(max_length=255)
    method = models.CharField(max_length=10, choices=[('+', '+'), ('-', '-')])  # Choose between '+' or '-'
    value = models.CharField(max_length=255)

    # Add a unique constraint to part_model and parameter_name to ensure there is only one per combination
    class Meta:
        unique_together = ('part_model', 'parameter_name')  # Ensures unique (part_model, parameter_name) combination

    def __str__(self):
        return f"{self.part_model} - {self.parameter_name}"
