import re
from os import path
import requests
from multiprocessing.pool import ThreadPool
import math
import os
import json
import random
from urllib import parse
import logging


def extractFileId(links):
    links = re.findall(r"\b(?:https?:\/\/)?(?:drive\.google\.com[-_&?=a-zA-Z\/\d]+)",links)  
    fileIDs = [re.search(r"(?<=/d/|id=|rs/).+?(?=/|$)", link)[0] for link in links]
    print(fileIDs)
    return fileIDs

def downloadQualities(fileid,path,teamdrive=True):
    downloadFile(id=fileid,destination=path)
    return [{'path':path,'quality':'original'}]

def downloadFile(id, destination):
    URL = "https://docs.google.com/uc?export=download"

    session = requests.Session()

    response = session.get(URL, params = { 'id' : id }, stream = True)
    token = getConfirmToken(response)

    if token:
        params = { 'id' : id, 'confirm' : token }
        response = session.get(URL, params = params, stream = True)

    saveResponseContent(response, destination)    

def getConfirmToken(response):
    for key, value in response.cookies.items():
        if key.startswith('download_warning'):
            return value

    return None

def saveResponseContent(response, destination):
    CHUNK_SIZE = 32768

    with open(destination, "wb") as f:
        for chunk in response.iter_content(CHUNK_SIZE):
            if chunk: # filter out keep-alive new chunks
                f.write(chunk)


def parseCookie(cookie):
    items = cookie.split(";")
    parse_1 = []
    for i in items:
        a = i.split("=")
        try: 
            data = a[1]
        except:
            data =""
        parse_1.append({a[0].strip():data.strip()})
    return(items)

def extractCookie(metadata):
    cookie = parseCookie(metadata['set-cookie'])
    return cookie[0]
    
def getVideoInfo(fileid,proxies=None,headers=None):
    data = json.loads(open('proxy.json').read())
    sv = random.randrange(0,len(data)-1)
    proxy = data[sv]
    proxies = {
        'http': 'http://{}@{}:{}'.format(proxy['auth'],proxy['ip'],proxy['port']),
        'https' : 'http://{}@{}:{}'.format(proxy['auth'],proxy['ip'],proxy['port'])
    }
    print(proxies)
    response = requests.get('https://drive.google.com/get_video_info?docid='+fileid,proxies=proxies,headers=headers)
    query = response.text 
    print(query)
    data = dict(parse.parse_qsl(query))
    cookie = headers['cookie']
    files = []
    qualities = parseFmtStream(data['fmt_stream_map'])
    for i in qualities:
        if i['quality'] <= 720:
            quality = str(i['quality'])
            path = f'{fileid}_{quality}.mp4'
            chunkedDownloader(i['url'],path,cookie,proxies=proxies)
            files.append({
                'path' : path,
                'quality' : i['quality']
            })
    return files

def parseFmtStream(fmt_stream_map):
    qualities = fmt_stream_map.split(',')
    data = []
    for quality in qualities:
        comp = quality.split('|')
        itag = comp[0]
        url = comp[1]
        itags = {
            '18' : 360,
            '59' : 480,
            '22' : 720,
            '37' : 1080
        }
        data.append({
            'itag' : itag,
            'quality' : itags[itag],
            'url' : url
        })
    return data

def downloadFmt(url,filename,headers=None,proxies=None):
    response =requests.get(url,headers=headers,proxies=proxies,stream=True,verify=False)
    headers = dict(response.headers)
    total_size_in_bytes= int(headers["Content-Length"])
    block_size = 1024*1024
    with open(filename, 'wb') as file:
        for data in response.iter_content(block_size):
            file.write(data)
    return total_size_in_bytes

def downloadChunks(data):  
    headers = data['headers']
    url = data['url']
    filename = data['filename']
    proxies = {}
    while True:
        response = requests.head(url,headers=headers,proxies=proxies)
        headers_response = dict(response.headers)
        print(headers_response)
        if 'location' in headers_response.keys():
            url = headers_response['location']
            continue
        if 'Location' in headers_response.keys():
            url = headers_response['Location']
            continue
        else:
            break
    response = requests.get(url,headers=headers,proxies=proxies,stream=True)
    headers = dict(response.headers)               
    total_size_in_bytes= int(headers["Content-Length"])
    block_size = 1024*1024
    with open(filename, 'wb') as file:
        for data in response.iter_content(block_size):
            file.write(data)
    return total_size_in_bytes

def chunkedDownloader(url,filename,cookie,proxies,headers=None):  # Streaming, so we can iterate over the response.
    print('Downloading {}'.format(filename))
    while True:
        response = requests.head(url,headers={'range':'bytes=0-','cookie':cookie},proxies=proxies)
        headers_response = dict(response.headers)
        print(headers_response)
        if 'location' in headers_response.keys():
            url = headers_response['location']
            continue
        if 'Location' in headers_response.keys():
            url = headers_response['Location']
            continue
        else:
            break

    content_length = int(headers_response['Content-Length'])
    chunks = generateChunks(url,filename,content_length,cookie,proxies)
    pool = ThreadPool(20)
    pool.map(downloadChunks,chunks)
    f= open(filename,'ab')
    for i in chunks:
        data  = open(i['filename'],'rb').read()
        f.write(data)
        os.remove(i['filename'])
    return filename

def generateChunks(url,filename,content_length,cookie,proxies):
    chunks = []
    chunk_size = 1024*1024*5
    start = 0
    end = chunk_size
    counter = 0
    no_chunks = math.ceil(content_length/chunk_size)
    for i in range(no_chunks):
        data = {
            'headers': {'range':'bytes={}-{}'.format(str(start),str(end)),'cookie':cookie},
            'url' : url,
            'filename' : filename+'_'+str(counter),
            'proxies' : proxies
        }
        chunks.append(data)
        start = end+1
        end += chunk_size
        if end > content_length:
            end = content_length
        counter += 1
    return chunks


def recursiveSearch(drive,folderID):
    files = []
    folder = drive.ListFile({'q': "'" + folderID + "' in parents"}).GetList()
    for i in folder:
        if(i['mimeType'] == "application/vnd.google-apps.folder"):
            for a in recursiveSearch(drive,i['id']):
                files.append(a)
        else:
            files.append({'title':i["title"],'drive-id':i['id']})
    return(files)