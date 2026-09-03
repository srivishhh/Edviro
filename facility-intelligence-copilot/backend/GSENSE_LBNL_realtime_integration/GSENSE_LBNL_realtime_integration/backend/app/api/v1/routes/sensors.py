from fastapi import APIRouter

router = APIRouter()


@router.get("/sensors")
def list_sensors():
    return {"items": [], "count": 0}


@router.get("/sensors/{sensor_id}")
def get_sensor(sensor_id: int):
    return {"sensor_id": sensor_id, "status": "not_implemented"}


@router.post("/sensors")
def create_sensor():
    return {"status": "not_implemented"}
