# your_app/forms.py
from django import forms

class ImportForm(forms.Form):
    file = forms.FileField()

class BackupForm(forms.Form):
    file = forms.FileField()



from .models import Link

class LinkForm(forms.ModelForm):
    class Meta:
        model = Link
        fields = ['nombre', 'url', 'comentario']
