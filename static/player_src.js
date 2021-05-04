// var _0x3181=['Firefox','indexOf','detail','userAgent','dir','MSIE','href','off','addEventListener','location','devtoolschange','Dev\x20tools\x20checker','defineProperty','Chrome','isOpen','coc_coc_browser','http://animevietsub.tv/','Safari'];(function(_0x40ea5a,_0x318136){var _0x3390a3=function(_0x5ac0e8){while(--_0x5ac0e8){_0x40ea5a['push'](_0x40ea5a['shift']());}};_0x3390a3(++_0x318136);}(_0x3181,0x174));var _0x3390=function(_0x40ea5a,_0x318136){_0x40ea5a=_0x40ea5a-0x0;var _0x3390a3=_0x3181[_0x40ea5a];return _0x3390a3;};if(navigator['userAgent']['indexOf'](_0x3390('0x1'))!=-0x1||navigator[_0x3390('0x9')][_0x3390('0x7')](_0x3390('0x5'))!=-0x1||navigator[_0x3390('0x9')][_0x3390('0x7')](_0x3390('0xb'))!=-0x1||navigator[_0x3390('0x9')]['indexOf'](_0x3390('0x3'))!=-0x1){var checkStatus;var element=new Image();Object[_0x3390('0x0')](element,'id',{'get':function(){checkStatus='on';throw new Error(_0x3390('0x11'));}});setInterval(function check(){checkStatus=_0x3390('0xd');console[_0x3390('0xa')](element);if(checkStatus=='on'){window[_0x3390('0xf')][_0x3390('0xc')]=_0x3390('0x4');}},0x3e8);}if(navigator[_0x3390('0x9')][_0x3390('0x7')](_0x3390('0x6'))!=-0x1){window[_0x3390('0xe')](_0x3390('0x10'),_0x1eb97b=>{if(_0x1eb97b[_0x3390('0x8')][_0x3390('0x2')]==!![]){window[_0x3390('0xf')][_0x3390('0xc')]=_0x3390('0x4');}});};
jwplayer.key = "W7zSm81+mmIsg7F+fyHRKhF3ggLkTqtGMhvI92kbqf/ysE99";
const getParams = (name, url) => {
    if (!url) url = location.href;
    name = name.replace(/[\[]/,"\\\[").replace(/[\]]/,"\\\]");
    var regexS = "[\\?&]"+name+"=([^&#]*)";
    var regex = new RegExp(regexS);
    var results = regex.exec(url);
    return results == null ? null : results[1];
}
function loadPlayer(){  
    $.ajax({
        type: "POST",
        url: window.location.pathname,
        success: function (data){
            initPlayer(data)
        }  
    });    
}
const initPlayer = (link) =>  {
    let subname = getParams("subname");
    let sub = getParams("sub");

    let player = jwplayer("player");
    let object = {
        playbackRateControls: [0.75, 1, 1.25, 1.5, 2],
        width: "100%",
        height: "100%",
        sources: link,
        preload: "auto",
    };
    if(!subname) subname = 'Sub'
    if(sub) {
        object.tracks = [{
            file: sub,
            label: subname,
            kind: "captions",
            default: true
        }]
    }
    player.setup(object);
}
window.onload = function() {
    loadPlayer()
}