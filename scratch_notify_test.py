from apps.backendDDD.domains.platform.events.adapters.event_bus_memory import InMemoryEventBus
from apps.backendDDD.domains.platform.events.adapters.outbox_memory import MemoryOutbox
from apps.backendDDD.domains.platform.events.service import Events
from apps.backendDDD.domains.platform.notifications.logic.dispatcher import register_channel
from apps.backendDDD.domains.platform.notifications.wires import register_event_relays

bus = InMemoryEventBus()
outbox = MemoryOutbox()
events = Events(outbox=outbox, bus=bus)
captured = []
register_channel('log', lambda payload: captured.append(dict(payload)))
register_event_relays(events, ['profile.updated.v1'])
print('routes:', list(bus._routes.keys()))
bus.emit('profile.updated.v1', {'id':'u1','username':'Neo'})
print('captured:', captured)
