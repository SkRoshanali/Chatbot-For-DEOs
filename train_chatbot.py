import json
import re
import pickle
from collections import defaultdict, Counter
import os

class ChatbotTrainer:
    def __init__(self):
        self.training_data = {
            'intents': defaultdict(list),
            'entities': defaultdict(list),
            'responses': defaultdict(list),
            'patterns': defaultdict(list)
        }
        self.model_data = {
            'intent_keywords': defaultdict(list),
            'entity_patterns': defaultdict(list),
            'response_templates': defaultdict(list),
            'confidence_scores': defaultdict(float)
        }
    
    def add_training_example(self, query, intent, entities=None, response=None):
        """Add a training example"""
        query_lower = query.lower().strip()
        
        # Add to training data
        self.training_data['intents'][intent].append(query_lower)
        if entities:
            for entity_type, entity_value in entities.items():
                self.training_data['entities'][entity_type].append(entity_value)
        if response:
            self.training_data['responses'][intent].append(response)
        
        # Extract keywords and patterns
        self._extract_keywords(query_lower, intent)
        self._extract_patterns(query_lower, intent)
    
    def _extract_keywords(self, query, intent):
        """Extract keywords from query"""
        # Remove common stop words
        stop_words = {'the', 'is', 'at', 'which', 'on', 'a', 'an', 'and', 'or', 'but', 'in', 'with', 'to', 'for', 'of', 'as', 'by', 'that', 'this', 'it', 'from', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'must', 'can', 'shall'}
        
        words = re.findall(r'\b\w+\b', query)
        keywords = [word for word in words if word not in stop_words and len(word) > 2]
        
        for keyword in keywords:
            if keyword not in self.model_data['intent_keywords'][intent]:
                self.model_data['intent_keywords'][intent].append(keyword)
    
    def _extract_patterns(self, query, intent):
        """Extract patterns from query"""
        # Common patterns for academic queries
        patterns = {
            'roll_pattern': r'\b\d+[a-zA-Z]+\d*\b|\broll\s+(?:no|number)?\s*[:\s]*\w+',
            'section_pattern': r'\bsec[-\s]?(\d+|[a-zA-Z]+)\b|\bsection\s+(\w+)',
            'subject_pattern': r'\b(CN|SE|ADS|PDC|DBMS|OS|DS|ALGO|MATH|PHYSICS|CHEMISTRY)\b',
            'percentage_pattern': r'\b\d+\.?\d*%?\b',
            'number_pattern': r'\b\d+\b',
            'grade_pattern': r'\b[ABCDF][+-]?\b',
            'comparison_pattern': r'\b(compare|vs|versus|than|better|worse)\b',
            'top_pattern': r'\b(top\s+\d+|highest|best|first|second|third)\b',
            'low_pattern': r'\b(low|lowest|worst|bottom|failed|backlog)\b'
        }
        
        for pattern_name, pattern in patterns.items():
            if re.search(pattern, query, re.IGNORECASE):
                if pattern_name not in self.model_data['entity_patterns'][intent]:
                    self.model_data['entity_patterns'][intent].append(pattern_name)
    
    def load_default_training_data(self):
        """Load default academic chatbot training data"""
        
        # Student lookup examples
        student_queries = [
            "show me student with roll number 231FA00001",
            "find student 231FA00001",
            "details of roll 231FA00001",
            "who is student 231FA00001",
            "get information about 231FA00001"
        ]
        for query in student_queries:
            self.add_training_example(query, 'student_lookup', 
                                 {'roll_number': '231FA00001'}, 
                                 "Student found: Roll 231FA00001")
        
        # Section lookup examples
        section_queries = [
            "show students in SEC-1",
            "list all students from section 1",
            "who are in SEC-A",
            "students of SEC-2",
            "get me students from SEC-3"
        ]
        for query in section_queries:
            self.add_training_example(query, 'section_lookup',
                                 {'section': 'SEC-1'},
                                 "Showing students from section")
        
        # Subject queries
        subject_queries = [
            "show me CN subject results",
            "who scored high in Software Engineering",
            "SE subject performance",
            "ADS marks analysis",
            "PDC subject report",
            "database management system results"
        ]
        for query in subject_queries:
            self.add_training_example(query, 'subject_filter',
                                 {'subject': 'CN'},
                                 "Subject analysis results")
        
        # Attendance queries
        attendance_queries = [
            "show attendance report",
            "students with low attendance",
            "who has below 75% attendance",
            "attendance percentage",
            "present students list"
        ]
        for query in attendance_queries:
            self.add_training_example(query, 'attendance',
                                 {'threshold': 75},
                                 "Attendance report generated")
        
        # Topper queries
        topper_queries = [
            "show me toppers in SEC-1",
            "who are the top 5 students",
            "highest scorers in CN",
            "best performing students",
            "top 10 in academics"
        ]
        for query in topper_queries:
            self.add_training_example(query, 'toppers',
                                 {'top_n': 5},
                                 "Topper list generated")
        
        # Backlog queries
        backlog_queries = [
            "students with backlogs",
            "who has arrears",
            "failed students list",
            "backlog report",
            "students with failed subjects"
        ]
        for query in backlog_queries:
            self.add_training_example(query, 'backlogs',
                                 {'backlog_count': 2},
                                 "Backlog report generated")
        
        # General queries
        general_queries = [
            ("hello", "Hello! How can I help you with student data?"),
            ("hi there", "Hi! Ask me about student information, attendance, or reports."),
            ("what can you do", "I can help you find student data, attendance reports, and academic performance. Try asking about specific students, sections, or subjects."),
            ("help me", "I can help you with student data, attendance, and academic reports. Please ask a specific question."),
            ("who are you", "I am a DEO Chatbot for academic data management."),
            ("bye", "Goodbye! Feel free to ask if you need more help.")
        ]
        
        for query, response in general_queries:
            self.add_training_example(query, 'general', {}, response)
    
    def train_model(self):
        """Train the model based on collected data"""
        print("🤖 Training chatbot model...")
        
        # Calculate confidence scores based on keyword frequency
        for intent, keywords in self.model_data['intent_keywords'].items():
            keyword_count = len(keywords)
            example_count = len(self.training_data['intents'][intent])
            confidence = min(1.0, (keyword_count * 0.3 + example_count * 0.7) / 20)
            self.model_data['confidence_scores'][intent] = confidence
        
        print(f"✅ Trained {len(self.model_data['intent_keywords'])} intents")
        for intent, confidence in self.model_data['confidence_scores'].items():
            print(f"   - {intent}: {confidence:.2f} confidence")
    
    def save_model(self, filename='chatbot_model.pkl'):
        """Save the trained model"""
        model_data = {
            'intent_keywords': dict(self.model_data['intent_keywords']),
            'entity_patterns': dict(self.model_data['entity_patterns']),
            'response_templates': dict(self.model_data['response_templates']),
            'confidence_scores': dict(self.model_data['confidence_scores'])
        }
        
        with open(filename, 'wb') as f:
            pickle.dump(model_data, f)
        
        print(f"💾 Model saved to {filename}")
    
    def load_model(self, filename='chatbot_model.pkl'):
        """Load a trained model"""
        if os.path.exists(filename):
            with open(filename, 'rb') as f:
                model_data = pickle.load(f)
                self.model_data = {
                    'intent_keywords': defaultdict(list, model_data['intent_keywords']),
                    'entity_patterns': defaultdict(list, model_data['entity_patterns']),
                    'response_templates': defaultdict(list, model_data['response_templates']),
                    'confidence_scores': defaultdict(float, model_data['confidence_scores'])
                }
            print(f"📂 Model loaded from {filename}")
            return True
        return False
    
    def predict_intent(self, query):
        """Predict intent for a given query"""
        query_lower = query.lower()
        scores = {}
        
        # Score based on keyword matching
        for intent, keywords in self.model_data['intent_keywords'].items():
            score = 0
            for keyword in keywords:
                if keyword in query_lower:
                    score += 1
            
            # Apply confidence score
            confidence = self.model_data['confidence_scores'][intent]
            final_score = score * confidence
            scores[intent] = final_score
        
        # Return best intent
        if scores:
            best_intent = max(scores, key=scores.get)
            if scores[best_intent] > 0:
                return best_intent, scores[best_intent]
        
        return 'general', 0.0
    
    def add_custom_training(self, training_file='custom_training.json'):
        """Add custom training from JSON file"""
        if os.path.exists(training_file):
            with open(training_file, 'r') as f:
                custom_data = json.load(f)
            
            for example in custom_data.get('examples', []):
                self.add_training_example(
                    example['query'],
                    example['intent'],
                    example.get('entities'),
                    example.get('response')
                )
            print(f"📚 Loaded {len(custom_data.get('examples', []))} custom examples")
    
    def create_custom_training_template(self):
        """Create a template for custom training data"""
        template = {
            "examples": [
                {
                    "query": "your example query here",
                    "intent": "intent_name",
                    "entities": {"entity_type": "entity_value"},
                    "response": "Expected response"
                }
            ]
        }
        
        with open('custom_training.json', 'w') as f:
            json.dump(template, f, indent=2)
        
        print("📝 Created custom_training.json template")

def main():
    trainer = ChatbotTrainer()
    
    print("🚀 Starting Chatbot Training...")
    
    # Load default training data
    trainer.load_default_training_data()
    
    # Try to load custom training
    trainer.add_custom_training()
    
    # Train the model
    trainer.train_model()
    
    # Save the model
    trainer.save_model()
    
    # Test the model
    print("\n🧪 Testing trained model...")
    test_queries = [
        "show me student 231FA00001",
        "students in SEC-1",
        "CN subject results",
        "attendance report",
        "top 5 students",
        "hello"
    ]
    
    for query in test_queries:
        intent, confidence = trainer.predict_intent(query)
        print(f"Query: '{query}' -> Intent: {intent} (Confidence: {confidence:.2f})")
    
    print("\n✅ Training completed successfully!")
    print("💡 Tips:")
    print("   - Edit custom_training.json to add more examples")
    print("   - Run train_chatbot.py again to retrain")
    print("   - The model will be automatically loaded by the chatbot")

if __name__ == "__main__":
    main()
