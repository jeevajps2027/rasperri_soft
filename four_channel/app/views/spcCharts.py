import json
from django.http import JsonResponse
import numpy as np
import pandas as pd

from django.shortcuts import render
import matplotlib.pyplot as plt
import io
import base64

from app.models import Data_Shift, MeasurementData, Parameter_Settings, paraTableData


def encode_chart_to_base64(fig):
    """Encodes a Matplotlib figure to a base64 image string."""
    buf = io.BytesIO()
    fig.savefig(buf, format='png', bbox_inches='tight')
    buf.seek(0)
    image_base64 = base64.b64encode(buf.read()).decode('utf-8')
    buf.close()
    plt.close(fig)  # Close the figure to free memory
    return image_base64

def generate_r_chart(readings, sample_size):
    """Generates an X-bar and R chart and returns the image as a base64 string."""
    subgroups = [readings[i:i + sample_size] for i in range(0, len(readings), sample_size)]
    x_bar = [np.mean(group) for group in subgroups]
    r_values = [np.max(group) - np.min(group) for group in subgroups]

    # Plot X-bar and R charts
    fig, axs = plt.subplots(2, 1, figsize=(10, 5))
    axs[0].plot(x_bar, marker='o', label='X-bar')
    axs[0].set_title('X-bar Chart')
    axs[0].set_xlabel('Subgroup')
    axs[0].set_ylabel('X-bar')
    axs[0].legend()

    axs[1].plot(r_values, marker='o', color='orange', label='Range')
    axs[1].set_title('R Chart')
    axs[1].set_xlabel('Subgroup')
    axs[1].set_ylabel('Range')
    axs[1].legend()

    plt.tight_layout()
    return encode_chart_to_base64(fig)
def generate_readings_table(subgroups, x_bars, ranges):
    """
    Generates an HTML table for subgroup readings with sum, mean, and range rows.
    Limits to 20 columns, and shows alert if more data is present.
    """
    max_columns = 20
    df = pd.DataFrame(subgroups).transpose()

    alert_message = ""
    if df.shape[1] > max_columns:
        df = df.iloc[:, :max_columns]
        alert_message = """
        <script>
            alert("Only the first 20 subgroups are displayed. Some data is hidden.");
        </script>
        """

    df.columns = [f'X{i + 1}' for i in range(df.shape[1])]
    df.loc['Sum'] = df.sum()
    df.loc['X̄ (Mean)'] = x_bars[:max_columns]
    df.loc['R̄ (Range)'] = ranges[:max_columns]

    style = """
    <style>
        table.table {
            font-size: 10px;
            width: 100%;
        }
        table.table th, table.table td {
            padding: 2px;
            max-width: 50px;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }
        table.table th {
            background-color: #20b2aa;
        }
    </style>
    """

    return alert_message + style + df.to_html(classes="table table-striped", index=True, header=True)


def generate_histogram(readings):
    """Generates a histogram and returns the image as a base64 string."""
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.hist(readings, bins=10, color='skyblue', edgecolor='black')
    ax.set_title('Histogram')
    ax.set_xlabel('Readings')
    ax.set_ylabel('Frequency')
    plt.tight_layout()
    return encode_chart_to_base64(fig)


def generate_pie_chart(status):
    """Generates a pie chart based on the status values and returns it as a base64 string."""
    # Count the occurrences of each unique status
    status_counts = pd.Series(status).value_counts()

    # Map colors for the pie chart
    colors = {
        'accept': '#32CD32',  # Parrot green
        'reject': '#FF6347',  # Tomato red
        'rework': '#FFFF00',  # Yellow
    }
    # Assign colors based on status keys
    pie_colors = [colors.get(key.lower(), '#808080') for key in status_counts.index]  # Default to gray if not mapped

    # Generate the pie chart
    fig, ax = plt.subplots(figsize=(8, 6))
    ax.pie(
        status_counts, 
        labels=status_counts.index, 
        autopct='%1.1f%%', 
        startangle=90, 
        colors=pie_colors
    )
    ax.set_title('Status Distribution')

    return encode_chart_to_base64(fig)


def spcCharts(request):
    if request.method == 'POST':
        raw_data = request.POST.get('data')
        if raw_data:
            data = json.loads(raw_data)

            from_date = data.get('from_date')
            part_model = data.get('part_model')
            parameter_name = data.get('parameter_name')
            mode = data.get('mode')  # Can be 'r_chart', 'histogram', or 'piechart'
            sample_size = int(data.get('sample_size'))
            to_date = data.get('to_date')
            shift = data.get('shift')

            if not all([from_date, to_date, part_model]):
                return JsonResponse({'error': 'Missing required fields: from_date, to_date, or part_model'}, status=400)

            # Query filter setup
            filter_kwargs = {
                'date__range': (from_date, to_date),
                'part_model': part_model,
            }
            if shift != "ALL":
                filter_kwargs['shift'] = shift
            if parameter_name != "ALL":
                filter_kwargs['parameter_name'] = parameter_name

            filtered_data = MeasurementData.objects.filter(**filter_kwargs).order_by('date')
            filtered_list = filtered_data.values('output')
            filtered_result = filtered_data.values('overall_status')

            if not filtered_list:
                return JsonResponse({'error': 'No data found for the given criteria'}, status=404)

            # Extract readings
            readings = [float(r['output']) for r in filtered_list]

            # Handle `overall_status` values
            status = []
            for r in filtered_result:
                try:
                    # Attempt to convert to float
                    status.append(float(r['overall_status']))
                except ValueError:
                    # If conversion fails, append the original string
                    status.append(r['overall_status'])

            print("Status:", status)
            print("Status Length:", len(status))

            # Generate the chart based on mode
            chart_img = None
            table_html = None
            if mode == 'r_chart':
                chart_img = generate_r_chart(readings, sample_size)
                subgroups = [readings[i:i + sample_size] for i in range(0, len(readings), sample_size)]
                x_bars = [np.mean(group) for group in subgroups]
                ranges = [np.max(group) - np.min(group) for group in subgroups]
                table_html = generate_readings_table(subgroups, x_bars, ranges)
            elif mode == 'histogram':
                chart_img = generate_histogram(readings)
            elif mode == 'piechart':
                chart_img = generate_pie_chart(status)

            # Return both chart and table if applicable
            return JsonResponse({
                'chart_img': chart_img,
                'table': table_html if table_html else '',
            })

        return render(request, 'app/spcCharts.html')
  
    

    elif request.method == 'GET':

        part_model = request.GET.get('part_model', '')
        # Process the part_model as needed
        print(f'Received part model: {part_model}')

        parameter_setting = Parameter_Settings.objects.get(part_model=part_model)
            # Get all related paraTableData
        parameter_names = list(paraTableData.objects.filter(parameter_settings=parameter_setting).values_list('parameter_name', flat=True).order_by('id'))
        print("parameter_names",parameter_names)

       
        shift_values = Data_Shift.objects.order_by('id').values_list('shift', 'shift_time').distinct()
        shift_name_queryset = Data_Shift.objects.order_by('id').values_list('shift', flat=True).distinct()
        shift_name = list(shift_name_queryset)
        print ("shift_name",shift_name)

        # Convert the QuerySet to a list of lists
        shift_values_list = list(shift_values)
        
        # Serialize the list to JSON
        shift_values_json = json.dumps(shift_values_list)
        print("shift_values_json",shift_values_json)

         # Create a context dictionary to pass the data to the template
        context = {
            'shift_values': shift_values_json,
            'shift_name':shift_name,
            'parameter_names':parameter_names,
        }

    return render(request,'app/spcCharts.html',context)