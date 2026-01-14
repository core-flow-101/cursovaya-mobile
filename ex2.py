

import re
import os
from collections import Counter
import nltk
from nltk.corpus import stopwords

# Загрузка стоп-слов
try:
    nltk.download('stopwords', quiet=True)
    RUSSIAN_STOPWORDS = set(stopwords.words('russian'))
    ENGLISH_STOPWORDS = set(stopwords.words('english'))
except Exception:
    RUSSIAN_STOPWORDS = set()
    ENGLISH_STOPWORDS = set()


BASIC_STOPWORDS = {
    'это', 'как', 'так', 'или', 'но', 'что', 'для', 'при', 'из', 'на', 'по',
    'от', 'до', 'за', 'под', 'над', 'без', 'про', 'со', 'во', 'об', 'ко',
    'к', 'с', 'в', 'и', 'а', 'о', 'у', 'же', 'бы', 'ли', 'то', 'не', 'ни',
    'да', 'он', 'она', 'они', 'мы', 'вы', 'ты', 'я', 'был', 'была', 'было',
    'были', 'есть', 'быть', 'если', 'когда', 'где', 'чем',
    'the', 'a', 'an', 'of', 'in', 'on', 'at', 'for', 'to', 'from', 'with',
    'by', 'and', 'or', 'but', 'as', 'is', 'are', 'was', 'were', 'be', 'been',
    'being', 'that', 'this', 'these', 'those', 'it', 'its', 'into', 'about',
    'over', 'under', 'between', 'among', 'up', 'down', 'out', 'off', 'than',
    'then', 'so', 'such', 'not', 'no', 'nor', 'very'
}


class TerminologyIndexer:

    def __init__(self, filepath):
        self.filepath = filepath
        self.text = ""
        self.words = []
        self.sentences = []
        self.terms = set()
        self.bigrams = []
        self.trigrams = []
        self.abbreviations = set()

    def load_text(self):
        try:
            with open(self.filepath, 'r', encoding='utf-8') as f:
                self.text = f.read()
        except UnicodeDecodeError:
            with open(self.filepath, 'r', encoding='cp1251') as f:
                self.text = f.read()
        

    def preprocess(self):
        self.sentences = re.split(r'[.!?]+', self.text)
        text_lower = self.text.lower()
        self.words = re.findall(r'\b[а-яёa-z]+\b', text_lower)
        self.words = [w for w in self.words if len(w) >= 3]
        

    def extract_abbreviations(self):
        """Извлечение аббревиатур"""
        patterns = [
            r'\b[А-ЯЁA-Z]{2,10}\b',          
            r'\b[А-ЯЁA-Z](?:\.[А-ЯЁA-Z]){1,5}\b',  
            r'\b[А-ЯЁA-Z]{2,}[0-9]+\b',       
        for pattern in patterns:
            self.abbreviations.update(re.findall(pattern, self.text))
        self.abbreviations = {abbr for abbr in self.abbreviations if 2 <= len(abbr.replace('.', '')) <= 15}

    def extract_terms(self, min_freq=2, min_len=4, top_n=150):
        """Извлечение терминов"""
        freq = Counter(self.words)
        filtered = {
            word: count for word, count in freq.items()
            if word not in BASIC_STOPWORDS and word not in RUSSIAN_STOPWORDS
            and word not in ENGLISH_STOPWORDS and len(word) >= min_len and count >= min_freq
        }
        sorted_terms = sorted(filtered.items(), key=lambda x: x[1], reverse=True)
        self.terms = {term for term, _ in sorted_terms[:top_n]}


    def extract_ngrams(self, n=2, min_freq=2, top_n=50):
        """Извлечение n-грамм"""
        ngrams = []
        for i in range(len(self.words) - n + 1):
            ngram = tuple(self.words[i:i + n])
            if any(word in BASIC_STOPWORDS or word in RUSSIAN_STOPWORDS or word in ENGLISH_STOPWORDS for word in ngram):
                continue
            ngrams.append(' '.join(ngram))
        freq = Counter(ngrams)
        filtered = {ng: count for ng, count in freq.items() if count >= min_freq}
        sorted_ngrams = sorted(filtered.items(), key=lambda x: x[1], reverse=True)
        if n == 2:
            self.bigrams = [ng for ng, _ in sorted_ngrams[:80]]
            
        elif n == 3:
            self.trigrams = [ng for ng, _ in sorted_ngrams[:top_n]]
        

    def build_index(self):
        """Построение полного предметного указателя"""
        self.load_text()
        self.preprocess()
        self.extract_abbreviations()
        self.extract_terms()
        self.extract_ngrams(n=2)
        self.extract_ngrams(n=3)

        all_concepts = set(self.terms) | set(self.bigrams) | set(self.trigrams)
        if len(all_concepts) < 100:
            freq = Counter(self.words)
            sorted_terms = sorted(freq.items(), key=lambda x: x[1], reverse=True)
            for term, _ in sorted_terms[150:]:
                if term not in all_concepts:
                    all_concepts.add(term)
                if len(all_concepts) >= 100:
                    break
            self.terms.update(all_concepts - set(self.terms))
        return all_concepts

    def save_index(self):
        """Сохранение предметного указателя в текстовый файл"""
        output_dir = 'Результаты анализа'
        os.makedirs(output_dir, exist_ok=True)
        base_name = os.path.splitext(os.path.basename(self.filepath))[0]
        output_file = os.path.join(output_dir, f'{base_name}_subject_index.txt')

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("ПРЕДМЕТНЫЙ (ТЕРМИНОЛОГИЧЕСКИЙ) УКАЗАТЕЛЬ\n")
            f.write("="*60 + "\n\n")
            f.write("1. ОТДЕЛЬНЫЕ ТЕРМИНЫ\n" + "-"*60 + "\n")
            for i, term in enumerate(sorted(self.terms), 1):
                f.write(f"{i}. {term}\n")
            f.write(f"\nВсего терминов: {len(self.terms)}\n\n")

            f.write("2. ДВУХСЛОВНЫЕ СЛОВОСОЧЕТАНИЯ\n" + "-"*60 + "\n")
            for i, bg in enumerate(self.bigrams, 1):
                f.write(f"{i}. {bg}\n")
            f.write(f"\nВсего двухсловных словосочетаний: {len(self.bigrams)}\n\n")

            f.write("3. ТРЕХСЛОВНЫЕ СЛОВОСОЧЕТАНИЯ\n" + "-"*60 + "\n")
            for i, tg in enumerate(self.trigrams, 1):
                f.write(f"{i}. {tg}\n")
            f.write(f"\nВсего трехсловных словосочетаний: {len(self.trigrams)}\n\n")

            f.write("4. АББРЕВИАТУРЫ\n" + "-"*60 + "\n")
            for i, abbr in enumerate(sorted(self.abbreviations), 1):
                f.write(f"{i}. {abbr}\n")
            f.write(f"\nВсего аббревиатур: {len(self.abbreviations)}\n\n")

            total = len(self.terms) + len(self.bigrams) + len(self.trigrams) + len(self.abbreviations)
            f.write("="*60 + "\n")
            f.write(f"ОБЩЕЕ КОЛИЧЕСТВО ПОНЯТИЙ: {total}\n")
            f.write("="*60 + "\n")


def main():
    text_files = [f for f in os.listdir('.') if f.lower().endswith('.txt')]
    if not text_files:
        return


    for f in text_files:

    for file_path in text_files:
        indexer = TerminologyIndexer(file_path)
        indexer.build_index()
        indexer.save_index()



if __name__ == "__main__":
    main()
