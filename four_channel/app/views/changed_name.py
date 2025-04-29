from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from app.models import part_retrived
import json
from django.shortcuts import render
from django.urls import reverse
@csrf_exempt
def changed_name(request):
    if request.method == "POST":
        # Parse incoming JSON data
        try:
            data = json.loads(request.body.decode('utf-8'))  # Decode JSON data
            print('Your received data is this:', data)

            # Extract part_name from data
            part_name = data.get('part_names', '')

            if part_name:  # Validate input
                # Fetch or create a row with ID 1
                measurement, created = part_retrived.objects.get_or_create(id=1)
                measurement.part_name = part_name  # Update part_name
                measurement.save()  # Save changes

                return JsonResponse({
                    "redirect_url": reverse('master'),
                    "status": "success", 
                    "message": "Part name saved successfully!"
                })
            else:
                return JsonResponse({
                    "status": "error", 
                    "message": "Part name is required!"
                })
        except json.JSONDecodeError:
            return JsonResponse({"status": "error", "message": "Invalid JSON data!"})

    elif request.method == "GET":
        # Fetch all stored values
        new_part = list(part_retrived.objects.all().values())  # Convert QuerySet to list
        print('Stored values in the database:', new_part)  # Print in terminal


    # Render the HTML template
    return render(request, 'app/master.html')
