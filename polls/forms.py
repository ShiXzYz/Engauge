from django import forms
from .models import Course


class UploadForm(forms.Form):
    title = forms.CharField(max_length=255, required=False)
    file = forms.FileField()
    course = forms.ModelChoiceField(queryset=Course.objects.none(), required=True, help_text="Select the class to attach this upload to.")

    def set_courses_for_user(self, user):
        qs = Course.objects.all()
        if hasattr(user, 'profile') and user.profile.role == 'professor':
            qs = qs.filter(created_by=user)
        self.fields['course'].queryset = qs


class CourseCreateForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = ['name']


class JoinClassForm(forms.Form):
    join_code = forms.CharField(max_length=12)


class RegisterForm(forms.Form):
    username = forms.CharField(max_length=150)
    password = forms.CharField(widget=forms.PasswordInput())
    role = forms.ChoiceField(choices=[('professor','Professor'),('student','Student')])

class ReviewForm(forms.Form):
    action = forms.ChoiceField(choices=[('accept', 'Accept'), ('reject', 'Reject')])
