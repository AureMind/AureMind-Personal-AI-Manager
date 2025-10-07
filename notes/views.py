from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator
from .models import Note
from .forms import NoteForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages

@login_required
def home(request):
    q = request.GET.get('q', '')
    notes = Note.objects.filter(user=request.user)
    if q:
        notes = notes.filter(title__icontains=q)
    paginator = Paginator(notes.order_by('-created_at'), 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'notes/home.html', {'page_obj': page_obj, 'q': q})

@login_required
def note_create(request):
    if request.method == 'POST':
        form = NoteForm(request.POST, request.FILES)
        if form.is_valid():
            note = form.save(commit=False)
            note.user = request.user
            note.save()
            return redirect('notes:home')
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
        return redirect('notes:home')
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
def calendar_view(request):
    return render(request, 'notes/calendar.html')

@login_required
def issues(request):
    return render(request, 'notes/issues.html')

@login_required
def files(request):
    return render(request, 'notes/files.html')

def about(request):
    return render(request, 'notes/about.html')