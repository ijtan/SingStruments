//webkitURL is deprecated but nevertheless
URL = window.URL || window.webkitURL;

var gumStream; 						//stream from getUserMedia()
var rec; 							//Recorder.js object
var input; 							//MediaStreamAudioSourceNode we'll be recording
var count = 0;
var recording = false;
var canPlay = false;
var playing = false;
var iconSelect;
var selectedInstrument = 'Violin';


// shim for AudioContext when it's not avb. 
var AudioContext = window.AudioContext || window.webkitAudioContext;
var audioContext //audio context to help us record

var recordButton = document.getElementById("recordButton");
var recordButtonImage = document.getElementById("recordButtonImage");

// var pauseButton = document.getElementById("pauseButton");
var startButton = document.getElementById("startButton");
var stopButton = document.getElementById("stopButton");
var playButton = document.getElementById("playButton");
var playButtonImage = document.getElementById("playButtonImage");
// var midi_playerButton = document.getElementById("player-button");
var midi_player = document.getElementById("audio-player");



window.onload = function () {

    iconSelect = new IconSelect("my-icon-select",
        {
            'selectedIconWidth': 70,
            'selectedIconHeight': 70,
            'selectedBoxPadding': 1,
            'iconsWidth': 48,
            'iconsHeight': 48,
            'boxIconSpace': 1,
            'vectoralIconNumber': 3,
            'horizontalIconNumber': 6
        });

    var icons = [];
    icons.push({ 'iconFilePath': 'static/Images/violin.png', 'iconValue': 'Violin'});
    icons.push({ 'iconFilePath': 'static/Images/piano.png', 'iconValue': 'Piano' });
    icons.push({ 'iconFilePath': 'static/Images/trumpet.png', 'iconValue': 'Trumpet' });
    icons.push({ 'iconFilePath': 'static/Images/saxophone.png', 'iconValue': 'Saxophone' });
    icons.push({ 'iconFilePath': 'static/Images/harmonica.png', 'iconValue': 'Harmonica' });
    icons.push({ 'iconFilePath': 'static/Images/guitar.png', 'iconValue': 'Electric Guitar' });

    iconSelect.refresh(icons);

    document.getElementById('my-icon-select').addEventListener('changed', function (e) {
        selectedInstrument = iconSelect.getSelectedValue();
        if(playButton.disabled == false){
            audioStopped()
            
            getMidiAudio(1, selectedInstrument,reRender=false)
        }
    });

};



midi_player.onended = function () {
    audioStopped()
}

// var instrumentDropDown = document.getElementById("instrumentSelect");

//add events to those 2 buttons
recordButton.addEventListener("click", startRecording);
playButton.addEventListener("click", toggleAudioPlay);



function toggleAudioPlay() {
    console.log("player button clicked!")
    if (!playing) {
        console.log("currently not playing!")

        console.log("starting player!")
        if (!canPlay) {
            console.log("cannot play!")
            return
        }

        playButtonImage.src = playButtonImage.src.replace("play.png", "pause.png")
        midi_player.play();

        playing = true
    } else {
        console.log("currently playing!")
        midi_player.pause();
        playing = false
        playButtonImage.src = playButtonImage.src.replace("pause.png", "play.png")

    }
}

function audioStopped() {
    console.log("Audio stopped!")
    midi_player.pause();
    if (playing) {
        playing = false
    }

    playButtonImage.src = playButtonImage.src.replace("pause.png", "play.png")
}

function startRecording() {
    console.log("recordButton clicked");

    if (recording) {
        console.log("stopping!");
        stopRecording();
        return;
    }
    playButton.disabled = true;
    playButtonImage.src = playButtonImage.src.replace("play.png", "play_greyed.png")
    recording = true



    var constraints = { audio: true, video: false }
    recordButtonImage.src = recordButtonImage.src.replace("record.png", "recording.png")


    navigator.mediaDevices.getUserMedia(constraints).then(function (stream) {
        console.log("getUserMedia() success, stream created, initializing Recorder.js ...");

        audioContext = new AudioContext();

        //update the format 
        document.getElementById("formats").innerHTML = "Format: 1 channel pcm @ " + audioContext.sampleRate / 1000 + "kHz"

        gumStream = stream;

        input = audioContext.createMediaStreamSource(stream);

        rec = new Recorder(input, { numChannels: 1 })

        //start the recording process
        rec.record()

        console.log("Recording started");

    }).catch(function (err) {
        //enable the record button if getUserMedia() fails
        console.log("Getting usr media failed!")
        alert("Error: Getting usr media failed!")
        recordButtonImage.src = recordButtonImage.src.replace("recording.png", "record.png")

        recording = false
    });
}

function pauseRecording() {
    console.log("pauseButton clicked rec.recording=", rec.recording);
    if (rec.recording) {
        //pause
        rec.stop();
    } else {
        //resume
        rec.record();

    }

}

function stopRecording() {
    console.log("stopButton clicked");

    recordButtonImage.src = recordButtonImage.src.replace("recording.png", "record.png")
    rec.stop();

    gumStream.getAudioTracks()[0].stop();

    rec.exportWAV(createDownloadLink);
    recording = false;
}

function showOSMD(xml_data) {
    var div_id = "OSMD_div";
    function loadOSMD() {
        return new Promise(function (resolve, reject) {
            if (window.opensheetmusicdisplay) {
                return resolve(window.opensheetmusicdisplay)
            }
            // OSMD script has a 'define' call which conflicts with requirejs
            var _define = window.define // save the define object
            window.define = undefined // now the loaded script will ignore requirejs
            var s = document.createElement('script');
            s.setAttribute('src', "https://cdn.jsdelivr.net/npm/opensheetmusicdisplay@0.7.6/build/opensheetmusicdisplay.min.js");
            //s.setAttribute( 'src', "/custom/opensheetmusicdisplay.js" );
            s.onload = function () {
                window.define = _define
                resolve(opensheetmusicdisplay);
            };
            document.body.appendChild(s); // browser will try to load the new script tag
        })
    }
    loadOSMD().then((OSMD) => {
        window.openSheetMusicDisplay = new OSMD.OpenSheetMusicDisplay(div_id, {
            drawingParameters: "compacttight"
        });
        openSheetMusicDisplay
            .load(xml_data)
            .then(
                function () {
                    openSheetMusicDisplay.render();
                }
            );
    })
}

function getMidiAudio(id, instrument,reRender=true) {


    url = '/get_audio_file?item_id=' + id + "&instrument=" + instrument
    midi_player.src = url


    var xml_url = '/get_xml?id=' + id;
    var storedText;
    if (reRender){
        $.getJSON(xml_url, function (data) {
            // JSON result in `data` variable
            console.log(data);
            showOSMD(data['xml'])
        });
    }
    

    // fetch(xml_url)
    //     .then(function (response) {
    //         response.text().then(function (text) {
    //             storedText = text;
    //             done();
    //         });
    //     });

    // function done() {
    //     document.getElementById('log').textContent =
    //         "Here's what I got! \n" + storedText;

    //     showOSMD(storedText)
    // }

}


function createDownloadLink(blob) {

    var xhr = new XMLHttpRequest();
    xhr.onload = function (e) {
        if (this.readyState === 4) {
            var server_resp = e.target.responseText
            console.log("Server returned: ", server_resp);
            var jrsp = JSON.parse(server_resp);

            var notes_txt_jrsp = jrsp["notes"].toString();

            playButton.disabled = false;
            playButtonImage.src = playButtonImage.src.replace("play_greyed.png", "play.png")
            canPlay = true;
            getMidiAudio(jrsp["id"], selectedInstrument)

        }
    }
    var fd = new FormData();


    // console.log('count ps is ' + curr_id.toString())
    fd.append("item_id", 1);
    var filename = new Date().toISOString();
    fd.append("file", blob, filename);

    for (var pair of fd.entries()) {
        console.log(pair[0] + ', ' + pair[1] + ' , ' + typeof pair[1]);
    }

    // xhr.open("POST", "upload_audio_file", true);
    xhr.open("POST", "upload_audio_file", true);
    xhr.send(fd);
}