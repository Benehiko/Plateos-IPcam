let images = [];

let get_view = function () {
    $.ajax({
        type: "GET",
        url: "http://localhost:8081/get-views",
        success: function (data) {
            images = JSON.parse(data);
            for (let x in images) {
                if (!document.getElementById(images[x])) {
                    $("#image-container").append('<img src="" id="' + images[x] + '" width="100%" height="100%"/>');
                    $("#image-container").append('<img src="" id="' + images[x] + '-raw" width="100%" height="100%"/>');
                }
            }
        }
    });
};

let get_frame = function () {
    if (images.length > 0) {
        for (let x in images) {
            $.ajax({
                type: "GET",
                url: "http://localhost:8081/get-frame",
                data: {"name": images[x]},
                success: function (data) {
                    console.log(data);
                    let img = new Image();
                    img.src = "data:image/jpg;base64," + data;
                    let elem = document.getElementById(images[x]);
                    elem.src = img.src;
                }
            });
            $.ajax({
                type: "GET",
                url: "http://localhost:8081/get-raw-frame",
                data: {"name": images[x]},
                success: function (data) {
                    console.log(data);
                    let img = new Image();
                    img.src = "data:image/jpg;base64," + data;
                    let elem = document.getElementById(images[x] + "-raw");
                    elem.src = img.src;
                }
            });
            $.ajax({
                type: "GET",
                url: "http://localhost:8081/get-char-frame",
                data: {"name": images[x]},
                success: function (data) {
                    if (!document.getElementById(images[x] + "-char" + data)) {
                        $("#image-container").append('<img src="data:image/jpg;base64,' + data + ';" id="' + images[x] + '-char' + data + '" width="20%" height="20%"/>');
                    } else {
                        let img = new Image();
                        img.src = "data:image/jpg;base64," + data;
                        let elem = document.getElementById(images[x] + "-char" + data);
                        elem.src = img.src;
                    }

                }
            });
            $.ajax({
                type: "GET",
                url: "http://localhost:8081/get-char-raw",
                data: {"name": images[x]},
                success: function (data) {
                    if (!document.getElementById(images[x] + "-char-raw" + data)) {
                        $("#image-container").append('<img src="data:image/jpg;base64,' + data + ';" id="' + images[x] + '-char-raw' + data + '" width="20%" height="20%"/>');
                    } else {
                        let img = new Image();
                        img.src = "data:image/jpg;base64," + data;
                        let elem = document.getElementById(images[x] + "-char-raw" + data);
                        elem.src = img.src;
                    }
                }
            });
        }
    }
};

setInterval(get_view, 500);
setInterval(get_frame, 500);