
from django.http import FileResponse
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from .forms import RegisterForm, LoginForm, ResumeUploadForm,ProfileUpdateForm
from django.contrib import messages

from .ml_logic import analyze_resume_ats,generate_feedback_pdf
import os
from django.http import HttpResponse
from fpdf import FPDF
from django.conf import settings
def home(request):
     return render(request, 'analyzer/home.html')
   
@login_required
def profile_view(request):
    return render(request, 'analyzer/profile.html') 
@login_required
def profile_edit(request):
    if request.method == 'POST':
        form = ProfileUpdateForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated successfully.")
            return redirect('profile')
        else:
              messages.error(request, "Please correct the errors below.")
    else:
        form = ProfileUpdateForm(instance=request.user)

    return render(request, 'analyzer/profile_edit.html', {'form': form})

@login_required
def profile_delete(request):
    if request.method == 'POST':
        user = request.user
        user.delete()
        messages.success(request, "Your account has been deleted.")
        return redirect('home')
    return render(request, 'analyzer/profile_delete.html')  
def about(request):
    return render(request, 'analyzer/about.html')
    
def register_view(request):
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.save()
            messages.success(request, "Registration successful! You can now log in.")
            return redirect('login')
    else:
        form = RegisterForm()
    return render(request, 'analyzer/register.html', {'form': form})

def login_view(request):
    if request.method == "POST":
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)

            if user is not None:
                login(request, user)
                messages.success(request, f"Welcome back, {user.username}!")
                return redirect('upload_resume')  # ✅ redirect to upload
            else:
                messages.error(request, "Invalid username or password.")
    else:
        form = LoginForm()
    return render(request, 'analyzer/login.html', {'form': form})
def logout_view(request):
    logout(request)
    return redirect('home')

@login_required
def upload_resume(request):
    context = {}
    if request.method == 'POST':
        resume_file = request.FILES.get('resume')
        job_desc = request.POST.get('job_description')

        if resume_file and job_desc:
            result = analyze_resume_ats(resume_file, job_desc)
            request.session['analysis_result'] = result  # store in session for export
            context.update({
                'score': result['score'],
                'feedback': {
                    'matched': result['matched'],
                    'missing': result['missing'],
                    'summary': result['summary'],
                    'suggestions': result['suggestions'],
                    'job_description': result['job_description']
                }
            })
        else:
            messages.error(request, "Please upload both a resume and a job description.")
    return render(request, 'analyzer/upload.html', context)

@login_required
def export_pdf(request):
    result = request.session.get('analysis_result')
    if not result:
        return HttpResponse("No analysis found. Please analyze your resume first.")

    pdf = generate_feedback_pdf(result)
    response = HttpResponse(pdf.output(dest='S').encode('latin-1'), content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="resume_feedback.pdf"'
    return response
