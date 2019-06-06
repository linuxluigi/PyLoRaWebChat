function setLayout() {
    let inbox_chat_position = $(".inbox_chat").position();
    let chatWindowHeight = $(window).height() - inbox_chat_position.top;
    $(".inbox_chat").height(chatWindowHeight);

    let typeMsg = $(".type_msg").outerHeight();
    let sendBtn = $("#send_btn").outerHeight();
    let msgWindowHeight = $(window).height() - typeMsg - sendBtn - 10;
    $(".msg_history").height(msgWindowHeight);
}

setLayout();
$(window).on('resize', function () {
    setLayout();
});

// set color style
function setColor(style) {
    if (style === null) {
        style = "cyborg"
    }
    $("#bootswatchCSS").attr("href", "https://stackpath.bootstrapcdn.com/bootswatch/4.3.1/" + style + "/bootstrap.min.css");

    for (let i = 0; i < 100; i++) {
        window.setTimeout(setLayout, 250);
    }

}

setColor(localStorage.getItem("color"));

$(".settings-color-button").click(function () {
    localStorage.setItem("color", $(this).attr("color"));
    setColor($(this).attr("color"));
});

// set chat people
function loadChatListener() {
    $(".chat_list").hover(
        function () {
            $(this).addClass("bg-primary");
        }, function () {
            $(this).removeClass("bg-primary");
        }
    );

    $(".chat_list").click(function () {
        let pk = $(this).attr("pk");
        $(".chat_list").removeClass("bg-secondary");
        $(this).addClass("bg-secondary");
        $(".msg_history").addClass("d-none");
        $("#msg_history_" + pk).removeClass("d-none");
        $("textarea").attr("pk", pk);
    });
}

loadChatListener();

// WebSocket
let chatSocket = null;

function connectToWebsocket() {
    chatSocket = new WebSocket(
        'ws://' + window.location.host + '/ws/chat/');
}
connectToWebsocket();

async function reconnectToWebsocket() {
    connectToWebsocket();
    await sleep(2000);

     if (chatSocket['readyState'] === 0) {
        console.log("conn");
    } else {
        console.log("no");
        reconnectToWebsocket();
    }
}

chatSocket.onmessage = function (e) {
    let data = JSON.parse(e.data);
    let message = data['message'];

    // node
    if (message['model'] === "node") {
        if (message['created']) {
            // create
            $(".inbox_chat").append(`
                <div id="chat_list_{{ node.pk }}" pk="` + message['id'] + `" class="chat_list">
                  <div class="chat_people">
                    <div class="chat_img"><img id="node_img_` + message['id'] + `" src="/robohash/` + message['id'] + `/?width=200&height=200" alt="{{ node.nick }}"></div>
                    <div class="chat_ib">
                      <h5 id="node_nick_` + message['id'] + `" >` + message['nick'] + ` <span class="chat_date">` + message['last_seen'] + `</span></h5>
                      <p id="node_hops_` + message['id'] + `">` + message['hops'] + `</p>
                    </div>
                  </div>
                </div>
            `);

            $(".mesgs").prepend(`
                <div id="msg_history_` + message['id'] + `" class="msg_history d-none">
                </div>
            `);
            loadChatListener();
            setLayout();
        } else if (message['delete']) {
            // delete
            $("#msg_history_" + message['id']).remove();
            $("#chat_list_" + message['id']).remove();
        } else {
            // update
            $('#node_img_' + message['id']).attr("alt", message['nick']);
            $('#node_nick_' + message['id']).html(' ' + message['nick'] + '<span class="chat_date">' + message['last_seen'] + '</span>');
            $('#node_hops_' + message['id']).html(" " + message['hops']);
        }
    }

    // message
    if (message['model'] === "message") {

        if (message['created']) {
            // create
            let msg_histroy = "#msg_history_" + message['node_id'];
            if (message['message_type'] === 'o') {
                // outgoing message
                $(msg_histroy).append(`
                  <div id="msg_` + message['id'] + `" class="outgoing_msg">
                      <div id="msg_val_` + message['id'] + `" class="sent_msg alert alert-info">
                      ` + message['message'] + `
                      <span id="msg_timestamp_` + message['id'] + `" class="time_date"> ` + message['timestamp'] + `</span></div>
                  </div>
            `);
            } else {
                // incoming message
                $(msg_histroy).append(`
                <div id="msg_` + message['id'] + `" class="incoming_msg">
                <div class="incoming_msg_img"><img src="/robohash/` + message['node_id'] + `/?width=200&height=200"
                                                   alt="` + message['node_nick'] + `">
                </div>
                <div class="received_msg">
                  <div id="msg_val_` + message['id'] + `" class="received_withd_msg alert alert-secondary">
                    ` + message['message'] + `
                    <span class="time_date"> ` + message['timestamp'] + `</span>
                  </div>
                </div>
              </div>
            `);
            }
            // scroll down msg history
            $(msg_histroy).scrollTop($(msg_histroy).height());
        } else if (message['delete']) {
            // delete
            $("#msg_" + message['id']).remove();
        } else {
            // update
            $('#msg_val_' + message['id']).html(message['message'] + '<span class="time_date"> ' + message['timestamp'] + '</span>');
        }

    }
};

chatSocket.onclose = function (e) {
    console.error('Chat socket closed unexpectedly');
    $('#connection-lost-alert').removeClass("d-none");
    // reconnectToWebsocket();
};

// textarea
function sendMsg() {
    let msg = $("textarea").val();
    let node_pk = $("textarea").attr('pk');
    chatSocket.send(JSON.stringify({
        'message': {
            'node_pk': node_pk,
            'message': msg
        }
    }));

    $("textarea").val('');
}

$("#send_btn").click(function () {
    sendMsg();
});

$("textarea").keydown(function (e) {
    if ((e.keyCode || e.which) == 13) { //Enter keycode
        if (e.keyCode == 13 && !e.shiftKey) {
            // prevent default behavior
            e.preventDefault();
            sendMsg();
        }
    }
});
