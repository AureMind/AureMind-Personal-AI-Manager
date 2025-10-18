from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator
from .models import Note, Task
from .forms import NoteForm, TimeScheduleForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from datetime import datetime , date, time
from calendar import monthrange
from django.db.models import Q


@login_required
def home(request):
    q = request.GET.get('q', '')
    notes = Note.objects.filter(user=request.user)
    if q:
        notes = notes.filter(Q(title__icontains=q) | Q(content__icontains=q))
    paginator = Paginator(notes.order_by('-created_at'), 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'page_obj': page_obj,
        'q': q,
        'year': datetime.now().year,
    }
    return render(request, 'notes/dashboard.html', context)


@login_required
def note_create(request):
    if request.method == 'POST':
        form = NoteForm(request.POST, request.FILES)
        if form.is_valid():
            note = form.save(commit=False)
            note.user = request.user
            note.save()
            return redirect('notes:dashboard')
        else:
            return render(request, 'notes/note_form.html', {'form': form})
    else:
        form = NoteForm()
    return render(request, 'notes/note_form.html', {'form': form})


@login_required
def note_update(request, pk):
    note = get_object_or_404(Note, pk=pk)
    if request.method == 'POST':
        form = NoteForm(request.POST, request.FILES, instance=note)
        if form.is_valid():
            form.save()
            return redirect('notes:detail', pk=note.pk)
        else:
            return render(request, 'notes/note_form.html', {'form': form, 'note': note})
    else:
        form = NoteForm(instance=note)
    return render(request, 'notes/note_form.html', {'form': form, 'note': note})

@login_required
def note_delete(request, pk):
    note = get_object_or_404(Note, pk=pk)
    if request.method == 'POST':
        note.delete()
        return redirect('notes:dashboard')
    return render(request, 'notes/confirm_delete.html', {'note': note})

def note_detail(request, pk):
    note = get_object_or_404(Note, pk=pk)
    return render(request, 'notes/detail.html', {'note': note})

def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            messages.success(request, f'Account created for {username}! You can now log in.')
            return redirect('notes:login')
    else:
        form = UserCreationForm()
    return render(request, 'notes/register.html', {'form': form})

@login_required
def dashboard(request):
    total_notes = Note.objects.filter(user=request.user).count()
    context = {'total_notes': total_notes}
    return render(request, 'notes/dashboard.html', context)


@login_required
def calendar_view(request, year=None, month=None):
    today = date.today()
    year = int(year) if year else today.year
    month = int(month) if month else today.month

    # 1. Fetch only tasks, and order them by time
    tasks = Task.objects.filter(
        user=request.user, 
        due_date__year=year, 
        due_date__month=month
    ).order_by('due_date') # order_by also sorts by time

    # 2. Create the new calendar structure
    calendar_tasks = {}
    
    # Add tasks to the structure
    for task in tasks:
        day = task.due_date.day
        if day not in calendar_tasks:
            calendar_tasks[day] = []
        calendar_tasks[day].append(task) # Add the whole task object

    total_days = monthrange(year, month)[1]
    
    context = {
        'year': year,
        'month': month,
        'calendar_tasks': calendar_tasks, # Pass the new task structure
        'total_days': total_days,
        'today_day': today.day if today.year == year and today.month == month else None,
    }
    return render(request, 'notes/calendar.html', context)

@login_required
def task(request):
    tasks = Task.objects.filter(user=request.user).order_by('due_date')
    context = {
        'tasks': tasks,
    }
    return render(request, 'task/task.html', context)

@login_required
def task_create(request):
    if request.method == 'POST':
        form = TimeScheduleForm(request.POST)
        if form.is_valid():
            task = form.save(commit=False)
            task.user = request.user
            task.save()
            return redirect('notes:task')
        else:
            return render(request, 'task/task_form.html', {'form': form})
    else:
        form = TimeScheduleForm()
    return render(request, 'task/task_form.html', {'form': form})

@login_required
def task_update(request, pk):
    task = get_object_or_404(Task, pk=pk, user=request.user) 
    if request.method == 'POST':
        form = TimeScheduleForm(request.POST, instance=task)
        if form.is_valid():
            form.save()
            return redirect('notes:task') 
        else:
            return render(request, 'task/task_form.html', {'form': form, 'task': task})
    else:
        form = TimeScheduleForm(instance=task)
    return render(request, 'task/task_form.html', {'form': form, 'task': task})

@login_required
def task_delete(request, pk):
    task = get_object_or_404(Task, pk=pk, user=request.user) 
    if request.method == 'POST':
        task.delete()
        return redirect('notes:task') 
    return render(request, 'task/confirm_delete.html', {'task': task})


@login_required
def note(request):
    q = request.GET.get('q', '')
    notes = Note.objects.filter(user=request.user)
    if q:
        notes = notes.filter(Q(title__icontains=q) | Q(content__icontains=q))
    paginator = Paginator(notes.order_by('-created_at'), 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'page_obj': page_obj,
        'q': q,
        'year': datetime.now().year,
    }
    return render(request, 'notes/note.html', context)

@login_required
def files(request):
    notes_with_files = Note.objects.filter(user=request.user).exclude(attachment='')
    context = {
        'notes_with_files': notes_with_files,
    }
    return render(request, 'notes/files.html', context)

def about(request):
    return render(request, 'notes/about.html')