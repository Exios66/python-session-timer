from dataclasses import dataclass
from typing import List, Dict, Any
import csv
import json
import statistics

@dataclass
class SurveyCollector:
    survey_id: str
    title: str
    blocks: List['Block']
    responses: List[Dict[str, Any]] = None

    def __init__(self, survey_id, title):
        self.survey_id = survey_id
        self.title = title
        self.blocks = []
        self.responses = []

    def add_block(self, block):
        self.blocks.append(block)
    
    def collect_response(self, response):
        self.responses.append(response)
    
    def get_block(self, block_id):
        for block in self.blocks:
            if block.block_id == block_id:
                return block
        raise ValueError("Block not found")
    
    def process_responses(self):
        results = {}
        for response in self.responses:
            for question_id, answer in response.items():
                if question_id not in results:
                    results[question_id] = []
                results[question_id].append(answer)
        
        processed_results = {}
        for question_id, answers in results.items():
            if isinstance(answers[0], list):  # For multi-select questions
                processed_results[question_id] = {option: answers.count([option]) for option in set(answer for answer_list in answers for answer in answer_list)}
            elif isinstance(answers[0], str):  # For single choice or open-ended
                processed_results[question_id] = {option: answers.count(option) for option in set(answers)}
            elif isinstance(answers[0], int) or isinstance(answers[0], float):  # For scale or numerical questions
                processed_results[question_id] = {
                    'mean': statistics.mean(answers),
                    'median': statistics.median(answers),
                    'mode': statistics.mode(answers) if len(set(answers)) > 1 else answers[0],
                    'count': len(answers)
                }
            else:  # For other types, just count occurrences
                processed_results[question_id] = {answer: answers.count(answer) for answer in set(answers)}
        return processed_results

    def export_results(self, filename='results', format='csv'):
        results = self.process_responses()
        if format == 'csv':
            with open(f"{filename}.csv", 'w', newline='') as csvfile:
                writer = csv.writer(csvfile)
                for question_id, data in results.items():
                    writer.writerow([question_id])
                    if isinstance(data, dict):
                        for option, count in data.items():
                            writer.writerow([option, count])
                    else:
                        writer.writerow([data])
        elif format == 'json':
            with open(f"{filename}.json", 'w') as jsonfile:
                json.dump(results, jsonfile, indent=4)
        else:
            raise ValueError("Unsupported format. Please use 'csv' or 'json'.")

@dataclass
class Block:
    block_id: str
    questions: List['Question']

    def add_question(self, question):
        self.questions.append(question)

@dataclass
class Question:
    question_id: str
    question_text: str
    question_type: str
    options: List[str] = None

    def validate_response(self, response):
        if self.question_type == 'multiple_choice':
            if isinstance(response, list):
                if not all(r in self.options for r in response):
                    raise ValueError(f"Invalid response for question: {self.question_text}. Must be one of {self.options}")
            elif response not in self.options:
                raise ValueError(f"Invalid response for question: {self.question_text}. Must be one of {self.options}")
        elif self.question_type == 'open_ended':
            if not response:
                raise ValueError(f"Response cannot be empty for question: {self.question_text}")
        elif self.question_type == 'likert_scale' or self.question_type == 'scale':
            if not isinstance(response, int) or response < 0 or response > 10:  # Adjust range as needed
                raise ValueError(f"Response must be an integer between 0 and 10 for question: {self.question_text}")
        return True

# Creating blocks and questions

# Demographics Block
demographics = Block("Demographics", [])
demographics.add_question(Question("Age", "What is your age?", "open_ended"))
demographics.add_question(Question("Year", "What year are you in college?", "multiple_choice", 
                                   ["First Year (1)", "Sophomore (2)", "Junior (3)", "Senior (4)", "5+ Years (5)"]))
demographics.add_question(Question("Ethnicity", "Are you of Spanish, Hispanic, or Latino origin?", "multiple_choice", 
                                   ["Yes (1)", "No (2)"]))
demographics.add_question(Question("Race", "Choose one or more races that you consider yourself to be", "multiple_choice", 
                                   ["White or Caucasian (1)", "Black or African American (2)", 
                                    "American Indian/Native American or Alaska Native (3)", "Asian (4)", 
                                    "Native Hawaiian or Other Pacific Islander (5)", "Other (6)", 
                                    "Prefer not to say (7)"]))
demographics.add_question(Question("Household_Income", "What was your total household income before taxes during the past 12 months?", "multiple_choice", 
                                   ["Less than $25,000 (1)", "$25,000-$49,999 (2)", "$50,000-$74,999 (3)", 
                                    "$75,000-$99,999 (4)", "$100,000-$149,999 (5)", "$150,000 or more (6)", 
                                    "Prefer not to say (7)"]))

# Political Demographics Block
demographics_political = Block("Demographics Political", [])
demographics_political.add_question(Question("Election", "Do you plan to vote in the upcoming 2024 election?", "multiple_choice", 
                                             ["Yes (1)", "No (2)"]))
demographics_political.add_question(Question("Party_Affiliation", "Generally speaking, do you usually think of yourself as a Republican, a Democrat, an Independent, or something else?", "multiple_choice", 
                                             ["Republican (1)", "Democrat (2)", "Independent (3)", "Other (4)", "No preference (5)"]))
demographics_political.add_question(Question("R_Strength", "Would you call yourself a strong Republican or a not very strong Republican?", "multiple_choice", 
                                             ["Strong (1)", "Not very strong (2)"]))
demographics_political.add_question(Question("D_Strength", "Would you call yourself a strong Democrat or a not very strong Democrat?", "multiple_choice", 
                                             ["Strong (1)", "Not very strong (2)"]))
demographics_political.add_question(Question("Independent_Lean", "Do you think of yourself as closer to the Republican or Democratic party?", "multiple_choice", 
                                             ["Republican (1)", "Democratic (2)"]))
demographics_political.add_question(Question("Political_Views", "Here is a 7-point scale on which the political views that people might hold are arranged from extremely liberal (left) to extremely conservative (right). Where would you place yourself on this scale?", "scale", 
                                             ["0", "1", "2", "3", "4", "5", "6", "7"]))
demographics_political.add_question(Question("Party_Registration", "What political party are you registered with, if any?", "multiple_choice", 
                                             ["Republican (1)", "Democratic (2)", "Independent (3)", "Other (4)", "None (5)"]))

# Personal Political Characteristics Block
personal_political = Block("Personal Political Characteristics", [])
personal_political.add_question(Question("P_Efficacy", "For each question below, please choose the response that best reflects how you feel.", "likert_scale", 
                                        ["Strongly Disagree (1)", "Somewhat disagree (2)", "Neither agree nor disagree (3)", "Somewhat agree (4)", "Strongly agree (5)"]))
personal_political.add_question(Question("P_Knowledge_Intro", "Here are a few questions about the federal government. Many people don't know the answers to these questions, so if there are some you don't know, just provide your best guess.", "intro"))
personal_political.add_question(Question("P_Knowledge_1", "Do you happen to know what job or political office is now held by Kamala Harris?", "open_ended"))
personal_political.add_question(Question("P_Knowledge_2", "Whose responsibility is it to determine if a law is constitutional or not? Is it the president, the Congress, or the Supreme Court?", "multiple_choice", 
                                       ["President", "Congress", "Supreme Court"]))
personal_political.add_question(Question("P_Knowledge_3", "How much of a majority is required for the U.S. Senate and House to override a presidential veto?", "open_ended"))
personal_political.add_question(Question("P_Knowledge_4", "Do you happen to know which party has the most members in the House of Representatives currently?", "open_ended"))
personal_political.add_question(Question("P_Knowledge_5", "Would you say that one of the parties is more conservative than the other at the national level? Which party is more conservative?", "open_ended"))

# Perception of News Sources Block
perception_news = Block("Perception of News Sources", [])
# Add all the news sources as individual questions here. For brevity, only one example is shown:
perception_news.add_question(Question("ABC_News", "ABC News", "likert_scale", 
                                      ["1 (Definitely not)", "2 (Probably not)", "3 (Might or might not be)", "4 (Probably is)", "5 (Definitely is)"]))

# Social Media Block
social_media = Block("Perception of Political Information on Social Media", [])
social_media.add_question(Question("Social_Media", "Social media as a source of political information and news is...", "likert_scale", 
                                   ["Does not apply at all (1)", "2", "3", "4", "5", "6", "Fully Applies (7)"]))

# Media Consumption Block
media_consumption = Block("Media Consumption Questions", [])
media_consumption.add_question(Question("News_1", "Where do you typically get your news?", "multiple_choice", 
                                        ["Print newspapers (1)", "Television (2)", "News websites (3)", "Social media (4)", "Radio (5)", "Podcasts (6)"]))
media_consumption.add_question(Question("News_frequency", "How often do you consume news?", "multiple_choice", 
                                       ["Daily", "A few times a week", "Once a week", "A few times a month", "Rarely", "Never"]))

# Misinformation Threat Block
misinformation_threat = Block("Mis_Threat", [])
misinformation_threat.add_question(Question("Disinfo_threat", "On the scale from 0 to 10, where 0 means no risk and 10 means extreme risk, how would you rate the risk of disinformation campaigns to each of the following?", "scale", 
                                            ["0 (No risk)", "1", "2", "3", "4", "5", "6", "7", "8", "9", "10 (Extreme risk)"]))
misinformation_threat.add_question(Question("Disinfo_Res", "In your opinion, who is primarily responsible for combating disinformation?", "multiple_choice", 
                                            ["Government", "Social Media Companies", "Educational Institutions", "News Outlets", "Individuals", "Other (Please specify)"]))

# Adding blocks to survey
survey = SurveyCollector("PSY_492", "Election Experience Survey")
survey.add_block(demographics)
survey.add_block(demographics_political)
survey.add_block(personal_political)
survey.add_block(perception_news)
survey.add_block(social_media)
survey.add_block(media_consumption)
survey.add_block(misinformation_threat)

# Example of collecting a response
sample_response = {
    "Age": "23",
    "Year": "Junior (3)",
    "Ethnicity": "No (2)",
    "Race": ["White or Caucasian (1)", "Other (6)"],
    "Household_Income": "Prefer not to say (7)",
    "Election": "Yes (1)",
    "Party_Affiliation": "Democrat (2)",
    "R_Strength": "Not very strong (2)",
    "D_Strength": "Strong (1)",
    "Independent_Lean": "Democratic (2)",
    "Political_Views": 4,
    "Party_Registration": "Democratic (2)",
    "P_Efficacy": 3,
    "P_Knowledge_1": "Vice President",
    "P_Knowledge_2": "Supreme Court",
    "P_Knowledge_3": "Two-thirds",
    "P_Knowledge_4": "Democratic",
    "P_Knowledge_5": "Republican",
    "ABC_News": 4,
    "Social_Media": 5,
    "News_1": "Television (2)",
    "News_frequency": "A few times a week",
    "Disinfo_threat": 8,
    "Disinfo_Res": "Social Media Companies"
}

    {if survey.collect_response(sample_response):
    print("Response collected successfully")
    else:
    print("Failed to collect response")

# Process and export results
survey.export_results()