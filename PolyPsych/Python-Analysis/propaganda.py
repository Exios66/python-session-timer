import re
import csv
import json
import argparse
import logging
from pathlib import Path
from typing import List, Dict, Any
from collections import Counter

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from sklearn.metrics import cohen_kappa_score

# If you need to perform reliability analysis
# Ensure nltk resources are downloaded
import nltk

# Download required NLTK data
nltk.download('punkt')
nltk.download('stopwords')
nltk.download('wordnet')
nltk.download('omw-1.4')

# Configure logging
logging.basicConfig(
    filename='processing.log',
    filemode='a',
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

class CodingSchemeLoader:
    """
    Loads coding schemes from JSON files.
    """
    def __init__(self, definition_scheme_path: str, verification_scheme_path: str):
        self.definition_scheme_path = definition_scheme_path
        self.verification_scheme_path = verification_scheme_path

    def load_scheme(self, path: str) -> Dict[str, List[str]]:
        try:
            with open(path, 'r', encoding='utf-8') as file:
                scheme = json.load(file)
            logging.info(f"Loaded coding scheme from {path}")
            return scheme
        except Exception as e:
            logging.error(f"Error loading coding scheme from {path}: {e}")
            raise

    def get_definition_scheme(self) -> Dict[str, List[str]]:
        return self.load_scheme(self.definition_scheme_path)

    def get_verification_scheme(self) -> Dict[str, List[str]]:
        return self.load_scheme(self.verification_scheme_path)

class TextPreprocessor:
    """
    Preprocesses text data by cleaning, lemmatizing, and removing stopwords.
    """
    def __init__(self):
        self.lemmatizer = WordNetLemmatizer()
        self.stop_words = set(stopwords.words('english'))

    def preprocess(self, text: str) -> str:
        text = self.clean_text(text)
        tokens = text.split()
        tokens = [self.lemmatizer.lemmatize(token) for token in tokens if token not in self.stop_words]
        preprocessed_text = ' '.join(tokens)
        logging.debug(f"Preprocessed text: {preprocessed_text}")
        return preprocessed_text

    @staticmethod
    def clean_text(text: str) -> str:
        # Remove URLs
        text = re.sub(r'http\S+|www.\S+', '', text)
        # Remove special characters and digits
        text = re.sub(r'[^A-Za-z\s]', '', text)
        # Convert to lowercase
        text = text.lower()
        return text

class ResponseCoder:
    """
    Codes responses based on provided coding schemes.
    """
    def __init__(self, coding_scheme: Dict[str, List[str]]):
        self.coding_scheme = coding_scheme

    def code_response(self, text: str) -> List[str]:
        codes_matched = []
        for code, keywords in self.coding_scheme.items():
            for keyword in keywords:
                # Use word boundaries to match whole words
                if re.search(r'\b' + re.escape(keyword) + r'\b', text):
                    codes_matched.append(code)
                    break  # Avoid duplicate coding for the same category
        logging.debug(f"Codes matched for text: {codes_matched}")
        return codes_matched

class DataProcessor:
    """
    Processes responses by reading, preprocessing, coding, and analyzing data.
    """
    def __init__(self, preprocessor: TextPreprocessor, definition_coder: ResponseCoder, verification_coder: ResponseCoder):
        self.preprocessor = preprocessor
        self.definition_coder = definition_coder
        self.verification_coder = verification_coder

    @staticmethod
    def read_responses(file_path: str) -> List[str]:
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                responses = [line.strip() for line in file if line.strip()]
            logging.info(f"Read {len(responses)} responses from {file_path}")
            return responses
        except Exception as e:
            logging.error(f"Error reading responses from {file_path}: {e}")
            raise

    @staticmethod
    def count_steps(response: str) -> int:
        steps = re.split(r'[.,;\n]+', response)
        steps = [step.strip() for step in steps if step.strip()]
        return len(steps)

    def process_definitions(self, responses: List[str]) -> pd.DataFrame:
        data = []
        for response in responses:
            cleaned_text = self.preprocessor.preprocess(response)
            codes = self.definition_coder.code_response(cleaned_text)
            data.append({'Response': response, 'Codes': codes})
        df = pd.DataFrame(data)
        logging.info("Processed definitions responses")
        return df

    def process_verifications(self, responses: List[str]) -> pd.DataFrame:
        data = []
        for response in responses:
            cleaned_text = self.preprocessor.preprocess(response)
            codes = self.verification_coder.code_response(cleaned_text)
            num_steps = self.count_steps(response)
            data.append({'Response': response, 'Codes': codes, 'Number of Steps': num_steps})
        df = pd.DataFrame(data)
        logging.info("Processed verifications responses")
        return df

class Analyzer:
    """
    Performs analysis on the processed data, including frequency counts, descriptive statistics, and reliability analysis.
    """
    def __init__(self):
        pass

    @staticmethod
    def compute_frequency(df: pd.DataFrame, column_name: str) -> pd.Series:
        all_codes = df[column_name].explode()
        frequency = all_codes.value_counts()
        logging.info(f"Computed frequency for {column_name}")
        return frequency

    @staticmethod
    def compute_descriptive_stats(series: pd.Series) -> pd.Series:
        stats = series.describe()
        logging.info("Computed descriptive statistics")
        return stats

    @staticmethod
    def plot_frequency(frequency: pd.Series, title: str, output_path: str):
        plt.figure(figsize=(10, 6))
        sns.barplot(x=frequency.values, y=frequency.index, palette='viridis')
        plt.title(title)
        plt.xlabel('Frequency')
        plt.ylabel('Codes')
        plt.tight_layout()
        plt.savefig(output_path)
        plt.close()
        logging.info(f"Saved frequency plot to {output_path}")

    @staticmethod
    def plot_descriptive_stats(series: pd.Series, title: str, output_path: str):
        plt.figure(figsize=(8, 6))
        sns.histplot(series, kde=True, bins=10, color='skyblue')
        plt.title(title)
        plt.xlabel('Number of Steps')
        plt.ylabel('Frequency')
        plt.tight_layout()
        plt.savefig(output_path)
        plt.close()
        logging.info(f"Saved descriptive statistics plot to {output_path}")

    @staticmethod
    def compute_cohens_kappa(ratings1: List[str], ratings2: List[str], coding_categories: List[str]) -> float:
        # Flatten the codes for each rater
        # For simplicity, assume binary coding per category
        binary_ratings1 = [1 if category in codes else 0 for codes in ratings1 for category in coding_categories]
        binary_ratings2 = [1 if category in codes else 0 for codes in ratings2 for category in coding_categories]
        kappa = cohen_kappa_score(binary_ratings1, binary_ratings2)
        logging.info(f"Computed Cohen's Kappa: {kappa}")
        return kappa

class Visualizer:
    """
    Handles the creation of visualizations for the analysis.
    """
    def __init__(self):
        sns.set(style="whitegrid")

    # Visualization methods are integrated into the Analyzer class for simplicity

def main():
    # Argument parsing
    parser = argparse.ArgumentParser(description="Process and analyze fake news definitions and verifications.")
    parser.add_argument('--definitions_input', type=str, default='fake_news_definitions.txt', help='Path to definitions input file')
    parser.add_argument('--verifications_input', type=str, default='fake_news_verification.txt', help='Path to verifications input file')
    parser.add_argument('--definition_scheme', type=str, default='definition_coding_scheme.json', help='Path to definition coding scheme JSON file')
    parser.add_argument('--verification_scheme', type=str, default='verification_coding_scheme.json', help='Path to verification coding scheme JSON file')
    parser.add_argument('--definitions_output', type=str, default='processed_definitions.csv', help='Path to definitions output CSV file')
    parser.add_argument('--verifications_output', type=str, default='processed_verifications.csv', help='Path to verifications output CSV file')
    parser.add_argument('--plots_dir', type=str, default='plots', help='Directory to save plots')
    args = parser.parse_args()

    # Ensure plots directory exists
    Path(args.plots_dir).mkdir(parents=True, exist_ok=True)

    # Load coding schemes
    loader = CodingSchemeLoader(args.definition_scheme, args.verification_scheme)
    definition_scheme = loader.get_definition_scheme()
    verification_scheme = loader.get_verification_scheme()

    # Initialize components
    preprocessor = TextPreprocessor()
    definition_coder = ResponseCoder(definition_scheme)
    verification_coder = ResponseCoder(verification_scheme)
    processor = DataProcessor(preprocessor, definition_coder, verification_coder)
    analyzer = Analyzer()

    # Read responses
    definitions_responses = processor.read_responses(args.definitions_input)
    verifications_responses = processor.read_responses(args.verifications_input)

    # Process and code responses
    definitions_df = processor.process_definitions(definitions_responses)
    verifications_df = processor.process_verifications(verifications_responses)

    # Save processed data
    definitions_df.to_csv(args.definitions_output, index=False)
    verifications_df.to_csv(args.verifications_output, index=False)
    logging.info(f"Saved processed definitions to {args.definitions_output}")
    logging.info(f"Saved processed verifications to {args.verifications_output}")

    # Perform analysis
    # Definitions
    print("Definitions - Code Frequencies:")
    def_freq = analyzer.compute_frequency(definitions_df, 'Codes')
    print(def_freq)
    analyzer.plot_frequency(def_freq, 'Definitions Code Frequencies', f"{args.plots_dir}/definitions_code_frequencies.png")

    # Definitions Descriptive Statistics (if numerical coding is added)
    # Placeholder: Assuming numerical coding not implemented yet

    # Verifications
    print("\nVerifications - Code Frequencies:")
    ver_freq = analyzer.compute_frequency(verifications_df, 'Codes')
    print(ver_freq)
    analyzer.plot_frequency(ver_freq, 'Verifications Code Frequencies', f"{args.plots_dir}/verifications_code_frequencies.png")

    print("\nVerifications - Number of Steps Statistics:")
    steps_stats = analyzer.compute_descriptive_stats(verifications_df['Number of Steps'])
    print(steps_stats)
    analyzer.plot_descriptive_stats(verifications_df['Number of Steps'], 'Number of Steps Distribution', f"{args.plots_dir}/verifications_steps_distribution.png")

    # Reliability Analysis Placeholder
    # Assuming we have ratings from two coders
    # For demonstration, we'll simulate another set of codes
    # In practice, you'd have actual data from multiple coders

    # Simulate second coder's codes (for example purposes only)
    # This section should be adapted based on actual multi-coder data
    # Uncomment and modify if you have multiple coders

    """
    second_coder_codes = definitions_df['Codes'].apply(lambda codes: codes)  # Replace with actual second coder's codes
    kappa = analyzer.compute_cohens_kappa(definitions_df['Codes'].tolist(), second_coder_codes.tolist(), list(definition_scheme.keys()))
    print(f"Cohen's Kappa for Definitions: {kappa}")
    """

    # Additional psychometric analyses can be added here
    # For example, factor analysis, item response theory, etc.

if __name__ == "__main__":
    main()