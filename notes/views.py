from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator
from .models import Note, Task
from .forms import NoteForm , TimeScheduleForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from datetime import datetime , date, timedelta
from django.utils import timezone
from calendar import monthrange
from django.db.models import Q  
import json
from django.http import JsonResponse, HttpResponse, Http404
from django.conf import settings
from django.urls import reverse
import google.generativeai as genai
import mimetypes # To guess the file type


@login_required
def search_notes(request):
    query = request.GET.get('q', '')
    notes = []
    if query and len(query) > 2:
        note_results = Note.objects.filter(
            user=request.user
        ).filter(
            Q(title__icontains=query) | Q(encrypted_content__icontains=query)
        ).order_by('-created_at')[:10]
        
        for note in note_results:
            notes.append({
                'id': note.id,
                'title': note.title,
                'url': reverse('notes:detail', kwargs={'pk': note.id})
            })
            
    return JsonResponse({'notes': notes})


@login_required
def home(request):
    recent_notes = Note.objects.filter(user=request.user).order_by('-created_at')[:5]
    upcoming_tasks = Task.objects.filter(
        user=request.user, 
        due_date__gte=timezone.now()
    ).order_by('due_date')[:5]

    context = {
        'total_notes': Note.objects.filter(user=request.user).count(),
        'recent_notes': recent_notes,
        'upcoming_tasks': upcoming_tasks,
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
            messages.success(request, f"Note '{note.title}' created successfully!")
            return redirect('notes:note')
        else:
            return render(request, 'notes/note_form.html', {'form': form})
    else:
        form = NoteForm()
    return render(request, 'notes/note_form.html', {'form': form})


@login_required
def note_update(request, pk):
    note = get_object_or_404(Note, pk=pk, user=request.user) 
    if request.method == 'POST':
        form = NoteForm(request.POST, request.FILES, instance=note)
        if form.is_valid():
            form.save()
            messages.success(request, f"Note '{note.title}' updated successfully!")
            return redirect('notes:detail', pk=note.pk)
        else:
            return render(request, 'notes/note_form.html', {'form': form, 'note': note})
    else:
        form = NoteForm(instance=note)
    return render(request, 'notes/note_form.html', {'form': form, 'note': note})

@login_required
def note_delete(request, pk):
    note = get_object_or_404(Note, pk=pk, user=request.user) 
    if request.method == 'POST':
        note.delete()
        messages.success(request, f"Note '{note.title}' updated successfully!")
        return redirect('notes:note')
    return render(request, 'notes/confirm_delete.html', {'note': note})

@login_required 
def note_detail(request, pk):
    note = get_object_or_404(Note, pk=pk, user=request.user) 
    return render(request, 'notes/note_detail.html', {'note': note})

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
    context = {'total_notes': total_notes, 'year': datetime.now().year} 
    return render(request, 'notes/dashboard.html', context)


@login_required
def note(request):
    q = request.GET.get('q', '')
    notes = Note.objects.filter(user=request.user)
    if q:
        notes = notes.filter(Q(title__icontains=q))
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
    notes_with_files = Note.objects.filter(user=request.user).exclude(attachment_name__isnull=True).exclude(attachment_name__exact='')
    context = {
        'notes_with_files': notes_with_files,
    }
    return render(request, 'notes/files.html', context)


@login_required
def serve_attachment(request, pk):
    note = get_object_or_404(Note, pk=pk, user=request.user)
    
    decrypted_bytes, file_name = note.get_attachment()
    
    if decrypted_bytes is None:
        raise Http404("No attachment found or decryption failed.")

    content_type, _ = mimetypes.guess_type(file_name)
    if content_type is None:
        content_type = 'application/octet-stream' 

    response = HttpResponse(decrypted_bytes, content_type=content_type)
    response['Content-Disposition'] = f'inline; filename="{file_name}"'
    return response


@login_required
def chat_view(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            prompt = data.get('prompt')
            note_id = data.get('note_id') 

            if not prompt:
                return JsonResponse({'error': 'No prompt provided.'}, status=400)
            
            final_prompt = prompt
            
            if note_id:
                try:
                    note = Note.objects.get(pk=note_id, user=request.user)
                    final_prompt = (
                        f"Please use the following note as context:\n"
                        f"--- NOTE START ---\n"
                        f"Title: {note.title}\n"
                        f"Content: {note.content}\n" 
                        f"--- NOTE END ---\n\n"
                        f"Now, please respond to this prompt: {prompt}"
                    )
                except Note.DoesNotExist:
                    pass 

            genai.configure(api_key=settings.GOOGLE_API_KEY)
            model = genai.GenerativeModel('gemini-2.5-pro') 
            response = model.generate_content(final_prompt) 
            ai_response = response.text

            return JsonResponse({'response': ai_response})

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    else:
        user_notes = Note.objects.filter(user=request.user).order_by('-created_at')
        context = {
            'all_notes': user_notes
        }
        return render(request, 'AI/chat.html', context)


@login_required
def save_chat_note(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            prompt = data.get('prompt')
            ai_response = data.get('ai_response')

            if not prompt or not ai_response:
                return JsonResponse({'error': 'Missing prompt or response.'}, status=400)

            title = ' '.join(ai_response.split()[:5]) + "..."
            content = f"**My Prompt:**\n{prompt}\n\n**AI Response:**\n{ai_response}"

            new_note = Note(
                user=request.user,
                title=f"Chat: {title}"
            )
            new_note.content = content 
            new_note.save()

            return JsonResponse({'status': 'success', 'message': 'Note saved!'})

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'error': 'Invalid request method.'}, status=405)

def about(request):
    return render(request, 'notes/about.html', {'year': datetime.now().year}) 
    
@login_required
def calendar_view(request, year=None, month=None):
    today = date.today()
    year = int(year) if year else today.year
    month = int(month) if month else today.month

    tasks = Task.objects.filter(
        user=request.user, 
        due_date__year=year, 
        due_date__month=month
    ).order_by('due_date') 

    calendar_tasks = {}
    
    for task in tasks:
        day = task.due_date.day
        if day not in calendar_tasks:
            calendar_tasks[day] = []
        calendar_tasks[day].append(task) 

    total_days = monthrange(year, month)[1]
    
    context = {
        'year': year,
        'month': month,
        'calendar_tasks': calendar_tasks, 
        'total_days': total_days,
        'today_day': today.day if today.year == year and today.month == month else None,
    }
    return render(request, 'task/calendar.html', context)

@login_required
def task(request):
    # --- REVERTED: Fetches all tasks again ---
    tasks = Task.objects.filter(user=request.user).order_by('due_date')
    context = {
        'tasks': tasks,
    }
    return render(request, 'task/task.html', context)

@login_required
def task_create(request):
    # --- REVERTED: Removed parent_pk ---
    if request.method == 'POST':
        # --- REVERTED: Removed user=request.user ---
        form = TimeScheduleForm(request.POST)
        if form.is_valid():
            task = form.save(commit=False)
            task.user = request.user
            task.save()
            messages.success(request, f"Task '{task.title}' created successfully!")
            return redirect('notes:task')
        else:
            return render(request, 'task/task_form.html', {'form': form})
    else:
        # --- REVERTED: Removed user=request.user ---
        form = TimeScheduleForm()
    return render(request, 'task/task_form.html', {'form': form})

@login_required
def task_update(request, pk):
    task = get_object_or_404(Task, pk=pk, user=request.user) 
    if request.method == 'POST':
        # --- REVERTED: Removed user=request.user ---
        form = TimeScheduleForm(request.POST, instance=task)
        if form.is_valid():
            form.save()
            messages.success(request, f"Task '{task.title}' updated successfully!")
            return redirect('notes:task') 
        else:
            return render(request, 'task/task_form.html', {'form': form, 'task': task})
    else:
        # --- REVERTED: Removed user=request.user ---
        form = TimeScheduleForm(instance=task)
    return render(request, 'task/task_form.html', {'form': form, 'task': task})

@login_required
def task_delete(request, pk):
    task = get_object_or_404(Task, pk=pk, user=request.user) 
    if request.method == 'POST':
        task.delete()
        messages.success(request, f"Task '{task.title}' deleted successfully!")
        return redirect('notes:task') 
    return render(request, 'task/confirm_delete.html', {'task': task})

@login_required
def check_task_notifications(request):
    now = timezone.now()
    upcoming_tasks = Task.objects.filter(
        user=request.user,
        due_date__lte=now + timedelta(minutes=30), 
        due_date__gt=now                          
    )

    notified_tasks = request.session.get('notified_tasks', [])
    tasks_to_notify = []
    local_tz = timezone.get_current_timezone()

    for task in upcoming_tasks:
        if task.pk not in notified_tasks:
            local_due_date = task.due_date.astimezone(local_tz)
            tasks_to_notify.append({
                'id': task.pk,
                'title': task.title,
                'due_date_str': local_due_date.strftime("%#I:%M %p") 
            })
            notified_tasks.append(task.pk)

    request.session['notified_tasks'] = notified_tasks
    return JsonResponse({'tasks': tasks_to_notify})