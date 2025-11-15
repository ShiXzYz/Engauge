from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json

from .forms import UploadForm
from .models import Document, GeneratedQuestion, Poll, PollResponse
from .utils import extract_text_from_file
from .llm_client import generate_questions_from_text, LAST_SOURCE as LLM_LAST_SOURCE


# ========== EXISTING VIEWS ==========

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
                messages.info(request, "Using mock questions (no API key or API error). Add GROQ_API_KEY to .env and restart.")
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
        return redirect('polls:poll_results', poll_id=poll.id)
    return redirect('polls:poll_display', poll_id=poll.id)


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


# ========== NEW STUDENT POLL VIEWS ==========

def student_poll_view(request):
    """
    Render the student poll page.
    Students access this via a simple URL or QR code.
    """
    return render(request, 'polls/student_poll.html')


def knowledge_garden_view(request):
    """
    Render the knowledge garden page.
    Shows student's plant growth based on accumulated XP.
    """
    return render(request, 'polls/knowledge_garden.html')


@require_http_methods(["GET"])
def get_active_poll(request):
    """
    API endpoint: Get the currently active poll for students.
    Returns the most recently created poll (or first active poll if you add is_active field).
    """
    try:
        # Option 1: Get the most recent poll (simple approach for hackathon)
        active_poll = Poll.objects.order_by('-created_at').first()
        
        # Option 2: If you add an 'is_active' boolean field to Poll model, use this instead:
        # active_poll = Poll.objects.filter(is_active=True).first()
        
        if not active_poll:
            return JsonResponse({
                'error': 'No active poll at the moment. Please wait for your instructor.'
            }, status=404)
        
        return JsonResponse({
            'id': active_poll.id,
            'question': active_poll.question_text,
            'choices': active_poll.choices,  # Already a list
        })
    except Exception as e:
        return JsonResponse({
            'error': f'Server error: {str(e)}'
        }, status=500)


@csrf_exempt  # For demo only - remove in production and use proper CSRF handling
@require_http_methods(["POST"])
def submit_student_answer(request):
    """
    API endpoint: Handle student poll answer submission.
    Awards XP and saves the response to the database.
    """
    try:
        data = json.loads(request.body)
        poll_id = data.get('poll_id')
        choice_text = data.get('choice')
        
        if not poll_id or choice_text is None:
            return JsonResponse({
                'success': False,
                'error': 'Missing poll_id or choice'
            }, status=400)
        
        # Get the poll
        poll = Poll.objects.get(id=poll_id)
        
        # Find the choice index
        try:
            choice_index = poll.choices.index(choice_text)
        except ValueError:
            return JsonResponse({
                'success': False,
                'error': 'Invalid choice'
            }, status=400)
        
        # Save the response
        PollResponse.objects.create(
            poll=poll,
            choice=choice_index
        )
        
        return JsonResponse({
            'success': True,
            'xp_award': 10,  # Award 10 XP per answer
            'message': 'Answer recorded successfully!'
        })
        
    except Poll.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Poll not found'
        }, status=404)
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Server error: {str(e)}'
        }, status=500)