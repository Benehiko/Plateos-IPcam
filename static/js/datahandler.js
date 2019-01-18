let socket = io.connect('http://' + document.domain + ":" + location.port);
socket.on('connect', function () {
    socket.emit('connected');
    console.log("Connected to Server")

});

let get_image = function () {
    console.log("Emitting get-image");
    socket.emit('get-image')
};

socket.on('image', function (data) {
    console.log("Image DATA");
    $("#image-container").append('<img src="" id="' + j["name"] + '" width="100%" height="100%"/>');
    $("#image-container").append('<img src="" id="' + j["name"] + '-raw" width="100%" height="100%"/>');

    let j = JSON.parse(data);

    let frame = new Image();
    frame.src = "data:image/jpg;base64," + j["frame"];
    let frameElem = document.getElementById(j["name"]);
    frameElem.src = frame.src;

    let raw = new Image();
    raw.src = "data:image/jpg;base64," + j["raw"];
    let rawElem = document.getElementById(j["name"]);
    rawElem.src = raw.src;
});

$("#shape-height").bootstrapSlider({});
$("#shape-height").on("slide", function (evt) {
    $("#shape-height-min").text(evt.value[0]);
    $("#shape-height-max").text(evt.value[1]);
    let d = {
        "height": {"min": evt.value[0], "max": evt.value[1]}
    };
    socket.emit("shape-height", d);
});

$("#shape-width").bootstrapSlider({});
$("#shape-width").on("slide", function (evt) {
    $("#shape-width-min").text(evt.value[0]);
    $("#shape-width-max").text(evt.value[1]);
    let data = {
        "width": {"min": evt.value[0], "max": evt.value[1]}
    };
    socket.emit("shape-width", data);
});

$("#shape-area").bootstrapSlider({});
$("#shape-area").on("slide", function (evt) {
    $("#shape-area-min").text(evt.value[0]);
    $("#shape-area-max").text(evt.value[1]);
    let data = {
        "area": {"min": evt.value[0], "max": evt.value[1]}
    };
    socket.emit("shape-area", data);
});

$("#morph-width").bootstrapSlider({});
$("#morph-width").on("slide", function (evt) {
    $("#morph-width-value").text(evt.value);
    let data = {
        "morph": {"height": $("#morph-height").val(), "width": evt.value}
    };
    socket.emit("preprocessing-morph", data);
});

$("#morph-height").bootstrapSlider({});
$("#morph-height").on("slide", function (evt) {
    $("#morph-height-value").text(evt.value);
    let data = {
        "morph": {"height": evt.value, "width": $("#morph-width").val()}
    };
    socket.emit("preprocessing-morph", data);
});

$("#otsu").bootstrapSlider({});
$("#otsu").on("slide", function (evt) {
    $("#otsu-value").text(evt.value);
    let data = {
        "otsu": evt.value
    };
    socket.emit("preprocessing-otsu", data);
});

$("#sobel").bootstrapSlider({});
$("#sobel").on("slide", function (evt) {
    $("#sobel-value").text(evt.value);
    let data = {
        "sobel": {
            "kernel": evt.value
        }
    };
    socket.emit("preprocessing-sobel", data);
});

$("#char-area").bootstrapSlider({});
$("#char-area").on("slide", function (evt) {
    $("#char-area-min").text(evt.value[0]);
    $("#char-area-max").text(evt.value[1]);
    let data = {
        "area": {"min": evt.value[0], "max": evt.value[1]}
    };
    socket.emit("char-area", data)
});

$("#char-height").bootstrapSlider({});
$("#char-height").on("slide", function (evt) {
    $("#char-height-min").text(evt.value[0]);
    $("#char-height-max").text(evt.value[1]);
    let data = {
        "height": {"min": evt.value[0], "max": evt.value[1]}
    };
    socket.emit("char-height", data)
});

$("#char-width").bootstrapSlider({});
$("#char-width").on("slide", function (evt) {
    $("#char-width-min").text(evt.value[0]);
    $("#char-width-max").text(evt.value[1]);
    let data = {
        "width": {"min": evt.value[0], "max": evt.value[1]}
    };
    socket.emit("char-width", data)
});

$("#angle").bootstrapSlider({});
$("#angle").on("slide", function (evt) {
    $("#angle-min-value").text(evt.value[0]);
    $("#angle-max-value").text(evt.value[1]);
    let data = {
        "angle": {
            "min": evt.value[0], "max": evt.value[1]
        }
    };
    socket.emit("angle", data)
});

$("#mask").bootstrapSlider({});
$("#mask").on("slide", function (evt) {
    $("#mask-min").text(evt.value[0]);
    $("#mask-max").text(evt.value[1]);
    let data = {
        "mask": {"lower": evt.value[0], "upper": evt.value[1]}
    };
    socket.emit("mask", data);
});

$("#char-morph").bootstrapSlider({});
$("#char-morph").on("slide", function (evt) {
    $("#char-morph-min").text(evt.value[0]);
    $("#char-morph-max").text(evt.value[1]);
    let data = {
        "morph": {"min": evt.value[0], "max": evt.value[1]}
    };
    socket.emit("char-morph", data)
});
$("#save-sliders").on("click", function (evt) {
    socket.emit("save");
});

setInterval(get_image, 1000);