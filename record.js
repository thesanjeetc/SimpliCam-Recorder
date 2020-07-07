function handleDataAvailable(event) {
  if (event.data && event.data.size > 0) {
    recordedBlobs.push(event.data);
  }
}

function handleStop(event) {
  console.log("Recorder stopped: ", event);
  const superBuffer = new Blob(recordedBlobs);
  url = window.URL.createObjectURL(superBuffer);
  recording.src = url;
  recording.controls = true;

  blobToBase64(superBuffer, (abc) => {
    callback(abc);
  });
}

function startRecording(callback) {
  recordedBlobs = [];
  mediaRecorder = new MediaRecorder(stream);
  console.log("Created MediaRecorder", mediaRecorder);
  mediaRecorder.onstop = handleStop;
  mediaRecorder.ondataavailable = handleDataAvailable;
  mediaRecorder.start(100);
  console.log("MediaRecorder started", mediaRecorder);
}

function stopRecording() {
  mediaRecorder.stop();
  console.log("Recorded Blobs: ", recordedBlobs);
}

function play() {
  recording.play();
}

var blobToBase64 = function (blob, callback) {
  var reader = new FileReader();
  reader.onload = function () {
    var dataUrl = reader.result;
    var base64 = dataUrl.split(",")[1];
    callback(base64);
  };
  reader.readAsDataURL(blob);
};

let mediaRecorder;
let recordedBlobs;
let sourceBuffer;

const camera = document.querySelector("video");
const recording = document.createElement("video");

let stream = camera.captureStream();
console.log("Started stream capture from camera element: ", stream);

callback = arguments[1];

startRecording();
setTimeout(() => {
  stopRecording();
}, arguments[0]);
