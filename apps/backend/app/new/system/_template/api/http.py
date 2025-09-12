
from fastapi import APIRouter, Depends
from ..logic.dispatcher import Dispatcher
from ..logic.retry import Retry
from ..logic.policies import Quota

router = APIRouter(prefix="/v1/system/sample", tags=["system-sample"])

class Transport:
    def deliver(self, message: dict):
        # Заглушка реальной доставки
        _ = message
        return

def get_dispatcher() -> Dispatcher:
    return Dispatcher(transport=Transport(), retry=Retry(), quota=Quota())

@router.post("/send")
def send_message(body: dict, d: Dispatcher = Depends(get_dispatcher)):
    d.send(body)
    return {"ok": True}
