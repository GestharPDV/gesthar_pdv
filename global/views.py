from django.shortcuts import render

def login_view(request):
    return render(request, "global/login_page.html")
