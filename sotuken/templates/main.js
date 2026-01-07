navigator.mediaDevices.getUserMedia({ video: true })
    .then(function(stream) {
        var video = document.getElementById('webcam-stream');
        video.srcObject = stream;
    })
    .catch(function(err) {
        console.error("カメラへのアクセスが拒否されました: " + err);
    });