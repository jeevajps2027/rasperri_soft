from django.http import JsonResponse
from django.shortcuts import render
from app.models import BackupSettings, Operator_setting, User_Data
import json
from django.views.decorators.csrf import csrf_exempt



@csrf_exempt
def login(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            username = data.get('username')
            password = data.get('password')

            # Ensure username is not empty or None
            if not username:
                return JsonResponse({'status': 'error', 'message': 'Username is required.'}, status=400)

            if not username == 'SAADMIN':
                user, created = User_Data.objects.get_or_create(id=1)  # Always use ID 1
                user.username = username  # Update the username field with the new value
                user.save()

                # Print information about the operation
                if created:
                    print(f'New username created: {user.username}')
                else:
                    print(f'Username already exists: {user.username}')

            # Check credentials
            if username == 'SAADMIN' and password == 'saadmin':
                request.session['username'] = username
                return JsonResponse({'status': 'success', 'message': 'Login successful', 'redirect': '/measurement/'})
            
            # Check against Operator_setting
            elif Operator_setting.objects.filter(operator_name=username).exists() and password == 'admin@1234':
                request.session['username'] = username
                return JsonResponse({'status': 'success', 'message': 'Login successful', 'redirect': '/measurement/'})
            else:
                return JsonResponse({'status': 'error', 'message': 'Invalid username or password'})

        except json.JSONDecodeError:
            return JsonResponse({'status': 'error', 'message': 'Invalid request format'}, status=400)
    elif request.method == 'GET':
        # Fetch all operator names
        operators = Operator_setting.objects.all()
        operator_names = [operator.operator_name for operator in operators]

        # Get the latest BackupSettings entry
        backup_settings = BackupSettings.objects.order_by('-id').first()

        # Prepare context for BackupSettings
        if backup_settings:
            # Print both backup_date and confirm_backup values in the terminal
            print('ID:', backup_settings.id)
            print('Backup Date:', backup_settings.backup_date)
            print('Confirm Backup:', backup_settings.confirm_backup)

            # Add backup settings data to the context
            context = {
                'operator_names': operator_names,
                'backup_date': backup_settings.backup_date,
                'confirm_backup': backup_settings.confirm_backup,
                'id': backup_settings.id
            }
        else:
            # Handle empty backup settings
            context = {
                'operator_names': operator_names,
                'backup_date': None,
                'confirm_backup': None,
                'id': None
            }

        # Render the template with the combined context
        return render(request, 'app/login.html', context)

    else:
        # Handle invalid HTTP method
        return JsonResponse({'status': 'error', 'message': 'Invalid HTTP method'}, status=405)
