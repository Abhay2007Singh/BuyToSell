from fastapi import Query

def pagination(limit: int = Query(10, ge=1, le=100), skip:int = Query(0, ge=0)):
    return {"limit": limit, "skip": skip}