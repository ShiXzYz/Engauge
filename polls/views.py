import os
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .forms import UploadForm
from .models import Document, GeneratedQuestion, Poll, PollResponse
from .utils import extract_text_from_file
from .llm_client import (
    generate_questions_from_text,
    LAST_SOURCE as LLM_LAST_SOURCE,
    LAST_ERROR as LLM_LAST_ERROR,
)

def index(request):
    docs = Document.objects.order_by('-uploaded_at')[:20]
    return render(request, 'polls/index.html', {'documents': docs})


def upload_document(request):
    if request.method == 'POST':
        form = UploadForm(request.POST, request.FILES)
        if form.is_valid():
            f = form.cleaned_data['file']
            title = form.cleaned_data.get('title') or getattr(f, 'name', '')
            doc = Document.objects.create(file=f, title=title)
            # extract text
            text = extract_text_from_file(doc.file.path)
            # call Claude to generate questions
            generated = generate_questions_from_text(text)
            for item in generated:
                GeneratedQuestion.objects.create(document=doc, text=item.get('text'), choices=item.get('choices', []))
            if LLM_LAST_SOURCE == 'groq':
                messages.success(request, f"Generated {len(generated)} questions using Groq.")
            else:
                has_key = bool(os.getenv('GROQ_API_KEY'))
                if not has_key:
                    messages.warning(request, "No GROQ_API_KEY found. Using mock questions.")
                else:
                    err = LLM_LAST_ERROR or 'Unknown error'
                    messages.error(request, f"Groq API call failed: {err}. Using mock questions.")
            return redirect('polls:review_generated', doc_id=doc.id)
    else:
        form = UploadForm()
    return render(request, 'polls/upload.html', {'form': form})


def review_generated(request, doc_id):
    doc = get_object_or_404(Document, id=doc_id)
    questions = doc.generated_questions.filter(status='pending')
    if request.method == 'POST':
        qid = request.POST.get('question_id')
        action = request.POST.get('action')
        q = get_object_or_404(GeneratedQuestion, id=qid, document=doc)
        # allow inline edits of question text and choices
        new_text = request.POST.get('text')
        if new_text:
            q.text = new_text.strip()
        # collect any posted choices in order: choice_0..choice_9 (cap)
        new_choices = []
        for i in range(10):
            key = f'choice_{i}'
            if key in request.POST:
                val = request.POST.get(key, '').strip()
                if val:
                    new_choices.append(val)
        if new_choices:
            q.choices = new_choices[:4]
        if action == 'accept':
            q.status = 'accepted'
            q.save()
            # create poll
            Poll.objects.create(question_text=q.text, choices=q.choices)
            return redirect('polls:manage_polls')
        else:
            q.status = 'rejected'
            q.save()
        return redirect('polls:review_generated', doc_id=doc.id)
    return render(request, 'polls/review.html', {
        'document': doc,
        'questions': questions,
        'groq_active': (LLM_LAST_SOURCE == 'groq')
    })


def poll_display(request, poll_id):
    poll = get_object_or_404(Poll, id=poll_id)
    return render(request, 'polls/poll_display.html', {'poll': poll})


def poll_vote(request, poll_id):
    poll = get_object_or_404(Poll, id=poll_id)
    if request.method == 'POST':
        choice = int(request.POST.get('choice'))
        PollResponse.objects.create(poll=poll, choice=choice)
        return redirect('polls:poll_submitted', poll_id=poll.id)
    return redirect('polls:poll_display', poll_id=poll.id)


def poll_submitted(request, poll_id):
    poll = get_object_or_404(Poll, id=poll_id)
    return render(request, 'polls/submitted.html', {'poll': poll})


def poll_results(request, poll_id):
    poll = get_object_or_404(Poll, id=poll_id)
    counts_list = []
    for i, _ in enumerate(poll.choices):
        counts_list.append(poll.responses.filter(choice=i).count())
    paired = list(zip(poll.choices, counts_list))
    total = sum(counts_list)
    return render(request, 'polls/results.html', {'poll': poll, 'paired': paired, 'total': total})


def manage_polls(request):
    polls = Poll.objects.order_by('-created_at')
    return render(request, 'polls/manage.html', {'polls': polls})
