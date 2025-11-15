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
            question_format = request.POST.get('question_format', 'single_choice')
            Poll.objects.create(question_text=q.text, choices=q.choices, question_format=question_format)
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
    return render(request, 'polls/poll_display.html', {'poll': poll, 'hide_nav': True})


def poll_vote(request, poll_id):
    poll = get_object_or_404(Poll, id=poll_id)
    if request.method == 'POST':
        if poll.question_format == 'single_choice':
            # Single choice: store the choice index as an integer
            choice = int(request.POST.get('choice'))
        elif poll.question_format == 'speed_ranking':
            # Speed ranking: collect all ranks and create a list ordered by rank
            # rank_0, rank_1, rank_2, rank_3 contain the rank values (1-4)
            num_choices = len(poll.choices)
            rankings = []
            rank_values = []
            for i in range(num_choices):
                rank_value = int(request.POST.get(f'rank_{i}'))
                rank_values.append(rank_value)
                rankings.append((rank_value, i))  # (rank, choice_index)

            # Server-side validation: check for duplicate ranks
            if len(rank_values) != len(set(rank_values)):
                messages.error(request, 'Error: Each choice must have a unique rank. Please try again.')
                return redirect('polls:poll_display', poll_id=poll.id)

            # Sort by rank (1st, 2nd, 3rd, 4th) and extract choice indices
            rankings.sort(key=lambda x: x[0])
            choice = [choice_idx for _, choice_idx in rankings]
        else:
            choice = None

        if choice is not None:
            PollResponse.objects.create(poll=poll, choice=choice)
        return redirect('polls:poll_submitted', poll_id=poll.id)
    return redirect('polls:poll_display', poll_id=poll.id)


def poll_submitted(request, poll_id):
    poll = get_object_or_404(Poll, id=poll_id)
    return render(request, 'polls/submitted.html', {'poll': poll, 'hide_nav': True})


def poll_results(request, poll_id):
    poll = get_object_or_404(Poll, id=poll_id)
    total = poll.responses.count()

    if poll.question_format == 'single_choice':
        # Count votes for each choice
        counts_list = []
        for i, _ in enumerate(poll.choices):
            counts_list.append(poll.responses.filter(choice=i).count())
        paired = list(zip(poll.choices, counts_list))
        return render(request, 'polls/results.html', {
            'poll': poll,
            'paired': paired,
            'total': total,
            'format': 'single_choice'
        })

    elif poll.question_format == 'speed_ranking':
        # For ranking: calculate how many times each choice was ranked at each position
        num_choices = len(poll.choices)
        # rank_counts[choice_idx][rank_position] = count
        rank_counts = [[0] * num_choices for _ in range(num_choices)]

        for response in poll.responses.all():
            ranking = response.choice  # List of choice indices in rank order
            for rank_pos, choice_idx in enumerate(ranking):
                rank_counts[choice_idx][rank_pos] += 1

        # Calculate average rank for each choice (lower is better)
        avg_ranks = []
        for choice_idx in range(num_choices):
            total_rank = sum((rank_pos + 1) * count for rank_pos, count in enumerate(rank_counts[choice_idx]))
            avg_rank = total_rank / total if total > 0 else 0
            avg_ranks.append(avg_rank)

        results_data = []
        for i, choice_text in enumerate(poll.choices):
            results_data.append({
                'choice': choice_text,
                'rank_counts': rank_counts[i],
                'avg_rank': round(avg_ranks[i], 2)
            })

        return render(request, 'polls/results.html', {
            'poll': poll,
            'results_data': results_data,
            'total': total,
            'format': 'speed_ranking',
            'num_choices': num_choices
        })

    return render(request, 'polls/results.html', {'poll': poll, 'total': 0})


def manage_polls(request):
    polls = Poll.objects.order_by('-created_at')
    return render(request, 'polls/manage.html', {'polls': polls})


def delete_poll(request, poll_id):
    poll = get_object_or_404(Poll, id=poll_id)
    if request.method == 'POST':
        poll.delete()
        messages.success(request, f'Poll "{poll.question_text[:50]}" has been deleted.')
    return redirect('polls:manage_polls')
