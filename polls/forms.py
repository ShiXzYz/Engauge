from django import forms


class UploadForm(forms.Form):
    title = forms.CharField(max_length=255, required=False)
    file = forms.FileField()


class ReviewForm(forms.Form):
    action = forms.ChoiceField(choices=[('accept', 'Accept'), ('reject', 'Reject')])
