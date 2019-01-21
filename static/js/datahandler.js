let socket = io.connect('http://' + document.domain + ":" + location.port);
socket.on('connect', function () {
    socket.emit('connected');
});
socket.on('image', data => {
    let j = JSON.parse(data);
    if (!document.getElementById(j["name"])) {
        $("#image-container").append('<div class="col-sm">');
        $("#image-container").append('<img src="" id="' + j["name"] + '" width="100%" height="100%"/>');
        $("#image-container").append('<p id="' + j["name"] + '-output"/>');
        //$("#image-container").append('<img src="" id="' + j["name"] + '-plates" width="100%" height="100"/>');
        $("#image-container").append('</div>');
    }
    //$("#image-container").append('<img src="" id="' + j["name"] + '-raw" width="100%" height="100%"/>');

    let frame = new Image();
    frame.src = "data:image/jpg;base64," + j["image"];
    let frameElem = document.getElementById(j["name"]);
    frameElem.src = frame.src;

    // if (j["plates"] !== "") {
    //     let plates = new Image();
    //     plates.src = "data:image/jpg;base64," + j["plates"];
    //     let platesElem = document.getElementById(j["name"] + "-plates");
    //     platesElem.src = plates.src
    // }

    //"data:image/jpg;base64," + j["image"];
    //let outputElem = document.getElementById(j["name"] + "-output");
    // console.log(j["output"]);
    // outputElem.html = j["output"]
    // let raw = new Image();
    // raw.src = "data:image/jpg;base64," + j["raw"];
    // let rawElem = document.getElementById(j["name"]);
    // rawElem.src = raw.src;
});

socket.on('saved', function () {
        console.log("Saved");
    }
);

let get_image = function () {
    socket.emit('get-image')
};


// Shape Height
$("#shape-height").ionRangeSlider({
    type: "double",
    min: 0.01,
    max: 100,
    step: 0.01,
    from: 0.01,
    to: 100,
    grid: true,
    grid_snap: true,
    from_fixed: false,
    to_fixed: false,
    onChange: function (data) {
        let d = {
            "height": {"min": data.from, "max": data.to}
        };
        socket.emit("shape-height", d);
    }
});
// ----

// Shape Width
$("#shape-width").ionRangeSlider({
    type: "double",
    min: 0.01,
    max: 100,
    step: 0.01,
    from: 0.01,
    to: 100,
    grid: true,
    grid_snap: true,
    from_fixed: false,
    to_fixed: false,
    onChange: function (data) {
        let d = {
            "width": {"min": data.from, "max": data.to}
        };
        socket.emit("shape-width", d);
    }
});
// ----

// Shape Area
$("#shape-area").ionRangeSlider({
    type: "double",
    min: 0.01,
    max: 100,
    step: 0.01,
    from: 0.01,
    to: 100,
    grid: true,
    grid_snap: true,
    to_fixed: false,
    from_fixed: false,
    onChange: function (data) {
        let d = {
            "area": {"min": data.from, "max": data.to}
        };
        socket.emit("shape-area", d);
    }
});

// ----


// Morph Width
let morphwidth = $("#morph-width");
morphwidth.ionRangeSlider({
    type: "double",
    min: 1,
    max: 50,
    from: 1,
    grid: true,
    grid_snap: true,
    to_fixed: true,
    from_fixed: false,
    onChange: function (data) {
        let d = {
            "morph": {"width": data.from}
        };
        socket.emit("preprocessing-morph-width", d);
    }
});

// ----


// Morph Height
$("#morph-height").ionRangeSlider({
    type: "double",
    min: 1,
    max: 50,
    from: 1,
    grid: true,
    grid_snap: true,
    to_fixed: true,
    from_fixed: false,
    onChange: function (data) {
        let d = {
            "morph": {"height": data.from}
        };
        socket.emit("preprocessing-morph-height", d);
    }
});
// ----

// Char Area
$("#char-area").ionRangeSlider({
    type: "double",
    min: 0.01,
    max: 100,
    step: 0.01,
    from: 0.01,
    to: 100,
    grid: true,
    grid_snap: true,
    to_fixed: false,
    from_fixed: false,
    onChange: function (data) {
        let d = {
            "area": {"min": data.from, "max": data.to}
        };
        socket.emit("char-area", d)
    }
});
// ----

// Char Height
$("#char-height").ionRangeSlider({
    type: "double",
    min: 0.01,
    max: 100,
    step: 0.01,
    from: 0.01,
    to: 100,
    grid: true,
    grid_snap: true,
    to_fixed: false,
    from_fixed: false,
    onChange: function (data) {
        let d = {
            "height": {"min": data.from, "max": data.to}
        };
        socket.emit("char-height", d)
    }
});
// ----

// Char Width
$("#char-width").ionRangeSlider({
    type: "double",
    min: 0.01,
    max: 100,
    from: 0.01,
    to: 100,
    step: 0.01,
    grid: true,
    grid_snap: true,
    to_fixed: false,
    from_fixed: false,
    onChange: function (data) {
        let d = {
            "width": {"min": data.from, "max": data.to}
        };
        socket.emit("char-width", d)
    }
});
// ----

//Char Morph Dilate
$("#char-morph").ionRangeSlider({
    type: "double",
    min: 1,
    max: 9,
    from: 1,
    to: 9,
    step: 1,
    grid: true,
    grid_snap: true,
    to_fixed: false,
    from_fixed: false,
    onChange: function (data) {
        let d = {
            "char": {
                "morph":
                    {
                        "min":
                        data.from,
                        "max": data.to
                    }
            }
        };
        socket.emit("char-morph", d)
    }
});
// ----


// Angle
$("#angle").ionRangeSlider({
    type: "double",
    min: 0,
    max: 180,
    from: 0,
    to: 180,
    step: 1,
    grid: true,
    grid_snap: true,
    to_fixed: false,
    from_fixed: false,
    onChange: function (data) {
        let d = {
            "angle": {
                "min": data.from, "max": data.to
            }
        };
        socket.emit("angle", d)
    }
});

// ----

// Mask
$("#mask").ionRangeSlider({
    type: "double",
    min: 1,
    max: 254,
    from: 1,
    to: 254,
    step: 1,
    grid: true,
    grid_snap: true,
    to_fixed: false,
    from_fixed: false,
    onChange: function (data) {
        let d = {
            "mask": {"lower": data.from, "upper": data.to}
        };
        socket.emit("mask", d);
    }
});
// ----

// Otsu
$("#otsu").ionRangeSlider({
    type: "double",
    min: 0,
    max: 255,
    from: 0,
    to: 255,
    step: 1,
    grid: true,
    grid_snap: true,
    to_fixed: true,
    from_fixed: false,
    onChange: function (data) {
        let d = {
            "otsu": data.from
        };
        socket.emit("otsu", d);
    }
});

$("#erode").ionRangeSlider({
    type: "double",
    min: 1,
    max: 8,
    from: 2,
    to: 3,
    step: 1,
    grid: true,
    grid_snap: true,
    to_fixed: false,
    from_fixed: false,
    onChange: function (data) {
        let d = {
            "erode": {"min": data.from, "max": data.to}
        };
        socket.emit("erode", d);
    }
});

$("#save-sliders").on("click", function (evt) {
    socket.emit("save");
});

setInterval(get_image, 2000);