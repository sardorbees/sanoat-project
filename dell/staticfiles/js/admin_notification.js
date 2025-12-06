document.addEventListener("DOMContentLoaded", function () {
    fetch("http://127.0.0.1:8000/api/message_panel/api/messages/")
        .then((res) => res.json())
        .then((data) => {
            const unread = data.filter(m => !m.is_read).length;
            document.getElementById("msg-count").innerText = unread;
        });

    fetch("http://127.0.0.1:8000/api/message_panel/api/notifications/")
        .then((res) => res.json())
        .then((data) => {
            const unread = data.filter(n => !n.is_read).length;
            document.getElementById("notif-count").innerText = unread;
        });
});



