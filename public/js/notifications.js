(function () {
  const POLL_INTERVAL_MS = 15000;
  const LAST_POPPED_KEY = "ff_last_popped_notification_at";

  const badge = document.getElementById("notif-badge");
  if (!badge) return; // not signed in, nav didn't render the bell

  // Ask for OS-level notification permission once, on first load. Browsers
  // require this to be granted before `new Notification(...)` will actually
  // pop anything up outside the page.
  if (window.Notification && Notification.permission === "default") {
    Notification.requestPermission();
  }

  function getLastPopped() {
    return localStorage.getItem(LAST_POPPED_KEY) || "";
  }
  function setLastPopped(id) {
    localStorage.setItem(LAST_POPPED_KEY, id);
  }

  async function poll() {
    let data;
    try {
      const res = await fetch("/api/notifications");
      if (!res.ok) return;
      data = await res.json();
    } catch (e) {
      return;
    }

    if (data.unread_count > 0) {
      badge.textContent = data.unread_count > 9 ? "9+" : data.unread_count;
      badge.style.display = "block";
    } else {
      badge.style.display = "none";
    }

    // Real OS-level popup for anything newer than the last one we've
    // already popped. ISO 8601 timestamps compare correctly as plain
    // strings, unlike the random hex notification IDs.
    const lastPopped = getLastPopped();

    if (!lastPopped) {
      // First poll ever on this device — set a baseline quietly instead of
      // popping every historical notification at once.
      if (data.notifications.length > 0) setLastPopped(data.notifications[0].created_at);
      return;
    }

    const fresh = data.notifications.filter((n) => n.created_at > lastPopped).reverse();

    if (fresh.length > 0) {
      fresh.forEach((n) => {
        if (window.Notification && Notification.permission === "granted") {
          try {
            new Notification(n.title, { body: n.message });
          } catch (e) {
            /* some browsers restrict this outside a user gesture — the badge still works regardless */
          }
        }
      });
      setLastPopped(data.notifications[0].created_at);
    }
  }

  poll();
  setInterval(poll, POLL_INTERVAL_MS);
})();
