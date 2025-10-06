# notes/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator
from .models import Note
from .forms import NoteForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages

def home(request):
    q = request.GET.get('q', '').strip()
    notes = Note.objects.all().order_by('-created_at')
    if q:
        notes = notes.filter(title__icontains=q) | notes.filter(content__icontains=q)
    paginator = Paginator(notes, 10)  # 10 per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'notes/home.html', {'page_obj': page_obj, 'q': q})

def note_detail(request, pk):
    note = get_object_or_404(Note, pk=pk)
    return render(request, 'notes/detail.html', {'note': note})

def note_create(request):
    if request.method == 'POST':
        form = NoteForm(request.POST)
        if form.is_valid():
            note = form.save()
            return redirect('notes:detail', pk=note.pk)
    else:
        form = NoteForm()
    return render(request, 'notes/form.html', {'form': form})

def note_update(request, pk):
    note = get_object_or_404(Note, pk=pk)
    if request.method == 'POST':
        form = NoteForm(request.POST, instance=note)
        if form.is_valid():
            form.save()
            return redirect('notes:detail', pk=note.pk)
    else:
        form = NoteForm(instance=note)
    return render(request, 'notes/form.html', {'form': form, 'note': note})

def note_delete(request, pk):
    note = get_object_or_404(Note, pk=pk)
    if request.method == 'POST':
        note.delete()
        return redirect('notes:home')
    return render(request, 'notes/confirm_delete.html', {'note': note})

@login_required
def note_create(request):
    ...

@login_required
def note_update(request, pk):
    ...

@login_required
def note_delete(request, pk):
    ...

def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            messages.success(request, f'Account created for {username}! You can now log in.')
            return redirect('login')
    else:
        form = UserCreationForm()
    return render(request, 'register.html', {'form': form})