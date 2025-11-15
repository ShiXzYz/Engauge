from django.contrib import admin
from .models import Document, GeneratedQuestion, Poll, PollResponse, ExitTicket, ExitTicketResponse, Course, Enrollment, Profile


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ('title', 'uploaded_at', 'id')
    search_fields = ('title',)


@admin.register(GeneratedQuestion)
class GeneratedQuestionAdmin(admin.ModelAdmin):
    list_display = ('document', 'short_text', 'status', 'created_at')
    list_filter = ('status',)

    def short_text(self, obj):
        return (obj.text or '')[:80]
    short_text.short_description = 'Question'


@admin.register(Poll)
class PollAdmin(admin.ModelAdmin):
    list_display = ('question_text', 'active', 'created_at')


@admin.register(PollResponse)
class PollResponseAdmin(admin.ModelAdmin):
    list_display = ('poll', 'choice', 'created_at')


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('name', 'join_code', 'created_by', 'created_at')
    search_fields = ('name', 'join_code')


@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ('user', 'course', 'role', 'created_at')
    list_filter = ('role',)


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'role')


@admin.register(ExitTicket)
class ExitTicketAdmin(admin.ModelAdmin):
    list_display = ('prompt_text', 'active', 'created_at')


@admin.register(ExitTicketResponse)
class ExitTicketResponseAdmin(admin.ModelAdmin):
    list_display = ('ticket', 'created_at')
