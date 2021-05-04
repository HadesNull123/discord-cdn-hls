import os
import json

def splitChunks(file,dest):
    if not os.path.isdir(dest):
        os.mkdir(dest)
    os.system("ffmpeg -i "+file+" -metadata service_name='ffmpeg_spliiter' -metadata service_provider='kyunstreamml' -codec: copy -start_number 0 -hls_time 1 -hls_playlist_type vod -hls_list_size 0 -hls_segment_filename "+dest+"/%04d.ts "+dest+"/playlist.m3u8")

def generatePlaylist(data):
    folder = data[0]['chunk']['folder']

    playlist = open(os.path.join(folder,'playlist.m3u8'),'r').read()

    for i in data:
        chunk = i['chunk']['chunk']
        playlist = playlist.replace(i['chunk']['chunk'],i['url'])
    return playlist