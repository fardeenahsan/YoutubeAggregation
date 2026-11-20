from app.services.sentiment import classify_sentiments

# Manually assigned expected labels. This small development set is not a
# substitute for evaluation on a larger, representative held-out dataset.
dataset = [
    ("I love your videos. You inspire millions.", "praise"),
    ("This is the best video you have ever made!", "praise"),
    ("Thank you for changing my life.", "praise"),
    ("MrBeast is an amazing creator.", "praise"),
    ("Your generosity makes the world better.", "praise"),
    ("Your videos are getting boring.", "criticism"),
    ("This content is fake and misleading.", "criticism"),
    ("You only care about views and money.", "criticism"),
    ("That was a terrible video.", "criticism"),
    ("Your latest challenge was disappointing.", "criticism"),
    ("Please help me, my family is struggling.", "neutral"),
    ("I lost my job and I don't know what to do.", "neutral"),
    ("My father is sick. Please pray for him.", "neutral"),
    ("I need money to pay my school fees.", "neutral"),
    ("I live in a poor country and need support.", "neutral"),
    ("What was MrBeast doing in 2016?", "neutral"),
    ("When will your next video be uploaded?", "neutral"),
    ("How many people participated in this challenge?", "neutral"),
    ("I watched this video yesterday.", "neutral"),
    ("Who is the person standing next to you?", "neutral"),
    ("I love your videos but this one was disappointing.", "criticism"),
    ("Your content is great, but the editing is too long.", "criticism"),
    ("This video made me happy and sad at the same time.", "neutral"),
    ("I disagree with your decision in this video.", "criticism"),
    ("Bro, what is happening here?", "neutral"),
]


def main():
    comments = [item[0] for item in dataset]
    expected = [item[1] for item in dataset]
    predicted = classify_sentiments(comments)
    correct = 0

    print("\nSENTIMENT EVALUATION")
    print("-" * 110)
    for index, (comment, actual, prediction) in enumerate(
        zip(comments, expected, predicted), 1
    ):
        passed = actual == prediction
        correct += int(passed)
        status = "CORRECT" if passed else "WRONG"
        print(
            f"{index:02d}. {status:7} | "
            f"Expected: {actual:10} | "
            f"Predicted: {prediction:10} | {comment}"
        )

    accuracy = correct / len(dataset) * 100
    print("-" * 110)
    print(f"Correct predictions: {correct}/{len(dataset)}")
    print(f"Evaluation accuracy: {accuracy:.2f}%")


if __name__ == "__main__":
    main()
