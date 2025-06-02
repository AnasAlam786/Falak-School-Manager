# src/controller/utils/calc_grades.py
# Used in --> get_marks_api.py
# Used in --> report_card_api.py

from typing import Tuple, Union

def get_grade(score: Union[int, float]) -> Tuple[str, str]:
    """
    Returns a grade and its description based on the score.

    Parameters:
        score (int | float): A numerical score between 0 and 100.

    Returns:
        tuple: A tuple containing the grade (str) and a description (str).

    Raises:
        ValueError: If the score is not a number or is outside the range 0–100.
    """
    if not isinstance(score, (int, float)):
        raise ValueError("Score must be a number (int or float).")
    if not (0 <= score <= 100):
        raise ValueError("Score must be between 0 and 100.")

    if score >= 80:
        return "A", "Excellent"
    elif score >= 60:
        return "B", "Very Good"
    elif score >= 45:
        return "C", "Good"
    elif score >= 33:
        return "D", "Satisfactory"
    else:
        return "E", "Needs Improvement"
