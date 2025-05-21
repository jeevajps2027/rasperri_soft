from django.shortcuts import render


def keyboard(request):
    return render(request, 'app/keyboard.html')