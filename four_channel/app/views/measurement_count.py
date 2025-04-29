from datetime import datetime
import time
import os
from django.http import JsonResponse
from django.shortcuts import render
import json
from django.views.decorators.csrf import csrf_exempt
from app.models import MeasurementData
from collections import defaultdict
from django.db.models import Count



@csrf_exempt
def measurement_count(request):
    if request.method == 'POST':# Retrieve input parameters
        input_date = request.POST.get('date')
        input_shift = request.POST.get('shift')
        input_partModel = request.POST.get('part_model')

        print("Received Date:", input_date)
        print("Received Shift:", input_shift)
        print("Received partModel:", input_partModel)

        only_date = []
        formatted_date = []

        if input_date:
            # Parse the input_date string with the correct format 'YYYY/MM/DD hh:mm:ss AM/PM'
            try:
                input_date_obj = datetime.strptime(input_date, '%Y/%m/%d %I:%M:%S %p')
                
                # Extract only the date part
                only_date = input_date_obj.date()

                # Log the extracted date
                print("Only Date (without time):", only_date)

                # Convert the date to string format 'YYYY-MM-DD'
                formatted_date = only_date.strftime('%Y-%m-%d')
            except ValueError as e:
                print(f"Error parsing date: {e}")

        # Query MeasurementData to fetch date and overall_status
        filtered_data = (
            MeasurementData.objects
            .filter(part_model=input_partModel,date__date=formatted_date, shift=input_shift)  # Fetch date and overall_status
            .values('date', 'overall_status')
            .annotate(count=Count('overall_status'))  # Count occurrences of overall_status
            .order_by('date')  # Sort by date
        )

        # Initialize structures to store results
        distinct_status_counts = defaultdict(int)  # To track incremental counts for each status
        status_with_datetime = defaultdict(list)  # To store results by datetime and status

        # Initialize a dictionary to store the last occurrence for 'ACCEPT', 'REJECT', and 'REWORK'
        last_occurrence = {
            'accept': None,
            'reject': None,
            'rework': None
        }

        # Variable to track the total occurrence sum
        total_occurrence = 0

        # Process the query result
        for entry in filtered_data:
            status = entry['overall_status'].lower()  # Convert status to lowercase for comparison
            date_time = entry['date']
            formatted_date = date_time.strftime('%d/%m/%Y %I:%M:%S %p')  # Format date and time

            # Increment the counter for the current status
            distinct_status_counts[status] += 1

            # Store the formatted date, status, count, and occurrence number
            status_with_datetime[formatted_date].append({
                'status': status,
                'count': entry['count'],
                'occurrence': distinct_status_counts[status]
            })

            # Update the last occurrence for specific statuses (ACCEPT, REJECT, REWORK)
            if status in last_occurrence:
                last_occurrence[status] = {
                    'formatted_date': formatted_date,
                    'count': entry['count'],
                    'occurrence': distinct_status_counts[status]
                }

        # Calculate the total occurrence sum by adding the last occurrence values of 'accept', 'reject', and 'rework'
        for status in ['accept', 'reject', 'rework']:
            occurrence = last_occurrence[status]
            if occurrence:
                total_occurrence += occurrence['occurrence']

        # Print the last occurrence for each of 'accept', 'reject', and 'rework'
        print("\nLast Occurrence for Each Status (accept, reject, rework):")
        for status in ['accept', 'reject', 'rework']:
            occurrence = last_occurrence[status]
            if occurrence:
                print(f"Status: {status.capitalize()}, Last Occurrence: {occurrence['formatted_date']}, "
                    f"Count: {occurrence['count']}, Occurrence: {occurrence['occurrence']}")
            else:
                print(f"Status: {status.capitalize()} has no occurrences.")

        # Print the total occurrence sum
        print(f"\nTotal Occurrence (Last Occurrence Accept + Reject + Rework): {total_occurrence}")


        # Prepare the response data
        response_data = {
            'accept_occurrence': last_occurrence['accept']['occurrence'] if last_occurrence['accept'] else 0,
            'reject_occurrence': last_occurrence['reject']['occurrence'] if last_occurrence['reject'] else 0,
            'rework_occurrence': last_occurrence['rework']['occurrence'] if last_occurrence['rework'] else 0,
            'total_occurrence': total_occurrence,
        }

        return JsonResponse(response_data)
    return render(request,"app/measurement.html")