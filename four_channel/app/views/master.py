from collections import defaultdict
import json
from django.shortcuts import render
from django.http import JsonResponse
from django.urls import reverse
from app.models import Parameter_Settings,paraTableData,master_data,part_retrived
from django.views.decorators.csrf import csrf_exempt
from datetime import datetime
from django.core.serializers import serialize
from django.db.models import Max


@csrf_exempt
def master(request):
    if request.method == "POST" and request.headers.get('x-requested-with') == 'XMLHttpRequest':
        # Handle AJAX POST
        part_name = request.POST.get('part_name', '')
        print(f"your received value from front end:: {part_name}")

        
        filtered_data = Parameter_Settings.objects.filter(
            part_model=part_name
        ).order_by('id')  # Ensures the order is by 'id' 

        print('Filtered data from Parameter_Settings:', filtered_data)

        # Step 2: Get all `parameter_name` values from `paraTableData` related to `filtered_data`
        probe_no = paraTableData.objects.filter(
            parameter_settings__in=filtered_data
        ).values_list('channel_no', flat=True).distinct().order_by('parameter_settings__id')

        print('probe_no from paraTableData:', list(probe_no))




        # Convert probe_no list to integers (if they are strings)
        probe_no = list(map(int, probe_no))

        # Get the last stored `id` for each `probe_number`
        last_probes = (
            master_data.objects.filter(part_model=part_name, probe_number__in=probe_no)
            .values('probe_number')
            .annotate(last_id=Max('id'))  # Get the latest ID for each probe_number
        )

        # Fetch complete details of the last stored entry for each `probe_number`
        last_probe_dict = {}
        for entry in last_probes:
            probe_number = entry['probe_number']
            last_id = entry['last_id']
            
            # Retrieve full record with this last_id
            last_record = master_data.objects.filter(id=last_id).values('id', 'probe_number', 'e', 'd', 'o1').first()
            
            if last_record:
                last_probe_dict[probe_number] = last_record


        # Format the data
        parameter_values = [
            {
                "probe_number": f"{probe_number}",
                "id": values.get("id"),
                "e": values.get("e"),
                "d": values.get("d"),
                "o1": values.get("o1"),
            }
            for probe_number, values in last_probe_dict.items()
        ]

         # Print values in the terminal
        for param in parameter_values:
            print(f"Probe Name: {param['probe_number']}, ID: {param['id']}, e: {param['e']}, d: {param['d']}, o1: {param['o1']}")


      



        matching_settings = Parameter_Settings.objects.filter(part_model=part_name).distinct().order_by("id")

        # Dictionary to store grouped distinct data by channel_no
        grouped_data = {}

        for setting in matching_settings:
            para_data = paraTableData.objects.filter(parameter_settings=setting).order_by("id")

            for data in para_data:
                channel = data.channel_no

                if channel not in grouped_data:
                    grouped_data[channel] = {
                        "parameters": set(),
                        "channel_no":set(),
                        "low_master": set(),
                        "high_master": set(),
                        "nominal": set(),
                        "lsl": set(),
                        "usl": set(),
                        "ltl": set(),
                        "utl": set(),
                        "step_no": set(),
                        "master_grp": set(),
                        "id_od": set(),
                        "digits": set(),
                    }

                grouped_data[channel]["parameters"].add(data.parameter_name)
                grouped_data[channel]["low_master"].add(data.low_master)
                grouped_data[channel]["high_master"].add(data.high_master)
                grouped_data[channel]["channel_no"].add(data.channel_no)
                grouped_data[channel]["nominal"].add(data.nominal)
                grouped_data[channel]["lsl"].add(data.lsl)
                grouped_data[channel]["usl"].add(data.usl)
                grouped_data[channel]["ltl"].add(data.ltl)
                grouped_data[channel]["utl"].add(data.utl)
                grouped_data[channel]["step_no"].add(data.step_no)
                grouped_data[channel]["master_grp"].add(data.master_grp)
                grouped_data[channel]["id_od"].add(data.id_od)
                grouped_data[channel]["digits"].add(data.digits)

        # Convert sets to lists
        for channel, details in grouped_data.items():
            grouped_data[channel] = {key: list(value) for key, value in details.items()}

        # Extract final arrays across all channels
        final_data = {
            "low_master": [],
            "high_master": [],
            "nominal": [],
            "channel_no":[],
            "lsl": [],
            "usl": [],
            "ltl": [],
            "utl": [],
            "step_no": [],
            "master_grp":[],
            "id_od": [],
            "digits": [],
        }

        for channel, details in grouped_data.items():
            final_data["low_master"].extend(details["low_master"])
            final_data["high_master"].extend(details["high_master"])
            final_data["channel_no"].extend(details["channel_no"])
            final_data["nominal"].extend(details["nominal"])
            final_data["lsl"].extend(details["lsl"])
            final_data["usl"].extend(details["usl"])
            final_data["ltl"].extend(details["ltl"])
            final_data["utl"].extend(details["utl"])
            final_data["step_no"].extend(details["step_no"])
            final_data["master_grp"].extend(details["master_grp"])
            final_data["id_od"].extend(details["id_od"])
            final_data["digits"].extend(details["digits"])

        # Print the final arrays
       
       


       

        # Respond with redirect URL for client-side navigation
        return JsonResponse({
            "redirect_url": reverse('master'),
            "parameter_names": list(probe_no),  # Convert QuerySet to list
            "final_data": final_data,
            "parameter_values": parameter_values,
        }, safe=False)


    elif request.method == "GET":

        part_name = None
        # Fetch all stored values
        new_part = part_retrived.objects.filter(id=1).values('part_name').first()  # Get part_name only

        if new_part:  # Check if data exists
            part_name = new_part['part_name']  # Extract part_name
            print('Part name:', part_name)  # Print only part_name
        else:
            print('No data found!')  # Handle empty database


    return render(request, 'app/master.html',{"part_name":part_name})