from django.urls import path
from . import views

app_name = 'polls'

urlpatterns = [
    path('', views.index, name='index'),
    path('upload/', views.upload_document, name='upload_document'),
    path('review/<uuid:doc_id>/', views.review_generated, name='review_generated'),
    path('document/<uuid:doc_id>/delete/', views.delete_document, name='delete_document'),
    path('manage/', views.manage_polls, name='manage_polls'),
    path('poll/<uuid:poll_id>/', views.poll_display, name='poll_display'),
    path('poll/<uuid:poll_id>/vote/', views.poll_vote, name='poll_vote'),
    path('poll/<uuid:poll_id>/submitted/', views.poll_submitted, name='poll_submitted'),
    path('poll/<uuid:poll_id>/results/', views.poll_results, name='poll_results'),
    path('garden/', views.knowledge_garden_view, name='knowledge_garden'),
    path('poll/<uuid:poll_id>/toggle/', views.toggle_poll_active, name='toggle_poll_active'),
    path('poll/<uuid:poll_id>/delete/', views.delete_poll, name='delete_poll'),
    path('poll/<uuid:poll_id>/start-countdown/', views.start_countdown, name='start_countdown'),
    # exit tickets
    path('exit/<uuid:ticket_id>/', views.exit_ticket_display, name='exit_ticket_display'),
    path('exit/<uuid:ticket_id>/submit/', views.exit_ticket_submit, name='exit_ticket_submit'),
    path('exit/<uuid:ticket_id>/results/', views.exit_ticket_results, name='exit_ticket_results'),
    path('exit/<uuid:ticket_id>/toggle/', views.toggle_ticket_active, name='toggle_ticket_active'),
    path('exit/<uuid:ticket_id>/delete/', views.delete_ticket, name='delete_ticket'),
]
