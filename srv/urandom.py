import random as prng
# Truly random number source
random = prng.SystemRandom()

def choice(choices):
    return random.choice(choices)

def shuffle(objects):
    return random.shuffle(objects)
