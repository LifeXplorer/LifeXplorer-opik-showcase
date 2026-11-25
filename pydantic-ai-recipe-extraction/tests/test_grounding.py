from grounding import find_ungrounded

NOTE = "banana bread. oven 175C. 3 ripe bananas, 190g flour, 1 1/2 tsp bicarb, half tsp salt. bake ~55 min"


def card(**kw):
    base = {"title": "Banana bread", "ingredients": [], "steps": []}
    return {**base, **kw}


def test_grounded_card_has_no_problems():
    c = card(
        oven_temp_c=175,
        cook_minutes=55,
        ingredients=[
            {"name": "bananas", "quantity": "3"},
            {"name": "flour", "quantity": "190 g"},
            {"name": "bicarb", "quantity": "1 1/2 tsp"},
            {"name": "salt", "quantity": "half tsp"},
        ],
    )
    assert find_ungrounded(c, NOTE) == []


def test_invented_number_is_caught():
    problems = find_ungrounded(card(servings=12), NOTE)
    assert problems == ["servings=12 is not in the note"]


def test_invented_ingredient_and_quantity_are_caught():
    c = card(ingredients=[{"name": "vanilla extract", "quantity": "1 tsp"}, {"name": "flour", "quantity": "250 g"}])
    problems = find_ungrounded(c, NOTE)
    assert any("vanilla extract" in p for p in problems)
    assert any("'250 g' of flour" in p for p in problems)


def test_fahrenheit_note_allows_celsius_card():
    assert find_ungrounded(card(oven_temp_c=175), "bake at 350F") == []


def test_abbreviated_ingredient_still_counts_as_grounded():
    assert find_ungrounded(card(ingredients=[{"name": "bicarbonate of soda"}]), NOTE) == []


def test_computed_total_is_flagged():
    # 20 min + 25 min stated separately; a summed 45 is not in the note
    assert find_ungrounded(card(cook_minutes=45), "bake base 20 min then filling 25 min") != []
