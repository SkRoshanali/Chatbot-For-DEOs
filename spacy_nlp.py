import spacy
import re
import pickle
import os
from collections import defaultdict
from typing import List, Dict, Tuple, Optional

# Load spaCy model (free English model)
try:
    nlp = spacy.load("en_core_web_sm")
    print("✅ spaCy model loaded successfully")
except OSError:
    print("⚠️ spaCy model not found. Install with: python -m spacy download en_core_web_sm")
    nlp = None

class SpacyNLP:
    def __init__(self):
        self.intent_patterns = {
            'student_lookup': [
                r'student\s+(?:with\s+)?roll\s+(?:number\s+)?([a-zA-Z0-9]+)',
                r'roll\s*(?:number\s*)?([a-zA-Z0-9]+)',
                r'find\s+(?:student\s+)?([a-zA-Z0-9]+)',
                r'show\s+me\s+([a-zA-Z0-9]+)'
            ],
            'section_lookup': [
                r'students?\s+(?:in\s+)?sec[-\s]?([a-zA-Z0-9]+)',
                r'section\s+([a-zA-Z0-9]+)',
                r'who\s+(?:is\s+)?in\s+sec[-\s]?([a-zA-Z0-9]+)'
            ],
            'subject_filter': [
                r'(?:subject|marks|score|grade)\s+(?:in\s+)?([a-zA-Z]+)',
                r'([a-zA-Z]+)\s+(?:subject|marks|results?)',
                r'performance\s+in\s+([a-zA-Z]+)'
            ],
            'attendance': [
                r'attendance\s+(?:report|percentage|status)',
                r'(?:students?\s+)?with\s+(?:low|poor)\s+attendance',
                r'attendance\s+(?:below|above)\s+(\d+)',
                r'(\d+)%?\s+attendance'
            ],
            'toppers': [
                r'top\s+(\d+)\s+(?:students?|people)',
                r'(?:highest|best)\s+(?:scorers?|performers?)',
                r'topper?s?\s+(?:in\s+)?([a-zA-Z0-9]+)',
                r'first\s+(\d+)\s+students?'
            ],
            'backlogs': [
                r'students?\s+(?:with\s+)?backlogs?',
                r'(?:who\s+)?has\s+(?:arrears?|failed)',
                r'backlog\s+(?:report|count)',
                r'(\d+)\s+(?:backlogs?|arrears?)'
            ],
            'compare_sections': [
                r'compare\s+sec[-\s]?([a-zA-Z0-9]+)\s+(?:and|vs|versus)\s+sec[-\s]?([a-zA-Z0-9]+)',
                r'sec[-\s]?([a-zA-Z0-9]+)\s+(?:vs|versus|compared\s+to)\s+sec[-\s]?([a-zA-Z0-9]+)'
            ],
            'perfect_attendance': [
                r'perfect\s+attendance',
                r'100%\s+attendance',
                r'full\s+attendance',
                r'never\s+absent'
            ]
        }
        
        self.subjects = ['CN', 'SE', 'ADS', 'PDC', 'DBMS', 'OS', 'DS', 'ALGO', 'MATH', 'PHYSICS', 'CHEMISTRY', 'BIOLOGY']
        
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
                print("✅ Trained model loaded")
                return True
            except Exception as e:
                print(f"⚠️ Error loading trained model: {e}")
        
        self.trained_keywords = {}
        self.confidence_scores = {}
        return False
    
    def extract_entities(self, text: str) -> Dict[str, str]:
        """Extract entities using spaCy NER and patterns"""
        entities = {}
        
        if not nlp:
            return entities
        
        doc = nlp(text)
        
        # Extract named entities
        for ent in doc.ents:
            if ent.label_ == 'PERSON':
                entities['person'] = ent.text
            elif ent.label_ == 'ORG':
                entities['organization'] = ent.text
            elif ent.label_ == 'CARDINAL':
                entities['number'] = ent.text
        
        # Extract roll numbers
        roll_pattern = r'\b\d+[a-zA-Z]+\d*\b'
        roll_match = re.search(roll_pattern, text, re.IGNORECASE)
        if roll_match:
            entities['roll_number'] = roll_match.group().upper()
        
        # Extract sections
        section_pattern = r'\bsec[-\s]?([a-zA-Z0-9]+)\b'
        section_matches = re.findall(section_pattern, text, re.IGNORECASE)
        if section_matches:
            entities['sections'] = [f"SEC-{sec.upper()}" for sec in section_matches]
        
        # Extract subjects
        for subject in self.subjects:
            if subject.lower() in text.lower():
                entities['subject'] = subject.upper()
                break
        
        # Extract numbers with context
        number_pattern = r'(\d+(?:\.\d+)?)'
        numbers = re.findall(number_pattern, text)
        if numbers:
            if 'top' in text.lower() or 'highest' in text.lower():
                entities['top_n'] = int(numbers[0])
            elif 'attendance' in text.lower() or '%' in text:
                entities['percentage'] = float(numbers[0])
            elif 'backlog' in text.lower():
                entities['backlog_count'] = int(numbers[0])
        
        return entities
    
    def detect_intent(self, text: str) -> Tuple[str, Optional[str], Optional[str], Optional[str], Optional[str], Optional[str], Optional[str]]:
        """Detect intent using spaCy and patterns"""
        text_lower = text.lower()
        
        # Check trained model first
        if self.trained_keywords:
            for intent, keywords in self.trained_keywords.items():
                score = 0
                for keyword in keywords:
                    if keyword in text_lower:
                        score += 1
                
                if score > 0:
                    confidence = self.confidence_scores.get(intent, 0.5)
                    if score * confidence > 0.5:
                        return intent, None, None, None, None, None, None
        
        # Use pattern matching
        best_intent = 'general'
        best_score = 0
        
        for intent, patterns in self.intent_patterns.items():
            for pattern in patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    score = len(match.groups()) + 1
                    if score > best_score:
                        best_score = score
                        best_intent = intent
        
        # Extract entities for the detected intent
        entities = self.extract_entities(text)
        
        # Return structured response
        return (
            best_intent,
            entities.get('semester'),
            entities.get('batch'),
            entities.get('roll_number'),
            entities.get('sections', [None])[0],  # First section
            entities.get('subject'),
            entities.get('qualifier')
        )
    
    def get_general_response(self, text: str) -> str:
        """Generate contextual responses"""
        text_lower = text.lower()
        
        # Contextual responses using spaCy
        if nlp:
            doc = nlp(text)
            
            # Check for greetings
            greetings = ['hello', 'hi', 'hey', 'good morning', 'good afternoon', 'good evening']
            for greeting in greetings:
                if greeting in text_lower:
                    return f"{greeting.title()}! I'm your DEO academic assistant. How can I help you today?"
            
            # Check for thanks
            thanks = ['thank', 'thanks', 'appreciate', 'helpful']
            if any(thank in text_lower for thank in thanks):
                return "You're welcome! Feel free to ask if you need more assistance."
            
            # Check for help requests
            help_words = ['help', 'what can you do', 'abilities', 'features']
            if any(help_word in text_lower for help_word in help_words):
                return """I can help you with:
• Student information lookup
• Section-wise data
• Subject performance analysis
• Attendance reports
• Top performer identification
• Backlog analysis
• Section comparisons

Try asking about specific students, sections, or subjects!"""
        
        # Fallback responses
        return "I'm here to help with academic data. Please ask about students, sections, subjects, or attendance."

# Global instance
spacy_nlp = SpacyNLP()

# Export functions for compatibility
def detect_intent(query):
    return spacy_nlp.detect_intent(query)

def get_general_response(query):
    return spacy_nlp.get_general_response(query)

def extract_second_section(query):
    entities = spacy_nlp.extract_entities(query)
    sections = entities.get('sections', [])
    return sections[1] if len(sections) > 1 else None

def extract_threshold(query):
    entities = spacy_nlp.extract_entities(query)
    return entities.get('percentage')

def extract_topn(query):
    entities = spacy_nlp.extract_entities(query)
    return entities.get('top_n', 5)
