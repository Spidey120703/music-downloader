import time

class Event:
    def __init__(self, type: str, init = {}):
        self.type = type
        self.detail = init.get('detail', {})
        self.target = init.get('target', None)
        self.timeStamp = init.get('timeStamp', time.time() * 1000)
        self.cancelable = init.get('cancelable', True)
        self._stopped_propagation = False
    
    def stopPropagation(self) -> None:
        if self.cancelable:
            self._stopped_propagation = True


def EventListener(event: Event) -> bool | None: pass

class EventTarget:
    _listeners_map = {}

    def addEventListener(self, type: str, listener: EventListener, opts = {}) -> None:
        if type not in self._listeners_map.keys():
            self._listeners_map[type] = [ ]
        self._listeners_map[type].append({
            'once': opts.get('once', False), 
            'listener': listener
        })

    def removeEventListener(self, type: str, listener: EventListener, opts = {}) -> None:
        if type in self._listeners_map.keys():
            for item in self._listeners_map[type]:
                if item['listener'] == listener:
                    self._listeners_map[type].remove(item)
                    break

    def dispatchEvent(self, event: Event) -> bool:
        if event.type in self._listeners_map.keys():
            result = True
            listeners = self._listeners_map[event.type]
            # print(listeners)
            for listener_item in listeners:
                once = listener_item['once']
                listener = listener_item['listener']
                listener(event)
                if once:
                    self.removeEventListener(event.type, listener)
                if event._stopped_propagation:
                    event._stopped_propagation = False
                    result = False
                    break
            return result

if __name__ == "__main__":
    class MyEventTarget(EventTarget):
        def dispatch(self):
            self.dispatchEvent(Event('foo'))
    t = MyEventTarget()
    t.addEventListener('foo', lambda x: print(x), { 'once': False } )
    t.dispatch()
    print(t._listeners_map)