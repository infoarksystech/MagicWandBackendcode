import json
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.core.security import check_admin_role,get_current_user
from app.models.models import Prompt
from fastapi.responses import JSONResponse

router = APIRouter(tags=["prompts"], prefix="/prompts")

@router.get("/", dependencies=[Depends(check_admin_role)])
def get_all_prompts(
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(10, ge=1, le=100, description="Number of records to return (max 100)")
):
    try:
        prompts = (
            db.query(Prompt)
            .order_by(Prompt.id.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

        result = []

        for prompt in prompts:
            raw_urls = prompt.image_urls
            image_urls = []

            # ✅ Handle cases where image_urls might already be a list
            if isinstance(raw_urls, list):
                image_urls = raw_urls
            elif isinstance(raw_urls, str):
                if raw_urls.strip():  # make sure it's not empty string or just spaces
                    try:
                        parsed = json.loads(raw_urls)
                        image_urls = parsed if isinstance(parsed, list) else []
                    except json.JSONDecodeError:
                        image_urls = []

            result.append({
                "id": prompt.id,
                "user_id": prompt.user_id,
                "prompt": prompt.prompt,
                "image_urls": image_urls,
                "magic_prompt": prompt.magic_prompt,
                "story" : prompt.story,
                "story_title" : prompt.story_title,
                "user_parameters" : prompt.user_parameters,
                "created_at": prompt.created_at.isoformat() if prompt.created_at else None
            })

        total = db.query(Prompt).count()

        return JSONResponse(content={
            "total": total,
            "skip": skip,
            "limit": limit,
            "prompts": result
        })

    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})





@router.get(
    "/{id}",
    dependencies=[Depends(get_current_user)])
def get_prompt_by_id(id: int, db: Session = Depends(get_db)):
    prompt = db.query(Prompt).filter(Prompt.id == id).first()
    if not prompt:
        return JSONResponse(status_code=404, content={"error": "Prompt not found"})

    return JSONResponse({
                "id": prompt.id,
                "user_id": prompt.user_id,
                "prompt": prompt.prompt,
                "image_urls": prompt.image_urls,
                "magic_prompt": prompt.magic_prompt,
                "user_parameters" : prompt.user_parameters,
                "story": prompt.story,
                "story_title": prompt.story_title
                # "created_at": prompt.created_at.isoformat() if prompt.created_at else None
            })
