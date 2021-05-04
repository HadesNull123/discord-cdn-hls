from fastapi import FastAPI, Response, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from celery import Celery
from celery.utils.log import get_task_logger
import requests_async as requests
import os
import base64
import pymongo
import gDriveLib
from ds import Discord
import videoLib
import logging
from bson import ObjectId
import random
import json
import time

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")
celery_app = Celery('tasks', broker='amqp://localhost//')
mongoClient = pymongo.MongoClient("mongodb+srv://admin:bovDxKtwUSmeABPr@cluster0.ijhu7.mongodb.net/kyunstreaming?retryWrites=true&w=majority")
logger = get_task_logger(__name__)
drive = gDriveLib.create_drive_manager()
mydb = mongoClient["discord_img"]
video_db = mydb["video"]

BASEURL = 'https://ci3-euw.googleapiscdn.com/discord'
CACHEROOT = 'apicache'

@celery_app.task
def uploadProcess(fileid):
    try:
        data = {}
        files =  gDriveLib.downloadQualities(drive,fileid)
        if len(files) > 0:
            for file in files:
                folder = fileid+'_'+file['quality']
                videoLib.splitChunks(file['path'],folder)
                # cookie = random.choice(json.loads(open('cookies.json').read()))
                uploader = Discord(folder)
                chunks = uploader.upload()
                playlist = videoLib.generatePlaylist(chunks)
                data[file['quality']] = playlist
            query = video_db.find_one({'drive':fileid})      
            update = { "$set": { "sources":data}}
            video_db.update_one(query,update)
            os.system('sudo rm -r ./*{}*'.format(fileid))
            return 'successful'
        else:
            video_db.delete_many({'drive':fileid})
            os.system('sudo rm -r ./*{}*'.format(fileid))
            return 'unsucessful'            
    except BaseException:
        logging.exception('error')
        video_db.delete_many({'drive':fileid})
        os.system('sudo rm -r ./*{}*'.format(fileid))
        return 'unsucessful'

@celery_app.task
def uploadFolder(folderid,key):
    try:
        files =  gDriveLib.recursiveSearch(drive,folderid)
        if len(files) > 0:
            folder_db.update_one({'drive':folderid},{ "$set": { "files":files}})
            for i in files:
                if not video_db.find_one({'drive':i['drive-id']}):
                    video_db.insert_one({'drive':i['drive-id'],'title':i['title'],'key':key})
                    uploadProcess.delay(i['drive-id'])
            return 'sucessful'     
        else:
            return 'no file added'     
    except BaseException:
        logging.exception('error')
        return 'unsucessful'


def writeCacheAPI(slug,data):
    os.makedirs(CACHEROOT,exist_ok=True)
    path = '{}/{}.json'.format(CACHEROOT,slug)
    json.dump(data,open(path,'w'))

def readCacheAPI(slug):
    path = '{}/{}.json'.format(CACHEROOT,slug)
    if os.path.isfile(path):
        data =  json.loads(open(path).read())
        if data['ttl'] > round(time.time()):
            os.remove(path)
        return data
    else:
        return None

@app.get("/api/{key:path}/addFile/{fileid:path}")
async def addFile(key: str, fileid: str,response: Response, request: Request):
    try:
        if key:
            cache = readCacheAPI(fileid)
            if cache:
                return cache
            else:
                query = video_db.find_one({'drive':fileid})
                if query:
                    slug = str(query['_id'])
                    if 'sources' in query.keys():
                        playlists = {}
                        for i in query['sources'].keys():
                            playlists[i] =  '{}/playlist/{}/{}.m3u8'.format(BASEURL,slug,i)
                        data = {
                            'status':'done',
                            'slug':slug,
                            'drive':fileid,
                            'thumbnail':'https://drive.google.com/thumbnail?authuser=0&sz=w9999&id='+fileid,
                            'playlist':playlists,
                            'iframe':'{}/player/{}'.format(BASEURL,slug),
                            'ttl' : round(time.time())+3600
                            }
                        writeCacheAPI(fileid,data)
                        return data
                    else:
                        return {'status':'processing','slug':slug,'drive':fileid,'thumbnail':'https://drive.google.com/thumbnail?authuser=0&sz=w9999&id='+fileid,'iframe':'{}/player/{}'.format(BASEURL,slug)}
                else:
                    if len(fileid) >27:
                        video_db.insert_one({'drive':fileid,'key':key})
                        slug = str(video_db.find_one({'drive':fileid})['_id'])
                        uploadProcess.delay(fileid)
                        return {'status':'received','slug':slug,'drive':fileid,'thumbnail':'https://drive.google.com/thumbnail?authuser=0&sz=w9999&id='+fileid,'iframe':'{}/player/{}'.format(BASEURL,slug)}
                    else:
                        response.status_code = 404
                        return {'status':'invalid file id'}
        else:
            response.status_code = 404
            return {'status':'invalid key'}
    except Exception as exception:
        response.status_code = 500
        return {'error':str(exception)}

@app.get("/api/{key:path}/getFile/{fileid:path}")
async def getFile(key: str, fileid: str,response: Response, request: Request):
    try:
        if key:
            query = video_db.find_one({'drive':fileid})
            if query:
                slug = str(query['_id'])
                if 'sources' in query.keys():
                    playlists = {}
                    for i in query['sources'].keys():
                        playlists[i] =  query['sources'][i]
                    return {'status':'done','slug':slug,'drive':fileid,'thumbnail':'https://drive.google.com/thumbnail?authuser=0&sz=w9999&id='+fileid,'playlist':playlists,'iframe':'{}/player/{}'.format(BASEURL,slug)}
                else:
                    return {'status':'processing','slug':slug,'drive':fileid,'thumbnail':'https://drive.google.com/thumbnail?authuser=0&sz=w9999&id='+fileid,'playlist':playlists,'iframe':'{}/player/{}'.format(BASEURL,slug)}
            else:
                return {'status':'file does not exist'}
        else:
            response.status_code = 404
            return {'status':'invalid key'}
    except Exception as exception:
        response.status_code = 500
        return {'error':str(exception)}

@app.get("/api/{key:path}/addFolder/{folderid:path}")
async def addFolder(key: str, folderid: str,response: Response, request: Request):
    try:
        if key:
            if len(folderid) >27:
                query = folder_db.find_one({'drive':folderid})
                if query:
                    if 'files' in query.keys():
                        return {'status':'added','files':query['files']}
                    else:
                        return {'status':'processing'}
                else:
                    folder_db.insert_one({'drive':folderid,'key':key})
                    uploadFolder.delay(folderid,key)
                    return {'status':'added'}
            else:
                response.status_code = 404
                return {'status':'invalid folder id'}
        else:
            response.status_code = 404
            return {'status':'invalid key'}
    except Exception as exception:
        response.status_code = 500
        return {'error':str(exception)}
        
def playlistGenerator(lines):
    new_playlist = []
    counter = 0
    for i in lines:
        if 'https://cdn.discordapp.com/' in i:
            path = i.replace('https://cdn.discordapp.com/','https://media.discordapp.net/')
            new_playlist.append(path)
            counter += 1
        else:
            new_playlist.append(i)
    return new_playlist

def masterPlaylistGenerator(qualities,slug,cf=False):
    playlist = [
        '#EXTM3U',
        '#EXT-X-VERSION:3'        
    ]
    for i in qualities:
        try:
            height = int(i)
            width = round((height/9)*16)
            resolution = '{}x{}'.format(width,height)
            bandwidth = round(width*height/10)
        except:
            resolution = '480x360'
            bandwidth = '17280'
        playlist.append('#EXT-X-STREAM-INF:BANDWIDTH={},RESOLUTION={},CODECS="avc1.640028,mp4a.40.2"'.format(bandwidth,resolution))
        playlist.append(BASEURL+'/playlist/{}/{}.m3u8'.format(slug,i))
    return playlist

@app.get("/playlist/{slug:path}/master.m3u8")
def masterPlaylistAPI(slug: str,response: Response, request: Request):
    try:
        query = video_db.find_one({'_id':ObjectId(slug)})
        if query:
            if 'sources' in query.keys():
                qualities = query['sources'].keys()
                response.headers['Access-Control-Allow-Origin'] = '*'
                new_playlist = masterPlaylistGenerator(qualities,slug)
                playlist = '\n'.join(new_playlist)
                response.body = bytes(playlist,'UTF-8')
                response.status_code = 200
                return response
            else:
                response.status_code = 404
                return {'status':'processing?'}
        else:
            response.status_code = 404
            return {'status':'not found'}
    except Exception as exception:
        response.status_code = 500
        return {'error':str(exception)}

@app.get("/playlist/{slug:path}/{quality:path}.m3u8")
async def playlistAPI(slug: str, quality: str,response: Response, request: Request):
    try:
        query = video_db.find_one({'_id':ObjectId(slug)})
        if query:
            if 'sources' in query.keys():
                if quality in query['sources'].keys():
                    response.headers['Access-Control-Allow-Origin'] = '*'
                    playlist = query['sources'][quality]
                    playlist_lines = playlist.split('\n')
                    new_playlist = playlistGenerator(playlist_lines)
                    playlist = '\n'.join(new_playlist)
                    response.body = bytes(playlist,'UTF-8')
                    response.status_code = 200
                    return response
                else:
                    response.status_code = 404
                    return {'status':'not found'}
            else:
                response.status_code = 404
                return {'status':'processing?'}
        else:
            response.status_code = 404
            return {'status':'not found'}
    except Exception as exception:
        response.status_code = 500
        return {'error':str(exception)}


@app.get("/chunk/{path:path}/{number:path}.ts")
async def chunksRedirect(path: str, number:str, response: Response, request: Request):
    try:
        response.headers['Location'] = 'https://media.discordapp.net/'+decodeBase64(path)
        response.status_code = 301
        return response
    except Exception as exception:
            response.headers['server'] = 'minhpg.com'
            return {'error':str(exception)}
    return response

@app.get("/player/{path:path}", response_class=HTMLResponse)
async def player(request: Request, path: str, response: Response,sub: str='',subname: str=None):
    try:
        query = video_db.find_one({'_id':ObjectId(path)})
        if query:
            slug = str(query['_id'])
            if 'sources' in query.keys():
                return templates.TemplateResponse("player_jquery.html", {"request": request})
            else:
                response.status_code = 500
                return templates.TemplateResponse("error.html", {"request": request, "error":'500','status':'Processing'})
        else:
            response.status_code = 404
            return templates.TemplateResponse("error.html", {"request": request, "error":'404','status':'Not Found'})
    except Exception as exception:
        response.status_code = 500
        return templates.TemplateResponse("error.html", {"request": request, "error":'500','status':str(exception)})

@app.post("/player/{path:path}")
async def player(request: Request, path: str, response: Response,sub: str='',subname: str=None):
    try:
        query = video_db.find_one({'_id':ObjectId(path)})
        if query:
            slug = str(query['_id'])
            if 'sources' in query.keys():
                playlists = []
                if not subname:
                    subname = sub.split("/")[-1]
                playlists.append({'file':BASEURL+'/playlist/{}/master.m3u8'.format(slug),'type':'m3u8'})
                return playlists
            else:
                response.status_code = 500
                return {'status':'processing'}
        else:
            response.status_code = 404
            return {'status':'not found'}
    except Exception as exception:
        response.status_code = 500
        return {'status':str(exception)}

@app.get("/counter")
async def counter(request: Request, response: Response):
    done = video_db.find({'sources':{'$exists':True}}).count()
    notdone = video_db.find({'sources':{'$exists':False}}).count()
    return {
        'done' : done,
        'processing' : notdone,
        'total': done+notdone
    }



def generateBase64(string):
    return base64.b64encode(bytes(string, 'utf-8')).decode("utf-8")

def decodeBase64(string):
    return base64.b64decode(bytes(string, 'utf-8')).decode("utf-8")





    