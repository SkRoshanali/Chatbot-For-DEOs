import os
import re

# Gemini client — optional, falls back gracefully if unavailable
client = None
try:
    import google.generativeai as genai
    genai.configure(api_key=os.environ.get('GEMINI_API_KEY', 'AIzaSyCaJjPyGEM2sv1KCTtSfy1f6vqMLN4XioM'))
    client = genai.GenerativeModel('gemini-1.5-flash')
except Exception:
    pass

INTENT_PROMPT = """
You are an intent classifier for a university academic report chatbot.
Read the user message and return ONLY one of these exact labels — nothing else:

attendance
section_attendance
subject_attendance
department_attendance
low_attendance
internal_marks
external_marks
subject_performance
subject_filter
subject_section_attendance
section_toppers
section_backlogs
section_performance
section_cgpa_filter
compare_sections
subject_failure_rate
marks_distribution
subject_trend
perfect_attendance
section_stats
dept_summary
predict_backlog
internal_filter
semester_result
backlogs
repeated_subjects
pending_completions
cgpa
cgpa_distribution
toppers
rankings
risk
top_performers
average_marks
student_lookup
section_lookup
general

Rules:
- Return ONLY the label. No explanation, no punctuation, no extra words.
- "student_lookup": query has a specific roll number (e.g. CSE001, 231FA00001).
- "section_lookup": asks about students in a specific section with no subject/qualifier.
- "subject_filter": qualifier word (weak/low/poor/failing/top/best/excellent/strong/average) + specific subject (CN/CNS/SE/ADS/PDC).
- "subject_section_attendance": subject + section together, no qualifier (e.g. "PDC attendance from SEC-1").
- "section_toppers": top N students in a section by CGPA or marks, or highest scorer in a subject in a section.
- "section_backlogs": students with more than N backlogs in a section.
- "section_performance": overall performance report for a section.
- "section_cgpa_filter": students in a section with CGPA above/below a threshold.
- "compare_sections": compare two sections in a subject.
- "subject_failure_rate": which subject has highest/lowest failure rate or average marks.
- "marks_distribution": marks distribution of a subject in a section.
- "subject_trend": subject performance trend across all sections.
- "perfect_attendance": students with 100% or perfect attendance.
- "section_stats": student count per section, section with highest/lowest CGPA or attendance.
- "dept_summary": department average CGPA, attendance, or overall performance report.
- "predict_backlog": predict students likely to get backlog.
- "internal_filter": students scoring below/above a threshold in internal marks of a subject.
- "low_attendance": students with low/poor attendance (no specific subject).
- "risk": at-risk students overall.
- "general": greetings, small talk, help.

Examples:
"academic details of CSE001" → student_lookup
"show CSE002 from SEC-1" → student_lookup
"attendance of CSE003 in PDC" → student_lookup
"internal marks of CSE007 in PDC" → student_lookup
"backlogs of CSE019" → student_lookup
"subject-wise marks of CSE015" → student_lookup
"show section 3 students" → section_lookup
"section wise attendance" → section_attendance
"subject wise attendance" → subject_attendance
"CN attendance" → subject_attendance
"PDC attendance from SEC-1" → subject_section_attendance
"attendance report for PDC in SEC-12" → subject_section_attendance
"average marks of PDC in SEC-4" → subject_section_attendance
"weak students in PDC" → subject_filter
"failing students in SE" → subject_filter
"top students in ADS" → subject_filter
"students below 75 attendance in PDC from SEC-1" → subject_filter
"who scored highest in PDC in SEC-3" → section_toppers
"top 5 students in SEC-8 by CGPA" → section_toppers
"students in SEC-10 with more than 2 backlogs" → section_backlogs
"performance report for SEC-5" → section_performance
"students in SEC-17 with CGPA above 8.5" → section_cgpa_filter
"compare SEC-1 and SEC-2 in PDC" → compare_sections
"which subject has highest failure rate" → subject_failure_rate
"which subject has lowest average marks" → subject_failure_rate
"marks distribution of PDC in SEC-16" → marks_distribution
"subject performance trend for CNS across sections" → subject_trend
"students with perfect attendance" → perfect_attendance
"student count per section" → section_stats
"section with highest average CGPA" → section_stats
"section with lowest attendance" → section_stats
"department average CGPA" → dept_summary
"department average attendance" → dept_summary
"overall department performance report" → dept_summary
"predict students likely to get backlog in ADS" → predict_backlog
"students scoring below 20 in SE internals" → internal_filter
"low attendance students" → low_attendance
"at risk students" → risk
"toppers" → toppers
"hi" → general
"""

GENERAL_PROMPT = """
You are a friendly academic assistant chatbot for a university DEO system called EduBot.
Answer general questions and greetings briefly and professionally (under 3 sentences).
If asked what you can do, list: student lookup (roll number), section lookup, attendance reports,
subject-wise marks, section toppers, backlogs, CGPA reports, performance comparisons,
marks distribution, failure rate analysis, risk prediction, and more.
Never make up student data.
"""

VALID_INTENTS = [
    'attendance', 'section_attendance', 'subject_attendance', 'subject_section_attendance',
    'department_attendance', 'low_attendance', 'internal_marks', 'external_marks',
    'subject_performance', 'subject_filter', 'section_toppers', 'section_backlogs',
    'section_performance', 'section_cgpa_filter', 'compare_sections', 'subject_failure_rate',
    'marks_distribution', 'subject_trend', 'perfect_attendance', 'section_stats',
    'dept_summary', 'predict_backlog', 'internal_filter',
    'semester_result', 'backlogs', 'repeated_subjects', 'pending_completions',
    'cgpa', 'cgpa_distribution', 'toppers', 'rankings', 'risk',
    'top_performers', 'average_marks', 'student_lookup', 'section_lookup', 'general'
]

# Subject aliases — CNS maps to CN
SUBJECT_ALIASES = {'CNS': 'CN', 'CN': 'CN', 'SE': 'SE', 'ADS': 'ADS', 'PDC': 'PDC'}

QUALIFIER_LOW  = ['weak','poor','fail','failing','failed','bad','struggling','defaulter',
                  'defaulters','worst','not pass','not passing','critical','below average',
                  'at risk','low marks','low score']
QUALIFIER_HIGH = ['top','best','excellent','strong','bright','outstanding','topper','toppers',
                  'highest','great','brilliant','exceptional','merit','distinction','above']
QUALIFIER_AVG  = ['average','moderate','medium','mediocre','normal','typical']

ATTENDANCE_WORDS = ['attend', 'attendance', 'present', 'absent', 'absentee']
MARKS_WORDS      = ['mark', 'marks', 'score', 'scores', 'result', 'results',
                    'internal', 'external', 'grade', 'grades', 'performance']


def extract_qualifier(query: str, subject: str) -> str:
    q = query.lower()
    has_subject    = bool(subject)
    has_marks_ctx  = any(w in q for w in MARKS_WORDS)
    has_attend_ctx = any(w in q for w in ATTENDANCE_WORDS)

    if not has_subject and has_attend_ctx and not has_marks_ctx:
        for kw in QUALIFIER_LOW:
            if re.search(r'\b' + re.escape(kw) + r'\b', q):
                return 'low_attend_only'
        for kw in QUALIFIER_HIGH:
            if re.search(r'\b' + re.escape(kw) + r'\b', q):
                return 'high_attend_only'
        return ''

    for kw in QUALIFIER_LOW:
        if re.search(r'\b' + re.escape(kw) + r'\b', q):
            return 'low'
    for kw in QUALIFIER_HIGH:
        if re.search(r'\b' + re.escape(kw) + r'\b', q):
            return 'high'
    for kw in QUALIFIER_AVG:
        if re.search(r'\b' + re.escape(kw) + r'\b', q):
            return 'average'
    return ''


def extract_number(query: str) -> int:
    """Extract a standalone number from query (for top-N, threshold, etc.)"""
    m = re.search(r'\b(\d+)\b', query)
    return int(m.group(1)) if m else 0


def detect_intent(user_message: str):
    """Returns (intent, semester, batch, roll, section, subject, qualifier)"""
    roll    = extract_roll(user_message)
    section = extract_section(user_message)
    sem     = extract_semester(user_message)
    batch   = extract_batch(user_message)
    subject = extract_subject(user_message)
    raw_qualifier = extract_qualifier(user_message, subject)
    qualifier = raw_qualifier if raw_qualifier in ('low', 'high', 'average') else ''

    # Roll number → always student_lookup (handles CSE001, 231FA00001, etc.)
    if roll:
        return 'student_lookup', sem, batch, roll, section, subject, qualifier

    # qualifier + subject → subject_filter
    if qualifier and subject:
        return 'subject_filter', sem, batch, roll, section, subject, qualifier

    # subject + section (no qualifier) → subject_section_attendance
    if subject and section:
        return 'subject_section_attendance', sem, batch, roll, section, subject, qualifier

    # pure low-attendance signal
    if raw_qualifier == 'low_attend_only':
        return 'low_attendance', sem, batch, roll, section, subject, ''

    # Rule-based short-circuits before LLM (fast, reliable)
    q = user_message.lower()

    # section_toppers: "top N in SEC-X", "highest in SUBJ in SEC-X"
    if section and re.search(r'\b(top\s*\d+|highest|topper|best\s+student)', q):
        return 'section_toppers', sem, batch, roll, section, subject, qualifier

    # section_backlogs: "more than N backlogs in SEC-X"
    if section and re.search(r'\b(backlog|arrear)\b', q) and re.search(r'\b(more than|greater than|above|\d+)\b', q):
        return 'section_backlogs', sem, batch, roll, section, subject, qualifier

    # section_performance: "performance report for SEC-X"
    if section and re.search(r'\b(performance report|generate.*report|report for)\b', q):
        return 'section_performance', sem, batch, roll, section, subject, qualifier

    # section_cgpa_filter: "CGPA above/below X in SEC-Y"
    if section and re.search(r'\bcgpa\b', q) and re.search(r'\b(above|below|greater|less|more than|under|over)\b', q):
        return 'section_cgpa_filter', sem, batch, roll, section, subject, qualifier

    # compare_sections: "compare SEC-X and SEC-Y"
    if re.search(r'compare', q) and re.search(r'sec', q):
        return 'compare_sections', sem, batch, roll, section, subject, qualifier

    # subject_failure_rate: "highest failure rate", "lowest average marks"
    if re.search(r'\b(failure rate|fail rate|lowest average|highest failure|which subject)\b', q):
        return 'subject_failure_rate', sem, batch, roll, section, subject, qualifier

    # marks_distribution: "marks distribution"
    if re.search(r'\bmarks distribution\b', q) or re.search(r'\bdistribution\b', q) and subject:
        return 'marks_distribution', sem, batch, roll, section, subject, qualifier

    # subject_trend: "trend", "across sections"
    if re.search(r'\b(trend|across sections|section.wise performance)\b', q) and subject:
        return 'subject_trend', sem, batch, roll, section, subject, qualifier

    # perfect_attendance
    if re.search(r'\b(perfect attendance|100.{0,5}attendance|full attendance)\b', q):
        return 'perfect_attendance', sem, batch, roll, section, subject, qualifier

    # section_stats: "count per section", "section with highest/lowest"
    if re.search(r'\b(count per section|student count|section with highest|section with lowest|per section)\b', q):
        return 'section_stats', sem, batch, roll, section, subject, qualifier

    # dept_summary: "department average", "overall department"
    if re.search(r'\b(department average|dept average|overall department|department performance)\b', q):
        return 'dept_summary', sem, batch, roll, section, subject, qualifier

    # predict_backlog
    if re.search(r'\b(predict|likely to|at risk of failing|likely.*backlog)\b', q):
        return 'predict_backlog', sem, batch, roll, section, subject, qualifier

    # internal_filter: "below 20 in SE internals"
    if re.search(r'\b(below|above|less than|more than|scoring)\b', q) and re.search(r'\binternal\b', q) and subject:
        return 'internal_filter', sem, batch, roll, section, subject, qualifier

    # section with low attendance (no subject)
    if section and re.search(r'\b(attendance below|below.*attendance|low attendance)\b', q):
        return 'low_attendance', sem, batch, roll, section, subject, qualifier

    if client:
        try:
            response = client.generate_content(
                f"{INTENT_PROMPT}\n\nUser Message: {user_message}",
                generation_config={"temperature": 0, "max_output_tokens": 10}
            )
            intent = response.text.strip().lower()
            intent = intent if intent in VALID_INTENTS else fallback_intent(user_message)
        except Exception as e:
            print(f"Gemini API error (detect_intent): {e}")
            intent = fallback_intent(user_message)
    else:
        intent = fallback_intent(user_message)

    # Post-LLM fixes
    if subject and section and intent in ('subject_attendance', 'subject_performance', 'section_lookup'):
        intent = 'subject_section_attendance'

    return intent, sem, batch, roll, section, subject, qualifier


def extract_roll(query: str) -> str:
    """Match 231FA00001 OR CSE001–CSE999 style roll numbers"""
    m = re.search(r'231FA\d{5}', query, re.IGNORECASE)
    if m:
        return m.group(0).upper()
    m = re.search(r'\bCSE\d{3,5}\b', query, re.IGNORECASE)
    if m:
        return m.group(0).upper()
    return ''


def extract_section(query: str) -> str:
    q = query.lower()
    m = re.search(r'sec(?:tion)?[-\s]*0*(\d{1,2})', q)
    if m:
        return f'SEC-{int(m.group(1))}'
    return ''


def extract_second_section(query: str) -> str:
    """Extract second section for compare queries"""
    q = query.lower()
    matches = re.findall(r'sec(?:tion)?[-\s]*0*(\d{1,2})', q)
    if len(matches) >= 2:
        return f'SEC-{int(matches[1])}'
    return ''


def extract_semester(query: str) -> str:
    q = query.lower()
    for p in [r'semester\s*(\d)', r'sem\s*(\d)', r'(\d)(?:st|nd|rd|th)\s*sem(?:ester)?']:
        m = re.search(p, q)
        if m:
            return m.group(1)
    return ''


def extract_batch(query: str) -> str:
    m = re.search(r'(20\d{2}[-–](20)?\d{2})', query)
    return m.group(1) if m else ''


def extract_subject(query: str) -> str:
    """Extract subject, treating CNS as CN"""
    q = query.upper()
    # Check CNS before CN to avoid partial match issues
    for alias in ['CNS', 'ADS', 'PDC', 'CN', 'SE']:
        if re.search(r'\b' + alias + r'\b', q):
            return SUBJECT_ALIASES.get(alias, alias)
    return ''


def extract_threshold(query: str) -> float:
    """Extract numeric threshold from query (e.g. 'above 8.5', 'below 20')"""
    m = re.search(r'\b(\d+(?:\.\d+)?)\b', query)
    return float(m.group(1)) if m else 0.0


def extract_topn(query: str) -> int:
    """Extract top-N number, default 5"""
    m = re.search(r'\btop\s*(\d+)\b', query.lower())
    if m:
        return int(m.group(1))
    return 5


def get_general_response(user_message: str) -> str:
    if client:
        try:
            response = client.generate_content(
                f"{GENERAL_PROMPT}\n\nUser Message: {user_message}",
                generation_config={"temperature": 0.7, "max_output_tokens": 120}
            )
            return response.text.strip()
        except Exception as e:
            print(f"Gemini API error (general_response): {e}")
    return "Hi! I'm EduBot. Ask me about attendance, marks, backlogs, CGPA, toppers, or look up a student by roll number."


def fallback_intent(query: str) -> str:
    q = query.lower()
    greetings = ['hi','hello','hey','how are you','good morning','good evening',
                 'thanks','thank you','help','what can you do']
    if any(g in q for g in greetings):
        return 'general'

    has_subj = bool(re.search(r'\b(cn|cns|se|ads|pdc)\b', q))
    has_sec  = bool(re.search(r'sec(?:tion)?[-\s]*0*\d', q))

    if re.search(r'compare', q) and has_sec:                                         return 'compare_sections'
    if re.search(r'\b(failure rate|which subject)\b', q):                            return 'subject_failure_rate'
    if re.search(r'\bmarks distribution\b', q):                                      return 'marks_distribution'
    if re.search(r'\b(trend|across sections)\b', q) and has_subj:                    return 'subject_trend'
    if re.search(r'\bperfect attendance\b', q):                                      return 'perfect_attendance'
    if re.search(r'\b(count per section|per section)\b', q):                         return 'section_stats'
    if re.search(r'\b(department average|overall department)\b', q):                 return 'dept_summary'
    if re.search(r'\bpredict\b', q):                                                 return 'predict_backlog'
    if has_subj and has_sec:                                                         return 'subject_section_attendance'
    if has_subj and 'attend' in q:                                                   return 'subject_attendance'
    if has_subj and ('mark' in q or 'perf' in q or 'score' in q or 'result' in q):  return 'subject_performance'
    if has_sec and 'attend' in q:                                                    return 'section_attendance'
    if has_sec:                                                                      return 'section_lookup'
    if 'section' in q and 'attend' in q:                                             return 'section_attendance'
    if 'subject' in q and 'attend' in q:                                             return 'subject_attendance'
    if 'department' in q and 'attend' in q:                                          return 'department_attendance'
    if 'low attend' in q or 'absent' in q or 'below 75' in q:                       return 'low_attendance'
    if 'attend' in q:                                                                return 'attendance'
    if 'average' in q or 'mean' in q:                                                return 'average_marks'
    if 'internal' in q:                                                              return 'internal_marks'
    if 'external' in q:                                                              return 'external_marks'
    if 'result' in q or 'pass' in q or 'fail' in q:                                 return 'semester_result'
    if 'pending' in q or 'incomplete' in q:                                          return 'pending_completions'
    if 'repeat' in q:                                                                return 'repeated_subjects'
    if 'backlog' in q or 'arrear' in q:                                              return 'backlogs'
    if 'distribution' in q and 'cgpa' in q:                                         return 'cgpa_distribution'
    if 'topper' in q or 'highest' in q:                                              return 'toppers'
    if 'rank' in q:                                                                  return 'rankings'
    if 'risk' in q or 'danger' in q or 'struggling' in q:                           return 'risk'
    if 'top performer' in q or 'excellent' in q:                                     return 'top_performers'
    if 'cgpa' in q or 'gpa' in q:                                                    return 'cgpa'
    return 'general'
