export function notify(message: string) {
  if (typeof window === 'undefined' || !('Notification' in window)) return;
  try {
    if (Notification.permission === 'granted') {
      new Notification(message);
    } else if (Notification.permission !== 'denied') {
      Notification.requestPermission().then((perm) => {
        if (perm === 'granted') {
          new Notification(message);
        }
      });
    }
  } catch {
    // ignore
  }
}
