from django import forms

from .models import ContactMessage


class ContactForm(forms.ModelForm):
    class Meta:
        model = ContactMessage
        fields = ['name', 'email', 'subject', 'message']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control', 'placeholder': 'Name', 'required': True,
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control', 'placeholder': 'Email address',
                'pattern': '[^ @]*@[^ @]*', 'required': True,
            }),
            'subject': forms.TextInput(attrs={
                'class': 'form-control', 'placeholder': 'Subject',
            }),
            'message': forms.Textarea(attrs={
                'class': 'form-control', 'placeholder': 'Tell me about the project',
                'rows': 6, 'required': True,
            }),
        }
