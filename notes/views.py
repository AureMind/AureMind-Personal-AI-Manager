from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator
from .models import Note, Task
from .forms import NoteForm , TimeScheduleForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from datetime import datetime , date, time
from calendar import monthrange
from django.db.models import Q
import json
from django.http import JsonResponse
from django.conf import settings
from django.urls import reverse
import google.generativeai as genai


@login_required
def search_notes(request):
    """
    A view to handle live search requests and return matching notes as JSON.
    """
    query = request.GET.get('q', '')
    notes = []
    # Only perform a search if the query is at least 3 characters long
    if query and len(query) > 2:
        # Search in both title and content, limit results to the top 10
        note_results = Note.objects.filter(
            user=request.user
        ).filter(
            Q(title__icontains=query) | Q(content__icontains=query)
        ).order_by('-created_at')[:10]
        
        # Format the results for the JSON response
        for note in note_results:
            notes.append({
                'id': note.id,
                'title': note.title,
                'url': reverse('notes:detail', kwargs={'pk': note.id})
            })
            
    return JsonResponse({'notes': notes})


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


@login_required
def chat_view(request):
    if request.method == 'POST':
        try:
            # 1. Get data from the AJAX request
            data = json.loads(request.body)
            prompt = data.get('prompt')
            note_id = data.get('note_id') # Get the new note_id

            if not prompt:
                return JsonResponse({'error': 'No prompt provided.'}, status=400)
            
            final_prompt = prompt
            
            # 2. Check if a note_id was provided
            if note_id:
                try:
                    # Fetch the note, ensuring it belongs to the user
                    note = Note.objects.get(pk=note_id, user=request.user)
                    # Prepend the note content as context
                    final_prompt = (
                        f"Please use the following note as context:\n"
                        f"--- NOTE START ---\n"
                        f"Title: {note.title}\n"
                        f"Content: {note.content}\n"
                        f"--- NOTE END ---\n\n"
                        f"Now, please respond to this prompt: {prompt}"
                    )
                except Note.DoesNotExist:
                    # If note_id is invalid or doesn't belong to user, just ignore it
                    pass 

            # 3. Configure and call the Gemini API
            genai.configure(api_key=settings.GOOGLE_API_KEY)
            model = genai.GenerativeModel('gemini-2.5-flash')
            response = model.generate_content(final_prompt) # Use the final_prompt
            ai_response = response.text

            # 4. Return the AI response
            return JsonResponse({'response': ai_response})

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    # For GET requests, fetch user's notes and render the chat page
    else:
        user_notes = Note.objects.filter(user=request.user).order_by('-created_at')
        context = {
            'all_notes': user_notes
        }
        return render(request, 'AI/chat.html', context)


# --- ADD THIS NEW VIEW TO SAVE THE CHAT ---
@login_required
def save_chat_note(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            prompt = data.get('prompt')
            ai_response = data.get('ai_response')

            if not prompt or not ai_response:
                return JsonResponse({'error': 'Missing prompt or response.'}, status=400)

            # Create a title from the first few words of the AI response
            title = ' '.join(ai_response.split()[:5]) + "..."
            
            # Create the note content
            # Prompt already contains context info if it was used
            content = f"**My Prompt:**\n{prompt}\n\n**AI Response:**\n{ai_response}"

            Note.objects.create(
                user=request.user,
                title=f"Chat: {title}",
                content=content
            )

            return JsonResponse({'status': 'success', 'message': 'Note saved!'})

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'error': 'Invalid request method.'}, status=405)

def about(request):
    return render(request, 'notes/about.html')
    
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
    return render(request, 'task/calendar.html', context)

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
