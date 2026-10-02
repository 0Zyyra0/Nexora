from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm

from .models import Comment, ContactMessage, SecurityCredential

User = get_user_model()

_NB_INPUT = {'class': 'nb-input'}


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


class CommentForm(forms.ModelForm):
    # Present only to logged-out visitors — when someone is logged in, the
    # view fills name/email in from their account instead.
    class Meta:
        model = Comment
        fields = ['name', 'email', 'body']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control', 'placeholder': 'Name', 'required': True,
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control', 'placeholder': 'Email (never published)',
                'required': True,
            }),
            'body': forms.Textarea(attrs={
                'class': 'form-control', 'placeholder': 'Write a comment…',
                'rows': 4, 'required': True,
            }),
        }


class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs=_NB_INPUT))
    security_question = forms.CharField(
        max_length=255, required=True,
        widget=forms.TextInput(attrs={**_NB_INPUT, 'placeholder': 'e.g. What was your first pet\u2019s name?'}),
        help_text='Used to recover your account without email.',
    )
    security_answer = forms.CharField(
        max_length=255, required=True,
        widget=forms.TextInput(attrs={**_NB_INPUT, 'placeholder': 'Your answer'}),
    )

    class Meta:
        model = User
        fields = ['email', 'password1', 'password2']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].widget.attrs.update(_NB_INPUT)
        self.fields['password2'].widget.attrs.update(_NB_INPUT)

    def clean_email(self):
        email = self.cleaned_data['email'].strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError('An account with this email already exists.')
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        # We log people in with their email — base the username on it so
        # there's no separate "username" concept to explain at signup.
        user.username = self._unique_username(self.cleaned_data['email'])
        if commit:
            user.save()
            credential = SecurityCredential(user=user, question=self.cleaned_data['security_question'])
            credential.set_answer(self.cleaned_data['security_answer'])
            credential.save()
        return user

    @staticmethod
    def _unique_username(email):
        base = email.split('@')[0][:140] or 'user'
        username = base
        n = 1
        while User.objects.filter(username=username).exists():
            n += 1
            username = f'{base}{n}'
        return username


class ProfileEditForm(forms.ModelForm):
    """First/last name + email, edited from the account dashboard. Always
    bound to `request.user` by the view — never accepts a target user id,
    so there's no way to edit someone else's account through this form."""

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']
        widgets = {
            'first_name': forms.TextInput(attrs={**_NB_INPUT, 'placeholder': 'First name'}),
            'last_name': forms.TextInput(attrs={**_NB_INPUT, 'placeholder': 'Last name'}),
            'email': forms.EmailInput(attrs={**_NB_INPUT, 'placeholder': 'you@example.com'}),
        }

    def clean_email(self):
        email = self.cleaned_data['email'].strip().lower()
        if User.objects.filter(email__iexact=email).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError('Another account is already using this email.')
        return email


class SecurityQuestionEditForm(forms.ModelForm):
    """Lets a logged-in user replace their security question/answer. The
    current answer is never shown or pre-filled — only a fresh one is set."""
    new_answer = forms.CharField(
        max_length=255, required=True,
        widget=forms.TextInput(attrs={**_NB_INPUT, 'placeholder': 'New answer'}),
    )

    class Meta:
        model = SecurityCredential
        fields = ['question']
        widgets = {
            'question': forms.TextInput(attrs={**_NB_INPUT, 'placeholder': 'Security question'}),
        }

    def save(self, commit=True):
        credential = super().save(commit=False)
        credential.set_answer(self.cleaned_data['new_answer'])
        if commit:
            credential.save()
        return credential


class RecoverIdentifyForm(forms.Form):
    email = forms.EmailField(widget=forms.EmailInput(attrs={**_NB_INPUT, 'placeholder': 'you@example.com', 'autofocus': True}))


class RecoverAnswerForm(forms.Form):
    answer = forms.CharField(widget=forms.TextInput(attrs={**_NB_INPUT, 'placeholder': 'Your answer', 'autofocus': True}))
