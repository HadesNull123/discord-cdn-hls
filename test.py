from ds import Discord
import videoLib

videoLib.splitChunks('test-360.mp4','test')
# cookie = random.choice(json.loads(open('cookies.json').read()))
uploader = Discord('test')
chunks = uploader.upload()
playlist = videoLib.generatePlaylist(chunks)
print(playlist)
