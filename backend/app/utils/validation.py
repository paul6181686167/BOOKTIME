from fastapi import HTTPException

def validate_category(category: str) -> str:
    """Valider la catégorie d'un livre"""
    valid_categories = ["roman", "bd", "manga"]
    category_lower = category.lower()
    if category_lower not in valid_categories:
        raise HTTPException(
            status_code=422,
            detail=f"Invalid category '{category}'. Must be one of: {', '.join(valid_categories)}"
        )
    return category_lower