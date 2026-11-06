from app.upcoming.service import taste_queries


def test_taste_queries_from_current_reads_and_genres():
    books = [
        {
            "title": "Le Voleur de foudre",
            "author": "Rick Riordan",
            "genre": "fantasy, jeunesse",
            "category": "roman",
            "status": "reading",
            "rating": 5,
        },
        {
            "title": "Pour qui sonne le glas",
            "author": "Ernest Hemingway",
            "genre": "roman historique",
            "category": "roman",
            "status": "completed",
            "rating": 4,
        },
        {
            "title": "Déjà suivi",
            "author": "Stephen King",
            "genre": "",
            "category": "roman",
            "status": "reading",
            "rating": 0,
        },
    ]
    queries = taste_queries(books, followed_authors=["Stephen King"])
    reasons = [reason for _q, reason in queries]
    assert "Parce que tu lis Rick Riordan" in reasons
    assert all("Stephen King" not in reason for reason in reasons)
    assert "Dans tes genres : fantasy" in reasons
    assert "Dans tes genres : jeunesse" in reasons
    assert "Dans tes genres : historique" in reasons


def test_taste_queries_empty_library():
    assert taste_queries([], []) == []
