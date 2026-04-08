import re
import pickle
import os
from collections import defaultdict, Counter
from typing import List, Dict, Tuple, Optional
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer

# Download NLTK data (only once)
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')

try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords')

try:
    nltk.data.find('corpora/wordnet')
except LookupError:
    nltk.download('wordnet')

class NLTKNLP:
    def __init__(self):
        self.lemmatizer = WordNetLemmatizer()
        self.stop_words = set(stopwords.words('english'))
        
        # Enhanced intent patterns
        self.intent_keywords = {
            'student_lookup': [
                'student', 'roll', 'number', 'find', 'search', 'lookup', 'show', 'get', 'details'
            ],
            'section_lookup': [
                'section', 'sec', 'students', 'class', 'batch', 'group', 'list'
            ],
            'subject_filter': [
                'subject', 'marks', 'score', 'grade', 'performance', 'results', 'analysis'
            ],
            'attendance': [
                'attendance', 'present', 'absent', 'percentage', 'classes', 'presentee'
            ],
            'toppers': [
                'top', 'highest', 'best', 'first', 'excellent', 'merit', 'rank', 'scorer'
            ],
            'backlogs': [
                'backlog', 'arrears', 'failed', 'supplementary', 'compartment', 'clear'
            ],
            'compare_sections': [
                'compare', 'versus', 'vs', 'against', 'better', 'worse', 'difference'
            ],
            'perfect_attendance': [
                'perfect', '100%', 'full', 'never', 'absent', 'always', 'present'
            ]
        }
        
        self.subjects = ['CN', 'SE', 'ADS', 'PDC', 'DBMS', 'OS', 'DS', 'ALGO', 'MATH', 'PHYSICS', 'CHEMISTRY']
        
        # Load trained model if exists
        self.load_trained_model()
    
    def load_trained_model(self, filename='chatbot_model.pkl'):
        """Load existing trained model"""
        if os.path.exists(filename):
            try:
                with open(filename, 'rb') as f:
                    model_data = pickle.load(f)
                    self.trained_keywords = model_data.get('intent_keywords', {})
                    self.confidence_scores = model_data.get('confidence_scores', {})
                print("✅ Trained model loaded with NLTK enhancement")
                return True
            except Exception as e:
                print(f"⚠️ Error loading trained model: {e}")
        
        self.trained_keywords = {}
        self.confidence_scores = {}
        return False
    
    def preprocess_text(self, text: str) -> List[str]:
        """Preprocess text with NLTK"""
        # Tokenize
        tokens = word_tokenize(text.lower())
        
        # Remove stopwords and lemmatize
        filtered_tokens = []
        for token in tokens:
            if token.isalpha() and token not in self.stop_words and len(token) > 2:
                lemmatized = self.lemmatizer.lemmatize(token)
                filtered_tokens.append(lemmatized)
        
        return filtered_tokens
    
    def calculate_intent_score(self, text: str, intent: str) -> float:
        """Calculate intent score using keyword matching and trained model"""
        preprocessed = self.preprocess_text(text)
        text_lower = text.lower()
        
        score = 0
        
        # Check trained keywords first
        if intent in self.trained_keywords:
            for keyword in self.trained_keywords[intent]:
                if keyword in text_lower:
                    score += 2  # Higher weight for trained keywords
        
        # Check general keywords
        if intent in self.intent_keywords:
            for keyword in self.intent_keywords[intent]:
                if keyword in text_lower:
                    score += 1
        
        # Boost score for exact phrase matches
        exact_phrases = {
            'student_lookup': ['roll number', 'find student', 'show me student'],
            'section_lookup': ['students in sec', 'section students', 'show section'],
            'subject_filter': ['subject marks', 'performance in', 'results of'],
            'attendance': ['attendance report', 'attendance percentage', 'show attendance'],
            'toppers': ['top students', 'highest scorers', 'best performers'],
            'backlogs': ['backlog report', 'students with backlogs', 'failed students'],
            'compare_sections': ['compare sec', 'sec vs sec', 'section comparison'],
            'perfect_attendance': ['perfect attendance', '100% attendance', 'full attendance']
        }
        
        if intent in exact_phrases:
            for phrase in exact_phrases[intent]:
                if phrase in text_lower:
                    score += 3
        
        # Apply confidence score
        confidence = self.confidence_scores.get(intent, 0.5)
        final_score = score * confidence
        
        return final_score
    
    def extract_entities(self, text: str) -> Dict[str, str]:
        """Extract entities using regex and patterns"""
        entities = {}
        text_lower = text.lower()
        
        # Roll number extraction (enhanced pattern)
        roll_patterns = [
            r'\b\d+[a-zA-Z]+\d*\b',  # Standard roll format
            r'roll\s*(?:number\s*)?[:\s]*([a-zA-Z0-9]+)',  # Roll: 231FA00001
            r'student\s*(?:id\s*)?[:\s]*([a-zA-Z0-9]+)'  # Student ID: format
        ]
        
        for pattern in roll_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                if match.groups():
                    entities['roll_number'] = match.group(1).upper()
                else:
                    entities['roll_number'] = match.group().upper()
                break
        
        # Section extraction
        section_patterns = [
            r'\bsec[-\s]?([a-zA-Z0-9]+)\b',
            r'section\s+([a-zA-Z0-9]+)',
            r'class\s+([a-zA-Z0-9]+)'
        ]
        
        sections = []
        for pattern in section_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            sections.extend([f"SEC-{sec.upper()}" for sec in matches])
        
        if sections:
            entities['sections'] = sections
        
        # Subject extraction
        for subject in self.subjects:
            if subject.lower() in text_lower:
                entities['subject'] = subject.upper()
                break
        
        # Number extraction with context
        number_patterns = [
            (r'top\s+(\d+)', 'top_n'),
            (r'first\s+(\d+)', 'top_n'),
            (r'highest\s+(\d+)', 'top_n'),
            (r'(\d+)%?\s*attendance', 'percentage'),
            (r'attendance\s+(?:below|above)\s+(\d+)', 'percentage'),
            (r'(\d+)\s+(?:backlog|arrears?)', 'backlog_count'),
            (r'semester\s+(\d+)', 'semester'),
            (r'batch\s+(\d+)', 'batch')
        ]
        
        for pattern, key in number_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                if key == 'percentage' or key == 'backlog_count':
                    entities[key] = int(match.group(1))
                else:
                    entities[key] = int(match.group(1))
        
        # Qualifier extraction
        qualifiers = {
            'high': ['high', 'above', 'excellent', 'good', 'best', 'top'],
            'low': ['low', 'below', 'poor', 'weak', 'bad', 'worst'],
            'average': ['average', 'medium', 'moderate', 'normal']
        }
        
        for qualifier, words in qualifiers.items():
            if any(word in text_lower for word in words):
                entities['qualifier'] = qualifier
                break
        
        return entities
    
    def detect_intent(self, text: str) -> Tuple[str, Optional[str], Optional[str], Optional[str], Optional[str], Optional[str], Optional[str]]:
        """Enhanced intent detection using NLTK"""
        text_lower = text.lower()
        
        # Calculate scores for all intents
        intent_scores = {}
        for intent in self.intent_keywords.keys():
            score = self.calculate_intent_score(text, intent)
            if score > 0:
                intent_scores[intent] = score
        
        # Find best intent
        if intent_scores:
            best_intent = max(intent_scores, key=intent_scores.get)
            confidence = intent_scores[best_intent]
            
            # Only return intent if confidence is above threshold
            if confidence > 0.3:
                entities = self.extract_entities(text)
                return (
                    best_intent,
                    entities.get('semester'),
                    entities.get('batch'),
                    entities.get('roll_number'),
                    entities.get('sections', [None])[0],  # First section
                    entities.get('subject'),
                    entities.get('qualifier')
                )
        
        return 'general', None, None, None, None, None, None
    
    def get_general_response(self, text: str) -> str:
        """Enhanced general responses"""
        text_lower = text.lower()
        
        # Greeting responses
        greetings = {
            r'\bhello\b': "Hello! I'm your enhanced DEO academic assistant. How can I help you today?",
            r'\bhi\b': "Hi! I can help you find student data, attendance reports, and academic performance.",
            r'\bhey\b': "Hey there! Ask me about students, sections, or subjects.",
            r'\bgood morning\b': "Good morning! Ready to help with academic data.",
            r'\bgood afternoon\b': "Good afternoon! How can I assist you today?",
            r'\bgood evening\b': "Good evening! What academic information do you need?"
        }
        
        for pattern, response in greetings.items():
            if re.search(pattern, text_lower):
                return response
        
        # Help responses
        help_patterns = [
            r'\bhelp\b',
            r'\bwhat can you do\b',
            r'\babilities\b',
            r'\bfeatures\b'
        ]
        
        if any(re.search(pattern, text_lower) for pattern in help_patterns):
            return """🚀 I can help you with:

📊 **Academic Reports:**
• Student information lookup
• Section-wise data analysis
• Subject performance metrics
• Attendance tracking

🎯 **Advanced Queries:**
• Top performer identification
• Backlog analysis
• Section comparisons
• Perfect attendance reports

💡 **Try asking:**
• "Show me student 231FA00001"
• "Top 5 students in CN subject"
• "Compare SEC-1 and SEC-2"
• "Students with low attendance"

I'm powered by NLTK for better understanding!"""
        
        # Thanks responses
        thanks_patterns = [
            r'\bthank\b',
            r'\bthanks\b',
            r'\bappreciate\b'
        ]
        
        if any(re.search(pattern, text_lower) for pattern in thanks_patterns):
            return "You're welcome! I'm here to help with any academic data you need."
        
        # Who are you
        if re.search(r'\bwho are you\b', text_lower):
            return "I'm an enhanced DEO chatbot powered by NLTK natural language processing. I can help you analyze student data, track attendance, and generate academic reports efficiently."
        
        # Bye responses
        bye_patterns = [
            r'\bbye\b',
            r'\bgoodbye\b',
            r'\bsee you\b'
        ]
        
        if any(re.search(pattern, text_lower) for pattern in bye_patterns):
            return "Goodbye! Feel free to come back anytime you need academic data assistance."
        
        # Default response
        return "I can help you with student data, attendance reports, and academic performance. Try asking about specific students, sections, or subjects, or say 'help' for more options."

# Global instance
nltk_nlp = NLTKNLP()

# Export functions for compatibility
def detect_intent(query):
    return nltk_nlp.detect_intent(query)

def get_general_response(query):
    return nltk_nlp.get_general_response(query)

def extract_second_section(query):
    entities = nltk_nlp.extract_entities(query)
    sections = entities.get('sections', [])
    return sections[1] if len(sections) > 1 else None

def extract_threshold(query):
    entities = nltk_nlp.extract_entities(query)
    return entities.get('percentage')

def extract_topn(query):
    entities = nltk_nlp.extract_entities(query)
    return entities.get('top_n', 5)
