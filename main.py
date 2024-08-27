import customtkinter as tk
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import os
from dotenv import main
from PIL import Image, ImageTk
import random
import urllib.request
import io
import webbrowser
import json
import vlc
from threading import Timer
import time
import pickle
import inspect

# changes I want to make:
# remove vlc dependency
# use ffmpeg to convert to wav
# find way to host api key in cloud

#Create a spotify thingy
client_uri = "http://google.com/callback"
global playlistInfo
playlistInfo = []
global playlists 
playlists = []
global isPlaylistGotten
isPlaylistGotten = False
tracks = []
playlistNames = []
global acceptedTracks 
acceptedTracks = {}
global p
# loads spotify api 
main.load_dotenv()
oauth_object = spotipy.SpotifyOAuth(os.getenv('SPOTIPY_CLIENT_ID'), os.getenv('SPOTIPY_CLIENT_SECRET'), client_uri, scope=("playlist-read-private user-library-modify playlist-read-collaborative user-read-private"))
token = oauth_object.get_access_token(as_dict=False)
sp = spotipy.Spotify(auth=token)
playlists = sp.current_user_playlists(limit=50)

# window handles logging in to spotify
class MainWindow(tk.CTk):
  #initilize the window/app
  def __init__(self):
    # sets up window 
    super().__init__()
    self.check_if_directory_exists('saves')
    self.geometry("600x500")
    self.title("Waveify 1.0.0")
    self.finalTrackList = []
    self.resizable(False, False)
    tk.set_default_color_theme("theme.json")
    tk.set_appearance_mode("dark")
    # loads likes and dislikes
    self.likedSongs = self.load_saved_tracks('./saves/liked_songs.json')
    self.dislikedSongs = self.load_saved_tracks('./saves/disliked_songs.json')
    # creates basic gui elements 
    self.welcomeLbl = tk.CTkLabel(self, text="Welcome to Waveify!", font=("Gotham-Bold", 32))
    self.welcomeLbl.pack(side="top",padx=20,pady=20)
    # create a canvas to hold covers
    self.cover_canvas = tk.CTkCanvas(self, width=600, height=250, bg="#242424", highlightthickness=0)
    self.cover_canvas.place(relx=0.5, rely=0.45, anchor="center")
    self.cover_frame = tk.CTkFrame(self.cover_canvas, fg_color="#ffffff", width=600, height=250)
    self.cover_frame.grid_columnconfigure(0, weight=1)
    self.cover_canvas.create_window((0, 0), window=self.cover_frame, anchor="nw")
    self.left_to_right(self.get_all_covers())
    self.cover_canvas.update_idletasks()
    self.cover_canvas.configure(scrollregion=self.cover_canvas.bbox("all"))
    self.scroll_canvas()
    # get playlist btn
    self.getPlaylistBtn = tk.CTkButton(self, width=200, height=50, text="Sign in with Spotify", command=self.getPlaylists, corner_radius=30, fg_color="#51D75B", text_color="#1e1e1e")
    self.getPlaylistBtn.place(relx=0.5, rely=0.85, anchor="center")
    self.song_name_lbl = None
    self.song_artist_lbl = None
    
    
  def check_if_directory_exists(self, dir_name):
    if os.path.isdir(dir_name) != True:
      os.makedirs(dir_name)

  # gets all covers by either getting the covers of liked songs 
  # or getting the covers of the Spotify top 50. 
  def get_all_covers(self):   
    list_of_covers = []  # initialize an empty list to store cover URLs
    if self.likedSongs:
        # if there are liked songs, get the covers of those songs
        for key, value in self.likedSongs.items():
            cover_url = self.getSongArtFromID(value['id'])  # get cover URL from song ID
            list_of_covers.append(cover_url)  # add cover URL to the list
        return list_of_covers  # return the list of cover URLs
    else:
        # if there are no liked songs, get the covers of the Spotify top 50
        top_50_playlist_id = "37i9dQZF1DXcBWIGoYBM5M"  # ID of Spotify top 50 playlist
        results = sp.playlist_tracks(top_50_playlist_id)  # get tracks from the playlist
        for track in results['items']:
            cover_url = track['track']['album']['images'][0]['url']  # get cover URL from the track
            list_of_covers.append(cover_url)  # add cover URL to the list
        return list_of_covers  # return the list of cover URLs
  
  def left_to_right(self, list_of_images):
    images = []
    for i, cover in enumerate(list_of_images):
      with urllib.request.urlopen(cover) as u:
        raw_data = u.read()
      image = Image.open(io.BytesIO(raw_data)).resize((250,250), Image.LANCZOS)
      img = ImageTk.PhotoImage(image)
      image_lbl = tk.CTkLabel(self.cover_frame, image=img, text="")
      images.append(img) # keep reference to prevent garbage collection
      image_lbl.grid(row=0, column=i, padx=15, pady=15) # places image
    
  def scroll_canvas(self):
    scroll_amount = 0.25
    current_position = self.cover_canvas.xview()[0] # gets current position
    new_position = current_position - scroll_amount / 100.0
    if new_position < 0:
        new_position = 1.0 # if position is zero, moves it to one
    self.cover_canvas.xview_moveto(new_position)
    self.after(64, self.scroll_canvas)

# gets playlist names
  def getPlaylists(self):
    self.inPlaylistMode = True
    self.getPlaylistBtn.place_forget() # hides button
    self.cover_canvas.place_forget() # hides covers
    self.welcomeLbl.pack_forget()
    playlistInfo.append(self.getPlaylistUri(playlists))
    playlistNames.append(self.getPlaylistName(playlists))
    print(playlistInfo)
    self.displayPlaylists()
        
# displays playlists
  def displayPlaylists(self):
    self.enter_lbl = tk.CTkLabel(self, text="Enter Playlist URL or Choose Playlist", font=("Gotham-Bold", 28)).pack(side="top",padx=20,pady=12)
    posY = 0.1
    counter = 0
    self.listPlaylistBtns = []
    frame = tk.CTkScrollableFrame(self, fg_color="#696969")
    frame.place(relx =0.05, rely=0.225, anchor="nw")
    for x in range(len(playlistNames[0])):
      self.listPlaylistBtns.append(tk.CTkCheckBox(frame, width=20, height=40, text=playlistNames[0][x], corner_radius=10,hover_color="#76de7d",fg_color="#51d75b", text_color="#FFFFFF"))
      self.listPlaylistBtns[x].pack(side="top", anchor="w")
      posY += 0.1
      counter += 1
      width = 0
      if(self.listPlaylistBtns[x].winfo_width() > width):
        width = self.listPlaylistBtns[x].winfo_width()
        frame.configure(width=450, height=325)
    self.playlistSubmitBtn = tk.CTkButton(self, text="Submit", height=30, command=self.when_submit_btn_clicked).place(relx= 0.05, rely = 0.95, anchor="w")

  def getSelectedPlaylists(self): # works
    counter = 0
    playlist_ids = []
    for checkbox in self.listPlaylistBtns:
      if checkbox.get() == 1:
        print(playlistInfo[0][counter])
        playlist_ids.append(playlistInfo[0][counter])
      counter += 1
    return playlist_ids
        
  def getPlaylistTracks(self, playlist_ids):
    trackList = []
    offset = 0
    # Ref - https://stackoverflow.com/questions/39086287/spotipy-how-to-read-more-than-100-tracks-from-a-playlist?noredirect=1&lq=1
    for x in range (len(playlist_ids)):
      playlist_id = playlist_ids[x]
      offset += 100
      results = sp.playlist_tracks(playlist_id, offset=offset)
      tracks = results['items']
    while results['next']:
        results = sp.next(results)
        tracks.extend(results['items'])
    for item in tracks:
        is_local = item["is_local"]
        if is_local == True: # Filtering out any local tracks (not hosted by Spotify)
          continue
        else:
          track = item['track']['name']
          trackList.append(track)
    return trackList
  
  def getTrackUris(self, playlist_ids):
    track_uris = []
    for x in range(len(playlist_ids)):
      playlist_id = playlist_ids[x]
      results = sp.playlist_tracks(playlist_id)
      tracks = results['items']
    while results['next']:
        results = sp.next(results)
        tracks.extend(results['items'])
    for item in tracks:
        is_local = item["is_local"]
        if is_local == True: # Filtering out any local tracks (i.e. not hosted by Spotify)
          continue
        else:
          track = item['track']['uri']
          track_uris.append(track)
    return track_uris
  
  def getPlaylistUri(self, playlist_list):
    playlist_uris = []
    for item in playlist_list['items']:
      playlist_uris.append(item['uri'])
    return playlist_uris
  
  def getPlaylistName(self, playlist_list):
    playlist_names = []
    for item in playlist_list['items']:
      playlist_names.append(item['name'])
    return playlist_names
  
  def getMusicRecommendations(self, songs):
    print(songs)
    self.recommendedTracks = []
    randomSongList = []
    for x in range(5):
      randomSongList.append(songs[random.randint(0, len(songs)-1)])
    recommendations = sp.recommendations(seed_tracks=randomSongList, limit=100)
    for x in recommendations['tracks']:
      track = {'name': x['name'], 'artist': x['artists'][0]['name'], 'uri': x['uri'], 'art': x['album']['images'][0]['url'], 'preview_url': x['preview_url']}
      if(track['preview_url'] == None):
        continue
      if(track['uri'] == self.likedSongs or track['uri'] == self.dislikedSongs):
        continue
      self.recommendedTracks.append(track)
    self.createRecommendationWindow()
    
  def when_submit_btn_clicked(self):
    print("\n")
    print(self.getTrackUris(self.getSelectedPlaylists()))
    self.getMusicRecommendations(self.getTrackUris(self.getSelectedPlaylists()))
    
  # recommendation window and its functions
  
  def addSongToLiked(self):
      song = self.getRandomSongWNum(self.recommendedTracks, self.randomSongNum)
      cut_song = song[14:len(song)]
      sp.current_user_saved_tracks_add(tracks= [cut_song])
      if hasattr(self, 'likedSongs') and 'uri' in self.likedSongs:
          song = {**self.getSongFromUri(song), **self.getSongFromUri(self.likedSongs['uri'])}
      else:
          song = self.getSongFromUri(song)
      print("\n\n\n")
      print(song)
      try:
          with open('./saves/liked_songs.json', 'r+') as f:
              existing_data = json.load(f)
              existing_data.update({song['uri']: song})
              f.seek(0)
              json.dump(existing_data, f, indent=4)
              f.truncate()
      except FileNotFoundError:
          with open('./saves/liked_songs.json', 'w') as f:
              json.dump({song['uri']: song}, f)
      self.nextSong()
      self.stopSong()
      playTimer.cancel()
    
  def dislikeSong(self):
    song = self.getRandomSongWNum(self.recommendedTracks, self.randomSongNum)
    cut_song = song[14:len(song)]
    sp.current_user_saved_tracks_add(tracks= [cut_song])
    if hasattr(self, 'dislikedSongs') and 'uri' in self.likedSongs:
      song = {**self.getSongFromUri(song), **self.getSongFromUri(self.likedSongs['uri'])}
    else:
      song = self.getSongFromUri(song)
    print("\n\n\n")
    print(song)
    try:
      with open('./saves/disliked_songs.json', 'r') as f:
        disliked_songs = json.load(f)
    except FileNotFoundError:
      disliked_songs = {}
    song_uri = song['uri']
    disliked_songs[song_uri] = song
    print("\n\n\n")
    print(disliked_songs)
    with open('./saves/disliked_songs.json', 'w') as f:
      json.dump(disliked_songs, f)
    self.nextSong()
    self.stopSong()
    playTimer.cancel()
  
  def createRecommendationWindow(self):
    self.rcmdWindow = tk.CTkToplevel(self)
    self.rcmdWindow.geometry("600x600")
    self.rcmdWindow.title("Waveify Recommendations")
    self.font = tk.CTkFont(family="Gotham-Bold", size=32)
    self.song_name_lbl = tk.CTkLabel(self.rcmdWindow, text="")
    self.song_artists_lbl = tk.CTkLabel(self.rcmdWindow, text="")
    waveify_name = tk.CTkLabel(self.rcmdWindow, text="Waveify", font=("Gotham-Bold", 32), text_color="#51d75b", bg_color="transparent").pack(side="top",padx=20,pady=20)
    addBtn = tk.CTkButton(self.rcmdWindow, text="+", width = 50, height=50, command=self.addSongToLiked, font=("Gotham-Bold", 32), text_color="#1e1e1e").place(relx= 0.92, rely = 0.4, anchor="e")
    forgetBtn = tk.CTkButton(self.rcmdWindow, text="-", width = 50, height=50, command=self.dislikeSong, font=("Gotham-Bold", 32), text_color="#1e1e1e").place(relx= 0.08, rely = 0.4, anchor="w")
    self.nextSong()
  
  def when_playBtn_clicked(self):
    self.playSong(self.recommendedTracks[self.randomSongNum]['preview_url'])
    
  def getRandomSong(self, recommended_tracks):
    self.randomSongNum = random.randint(0, len(recommended_tracks)-1)
    randomSong = recommended_tracks[self.randomSongNum]['uri']
    return randomSong
  
  
  def getRandomSongWNum(self, recommended_tracks, song_num):
    randomSong = recommended_tracks[song_num]['uri']
    return randomSong

  def getSongArt(self, recommended_tracks):
    randomArt = recommended_tracks[self.randomSongNum]['art']
    return randomArt
  
  def getSongArtFromID(self, id):
    track = sp.track(id)
    return track['album']['images'][0]['url']
  
  def getSongArtFromURL(self, url):
    track_id = url[14:len(url)]
    track = sp.track(track_id)
    album = sp.album(track['album']['id'])
    return album["images"][0]['url']
  
  
  def getSongArtist(self, recommended_tracks):
    artist = recommended_tracks[self.randomSongNum]['artist']
    print(artist)
    return artist
  
  def getSongName(self, recommended_tracks):
    name = recommended_tracks[self.randomSongNum]['name']
    print(name)
    return name
  
  
  #Retrieves a song based on the provided URI.
  def getSongFromUri(self, uri):
    song = sp.track(uri)
    return song
    
  def displaySongArt(self, song_art_url):
    url = song_art_url
    with urllib.request.urlopen(url) as u:
      raw_data = u.read()
    image = Image.open(io.BytesIO(raw_data)).resize((300,300), Image.LANCZOS)
    songArt = ImageTk.PhotoImage(image)
    image = tk.CTkLabel(self.rcmdWindow, text="", image=songArt)
    image.place(relx=0.5, rely=0.41, anchor="center")
    
    
  def place_song_lbls(self):
    self.song_name_lbl = tk.CTkLabel(self.rcmdWindow, text=self.getSongName(self.recommendedTracks), font=("Gotham-Bold", 24), text_color="#FFFFFF", bg_color="transparent", justify="center")
    self.song_name_lbl.place(relx=0.07, rely=0.8)
    self.song_artists_lbl = tk.CTkLabel(self.rcmdWindow, text=self.getSongArtist(self.recommendedTracks), font=("Gotham-Bold", 18), text_color="#FFFFFF", bg_color="transparent", justify="center")
    self.song_artists_lbl.place(relx=0.07, rely=0.85)
    self.playBtnImage = tk.CTkImage(Image.open(r"playBtn50.png"))
    self.pauseBtnImage = tk.CTkImage(Image.open(r"pauseBtn50.png"))
    self.playBtn = tk.CTkButton(self.rcmdWindow, image=self.playBtnImage, width=30, height=50, text="", corner_radius=50, command=self.when_playBtn_clicked)
    self.playBtn.place(relx=0.5, rely=0.725, anchor="center")

  def nextSong(self):
    song = self.getRandomSong(self.recommendedTracks)
    if (isinstance(self.song_name_lbl, tk.CTkLabel)):
      self.song_name_lbl.destroy()
      self.song_artists_lbl.destroy()
    self.displaySongArt(self.getSongArt(self.recommendedTracks))
    self.place_song_lbls()
    
  def timer(self):
    global playTimer 
    playTimer = Timer(30, self.stopSong)
  
  def playSong(self, preview_url):
    global p
    p = vlc.MediaPlayer(preview_url)
    p.play()
    self.timer()
    self.timeout = 30
    self.callback = self.stopSong
    playTimer.start()
    self.start_time = time.time()
    self.playBtn.configure(command=self.pause)
    self.playBtn.configure(image=self.pauseBtnImage)
    
  
  def stopSong(self):
    p.stop()
    
   #ref https://stackoverflow.com/questions/26089391/pause-resume-functions-for-timer  
  def pause(self):
    self.cancel_time = time.time()
    playTimer.cancel()
    p.pause()
    self.playBtn.configure(command=self.resume)
    self.playBtn.configure(image=self.playBtnImage)
    
  def resume(self):
      print("in resume")
      self.timeout = self.get_remaining_time()
      playTimer = Timer(self.timeout, self.callback)
      self.start_time = time.time()
      playTimer.start()
      p.play()
      self.playBtn.configure(command=self.pause, image=self.pauseBtnImage)

  def get_remaining_time(self):
        if self.start_time is None or self.cancel_time is None:
            return self.timeout
        return self.timeout - (self.cancel_time - self.start_time)
    
  def load_saved_tracks(self, filePath):
    likedSongs = {}
    if not os.path.isfile(filePath):  # checks if file exists
      with open(filePath, 'w') as f:  # creates file if it does not
        json.dump({}, f)  # initialize with an empty dictionary
      return likedSongs
    try:
      with open(filePath, 'r') as f:  # reads file
        likedSongs = json.load(f)  # load JSON data
        print("\nLiked Songs:")
        print(likedSongs)
        return likedSongs
    except json.JSONDecodeError as e:
         print(f"Error parsing JSON: {e}")
         return likedSongs



# main 
app = MainWindow()
app.mainloop()



