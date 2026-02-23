QUIZ_PROMPT_V1 = """
You are an AI education expert.

Generate 7 multiple-choice questions based ONLY on the provided transcript.

Rules:
- Cover different concepts
- 4 options (A, B, C, D)
- One correct answer
- Include explanation
- Include concept label
- Return STRICT JSON

Format:
{
  "questions": [
    {
      "question_id": "q1",
      "question": "...",
      "options": {
        "A": "...",
        "B": "...",
        "C": "...",
        "D": "..."
      },
      "correct_answer": "A",
      "explanation": "...",
      "concept": "..."
    }
  ]
}
"""
