import hashlib
import itertools
import string


def generate_rainbow_table(charset, length):
    """
    Generate rainbow table
    """
    table = []
    for r in range(1, length + 1):
        for combination in itertools.product(charset, repeat=r):
            plaintext = ''.join(combination)
            hash = hashlib.sha256(plaintext.encode()).hexdigest()
            table.append(f"{hash}:{plaintext}")
    return table

if __name__ == "__main__":
    charset = string.ascii_letters + string.digits
    length = int(input("Enter rainbow table length: "))
    rainbow_table = generate_rainbow_table(charset, length)
    with open('rainbow_table.txt', 'w') as f:
        for entry in rainbow_table:
            f.write(entry + '\n')