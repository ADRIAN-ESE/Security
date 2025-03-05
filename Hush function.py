import hashlib
import json
import os

class PasswordHasher:
    def __init__(self, filename='passwords.json'):
        self.filename = filename
        self.passwords = self.load_passwords()

    def load_passwords(self):
        if os.path.exists(self.filename):
            with open(self.filename, 'r') as f:
                return json.load(f)
        else:
            return {}

    def save_passwords(self):
        with open(self.filename, 'w') as f:
            json.dump(self.passwords, f)

    def hash_password(self, password, algorithm='sha256'):
        if algorithm == 'sha256':
            return hashlib.sha256(password.encode()).hexdigest()
        elif algorithm == 'md5':
            return hashlib.md5(password.encode()).hexdigest()
        elif algorithm == 'sha512':
            return hashlib.sha512(password.encode()).hexdigest()
        else:
            raise ValueError('Invalid algorithm')

    def add_password(self, username, password, algorithm='sha256'):
        hashed_password = self.hash_password(password, algorithm)
        self.passwords[username] = {
            'password': hashed_password,
            'algorithm': algorithm
        }
        self.save_passwords()

    def verify_password(self, username, password):
        stored_password = self.passwords.get(username)
        if stored_password:
            hashed_password = self.hash_password(password, stored_password['algorithm'])
            return hashed_password == stored_password['password']
        else:
            return False


def main():
    hasher = PasswordHasher()

    while True:
        print('1. Add password')
        print('2. Verify password')
        print('3. Exit')
        choice = input('Choose an option: ')

        if choice == '1':
            username = input('Enter username: ')
            password = input('Enter password: ')
            algorithm = input('Choose algorithm (sha256, md5, sha512): ')
            hasher.add_password(username, password, algorithm)
            print('Password added successfully!')
        elif choice == '2':
            username = input('Enter username: ')
            password = input('Enter password: ')
            if hasher.verify_password(username, password):
                print('Password correct!')
            else:
                print('Password incorrect!')
        elif choice == '3':
            break
        else:
            print('Invalid option')


if __name__ == '__main__':
    main()