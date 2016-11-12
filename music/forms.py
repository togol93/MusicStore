from django import forms
from django.contrib.auth.models import User

from .models import Album, Song


class AlbumForm(forms.ModelForm):

    class Meta:
        model = Album
        fields = ['artist', 'album_title', 'genre', 'album_logo','is_public']


class SongForm(forms.ModelForm):

    class Meta:
        model = Song
        fields = ['song_title', 'audio_file']


class UserForm(forms.ModelForm):
    # password = forms.CharField(widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ['username', 'email', 'password']
        # fields = '__all__'

class SongFormNew(forms.Form):

    title = forms.CharField(max_length = 250)
    url = forms.CharField(max_length = 250)
