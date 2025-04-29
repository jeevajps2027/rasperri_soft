from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from app.models import Parameter_Settings, ParameterFactor, paraTableData
from django.db.models import Q

# Fetch parameter names based on selected part_model
def get_parameters(request):
    part_model = request.GET.get('part_model')

    if part_model:
        try:
            param_setting = Parameter_Settings.objects.get(part_model=part_model)
            table_data = paraTableData.objects.filter(parameter_settings=param_setting).order_by('id')

            parameter_names = list(table_data.values_list('parameter_name', flat=True))
            return JsonResponse({'parameter_names': parameter_names})

        except Parameter_Settings.DoesNotExist:
            return JsonResponse({'error': 'Part model not found'}, status=404)

    return JsonResponse({'parameter_names': []})


# Fetch parameter value based on selected part_model and parameter_name
def get_parameter_value(request):
    part_model = request.GET.get('part_model')
    parameter_name = request.GET.get('parameter_name')

    if part_model and parameter_name:
        parameter_factor = ParameterFactor.objects.filter(
            part_model=part_model, parameter_name=parameter_name
        ).first()

        if parameter_factor:
            return JsonResponse({
                'value': parameter_factor.value or '',
                'method': parameter_factor.method or ''  # Fetch method value
            })
        
        print("parameter_factor",parameter_factor)   

    return JsonResponse({'value': '', 'method': ''})
