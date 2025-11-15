from django.urls import path
from . import views

app_name = 'polls'

urlpatterns = [
    path('', views.index, name='index'),
    path('upload/', views.upload_document, name='upload_document'),
    path('review/<uuid:doc_id>/', views.review_generated, name='review_generated'),
    path('manage/', views.manage_polls, name='manage_polls'),
    path('poll/<uuid:poll_id>/', views.poll_display, name='poll_display'),
    path('poll/<uuid:poll_id>/vote/', views.poll_vote, name='poll_vote'),
    path('poll/<uuid:poll_id>/results/', views.poll_results, name='poll_results'),
    
    # Student poll page
    path('student/', views.student_poll_view, name='student_poll'),
    path('garden/', views.knowledge_garden_view, name='knowledge_garden'),
    # API endpoints
    path('api/active-poll/', views.get_active_poll, name='get_active_poll'),
    path('api/submit-answer/', views.submit_student_answer, name='submit_answer'),
]
