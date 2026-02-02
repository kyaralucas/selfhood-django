import random

QUESTIONS = [
    "What are some ways that you can grant yourself the rest you deserve?",
    "What is your rest plan?",
    "Who are you when you are not working?",
    "In what way do others show up for your softness?",
    "What does a life without taking care of others look like?",
    "How do you recharge?",
]

def pick_question():
    return random.choice(QUESTIONS)
