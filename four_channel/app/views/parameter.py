import json
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from app.models import MeasurementData, Parameter_Settings, master_data, paraTableData

@csrf_exempt  # For development only; use CSRF protection in production
def parameter(request):
    if request.method == "POST":
        try:
            # Parse the incoming JSON data
            data = json.loads(request.body)

            print("The values from the front end", data)

            # Extract parameter settings data
            parameter_settings_data = data.get('parameter_settings', {})
            part_model = parameter_settings_data.get('part_model')
            part_name = parameter_settings_data.get('part_name')
            char_lock = parameter_settings_data.get('char_lock')
            char_lock_limit = parameter_settings_data.get('char_lock_limit')
            punch_no = parameter_settings_data.get('punch_no')

            # Check if the part_model already exists
            existing_part_model = Parameter_Settings.objects.filter(part_model=part_model).first()

            if existing_part_model:
                # Update existing fields if they have changed
                updated = False
                if existing_part_model.part_name != part_name:
                    existing_part_model.part_name = part_name
                    updated = True
                if existing_part_model.char_lock != char_lock:
                    existing_part_model.char_lock = char_lock
                    updated = True
                if existing_part_model.char_lock_limit != char_lock_limit:
                    existing_part_model.char_lock_limit = char_lock_limit
                    updated = True
                if existing_part_model.punch_no != punch_no:
                    existing_part_model.punch_no = punch_no
                    updated = True

                if updated:
                    existing_part_model.save()

                # Update or delete the table data
                table_data = data.get('table_data', [])
                for row in table_data:
                    parameter_name = row.get('parameter_name', '').strip()
                    try:
                        sr_no = int(row.get('sr_no'))  # Cast sr_no to integer
                    except ValueError:
                        continue  # Skip if sr_no is invalid

                    # If parameter_name is cleared, delete the corresponding row
                    if not parameter_name:
                        paraTableData.objects.filter(parameter_settings=existing_part_model, sr_no=sr_no).delete()
                        continue  # Skip processing further for this row

                    # If parameter_name is not cleared, process the data
                    auto_man_value = row.get('auto_man', False)

                    existing_row = paraTableData.objects.filter(parameter_settings=existing_part_model, sr_no=sr_no).first()

                    if existing_row:
                        # If the row exists, update it
                        existing_row.parameter_name = parameter_name
                        existing_row.channel_no = row.get('channel_no')
                        existing_row.low_master = row.get('low_master')
                        existing_row.high_master = row.get('high_master')
                        existing_row.nominal = row.get('nominal')
                        existing_row.lsl = row.get('lsl')
                        existing_row.usl = row.get('usl')
                        existing_row.ltl = row.get('ltl')
                        existing_row.utl = row.get('utl')
                        existing_row.master_grp = row.get('master_grp')
                        existing_row.step_no = row.get('step_no')
                        existing_row.auto_man = auto_man_value
                        existing_row.timer = row.get('timer', '')
                        existing_row.digits = row.get('digits')
                        existing_row.id_od = row.get('id_od')
                        existing_row.save()
                    else:
                        # Create new row if it doesn't exist
                        paraTableData.objects.create(
                            parameter_settings=existing_part_model,
                            sr_no=sr_no,
                            parameter_name=parameter_name,
                            channel_no=row.get('channel_no'),
                            low_master=row.get('low_master'),
                            high_master=row.get('high_master'),
                            nominal=row.get('nominal'),
                            lsl=row.get('lsl'),
                            usl=row.get('usl'),
                            ltl=row.get('ltl'),
                            utl=row.get('utl'),
                            master_grp=row.get('master_grp'),
                            step_no=row.get('step_no'),
                            auto_man=auto_man_value,
                            timer=row.get('timer', ''),
                            digits=row.get('digits'),
                            id_od=row.get('id_od')
                        )

                return JsonResponse({'message': 'Data updated successfully!'}, status=200)

            else:
               # Safer sr_no extraction
                sr_no_value = parameter_settings_data.get('sr_no')
                sr_no = int(sr_no_value) if sr_no_value not in (None, '') else 0

                # Then use sr_no normally
                parameter_settings = Parameter_Settings.objects.create(
                    sr_no=sr_no,
                    part_model=part_model,
                    part_name=part_name,
                    char_lock=char_lock,
                    char_lock_limit=char_lock_limit,
                    punch_no=punch_no
                )


                # Save or delete the table data
                table_data = data.get('table_data', [])
                for row in table_data:
                    parameter_name = row.get('parameter_name', '').strip()
                    try:
                        sr_no = int(row.get('sr_no'))  # Cast sr_no to integer
                    except ValueError:
                        continue  # Skip if sr_no is invalid

                    # If parameter_name is cleared, delete the corresponding row
                    if not parameter_name:
                        paraTableData.objects.filter(parameter_settings=parameter_settings, sr_no=sr_no).delete()
                        continue  # Skip processing further for this row

                    paraTableData.objects.create(
                        parameter_settings=parameter_settings,
                        sr_no=sr_no,
                        parameter_name=parameter_name,
                        channel_no=row.get('channel_no'),
                        low_master=row.get('low_master'),
                        high_master=row.get('high_master'),
                        nominal=row.get('nominal'),
                        lsl=row.get('lsl'),
                        usl=row.get('usl'),
                        ltl=row.get('ltl'),
                        utl=row.get('utl'),
                        master_grp=row.get('master_grp'),
                        step_no=row.get('step_no'),
                        auto_man=row.get('auto_man', False),
                        timer=row.get('timer', ''),
                        digits=row.get('digits'),
                        id_od=row.get('id_od')
                    )

                return JsonResponse({'message': 'Data saved successfully!'}, status=200)

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

    elif request.method == "DELETE":
        try:
            # Parse the incoming JSON data
            data = json.loads(request.body)
            part_model = data.get('part_model')

            if not part_model:
                return JsonResponse({'error': 'Part Model is required.'}, status=400)

            # Attempt to delete the corresponding record
            deleted_count, _ = Parameter_Settings.objects.filter(part_model=part_model).delete()
            delete_count1, _ = MeasurementData.objects.filter(part_model=part_model).delete()
            delete_count2, _ = master_data.objects.filter(part_model=part_model).delete()

            if deleted_count > 0:
                return JsonResponse({'message': f'Part Model "{part_model}" deleted successfully.'}, status=200)
            else:
                return JsonResponse({'error': f'Part Model "{part_model}" not found.'}, status=404)

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

    elif request.method == "GET":
        part_model = request.GET.get('part_model', None)
        print("part model value from the front end:", part_model)

        if part_model:
            # Fetch records that match the given part_model and order by id (to keep the original save order)
            parameter_settings = Parameter_Settings.objects.filter(part_model=part_model).order_by('id')

            # Prepare data for response
            data = []

            for setting in parameter_settings:
                table_data = [
                    {
                        "sr_no": row.sr_no,
                        "parameter_name": row.parameter_name,
                        "channel_no": row.channel_no,
                        "low_master": row.low_master,
                        "high_master": row.high_master,
                        "nominal": row.nominal,
                        "lsl": row.lsl,
                        "usl": row.usl,
                        "ltl": row.ltl,
                        "utl": row.utl,
                        "master_grp":row.master_grp,
                        "step_no": row.step_no,
                        "auto_man": row.auto_man,  # Include auto_man field
                        "timer": row.timer,       # Include timer field
                        "digits": row.digits,
                        "id_od": row.id_od,
                    }
                    for row in setting.table_data.all()
                ]

                data.append({
                    "sr_no": setting.sr_no,
                    "part_model": setting.part_model,
                    "part_name": setting.part_name,
                    "char_lock": setting.char_lock,
                    "char_lock_limit": setting.char_lock_limit,
                    "punch_no": setting.punch_no,
                    "table_data": table_data,
                })
                print("table_data", table_data)

            return JsonResponse({'parameter_settings': data}, status=200)


        

        try:
            # Fetch all Parameter_Settings records
            parameter_settings = Parameter_Settings.objects.all().order_by('id')  # This retrieves all records
            table_data = paraTableData.objects.all()  # You can fetch all related paraTableData records if needed

            # Create a dictionary with sequential keys starting from 1
            parameter_settings_dict = {
                index + 1: setting.part_model
                for index, setting in enumerate(parameter_settings)
            }

            # Convert the dictionary to a JSON string
            parameter_settings_json = json.dumps(parameter_settings_dict)

            # Pass the data to the template
            context = {
                'parameter_settings_dict': parameter_settings_dict,
                'parameter_settings_json': parameter_settings_json,
            }
            return render(request, 'app/parameter.html', context)

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
            

    return render(request, 'app/parameter.html')

