function post_to_flask(url, d) {
    let base = "http://localhost:8081/";
    $.ajax({
        type: "POST",
        url: base + url,
        contentType: "application/json; charset=utf-8",
        data: JSON.stringify(d),
        dataType: "json"
    });
}

function get_to_flask(url) {
    let base = "http://localhost:8081/";
    $.ajax({
        type: "GET",
        url: base + url
    });
}