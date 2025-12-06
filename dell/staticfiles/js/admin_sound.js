let lastId = null;

function checkNotifications() {
  fetch("/api/notifications/")
    .then((res) => res.json())
    .then((data) => {
      if (data.length === 0) return;

      const latest = data[0];
      if (lastId !== null && latest.id > lastId) {
        const audio = new Audio("../sounds/iphone.mp3");
        audio.play().catch(e => console.log("🔇 Не могу проиграть звук:", e));
      }
      lastId = latest.id;
    });
}

console.log("🔔 Уведомления активны");
setInterval(checkNotifications, 5000);
