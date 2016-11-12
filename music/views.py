from django.contrib.auth import authenticate, login
from django.contrib.auth import logout
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404
from django.db.models import Q
from .forms import AlbumForm, SongForm, UserForm, SongFormNew
from .models import Album, Song
from django.http import HttpResponse
import os
from django.conf import settings
from wsgiref.util import FileWrapper
import mimetypes
import urllib2
from django.utils.encoding import smart_str


AUDIO_FILE_TYPES = ['wav', 'mp3', 'ogg']
IMAGE_FILE_TYPES = ['png', 'jpg', 'jpeg']


def create_album(request):
    if not request.user.is_authenticated():
        return render(request, 'music/login.html')
    else:
        form = AlbumForm(request.POST or None, request.FILES or None)
        if form.is_valid():
            album = form.save(commit=False)
            album.user = request.user
            album.album_logo = request.FILES['album_logo']
            file_type = album.album_logo.url.split('.')[-1]
            file_type = file_type.lower()
            if file_type not in IMAGE_FILE_TYPES:
                context = {
                    'album': album,
                    'form': form,
                    'error_message': 'Image file must be PNG, JPG, or JPEG',
                }
                return render(request, 'music/create_album.html', context)
            album.save()
            return render(request, 'music/detail.html', {'album': album, 'flag': True})
        context = {
            "form": form,
        }
        return render(request, 'music/create_album.html', context)


def create_song(request, album_id):
    form = SongForm(request.POST or None, request.FILES or None)
    album = get_object_or_404(Album, pk=album_id)
    if form.is_valid():
        albums_songs = album.song_set.all()
        for s in albums_songs:
            if s.song_title == form.cleaned_data.get("song_title"):
                context = {
                    'album': album,
                    'form': form,
                    'error_message': 'You already added that song',
                }
                return render(request, 'music/create_song.html', context)
        song = form.save(commit=False)
        song.album = album
        print request.FILES['audio_file']
        song.audio_file = request.FILES['audio_file']
        # print song.audio_file.url
        file_type = song.audio_file.url.split('.')[-1]
        file_type = file_type.lower()
        if file_type not in AUDIO_FILE_TYPES:
            context = {
                'album': album,
                'form': form,
                'error_message': 'Audio file must be WAV, MP3, or OGG',
            }
            return render(request, 'music/create_song.html', context)

        song.save()
        return render(request, 'music/detail.html', {'album': album, 'flag': True})
    context = {
        'album': album,
        'form': form,
    }
    return render(request, 'music/create_song.html', context)


def delete_album(request, album_id):
    album = Album.objects.get(pk=album_id)
    albums1 = Album.objects.filter(is_public=True).exclude(user=request.user)
    file_name = []

    for s in album.song_set.all():
        os.remove(os.path.join(settings.MEDIA_ROOT, s.audio_file.url.split('/')[-1]))
    # print file_name
    album.delete()

    albums = Album.objects.filter(user=request.user)
    return render(request, 'music/index.html', {'albums': albums, 'public_albums': albums1})


def delete_song(request, album_id, song_id):
    album = get_object_or_404(Album, pk=album_id)
    song = Song.objects.get(pk=song_id)
    file_name = song.audio_file.url.split('/')[-1]

    song.delete()
    os.remove(os.path.join(settings.MEDIA_ROOT, file_name))
    return render(request, 'music/detail.html', {'album': album, 'flag': True})


def detail(request, album_id):
    if not request.user.is_authenticated():
        return render(request, 'music/login.html')
    else:
        user = request.user
        album = get_object_or_404(Album, pk=album_id)
        flag = False
        if album.user == user :
            flag = True
        return render(request, 'music/detail.html', {'album': album, 'user': user, 'flag' : flag})


def favorite(request, song_id):
    song = get_object_or_404(Song, pk=song_id)
    try:
        if song.is_favorite:
            song.is_favorite = False
        else:
            song.is_favorite = True
        song.save()
    except (KeyError, Song.DoesNotExist):
        return JsonResponse({'success': False})
    else:
        return JsonResponse({'success': True})


def favorite_album(request, album_id):
    album = get_object_or_404(Album, pk=album_id)
    try:
        if album.is_favorite:
            album.is_favorite = False
        else:
            album.is_favorite = True
        album.save()
    except (KeyError, Album.DoesNotExist):
        return JsonResponse({'success': False})
    else:
        return JsonResponse({'success': True})


def index(request):
    if not request.user.is_authenticated():
        return render(request, 'music/login.html')
    else:
        albums = Album.objects.filter(user=request.user)
        albums1 = Album.objects.filter(is_public=True).exclude(user=request.user)
        song_results = Song.objects.filter(Q(album__in=albums) | Q(album__in=albums1)).distinct()
        query = request.GET.get("q")
        if query:
            albums = albums.filter(
                Q(album_title__icontains=query) |
                Q(artist__icontains=query)
            ).distinct()
            albums1 = albums1.filter(
                Q(album_title__icontains=query) |
                Q(artist__icontains=query)
            ).distinct()
            song_results = song_results.filter(
                Q(song_title__icontains=query)
            ).distinct()
            return render(request, 'music/index.html', {
                'albums': albums,
                'public_albums': albums1,
                'songs': song_results,
            })
        else:
            return render(request, 'music/index.html', {'albums': albums, 'public_albums': albums1})


def logout_user(request):
    logout(request)
    form = UserForm(request.POST or None)
    context = {
        "form": form,
    }
    return render(request, 'music/login.html', context)


def login_user(request):
    if request.method == "POST":
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(username=username, password=password)
        if user is not None:
            if user.is_active:
                login(request, user)
                albums = Album.objects.filter(user=request.user)
                albums1 = Album.objects.filter(is_public=True).exclude(user=request.user)
                return render(request, 'music/index.html', {'albums': albums, 'public_albums': albums1})
            else:
                return render(request, 'music/login.html', {'error_message': 'Your account has been disabled'})
        else:
            return render(request, 'music/login.html', {'error_message': 'Invalid login'})
    return render(request, 'music/login.html')


def register(request):
    form = UserForm(request.POST or None)
    if form.is_valid():
        user = form.save(commit=False)
        username = form.cleaned_data['username']
        password = form.cleaned_data['password']
        user.set_password(password)
        user.save()
        user = authenticate(username=username, password=password)
        if user is not None:
            if user.is_active:
                login(request, user)
                albums = Album.objects.filter(user=request.user)
                return render(request, 'music/index.html', {'albums': albums})
    context = {
        "form": form,
    }
    return render(request, 'music/register.html', context)


def songs(request, filter_by):
    if not request.user.is_authenticated():
        return render(request, 'music/login.html')
    else:
        try:
            song_ids = []
            for album in Album.objects.filter( Q(user=request.user) |  Q(is_public=True)).distinct():
                for song in album.song_set.all():
                    song_ids.append(song.pk)
            users_songs = Song.objects.filter(pk__in=song_ids)
            if filter_by == 'favorites':
                users_songs = users_songs.filter(is_favorite=True)
        except Album.DoesNotExist:
            users_songs = []
        return render(request, 'music/songs.html', {
            'song_list': users_songs,
            'filter_by': filter_by,
        })

def download_song(request, song_id):
    song = Song.objects.get(pk=song_id)
    file_name = song.audio_file.url.split('/')[-1]
    file_path = os.path.join(settings.BASE_DIR,'media', file_name)
    file_wrapper = FileWrapper(file(file_path,'rb'))
    file_mimetype = mimetypes.guess_type(file_path)
    print file_mimetype
    response = HttpResponse(file_wrapper, content_type=file_mimetype )
    response['X-Sendfile'] = file_path
    response['Content-Length'] = os.stat(file_path).st_size
    response['Content-Disposition'] = 'attachment; filename=%s' % smart_str(file_name) 
    return response

def upload_song(request, album_id):
    form = SongFormNew(request.POST or None)
    album = get_object_or_404(Album, pk=album_id)
    if form.is_valid():
        song_title = form.cleaned_data["title"]
        albums_songs = album.song_set.all()
        for s in albums_songs:
            if s.song_title == form.cleaned_data.get("song_title"):
                return returnErrorMsgToUploadSong(request, album, form, 'You already added a song with same title')

        song_url = form.cleaned_data["url"]

        try:
            f = urllib2.urlopen(song_url)
        except (urllib2.URLError, ValueError):
            return returnErrorMsgToUploadSong(request, album, form, 'Something went wrong with the URL')

        if f.info().getmaintype() == "audio":
            ext = song_url.split('.')[-1]
            if ext not in AUDIO_FILE_TYPES:
                return returnErrorMsgToUploadSong(request, album, form, 'Audio file must be WAV, MP3, or OGG')

            file_name = album.album_title+'_'+song_title+"."+ext
            file_path = os.path.join(settings.MEDIA_ROOT, file_name)
            with open(file_path, 'wb') as f1:
                for line in f:
                    # print 'downloading'
                    f1.write(line)
            
            f.close()
            f1.close()

        else:
            return returnErrorMsgToUploadSong(request, album, form, 'This url does not contain any audio file')

        song = Song(album=album, song_title=song_title, audio_file=file_name)
        song.save()
        return render(request, 'music/detail.html', {'album': album, 'flag': True})
    context = {
        'album': album,
        'form': form,
    }
    return render(request, 'music/upload_song.html', context)


def returnErrorMsgToUploadSong(request, album, form, msg):
    context = {
        'album': album,
        'form': form,
        'error_message': msg,
    }
    return render(request, 'music/upload_song.html', context)