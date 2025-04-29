import json
from django.http import JsonResponse
from django.shortcuts import render
from app.models import BackupSettings, Operator_setting, ComportSetting,Data_Shift, Parameter_Settings, ParameterFactor, paraTableData  # Import your models
import serial.tools.list_ports  # Import list_ports module


def comport(request):
    if request.method == "POST":
        try:
            # Parse the incoming JSON data
            data = json.loads(request.body)
            print('Your data from comport:', data)

           

           

            request_type = data[0].get("request_type") if isinstance(data, list) and len(data) > 0 else data.get("request_type")  # Safely get the request type

            if request_type == 'delete':
                operator_no = data.get("operator_no")
                operator_name = data.get("operator_name")

                if operator_no and operator_name:
                    # Try to find and delete the operator using operator_no
                    try:
                        operator = Operator_setting.objects.get(operator_no=operator_no)
                        operator.delete()
                        return JsonResponse({"status": "success", "message": "Operator deleted successfully"})
                    except Operator_setting.DoesNotExist:
                        return JsonResponse({"status": "error", "message": "Operator not found"})
              # Save operator
            elif request_type == "operator":
                if isinstance(data, list):
                    for row in data:
                        operator_no = row.get("operator_no")
                        operator_name = row.get("operator_name")

                        print("operator_no:", operator_no)
                        print("operator_name:", operator_name)

                        if operator_no and operator_name:
                            operator, created = Operator_setting.objects.get_or_create(
                                operator_no=operator_no,
                                defaults={'operator_name': operator_name}
                            )
                            if not created:
                                operator.operator_name = operator_name
                                operator.save()
                        else:
                            return JsonResponse({
                                "status": "error",
                                "message": "Missing operator_no or operator_name"
                            })

                    return JsonResponse({
                        "status": "success",
                        "message": "Operator data saved successfully"
                    })
                else:
                    return JsonResponse({
                        "status": "error",
                        "message": "Invalid operator data format"
                    })
            
            elif request_type == 'backup_date':
                # Get the backup date from the request data
                backup_date = data.get('backup_data')
                confirm_backup = data.get('confirm_backup')  # Retrieve checkbox value

                
                print("Backup Date Settings:")
                print("backup_date:", backup_date)  # Print the received backup date
                print("Confirm Backup Checkbox:", confirm_backup)  # Print checkbox value


                BackupSettings.objects.create(
                    backup_date=backup_date,
                    confirm_backup=confirm_backup  # Save the checkbox state
                )

                return JsonResponse({'status': 'success'})

            elif request_type == "shift_settings":
                shift = data.get('shift')
                shift_time = data.get('shift_time')

                print("Shift Settings:")
                print("shift:", shift)
                print("shift_time:", shift_time)

                existing_shift = Data_Shift.objects.filter(shift=shift).first()

                if existing_shift:
                    existing_shift.shift_time = shift_time
                    existing_shift.save()
                else:
                    shift_settings_obj = Data_Shift.objects.create(shift=shift, shift_time=shift_time)
                    shift_settings_obj.save()


                return JsonResponse({"status": "success", "message": "Shift settings saved successfully!"})
    
            elif request_type == 'parameter_factor':
                part_model = data.get('part_model')
                parameter_name = data.get('parameter_name')
                method = data.get('method')
                value = data.get('value')

                 # Check if a ParameterFactor record already exists with the same part_model and parameter_name
                probe_factor, created = ParameterFactor.objects.update_or_create(
                    part_model=part_model,
                    parameter_name=parameter_name,
                    defaults={'method': method, 'value': value}  # Update method and value if exists
                )
                if part_model:
                    try:
                        param_setting = Parameter_Settings.objects.get(part_model=part_model)
                        table_data = paraTableData.objects.filter(parameter_settings=param_setting)

                        parameter_names = list(table_data.values_list('parameter_name', flat=True))
                        return JsonResponse({'parameter_names': parameter_names})

                    except Parameter_Settings.DoesNotExist:
                        return JsonResponse({'error': 'Part model not found'}, status=404)
                

            elif request_type == "comport":
                # Handle comport data
                com_port = data.get("com_port")
                baud_rate = data.get("baud_rate")
                parity = data.get("parity")
                stop_bit = data.get("stop_bit")
                data_bit = data.get("data_bit")

                # Validate the extracted values
                if com_port and baud_rate and parity and stop_bit and data_bit:
                    # Save to database using get_or_create
                    setting, created = ComportSetting.objects.get_or_create(
                        id=1,  # Assuming only one record for global settings
                        defaults={
                            "com_port": com_port,
                            "baud_rate": baud_rate,
                            "parity": parity,
                            "stop_bit": stop_bit,
                            "data_bit": data_bit,
                        }
                    )
                    if not created:
                        # Update the existing record
                        setting.com_port = com_port
                        setting.baud_rate = baud_rate
                        setting.parity = parity
                        setting.stop_bit = stop_bit
                        setting.data_bit = data_bit
                        setting.save()

                    return JsonResponse({"status": "success", "message": "Comport data saved successfully"})
                else:
                    return JsonResponse({"status": "error", "message": "Missing comport data"})

            
            else:
                return JsonResponse({"status": "error", "message": "Unknown request type"})

        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)})
        
    elif request.method == "GET":
        ports = serial.tools.list_ports.comports()
        port_list = [port.device for port in ports]
        
        # Print the serial ports to the terminal
        print("Available Serial Ports:")
        for port in port_list:
            print(port)


        operators_value = Operator_setting.objects.all().order_by('id')
        comport_data = ComportSetting.objects.all()
        shift_settings = Data_Shift.objects.all().order_by('id')
        backup_date = BackupSettings.objects.order_by('-id').first()
        part_model_values = Parameter_Settings.objects.values_list('part_model', flat=True).distinct()
        print('your data from shift_settings is this:',shift_settings)
        print('your comport data is thiss::',comport_data)
        context = {
            "operators_value": operators_value,
            "port_list": port_list,
            'shift_settings': shift_settings,
             'backup_date': backup_date,
             'part_model_values':part_model_values,
        }
    
        return render(request, "app/comport.html", context)


