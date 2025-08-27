import itertools
import string


def generate_wordlist(length):
    """
    Generate wordlist of specified length
    """
    words = []
    for r in range(1, length + 1):
        for combination in itertools.product(string.ascii_letters, repeat=r):
            words.append(''.join(combination))
    return words

if __name__ == "__main__":
    length = int(input("Enter wordlist length: "))
    wordlist = generate_wordlist(length)
    with open('wordlist.txt', 'w') as f:
        for word in wordlist:
            f.write(word + '\n')