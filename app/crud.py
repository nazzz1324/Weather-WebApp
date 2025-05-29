from app.models import SearchHistory
from app.database import SessionLocal
from sqlalchemy import func

def save_search(city: str):
    db = SessionLocal()
    search = SearchHistory(city=city)
    db.add(search)
    db.commit()
    db.close()

def get_stats():
    db = SessionLocal()
    result = (
        db.query(SearchHistory.city, func.count(SearchHistory.city))
        .group_by(SearchHistory.city)
        .all()
    )
    db.close()
    return [{"city": r[0], "count": r[1]} for r in result]

def get_recent_history(limit=10):
    db = SessionLocal()
    result = db.query(SearchHistory).order_by(SearchHistory.timestamp.desc()).limit(limit).all()
    db.close()
    return result
