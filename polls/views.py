import os
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .forms import UploadForm
from .models import Document, GeneratedQuestion, Poll, PollResponse
from .utils import extract_text_from_file
from .llm_client import (
    generate_questions_from_text,
    generate_exit_tickets_from_text,
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
            # generate multiple-choice questions
            generated_mcq = generate_questions_from_text(text)
            for item in generated_mcq:
                GeneratedQuestion.objects.create(document=doc, text=item.get('text'), choices=item.get('choices', []), kind='mcq')
            # generate exit ticket prompts (short response)
            generated_exit = generate_exit_tickets_from_text(text, max_tickets=3)
            for item in generated_exit:
                GeneratedQuestion.objects.create(document=doc, text=item.get('text'), choices=[], kind='exit')
            if LLM_LAST_SOURCE == 'groq':
                messages.success(request, f"Generated {len(generated_mcq)} MCQs and {len(generated_exit)} exit tickets using Groq.")
            else:
                has_key = bool(os.getenv('GROQ_API_KEY'))
                if not has_key:
                    messages.warning(request, "No GROQ_API_KEY found. Using mock MCQs and exit tickets.")
                else:
                    err = LLM_LAST_ERROR or 'Unknown error'
                    messages.error(request, f"Groq API call failed: {err}. Using mock MCQs and exit tickets.")
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
        # collect posted choices only for MCQ
        if q.kind == 'mcq':
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
            if q.kind == 'mcq':
                # create poll
                Poll.objects.create(question_text=q.text, choices=q.choices)
            else:
                # create exit ticket
                from .models import ExitTicket
                ExitTicket.objects.create(prompt_text=q.text)
            # create poll
            question_format = request.POST.get('question_format', 'single_choice')
            correct_answer = request.POST.get('correct_answer', None)
            if correct_answer:
                correct_answer = int(correct_answer)
            Poll.objects.create(
                question_text=q.text,
                choices=q.choices,
                question_format=question_format,
                correct_answer=correct_answer
            )

            # Check if there are any remaining pending questions
            remaining_questions = doc.generated_questions.filter(status='pending').count()
            if remaining_questions == 0:
                # No more pending questions, delete the document
                messages.success(request, f'Document "{doc.title}" has been automatically deleted (no pending questions remaining).')
                doc.delete()
                return redirect('polls:index')

            return redirect('polls:manage_polls')
        else:
            q.status = 'rejected'
            q.save()

        # Check if there are any remaining pending questions after rejection
        remaining_questions = doc.generated_questions.filter(status='pending').count()
        if remaining_questions == 0:
            # No more pending questions, delete the document
            messages.success(request, f'Document "{doc.title}" has been automatically deleted (no pending questions remaining).')
            doc.delete()
            return redirect('polls:index')

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
        elif poll.question_format == 'team_battle':
            # Team battle: store team side and answer choice
            team_side = request.POST.get('team_side')
            answer_choice = int(request.POST.get('answer_choice'))
            # Store as dict: {"team": "left"/"right", "answer": choice_index}
            choice = {"team": team_side, "answer": answer_choice}
        elif poll.question_format == 'meta_prediction':
            # Meta prediction: store predictions and actual answer
            num_choices = len(poll.choices)
            predictions = []
            for i in range(num_choices):
                pred = int(request.POST.get(f'prediction_{i}', 0))
                predictions.append(pred)
            actual_answer = int(request.POST.get('actual_answer'))
            # Store as dict: {"predictions": [25, 30, 20, 25], "answer": choice_index}
            choice = {"predictions": predictions, "answer": actual_answer}
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

    elif poll.question_format == 'team_battle':
        # Team battle: calculate correct answers for each side
        left_correct = 0
        left_total = 0
        right_correct = 0
        right_total = 0

        for response in poll.responses.all():
            response_data = response.choice

            # Handle both old format (string) and new format (dict)
            if isinstance(response_data, dict):
                # New format: {"team": "left"/"right", "answer": choice_index}
                team = response_data.get('team')
                answer = response_data.get('answer')

                if team == 'left':
                    left_total += 1
                    if answer == poll.correct_answer:
                        left_correct += 1
                elif team == 'right':
                    right_total += 1
                    if answer == poll.correct_answer:
                        right_correct += 1
            elif isinstance(response_data, str):
                # Old format: just "left" or "right" - count as participation only
                if response_data == 'left':
                    left_total += 1
                elif response_data == 'right':
                    right_total += 1

        # Calculate percentages
        left_percentage = (left_correct / left_total * 100) if left_total > 0 else 0
        right_percentage = (right_correct / right_total * 100) if right_total > 0 else 0

        # Determine winner based on percentage of correct answers
        if left_percentage > right_percentage:
            winner = 'left'
        elif right_percentage > left_percentage:
            winner = 'right'
        else:
            winner = 'tie'

        return render(request, 'polls/results.html', {
            'poll': poll,
            'left_count': left_total,
            'right_count': right_total,
            'left_correct': left_correct,
            'right_correct': right_correct,
            'left_percentage': round(left_percentage, 1),
            'right_percentage': round(right_percentage, 1),
            'total': total,
            'winner': winner,
            'format': 'team_battle'
        })

    elif poll.question_format == 'meta_prediction':
        # Meta prediction: calculate actual percentages and average predictions
        num_choices = len(poll.choices)
        actual_counts = [0] * num_choices
        avg_predictions = [0.0] * num_choices
        prediction_totals = [0] * num_choices

        for response in poll.responses.all():
            response_data = response.choice  # {"predictions": [25, 30, 20, 25], "answer": choice_index}

            # Count actual answers
            actual_answer = response_data.get('answer')
            actual_counts[actual_answer] += 1

            # Sum up predictions for averaging
            predictions = response_data.get('predictions', [])
            for i, pred in enumerate(predictions):
                prediction_totals[i] += pred

        # Calculate average predictions and actual percentages
        for i in range(num_choices):
            avg_predictions[i] = round(prediction_totals[i] / total, 1) if total > 0 else 0

        actual_percentages = []
        for count in actual_counts:
            actual_percentages.append(round((count / total * 100), 1) if total > 0 else 0)

        # Calculate prediction accuracy (how close predictions were to reality)
        accuracy_scores = []
        for i in range(num_choices):
            diff = abs(avg_predictions[i] - actual_percentages[i])
            accuracy = max(0, 100 - diff)  # 100 = perfect, 0 = way off
            accuracy_scores.append(round(accuracy, 1))

        overall_accuracy = round(sum(accuracy_scores) / num_choices, 1) if num_choices > 0 else 0

        results_data = []
        for i in range(num_choices):
            results_data.append({
                'choice': poll.choices[i],
                'predicted_pct': avg_predictions[i],
                'actual_pct': actual_percentages[i],
                'actual_count': actual_counts[i],
                'accuracy': accuracy_scores[i]
            })

        return render(request, 'polls/results.html', {
            'poll': poll,
            'results_data': results_data,
            'total': total,
            'overall_accuracy': overall_accuracy,
            'format': 'meta_prediction'
        })

    return render(request, 'polls/results.html', {'poll': poll, 'total': 0})


def manage_polls(request):
    polls = Poll.objects.order_by('-created_at')
    from .models import ExitTicket
    tickets = ExitTicket.objects.order_by('-created_at')
    return render(request, 'polls/manage.html', {'polls': polls, 'tickets': tickets})


def exit_ticket_display(request, ticket_id):
    from .models import ExitTicket
    ticket = get_object_or_404(ExitTicket, id=ticket_id)
    return render(request, 'polls/exit_ticket_display.html', {'ticket': ticket})


def exit_ticket_submit(request, ticket_id):
    from .models import ExitTicket, ExitTicketResponse
    ticket = get_object_or_404(ExitTicket, id=ticket_id)
    if request.method == 'POST':
        answer = (request.POST.get('answer') or '').strip()
        if answer:
            ExitTicketResponse.objects.create(ticket=ticket, answer=answer)
            return redirect('polls:exit_ticket_results', ticket_id=ticket.id)
    return redirect('polls:exit_ticket_display', ticket_id=ticket.id)


def exit_ticket_results(request, ticket_id):
    from .models import ExitTicket
    ticket = get_object_or_404(ExitTicket, id=ticket_id)
    responses = ticket.responses.order_by('-created_at')[:200]
    total = ticket.responses.count()
    return render(request, 'polls/exit_ticket_results.html', {'ticket': ticket, 'responses': responses, 'total': total})
    return render(request, 'polls/manage.html', {'polls': polls})


def toggle_poll_active(request, poll_id):
    poll = get_object_or_404(Poll, id=poll_id)
    if request.method == 'POST':
        poll.active = not poll.active
        poll.save()
        status = "activated" if poll.active else "deactivated"
        messages.success(request, f'Poll "{poll.question_text[:50]}" has been {status}.')
    return redirect('polls:manage_polls')


def delete_poll(request, poll_id):
    poll = get_object_or_404(Poll, id=poll_id)
    if request.method == 'POST':
        poll.delete()
        messages.success(request, f'Poll "{poll.question_text[:50]}" has been deleted.')
    return redirect('polls:manage_polls')


def delete_document(request, doc_id):
    doc = get_object_or_404(Document, id=doc_id)
    if request.method == 'POST':
        doc.delete()
        messages.success(request, f'Document "{doc.title}" has been deleted.')
    return redirect('polls:index')
