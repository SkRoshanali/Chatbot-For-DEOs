import re
import pickle
import os
from collections import defaultdict

class EnhancedNLP:
    def __init__(self):
        self.model_loaded = False
        self.model_data = {
            'intent_keywords': defaultdict(list),
            'entity_patterns': defaultdict(list),
            'response_templates': defaultdict(list),
            'confidence_scores': defaultdict(float)
        }
        self.load_model()
    
    def load_model(self, filename='chatbot_model.pkl'):
        """Load trained model"""
        if os.path.exists(filename):
            try:
                with open(filename, 'rb') as f:
                    model_data = pickle.load(f)
                    self.model_data = {
                        'intent_keywords': defaultdict(list, model_data.get('intent_keywords', {})),
                        'entity_patterns': defaultdict(list, model_data.get('entity_patterns', {})),
                        'response_templates': defaultdict(list, model_data.get('response_templates', {})),
                        'confidence_scores': defaultdict(float, model_data.get('confidence_scores', {}))
                    }
                self.model_loaded = True
                print(f"📂 Enhanced NLP model loaded from {filename}")
                return True
            except Exception as e:
                print(f"❌ Error loading model: {e}")
        
        print("⚠️ No trained model found, using fallback logic")
        return False
    
    def detect_intent(self, query):
        """Enhanced intent detection using trained model"""
        if self.model_loaded:
            return self._predict_with_model(query)
        else:
            return self._fallback_detection(query)
    
    def _predict_with_model(self, query):
        """Predict intent using trained model"""
        query_lower = query.lower()
        scores = {}
        
        # Score based on keyword matching
        for intent, keywords in self.model_data['intent_keywords'].items():
            score = 0
            matched_keywords = []
            
            for keyword in keywords:
                if keyword in query_lower:
                    score += 1
                    matched_keywords.append(keyword)
            
            # Apply confidence score
            confidence = self.model_data['confidence_scores'][intent]
            final_score = score * confidence
            
            if score > 0:
                scores[intent] = {
                    'score': final_score,
                    'matched_keywords': matched_keywords,
                    'confidence': confidence
                }
        
        # Extract entities
        entities = self._extract_entities(query_lower)
        
        # Return best intent
        if scores:
            best_intent = max(scores, key=lambda x: scores[x]['score'])
            return (
                best_intent,
                entities.get('semester'),
                entities.get('batch'),
                entities.get('roll_number'),
                entities.get('section'),
                entities.get('subject'),
                entities.get('qualifier')
            )
        
        return 'general', None, None, None, None, None, None
    
    def _fallback_detection(self, query):
        """Fallback simple keyword detection"""
        query_lower = query.lower()
        
        intents = {
            'student_lookup': ['roll number', 'student', 'roll'],
            'section_lookup': ['section', 'sec-', 'section students'],
            'subject_filter': ['subject', 'marks', 'score', 'grade'],
            'attendance': ['attendance', 'present', 'absent'],
            'toppers': ['top', 'highest', 'best', 'topper'],
            'backlogs': ['backlog', 'failed', 'arrear'],
            'general': ['hello', 'hi', 'help', 'who are you']
        }
        
        for intent, keywords in intents.items():
            if any(keyword in query_lower for keyword in keywords):
                return intent, None, None, None, None, None, None
        
        return 'general', None, None, None, None, None, None
    
    def _extract_entities(self, query):
        """Extract entities from query"""
        entities = {}
        
        # Roll number extraction
        roll_pattern = r'\b\d+[a-zA-Z]+\d*\b'
        roll_match = re.search(roll_pattern, query, re.IGNORECASE)
        if roll_match:
            entities['roll_number'] = roll_match.group().upper()
        
        # Section extraction
        section_pattern = r'\bsec[-\s]?(\d+|[a-zA-Z]+)\b'
        section_match = re.search(section_pattern, query, re.IGNORECASE)
        if section_match:
            entities['section'] = f"SEC-{section_match.group(1).upper()}"
        
        # Subject extraction
        subjects = ['CN', 'SE', 'ADS', 'PDC', 'DBMS', 'OS', 'DS', 'ALGO', 'MATH', 'PHYSICS', 'CHEMISTRY']
        for subject in subjects:
            if subject.lower() in query.lower():
                entities['subject'] = subject.upper()
                break
        
        # Number extraction
        number_pattern = r'\b(\d+)\b'
        number_match = re.search(number_pattern, query)
        if number_match:
            num = int(number_match.group(1))
            if 'top' in query.lower():
                entities['top_n'] = num
            elif 'attendance' in query.lower() or '%' in query:
                entities['threshold'] = num
        
        return entities
    
    def get_general_response(self, query):
        """Enhanced general responses"""
        if self.model_loaded and 'general' in self.model_data['response_templates']:
            responses = self.model_data['response_templates']['general']
            if responses:
                return responses[0]  # Return first response for simplicity
        
        # Fallback responses
        responses = {
            'hello': 'Hello! How can I help you with student data?',
            'hi': 'Hi! Ask me about student information, attendance, or reports.',
            'help': 'I can help you find student data, attendance reports, and academic performance. Try asking about specific students, sections, or subjects.',
            'who are you': 'I am a DEO Chatbot for academic data management.',
            'bye': 'Goodbye! Feel free to ask if you need more help.',
            'thanks': 'You\'re welcome! Is there anything else I can help you with?'
        }
        
        query_lower = query.lower()
        for key, response in responses.items():
            if key in query_lower:
                return response
        
        return 'I can help you with student data, attendance, and academic reports. Please ask a specific question.'
    
    def extract_second_section(self, query):
        """Extract second section for comparison"""
        section_pattern = r'\bsec[-\s]?(\d+|[a-zA-Z]+)\b'
        sections = re.findall(section_pattern, query, re.IGNORECASE)
        if len(sections) >= 2:
            return f"SEC-{sections[1].upper()}"
        return None
    
    def extract_threshold(self, query):
        """Extract threshold from query"""
        # Look for percentage or number thresholds
        patterns = [
            r'(\d+\.?\d*)%?\s*(?:above|below|greater|less|over|under)',
            r'(?:above|below|greater|less|over|under)\s*(\d+\.?\d*)%?',
            r'(\d+\.?\d*)\s*(?:percent|percentage)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                return float(match.group(1))
        
        return None
    
    def extract_topn(self, query):
        """Extract top N from query"""
        patterns = [
            r'top\s+(\d+)',
            r'first\s+(\d+)',
            r'best\s+(\d+)',
            r'highest\s+(\d+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                return int(match.group(1))
        
        return 5  # Default to 5

# Global instance
enhanced_nlp = EnhancedNLP()

# Export functions for compatibility
def detect_intent(query):
    return enhanced_nlp.detect_intent(query)

def get_general_response(query):
    return enhanced_nlp.get_general_response(query)

def extract_second_section(query):
    return enhanced_nlp.extract_second_section(query)

def extract_threshold(query):
    return enhanced_nlp.extract_threshold(query)

def extract_topn(query):
    return enhanced_nlp.extract_topn()
