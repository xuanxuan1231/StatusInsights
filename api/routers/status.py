from fastapi import APIRouter

router = APIRouter(prefix='/status', tags=['status'])


@router.post('/person/set')
async def set_person_status(status: str, description: str = ''):
    """
    设置人的状态。
    :return:
    """
    pass


@router.get('/person/get')
async def get_person_status() -> dict:
    """
    获取人的当前状态。
    :return:
    """
    pass


@router.post('/person/unset')
async def unset_person_status():
    """
    设置人的当前状态为空。
    :return:
    """
    pass

