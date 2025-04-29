from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from datetime import datetime
import pytz
from app.models import MeasurementData  # Import your model
from django.contrib.auth import authenticate

@csrf_exempt  # Disable CSRF for simplicity (only use in development or with proper safeguards)
def measure_data(request):
    if request.method == 'POST':

        
        try:
            data = json.loads(request.body)
            print("The value which is received from the frontend:", data)

            # Example of processing the data
            for entry in data:
                # Extract the date string from the request
                date_str = entry.get('date')  # Assuming 'date' is a string in 'dd/mm/yyyy hh:mm:ss AM/PM' format
                print("Original date string:", date_str)

                # Convert the date string to a datetime object
                try:
                    date_obj = datetime.strptime(date_str, '%d/%m/%Y %I:%M:%S %p')

                    # Make the datetime object timezone-aware
                    timezone = pytz.timezone('Asia/Kolkata')  # Replace with your desired timezone
                    date_obj_aware = timezone.localize(date_obj)

                    # Optionally, you can convert the datetime object to UTC or remove timezone info if needed
                    date_obj_naive = date_obj_aware.replace(tzinfo=None)

                    print("Timezone-aware date:", date_obj_aware)
                    print("Naive date (without timezone):", date_obj_naive)

                except ValueError as e:
                    return JsonResponse({'status': 'error', 'message': f"Invalid date format: {str(e)}"}, status=400)

                # Now proceed to extract and store other fields
                comp_sr_no = entry.get('punchNo')
                print("comp_sr_no",comp_sr_no)
                part_model = entry.get('partModel')
                part_name = entry.get('partName')
                operator = entry.get('operator')
                shift = entry.get('shift')
                parameter_name = entry.get('parameterName')
                lsl = entry.get('lsl')
                usl = entry.get('usl')
                ltl = entry.get('ltl')
                utl = entry.get('utl')
                nominal = entry.get('nominal')
                output = entry.get('output')
                max_value = entry.get('max')
                min_value = entry.get('min')
                tir_value = entry.get('tir')
                statusCell = entry.get('statusCell')
                overall_status = entry.get('overallStatusInput')

                # Create a new MeasurementData object and save it to the database
                measurement_data = MeasurementData(
                    date=date_obj_naive,
                    comp_sr_no=comp_sr_no,
                    part_model=part_model,
                    part_name=part_name,
                    operator=operator,
                    shift=shift,
                    parameter_name=parameter_name,
                    lsl=lsl,
                    usl=usl,
                    ltl=ltl,
                    utl=utl,
                    nominal=nominal,
                    output=output,
                    max_value=max_value,
                    min_value=min_value,
                    tir_value=tir_value,
                    statusCell = statusCell,
                    overall_status=overall_status,
                )

                # Save the measurement data to the database
                measurement_data.save()

            return JsonResponse({'status': 'success', 'message': 'Data received and saved successfully'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=400)



@csrf_exempt
def delete_measure_data(request):
    if request.method == 'POST':
        try:
            # Parse JSON data from request body
            data = json.loads(request.body)

            comp_sr_no = data.get('input_value', '')  # Get comp_sr_no
            part_model = data.get('part_model', '')  # Get part_model
            user_id = data.get('user_id', '')  # Get user ID (from credentials request)
            password = data.get('password', '')  # Get password (from credentials request)

            # Step 1: Check if comp_sr_no exists for the specified part_model
            existing_record = MeasurementData.objects.filter(comp_sr_no=comp_sr_no, part_model=part_model)

            if existing_record.exists():
                # Step 2: Send response for overwrite confirmation if the record exists
                if not user_id or not password:  # Credentials not provided yet
                    return JsonResponse({
                        'status': 'exists',
                        'message': f'Punch number "{comp_sr_no}" already exists for model "{part_model}". Do you want to overwrite it?'
                    })

                # Step 3: If credentials are provided, verify them and proceed with deletion
                if user_id != 'admin' or password != 'admin':
                    return JsonResponse({'success': False, 'message': 'Invalid credentials!'})

                # Proceed with deletion
                deleted_count, _ = existing_record.delete()

                if deleted_count > 0:
                    return JsonResponse({'success': True, 'message': 'Punch number deleted successfully!'})
                else:
                    return JsonResponse({'success': False, 'message': 'Punch number not found for this model!'})

            else:
                # If comp_sr_no doesn't exist, simply return a success response without triggering the overwrite flow
                return JsonResponse({'success': True, 'message': 'New punch number, no action needed for deletion.'})

        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})

    return JsonResponse({'success': False, 'message': 'Invalid request'})