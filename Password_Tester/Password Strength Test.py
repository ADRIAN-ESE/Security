import re


def check_password_strength(password):
    """
    Function to test the strength of a given password.
    Returns a score and feedback about the password strength.

    :param password: str
    :return: dict with score and feedback
    """
    score = 0
    feedback = []

    # Minimum length check
    if len(password) >= 8:
        score += 1
    else:
        feedback.append("Password should be at least 8 characters long.")

    # Check for uppercase letters
    if re.search(r'[A-Z]', password):
        score += 1
    else:
        feedback.append("Password should include at least one uppercase letter.")

    # Check for lowercase letters
    if re.search(r'[a-z]', password):
        score += 1
    else:
        feedback.append("Password should include at least one lowercase letter.")

    # Check for digits
    if re.search(r'[0-9]', password):
        score += 1
    else:
        feedback.append("Password should include at least one number.")

    # Check for special characters
    if re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        score += 1
    else:
        feedback.append("Password should include at least one special character (e.g., !, @, #, $).")

    # Check for common patterns or weaknesses
    common_passwords = ["password", "123456", "123456789", "qwerty", "abc123", "letmein", "123123"]
    if password.lower() in common_passwords:
        feedback.append("Avoid using common passwords.")
    else:
        score += 1

    return {
        "score": score,
        "feedback": feedback
    }


def main():
    print("\n--- Password Strength Tester ---")
    password = input("Enter a password to test its strength: ")
    result = check_password_strength(password)

    print(f"\nPassword Strength Score: {result['score']}/6")
    if result['feedback']:
        print("\nSuggestions to improve your password:")
        for tip in result['feedback']:
            print(f"- {tip}")
    else:
        print("Your password is strong!")


if __name__ == "__main__":
    main()
