import re


# Function to check password strength and provide suggestions
def password_strength(password):
    # Initialize score, feedback, and suggestions
    score = 0
    feedback = []
    suggestions = []

    # Check for password length (minimum 8 characters)
    if len(password) >= 12:
        score += 2
    elif len(password) >= 8:
        score += 1
    else:
        feedback.append("🔴 Length Issue: Password is too short.")
        suggestions.append(
            "🔑 Suggestion: Your password should be at least 12 characters long for optimal security. Try to include a mix of letters, numbers, and symbols to make it longer.")

    # Check for at least one uppercase letter
    if re.search(r'[A-Z]', password):
        score += 1
    else:
        feedback.append("🔴 Uppercase Letter Issue: Missing an uppercase letter.")
        suggestions.append(
            "🔑 Suggestion: Add at least one uppercase letter (e.g., A, B, C). It strengthens the password by adding variety in character types.")

    # Check for at least one lowercase letter
    if re.search(r'[a-z]', password):
        score += 1
    else:
        feedback.append("🔴 Lowercase Letter Issue: Missing a lowercase letter.")
        suggestions.append(
            "🔑 Suggestion: Add at least one lowercase letter (e.g., a, b, c). It helps increase the complexity of your password.")

    # Check for at least one digit
    if re.search(r'[0-9]', password):
        score += 1
    else:
        feedback.append("🔴 Digit Issue: Missing a number.")
        suggestions.append(
            "🔑 Suggestion: Include at least one digit (e.g., 1, 2, 3) to make the password harder to guess.")

    # Check for at least one special character
    if re.search(r'[@#$%^&+=!.,?<>;:*\-_]', password):
        score += 1
    else:
        feedback.append("🔴 Special Character Issue: Missing a special character.")
        suggestions.append(
            "🔑 Suggestion: Add a special character (e.g., @, #, $, %, &, etc.). This increases the complexity of the password, making it more secure.")

    # Check if password is too common (against a list of common passwords)
    common_passwords = ['password', '123456', 'qwerty', '12345', 'password1', 'welcome', 'admin']
    if password.lower() in common_passwords:
        feedback.append("🔴 Common Password Issue: This is a commonly used password.")
        suggestions.append(
            "🔑 Suggestion: Avoid using common passwords like 'password123' or 'qwerty'. Choose a unique password that combines letters, numbers, and symbols.")

    # Classify the password strength
    if score == 7:
        strength = "✔️ Very Strong"
    elif score == 6:
        strength = "✔️ Strong"
    elif score == 5:
        strength = "⚡ Medium"
    elif score >= 3:
        strength = "⚠️ Weak"
    else:
        strength = "❌ Very Weak"

    # Return the password strength, feedback, and suggestions
    return strength, feedback, suggestions


def main():
    password = input("Enter your password to analyze: ")
    strength, feedback, suggestions = password_strength(password)

    # Output the feedback and strength
    print("\n🛡️ Password Strength: " + strength)

    if feedback:
        print("\n⚠️ Issues with your password:")
        for issue in feedback:
            print(f"   {issue}")

        print("\n🔧 Suggestions to improve your password:")
        for suggestion in suggestions:
            print(f"   {suggestion}")
    else:
        print("\n🎉 Your password meets all the required criteria! It's strong!")


if __name__ == "__main__":
    main()
