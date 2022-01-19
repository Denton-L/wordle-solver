#!/usr/bin/env python3

import collections
import copy
import itertools
import multiprocessing
import random
import re

WORDS_FILE = '/usr/share/dict/words'
NUM_LETTERS = 5
MAX_WORDS_IN_LIST = 200

class Matcher:
    def __init__(self, num_letters):
        self.num_letters = num_letters
        self.known = collections.Counter()
        self.solved = [None] * num_letters
        self.wrong = [set() for _ in range(num_letters)]

    def advance_state(self, response):
        response = response.lower()

        known = collections.Counter()
        solved = self.solved.copy()
        wrong = copy.deepcopy(self.wrong)

        i = 0
        wi = 0
        while i < len(response):
            l = response[i]
            m = response[i+1] if i < len(response) - 1 else None
            i += 1

            if m == '?':
                known[l] += 1
                wrong[wi].add(l)
                i += 1
            elif m == '!':
                solved[wi] = l
                i += 1
            else:
                if known[l]:
                    wrong[wi].add(l)
                else:
                    for w in wrong:
                        w.add(l)

            wi += 1

        for l, c in self.known.items():
            known[l] = max(known[l], c)

        m = Matcher(self.num_letters)
        m.known = known
        m.solved = solved
        m.wrong = wrong

        return m

    def matches(self, word):
        count = collections.Counter(word)
        most_common = (self.known - count).most_common(1)
        if most_common and most_common[0][1]:
            return False

        for l, s, w in zip(word, self.solved, self.wrong):
            if s:
                if l == s:
                    continue
                else:
                    return False
            if l in w:
                return False

        return True

def generate_response(solution, word):
    matches = [s == w for s, w in zip(solution, word)]
    count = collections.Counter(s for s, m in zip(solution, matches) if not m)

    response = ''
    for w, m in zip(word, matches):
        if m:
            response += f'{w}!'
        elif count[w]:
            response += f'{w}?'
            count[w] -= 1
        else:
            response += w

    return response

def init_best_guess_worker(matcher, words):
    best_guess_worker.matcher = matcher
    best_guess_worker.words = words

def best_guess_worker(work):
        guess, solution = work
        new_matcher = best_guess_worker.matcher.advance_state(generate_response(solution, guess))
        return guess, sum(1 for w in best_guess_worker.words if new_matcher.matches(w))

def best_guess(matcher, words):
    words = random.sample(list(words), min(len(words), MAX_WORDS_IN_LIST))
    possibilties = collections.Counter()
    with multiprocessing.Pool(multiprocessing.cpu_count(), init_best_guess_worker, (matcher, words)) as pool:
        for guess, number in pool.imap_unordered(best_guess_worker, itertools.product(words, repeat=2)):
            possibilties[guess] += number
    return possibilties

def main():
    allow_regex = re.compile(f'[a-zA-Z]{{{NUM_LETTERS}}}')
    with open(WORDS_FILE) as f:
        all_words = {w.strip().lower() for w in f if allow_regex.fullmatch(w.strip())}

    empty_matcher = Matcher(NUM_LETTERS)
    states = [(empty_matcher, all_words)]

    while True:
        if not states:
            break
        matcher, words = states[-1]
        guesses = best_guess(matcher, words)
        for w, p in guesses.most_common():
            print(w, p)
        if len(guesses) == 1:
            break
        try:
            response = input('Wordle response: ')
        except EOFError:
            break
        if not response:
            states.pop()
        else:
            matcher = matcher.advance_state(response)
            words = {w for w in words if matcher.matches(w)}
            states.append((matcher, words))

if __name__ == '__main__':
    main()
