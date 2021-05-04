import os
import requests
import time
import random
import string
from requests_toolbelt import MultipartEncoder
import logging
from inject import chunkInject
import json
from multiprocessing.pool import ThreadPool

class Discord:
    def __init__(self,folder):
        self.files = self.injectPayload(folder)
        self.tokens = json.loads(open('token.json').read())

    def injectPayload(self,folder):
        counter = 0
        chunks = []
        new_folder = folder+'_output'
        if not os.path.isdir(new_folder):
            os.mkdir(new_folder)
        for i in os.listdir(folder):
            if not 'm3u8' in i:
                chunks.append({'source':os.path.join(folder,i),'folder':folder,'chunk':i,'dest':os.path.join(new_folder,str(counter)+'.png')})
                counter += 1
        for i in chunks:
            chunkInject(i['source'],i['dest'])
            os.remove(i['source'])
        return chunks


    def uploadAPI(self,file,token):     
        data = MultipartEncoder({
            'payload_json':json.dumps({
                'content' : '',
                'tts' : False
            }),
            'file' : (
                'unnamed.png',
                open(file,'rb'),
                'image/png'
            )
        })
        headers = {
        'authorization' : token,
        'content-type' : data.content_type,
        'referer' : 'https://discord.com/channels/759583019224399913/759583019680923700',
        'x-super-properties' : 'eyJvcyI6IldpbmRvd3MiLCJicm93c2VyIjoiQ2hyb21lIiwiZGV2aWNlIjoiIiwiYnJvd3Nlcl91c2VyX2FnZW50IjoiTW96aWxsYS81LjAgKFdpbmRvd3MgTlQgMTAuMDsgV2luNjQ7IHg2NCkgQXBwbGVXZWJLaXQvNTM3LjM2IChLSFRNTCwgbGlrZSBHZWNrbykgQ2hyb21lLzg3LjAuNDI4MC44OCBTYWZhcmkvNTM3LjM2IiwiYnJvd3Nlcl92ZXJzaW9uIjoiODcuMC40MjgwLjg4Iiwib3NfdmVyc2lvbiI6IjEwIiwicmVmZXJyZXIiOiIiLCJyZWZlcnJpbmdfZG9tYWluIjoiIiwicmVmZXJyZXJfY3VycmVudCI6IiIsInJlZmVycmluZ19kb21haW5fY3VycmVudCI6IiIsInJlbGVhc2VfY2hhbm5lbCI6InN0YWJsZSIsImNsaWVudF9idWlsZF9udW1iZXIiOjczODA2LCJjbGllbnRfZXZlbnRfc291cmNlIjpudWxsfQ=='
        }

        counter = 0
        while True:
            try:
                response = requests.post(
                'https://discord.com/api/v8/channels/759583019680923700/messages',
                headers = headers,
                data = data,
                )
                if 'attachments' in response.json().keys():
                    return response.json()
                else:
                    continue
            except:
                if counter <10:
                    counter +=1
                    continue
                else:
                    raise Exception("upload error")

    def uploadThread(self,data):
        file = data['meta']['dest']
        token = data['token']
        upload_details = self.uploadAPI(file,token)
        print(upload_details)
        return({'chunk':data['meta'],'url':upload_details['attachments'][0]['url']})

    def upload(self):
        files = self.files
        pool = ThreadPool(2)
        chunk_auth = []
        for file in files:
            chunk_auth.append({
                'token' :  random.choice(self.tokens),
                'meta' : file,
            })
        chunks = pool.map(self.uploadThread,chunk_auth)
        return chunks



