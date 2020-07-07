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

  const a = document.createElement("a");
  a.style.display = "none";
  a.href = url;
  a.download = "recording.mkv";
  document.body.appendChild(a);
  a.click();
  setTimeout(() => {
    document.body.removeChild(a);
    window.URL.revokeObjectURL(url);
  }, 100);
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

let mediaRecorder;
let recordedBlobs;
let sourceBuffer;

const camera = document.querySelector("video");
const recording = document.createElement("video");

let stream = camera.captureStream();
console.log("Started stream capture from camera element: ", stream);

startRecording();
setTimeout(() => {
  stopRecording();
  setTimeout(() => {
    arguments[1](1);
  }, 5000);
}, arguments[0]);
