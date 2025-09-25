import re
import json
from typing import Dict, List, Any
import PyPDF2
import docx
import nltk
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import spacy
import openai
from django.conf import settings

nltk.download('punkt')
nltk.download('stopwords')
nlp = spacy.load('en_core_web_sm')

class ATSService:
    def __init__(self):
        self.openai_client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
        self.tfidf = TfidfVectorizer(stop_words='english')
    
    def extract_text_from_resume(self, resume_file) -> str:
        """Extract text from PDF or DOCX resume"""
        text = ""
        
        if resume_file.name.endswith('.pdf'):
            pdf_reader = PyPDF2.PdfReader(resume_file)
            for page in pdf_reader.pages:
                text += page.extract_text()
        
        elif resume_file.name.endswith('.docx'):
            doc = docx.Document(resume_file)
            for paragraph in doc.paragraphs:
                text += paragraph.text + '\n'
        
        else:
            text = resume_file.read().decode('utf-8', errors='ignore')
        
        return text
    
    def extract_resume_entities(self, resume_text: str) -> Dict[str, Any]:
        """Extract entities from resume using NLP"""
        doc = nlp(resume_text)
        
        entities = {
            'skills': [],
            'education': [],
            'experience': [],
            'certifications': [],
            'contact': {}
        }
        
        # Extract email
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, resume_text)
        if emails:
            entities['contact']['email'] = emails[0]
        
        # Extract phone
        phone_pattern = r'[\+\d]?[\d\s\(\)\-]{10,}'
        phones = re.findall(phone_pattern, resume_text)
        if phones:
            entities['contact']['phone'] = phones[0].strip()
        
        # Extract skills using keyword matching
        skill_keywords = self._get_skill_keywords()
        for skill in skill_keywords:
            if skill.lower() in resume_text.lower():
                entities['skills'].append(skill)
        
        # Use OpenAI for better extraction
        if settings.OPENAI_API_KEY:
            entities = self._extract_with_ai(resume_text, entities)
        
        return entities
    
    def calculate_ats_score(self, application, job) -> Dict[str, Any]:
        """Calculate comprehensive ATS score"""
        resume_text = self.extract_text_from_resume(application.resume)
        resume_entities = self.extract_resume_entities(resume_text)
        
        scores = {
            'skill_match': self._calculate_skill_match(resume_entities['skills'], job.skills_required, job.skills_preferred),
            'experience_match': self._calculate_experience_match(resume_text, job),
            'education_match': self._calculate_education_match(resume_entities['education'], job.requirements),
            'keyword_match': self._calculate_keyword_match(resume_text, job)
        }
        
        # Calculate weighted average
        weights = {
            'skill_match': 0.35,
            'experience_match': 0.30,
            'education_match': 0.20,
            'keyword_match': 0.15
        }
        
        total_score = sum(scores[key] * weights[key] for key in scores)
        
        # Generate feedback
        feedback = self._generate_feedback(scores, resume_entities, job)
        
        return {
            'total_score': round(total_score, 2),
            'scores': scores,
            'feedback': feedback,
            'entities': resume_entities
        }
    
    def _calculate_skill_match(self, candidate_skills: List[str], required_skills: List[str], preferred_skills: List[str]) -> float:
        """Calculate skill match score"""
        if not required_skills:
            return 100.0
        
        candidate_skills_lower = [s.lower() for s in candidate_skills]
        required_matched = sum(1 for skill in required_skills if skill.lower() in candidate_skills_lower)
        preferred_matched = sum(1 for skill in preferred_skills if skill.lower() in candidate_skills_lower)
        
        required_score = (required_matched / len(required_skills)) * 70 if required_skills else 0
        preferred_score = (preferred_matched / len(preferred_skills)) * 30 if preferred_skills else 30
        
        return min(required_score + preferred_score, 100)
    
    def _calculate_experience_match(self, resume_text: str, job) -> float:
        """Calculate experience match score"""
        # Extract years of experience from resume
        years_pattern = r'(\d+)\+?\s*years?\s*(?:of\s*)?experience'
        matches = re.findall(years_pattern, resume_text.lower())
        
        if matches:
            candidate_years = max(int(m) for m in matches)
        else:
            return 50.0  # Default score if experience not found
        
        min_years = job.experience_min_years
        max_years = job.experience_max_years or min_years + 5
        
        if candidate_years < min_years:
            return max(0, 100 - (min_years - candidate_years) * 20)
        elif candidate_years > max_years:
            return max(60, 100 - (candidate_years - max_years) * 10)
        else:
            return 100.0
    
    def _calculate_keyword_match(self, resume_text: str, job) -> float:
        """Calculate keyword match using TF-IDF"""
        job_text = f"{job.title} {job.description} {' '.join(job.requirements)} {' '.join(job.responsibilities)}"
        
        try:
            vectors = self.tfidf.fit_transform([job_text, resume_text])
            similarity = cosine_similarity(vectors[0:1], vectors[1:2])[0][0]
            return min(similarity * 100, 100)
        except:
            return 50.0
    
    def _calculate_education_match(self, education: List[str], requirements: List[str]) -> float:
        """Calculate education match score"""
        req_text = ' '.join(requirements).lower()
        education_keywords = ['bachelor', 'master', 'phd', 'degree', 'diploma', 'certification']
        
        required_education = []
        for keyword in education_keywords:
            if keyword in req_text:
                required_education.append(keyword)
        
        if not required_education:
            return 100.0
        
        education_text = ' '.join(education).lower()
        matched = sum(1 for req in required_education if req in education_text)
        
        return (matched / len(required_education)) * 100 if required_education else 100
    
    def _generate_feedback(self, scores: Dict[str, float], entities: Dict, job) -> Dict[str, Any]:
        """Generate detailed feedback for the application"""
        feedback = {
            'strengths': [],
            'weaknesses': [],
            'suggestions': []
        }
        
        # Analyze scores
        for score_type, score in scores.items():
            if score >= 80:
                feedback['strengths'].append(f"Strong {score_type.replace('_', ' ')}: {score:.1f}%")
            elif score < 60:
                feedback['weaknesses'].append(f"Low {score_type.replace('_', ' ')}: {score:.1f}%")
        
        # Skill analysis
        missing_skills = set(job.skills_required) - set(entities['skills'])
        if missing_skills:
            feedback['suggestions'].append(f"Consider highlighting these skills if you have them: {', '.join(list(missing_skills)[:3])}")
        
        return feedback
    
    def _extract_with_ai(self, resume_text: str, entities: Dict) -> Dict:
        """Use OpenAI to extract better information"""
        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "Extract skills, education, experience, and certifications from the resume. Return as JSON."},
                    {"role": "user", "content": resume_text[:3000]}  # Limit tokens
                ],
                max_tokens=500
            )
            
            ai_entities = json.loads(response.choices[0].message.content)
            # Merge AI results with existing entities
            for key in entities:
                if key in ai_entities and ai_entities[key]:
                    entities[key] = ai_entities[key]
            
        except Exception as e:
            print(f"AI extraction failed: {e}")
        
        return entities
    
    def _get_skill_keywords(self) -> List[str]:
        """Get list of common skill keywords"""
        return [
            'Python', 'Java', 'JavaScript', 'C++', 'C#', 'Ruby', 'PHP', 'Swift', 'Kotlin',
            'React', 'Angular', 'Vue', 'Django', 'Flask', 'Spring', 'Node.js', 'Express',
            'SQL', 'NoSQL', 'MongoDB', 'PostgreSQL', 'MySQL', 'Redis', 'Elasticsearch',
            'AWS', 'Azure', 'GCP', 'Docker', 'Kubernetes', 'CI/CD', 'Jenkins', 'Git',
            'Machine Learning', 'Deep Learning', 'TensorFlow', 'PyTorch', 'Scikit-learn',
            'Data Analysis', 'Data Science', 'Pandas', 'NumPy', 'Tableau', 'Power BI',
            'Agile', 'Scrum', 'Project Management', 'Leadership', 'Communication'
        ]

class ApplicationFilterService:
    """Service for filtering and ranking applications"""
    
    def filter_applications(self, queryset, filters: Dict[str, Any]):
        """Apply filters to application queryset"""
        
        if 'min_score' in filters:
            queryset = queryset.filter(ats_score__gte=filters['min_score'])
        
        if 'max_score' in filters:
            queryset = queryset.filter(ats_score__lte=filters['max_score'])
        
        if 'skills' in filters:
            # Filter by required skills
            for skill in filters['skills']:
                queryset = queryset.filter(
                    candidate__profile__skills__contains=[skill]
                )
        
        if 'experience_min' in filters:
            queryset = queryset.filter(
                candidate__profile__experience_years__gte=filters['experience_min']
            )
        
        if 'status' in filters:
            queryset = queryset.filter(status__in=filters['status'])
        
        return queryset
    
    def rank_applications(self, applications, criteria: str = 'ats_score'):
        """Rank applications based on criteria"""
        ranking_functions = {
            'ats_score': lambda app: app.ats_score or 0,
            'experience': lambda app: app.candidate.profile.experience_years,
            'skill_match': lambda app: app.skill_match_score or 0,
            'recent': lambda app: app.submitted_at
        }
        
        if criteria in ranking_functions:
            return sorted(applications, key=ranking_functions[criteria], reverse=True)
        
        return applications
