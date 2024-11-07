from dataclasses import dataclass
from typing import List, Dict, Any, Optional, Union
import csv
import json
import statistics
from wsgiref import validate
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import logging
from datetime import datetime
import os

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
        """Export results with timestamp to PolyPsych/Data folder"""
        # Create timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Ensure the Data directory exists
        data_dir = os.path.join('PolyPsych', 'Data')
        os.makedirs(data_dir, exist_ok=True)
        
        # Create timestamped filename
        timestamped_filename = f"{filename}_{timestamp}"
        full_path = os.path.join(data_dir, timestamped_filename)
        
        results = self.process_responses()
        if format == 'csv':
            with open(f"{full_path}.csv", 'w', newline='') as csvfile:
                writer = csv.writer(csvfile)
                for question_id, data in results.items():
                    writer.writerow([question_id])
                    if isinstance(data, dict):
                        for option, count in data.items():
                            writer.writerow([option, count])
                    else:
                        writer.writerow([data])
        elif format == 'json':
            with open(f"{full_path}.json", 'w') as jsonfile:
                json.dump(results, jsonfile, indent=4)
        else:
            raise ValueError("Unsupported format. Please use 'csv' or 'json'.")

    def validate_response(self, response: Dict[str, Any]) -> bool:
        """Validate a complete survey response"""
        try:
            for block in self.blocks:
                for question in block.questions:
                    if question.question_id in response:
                        question.validate_response(response[question.question_id])
            return True
        except ValueError as e:
            logging.error(f"Response validation failed: {e}")
            return False
            
    def export_to_spss(self, filename: str) -> None:
        """Export responses to SPSS format with timestamp"""
        if not self.responses:
            raise ValueError("No responses to export")
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        data_dir = os.path.join('PolyPsych', 'Data')
        os.makedirs(data_dir, exist_ok=True)
        
        full_path = os.path.join(data_dir, f"{filename}_{timestamp}.sav")
        df = pd.DataFrame(self.responses)
        df.to_spss(full_path)
        
    def export_to_excel(self, filename: str) -> None:
        """Export responses to Excel with timestamp"""
        if not self.responses:
            raise ValueError("No responses to export")
            
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        data_dir = os.path.join('PolyPsych', 'Data')
        os.makedirs(data_dir, exist_ok=True)
        
        full_path = os.path.join(data_dir, f"{filename}_{timestamp}.xlsx")
        
        with pd.ExcelWriter(full_path) as writer:
            # Raw responses
            pd.DataFrame(self.responses).to_excel(writer, sheet_name='Raw Data')
            
            # Summary statistics
            analyzer = ResponseAnalyzer(self)
            summary_data = {}
            
            for block in self.blocks:
                for question in block.questions:
                    try:
                        summary_data[question.question_id] = analyzer.analyze_question(
                            question.question_id)
                    except Exception as e:
                        logging.warning(f"Could not analyze {question.question_id}: {e}")
                        
            pd.DataFrame(summary_data).to_excel(writer, sheet_name='Summary Statistics')

class ResponseAnalyzer:
    """Handles analysis of survey responses"""
    def __init__(self, survey_collector: SurveyCollector):
        self.survey = survey_collector
        self.df: Optional[pd.DataFrame] = None
        
    def create_dataframe(self) -> pd.DataFrame:
        """Convert responses to pandas DataFrame"""
        if not self.survey.responses:
            raise ValueError("No responses to analyze")
            
        self.df = pd.DataFrame(self.survey.responses)
        return self.df
    
    def analyze_question(self, question_id: str) -> Dict[str, Any]:
        """Analyze responses for a specific question"""
        if self.df is None:
            self.create_dataframe()
            
        if question_id not in self.df.columns:
            raise ValueError(f"Question {question_id} not found in responses")
            
        series = self.df[question_id]
        
        # Get question type from survey
        question = self._find_question(question_id)
        
        if question.question_type == 'likert_scale':
            return self._analyze_likert(series)
        elif question.question_type == 'multiple_choice':
            return self._analyze_categorical(series)
        elif question.question_type == 'scale':
            return self._analyze_numerical(series)
        else:
            return self._analyze_text(series)
            
    def _analyze_likert(self, series: pd.Series) -> Dict[str, Any]:
        """Analyze Likert scale responses"""
        return {
            'mean': series.mean(),
            'median': series.median(),
            'mode': series.mode().iloc[0],
            'distribution': series.value_counts().to_dict(),
            'std': series.std()
        }
        
    def _analyze_categorical(self, series: pd.Series) -> Dict[str, Any]:
        """Analyze categorical/multiple choice responses"""
        counts = series.value_counts()
        percentages = series.value_counts(normalize=True) * 100
        return {
            'counts': counts.to_dict(),
            'percentages': percentages.to_dict(),
            'mode': counts.index[0]
        }
        
    def plot_question(self, question_id: str, plot_type: str = 'auto', 
                     title: Optional[str] = None, **kwargs) -> None:
        """Create visualization for question responses"""
        if self.df is None:
            self.create_dataframe()
            
        question = self._find_question(question_id)
        data = self.df[question_id]
        
        plt.figure(figsize=(10, 6))
        
        if plot_type == 'auto':
            if question.question_type in ['likert_scale', 'scale']:
                sns.histplot(data=data, **kwargs)
            else:
                sns.countplot(data=data, **kwargs)
                
        plt.title(title or f'Responses for {question_id}')
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.show()

    def _find_question(self, question_id: str) -> 'Question':
        """Find a question by its ID across all blocks"""
        for block in self.survey.blocks:
            for question in block.questions:
                if question.question_id == question_id:
                    return question
        raise ValueError(f"Question {question_id} not found")

    def _analyze_numerical(self, series: pd.Series) -> Dict[str, Any]:
        """Analyze numerical responses"""
        return {
            'mean': series.mean(),
            'median': series.median(),
            'std': series.std(),
            'min': series.min(),
            'max': series.max(),
            'count': len(series)
        }

    def _analyze_text(self, series: pd.Series) -> Dict[str, Any]:
        """Analyze text responses"""
        # Count number of responses
        response_count = series.count()
        # Get unique responses
        unique_responses = series.unique().tolist()
        # Calculate average response length
        avg_length = series.str.len().mean()
        
        return {
            'response_count': response_count,
            'unique_responses': len(unique_responses),
            'avg_length': avg_length,
            'sample_responses': unique_responses[:5]  # Show first 5 unique responses
        }

    def analyze_text_responses(self, question_id: str) -> Dict[str, Any]:
        """Analyze open-ended text responses"""
        if self.df is None:
            self.create_dataframe()
            
        if question_id not in self.df.columns:
            raise ValueError(f"Question {question_id} not found in responses")
            
        return self._analyze_text(self.df[question_id])

    def calculate_correlations(self, question_ids: List[str]) -> pd.DataFrame:
        """Calculate correlations between specified questions"""
        if self.df is None:
            self.create_dataframe()
            
        # Filter numeric columns only
        numeric_data = self.df[question_ids].apply(pd.to_numeric, errors='coerce')
        
        return numeric_data.corr()

@dataclass
class Block:
    block_id: str
    title: str
    questions: List['Question'] = None

    def __init__(self, block_id: str, title: str):
        self.block_id = block_id
        self.title = title
        self.questions = []

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
demographics = Block("Demographics", "Demographics")
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
demographics_political = Block("Demographics Political", "Political Views and Affiliation")
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
personal_political = Block("Personal Political Characteristics", "Political Efficacy and Participation")
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
perception_news = Block("Perception of News Sources", "Perception of Political Information on Social Media")
# Add all the news sources as individual questions here. For brevity, only one example is shown:
perception_news.add_question(Question("ABC_News", "ABC News", "likert_scale", 
                                      ["1 (Definitely not)", "2 (Probably not)", "3 (Might or might not be)", "4 (Probably is)", "5 (Definitely is)"]))

# Social Media Block
social_media = Block("Perception of Political Information on Social Media", "Media Consumption Questions")
social_media.add_question(Question("Social_Media", "Social media as a source of political information and news is...", "likert_scale", 
                                   ["Does not apply at all (1)", "2", "3", "4", "5", "6", "Fully Applies (7)"]))

# Media Consumption Block
media_consumption = Block("Media Consumption Questions", "Misinformation Threat")
media_consumption.add_question(Question("News_1", "Where do you typically get your news?", "multiple_choice", 
                                        ["Print newspapers (1)", "Television (2)", "News websites (3)", "Social media (4)", "Radio (5)", "Podcasts (6)"]))
media_consumption.add_question(Question("News_frequency", "How often do you consume news?", "multiple_choice", 
                                       ["Daily", "A few times a week", "Once a week", "A few times a month", "Rarely", "Never"]))

# Misinformation Threat Block
misinformation_threat = Block("Mis_Threat", "Voting Behavior")
misinformation_threat.add_question(Question("Disinfo_threat", "On the scale from 0 to 10, where 0 means no risk and 10 means extreme risk, how would you rate the risk of disinformation campaigns to each of the following?", "scale", 
                                            ["0 (No risk)", "1", "2", "3", "4", "5", "6", "7", "8", "9", "10 (Extreme risk)"]))
misinformation_threat.add_question(Question("Disinfo_Res", "In your opinion, who is primarily responsible for combating disinformation?", "multiple_choice", 
                                            ["Government", "Social Media Companies", "Educational Institutions", "News Outlets", "Individuals", "Other (Please specify)"]))

# Voting Behavior Block
voting_behavior = Block("Voting Behavior", "Trust in Government")
voting_behavior.add_question(Question("Voted_2020", "Did you vote in the 2020 Presidential Election?", "multiple_choice", 
                                    ["Yes (1)", "No (2)"]))
voting_behavior.add_question(Question("Vote_Choice", "If you voted in the 2020 Presidential Election, which candidate did you vote for?", "multiple_choice", 
                                    ["Joe Biden (1)", "Donald Trump (2)", "Another Candidate (3)", "Did not vote (4)"]))
voting_behavior.add_question(Question("Voting_Motivation", "What were the main factors that influenced your decision to vote or not vote in the 2020 election?", "multiple_choice", 
                                    ["Candidate policy positions (1)", "Candidate character (2)", "Party affiliation (3)", 
                                     "Desire to influence election outcome (4)", "Civic duty (5)", "Social pressure (6)",
                                     "Availability of time (7)", "Voter suppression concerns (8)", 
                                     "Lack of trust in the electoral process (9)", "Other (10)"]))

# Adding blocks to survey
survey = SurveyCollector("PSY_492", "Election Experience Survey")
survey.add_block(demographics)
survey.add_block(demographics_political)
survey.add_block(personal_political)
survey.add_block(perception_news)
survey.add_block(social_media)
survey.add_block(media_consumption)
survey.add_block(misinformation_threat)
survey.add_block(voting_behavior)

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

if survey.collect_response(sample_response):
    print("Response collected successfully")
else:
    print("Failed to collect response")

# Process and export results
survey.export_results()

print("Here is the continuation of the **PSY 492 Election Experience Survey**:")

print("**Start of Block: Voting Behavior**")

print("Voted_2020 Did you vote in the 2020 Presidential Election?")

print("- Yes (1)")
print("- No (2)")

print("Vote_Choice If you voted in the 2020 Presidential Election, which candidate did you vote for?")

print("- Joe Biden (1)")
print("- Donald Trump (2)")
print("- Another Candidate (3) ______________________________________________________________")
print("- Did not vote (4)")

print("Voting_Motivation What were the main factors that influenced your decision to vote or not vote in the 2020 election? (Check all that apply)")

print("Voting_Motivation What were the main factors that influenced your decision to vote or not vote in the 2020 election? (Check all that apply)")
print("- [ ] Candidate policy positions (1)")
print("- [ ] validate character (2)")
print("- [ ] Party affiliation (3)")
print("- [ ] Desire to influence election outcome (4)")
print("- [ ] Civic duty (5)")
print("- [ ] Social pressure (6)")
print("- [ ] Availability of time (7)")
print("- [ ] Voter suppression concerns (8)")
print("- [ ] Lack of trust in the electoral process (9)")
print("- [ ] Other (10) ______________________________________________________________")

print("Election_Outcome How satisfied were you with the outcome of the 2020 Presidential Election?")
print("- Extremely dissatisfied (1)")
print("- Somewhat dissatisfied (2)")
print("- Neither satisfied nor dissatisfied (3)")
print("- Somewhat satisfied (4)")
print("- Extremely satisfied (5)")

print("Voting_2024 If you plan to vote in the upcoming 2024 election, what issues will be most important to you when deciding whom to vote for? (Please list in order of importance)")
print("1. ______________________________________________________________")
print("2. ______________________________________________________________")
print("3. ______________________________________________________________")

print("**End of Block: Voting Behavior**")

print("**Start of Block: Political Efficacy and Participation**")

print("Political_Efficacy On a scale from 1 to 7, where 1 means 'Not at all effective' and 7 means 'Extremely effective,' how effective do you feel your vote is in influencing political change?")
print("- 1 (Not at all effective) (1)")
print("- 2 (2)")
print("- 3 (3)")
print("- 4 (4)")
print("- 5 (5)")
print("- 6 (6)")
print("- 7 (Extremely effective) (7)")

print("Political_Activism Have you engaged in any of the following political activities in the last 12 months? (Check all that apply)")
print("- [ ] Attended a political rally or protest (1)")
print("- [ ] Volunteered for a political campaign (2)")
print("- [ ] Made political donations (3)")
print("- [ ] Contacted a public official (4)")
print("- [ ] Signed a political petition (5)")
print("- [ ] Discussed politics with friends or family (6)")
print("- [ ] None of the above (7)")

print("Volunteer_Why If you have volunteered for a political campaign or cause, what motivated you to do so?")
print("- ______________________________________________________________")

print("**End of Block: Political Efficacy and Participation**")

print("**Start of Block: Trust in Government**")

print("Trust_Government Please rate your level of trust in the following government institutions on a scale from 1 (No trust at all) to 5 (Complete trust):")
print("- Executive branch (President and administration)")
print("  - 1 (1)")
print("  - 2 (2)")
print("  - 3 (3)")
print("  - 4 (4)")
print("  - 5 (Complete trust) (5)")

print("- Legislative branch (Congress)")
print("  - 1 (1)")
print("  - 2 (2)")
print("  - 3 (3)")
print("  - 4 (4)")
print("  - 5 (Complete trust) (5)")

print("- Judicial branch (Courts)")
print("  - 1 (1)")
print("  - 2 (2)")
print("  - 3 (3)")
print("  - 4 (4)")
print("  - 5 (Complete trust) (5)")

print("- Local government")
print("  - 1 (1)")
print("  - 2 (2)")
print("  - 3 (3)")
print("  - 4 (4)")
print("  - 5 (Complete trust) (5)")

print("Trust_Loss What, if anything, would increase your trust in the government?")
print("- ______________________________________________________________")

print("**End of Block: Trust in Government**")

print("**Start of Block: Closing**")

print("Feedback Is there anything else you would like to share about your political views, experiences, or any suggestions for this survey?")
print("- ______________________________________________________________")

print("Thank you for participating in the PSY 492 Election Experience Survey. Your responses will contribute to valuable research on political behavior and media influence.")

print("**End of Block: Closing**")

def run_analysis():
    try:
        # Create survey collector
        survey = SurveyCollector("PSY_492", "Election Experience Survey")
        
        # Create and populate blocks
        demographics = Block("demographics", "Demographics")
        political_block = Block("political_views", "Political Views and Affiliation")
        efficacy_block = Block("efficacy", "Political Efficacy and Participation") 
        trust_block = Block("trust", "Trust in Government")
        closing_block = Block("closing", "Closing")
        
        # Add questions to blocks (add your existing questions here)
        # ...
        
        # Add blocks to survey
        for block in [demographics, political_block, efficacy_block, trust_block, closing_block]:
            survey.add_block(block)
        
        # Add sample response for testing
        sample_response = {
            "Age": "23",
            "Political_Views": 4,
            "Party_Affiliation": "Democrat (2)",
            "Trust_Government": 3,
            # Add other fields as needed
        }
        survey.collect_response(sample_response)
        
        # Create analyzer and run analysis
        analyzer = ResponseAnalyzer(survey)
        
        # Run your analyses
        try:
            political_views = analyzer.analyze_question("Political_Views")
            print("\nPolitical Views Analysis:")
            print(political_views)
        except Exception as e:
            logging.error(f"Error analyzing Political Views: {e}")
        
        # Export results
        try:
            survey.export_to_excel("survey_results.xlsx")
            print("\nResults exported successfully")
        except Exception as e:
            logging.error(f"Error exporting results: {e}")
            
    except Exception as e:
        logging.error(f"Analysis failed: {e}")
        raise

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run_analysis()
