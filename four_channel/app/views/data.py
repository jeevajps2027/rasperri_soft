import json
from django.shortcuts import render
from django.http import JsonResponse
from django.urls import reverse
from app.models import Parameter_Settings, paraTableData, master_data
from django.views.decorators.csrf import csrf_exempt
from datetime import datetime

@csrf_exempt
def data(request):
    if request.method == "POST" and request.headers.get('x-requested-with') == 'XMLHttpRequest':
        data = json.loads(request.body)  # Get the payload from the request body (not using 'POST.get' for JSON)
        print('your data from front end:', data)
        
        for item in data.get('payload', []):
        
            # Correct format for date_time
            date_time = datetime.strptime(item['date_time'], '%d/%m/%Y %I:%M:%S %p')
            print('your date and time is this:',date_time)
            
            # Save data to MasterData table with the unique_id
            master_data.objects.create(
                a=item['a'],
                a1=item['a1'],
                b=item['b'],
                b1=item['b1'],
                e=item['e'],
                d=item['d'],
                o1=item['o1'],
                part_model=item['part_model'],
                date_time=date_time,
                mastering=item['mastering'],
                probe_number=item['probeNumber']
            )

        # Respond with success message
        return JsonResponse({
            "message": "Data successfully saved!"
        })

    return render(request, 'app/master.html')
