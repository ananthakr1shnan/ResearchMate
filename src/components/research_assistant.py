"""
Research Assistant Component
Main research assistant logic and workflow management
"""

import os
import json
from typing import List, Dict, Optional, Any
from datetime import datetime
import logging

from .config import Config
from .groq_processor import GroqProcessor
from .rag_system import RAGSystem
from .unified_fetcher import PaperFetcher
from .pdf_processor import PDFProcessor
from .trend_monitor import AdvancedTrendMonitor


class ProjectManager:
    """Manages research projects"""
    
    def __init__(self, config: Config = None):
        self.config = config or Config()
        self.projects = {}
        self.project_counter = 0
        self.projects_file = os.path.join(self.config.BASE_DIR, 'projects.json')
        self.load_projects()
    
    def load_projects(self):
        """Load projects from storage"""
        try:
            if os.path.exists(self.projects_file):
                with open(self.projects_file, 'r') as f:
                    data = json.load(f)
                    self.projects = data.get('projects', {})
                    self.project_counter = data.get('counter', 0)
                print(f"Loaded {len(self.projects)} projects")
        except Exception as e:
            print(f"Error loading projects: {e}")
    
    def save_projects(self):
        """Save projects to storage"""
        try:
            os.makedirs(os.path.dirname(self.projects_file), exist_ok=True)
            with open(self.projects_file, 'w') as f:
                json.dump({
                    'projects': self.projects,
                    'counter': self.project_counter
                }, f, indent=2)
        except Exception as e:
            print(f"Error saving projects: {e}")
    
    def create_project(self, name: str, research_question: str, keywords: List[str], user_id: str) -> str:
        """Create a new research project"""
        self.project_counter += 1
        project_id = f"project_{self.project_counter}"
        
        self.projects[project_id] = {
            'id': project_id,
            'name': name,
            'research_question': research_question,
            'keywords': keywords,
            'papers': [],
            'notes': [],
            'status': 'active',
            'user_id': user_id,  # Track which user created this project
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }
        
        self.save_projects()
        return project_id
    
    def get_project(self, project_id: str, user_id: str = None) -> Optional[Dict[str, Any]]:
        """Get a project by ID, optionally checking user ownership"""
        project = self.projects.get(project_id)
        if project and user_id:
            # Check if user owns this project
            if project.get('user_id') != user_id:
                return None
        return project
    
    def update_project(self, project_id: str, user_id: str = None, **kwargs):
        """Update a project"""
        if project_id in self.projects:
            # Check user ownership if user_id provided
            if user_id and self.projects[project_id].get('user_id') != user_id:
                return False
            self.projects[project_id].update(kwargs)
            self.projects[project_id]['updated_at'] = datetime.now().isoformat()
            self.save_projects()
            return True
        return False
    
    def add_paper_to_project(self, project_id: str, paper: Dict[str, Any], user_id: str = None):
        """Add a paper to a project"""
        if project_id in self.projects:
            # Check user ownership if user_id provided
            if user_id and self.projects[project_id].get('user_id') != user_id:
                return False
            self.projects[project_id]['papers'].append(paper)
            self.update_project(project_id, user_id=user_id)
            return True
        return False
    
    def list_projects(self, user_id: str = None) -> List[Dict[str, Any]]:
        """List projects, optionally filtered by user ID"""
        if user_id:
            # Return only projects owned by this user
            return [project for project in self.projects.values() 
                   if project.get('user_id') == user_id]
        else:
            # Return all projects (for admin use)
            return list(self.projects.values())


class SimpleResearchAssistant:
    """
    Simplified research assistant that combines all components
    """
    
    def __init__(self, config: Config = None):
        self.config = config or Config()
        
        # Initialize components
        print("Initializing Research Assistant...")
        self.groq_processor = GroqProcessor(self.config)
        self.rag_system = RAGSystem(self.config)
        self.paper_fetcher = PaperFetcher(self.config)
        self.pdf_processor = PDFProcessor(self.config)
        self.project_manager = ProjectManager(self.config)
        self.trend_monitor = AdvancedTrendMonitor(self.groq_processor)
        
        print("Research Assistant initialized!")
        
        # Set up logging
        logging.basicConfig(level=getattr(logging, self.config.LOG_LEVEL))
        self.logger = logging.getLogger(__name__)
    
    def search_papers(self, query: str, max_results: int = 10, sources: List[str] = None) -> List[Dict[str, Any]]:
        """
        Search for papers across multiple sources
        
        Args:
            query: Search query
            max_results: Maximum number of results
            sources: List of sources to search ['arxiv', 'semantic_scholar', 'crossref', 'pubmed']
            
        Returns:
            List of papers
        """
        # Use all sources by default for comprehensive search
        if sources is None:
            sources = ['arxiv', 'semantic_scholar', 'crossref', 'pubmed']
        
        self.logger.info(f"Searching for: {query}")
        print(f"DEBUG: Starting multi-source search for '{query}' with max_results={max_results}")
        print(f"DEBUG: Using sources: {sources}")
        
        try:
            # Use the unified fetcher for all sources
            papers = self.paper_fetcher.search_papers(query, max_results, sources=sources)
            print(f"DEBUG: Unified fetcher returned {len(papers)} papers")
            
            # Add to RAG system for future querying
            if papers:
                try:
                    self.rag_system.add_papers(papers)
                    print("DEBUG: Papers added to RAG system")
                except Exception as e:
                    print(f"DEBUG: Failed to add papers to RAG system: {e}")
            
            self.logger.info(f"Found {len(papers)} papers from {len(sources)} sources")
            print(f"DEBUG: Returning {len(papers)} papers from multi-source search")
            return papers
            
        except Exception as e:
            print(f"DEBUG: Multi-source search failed: {e}")
            self.logger.error(f"Multi-source search failed: {e}")
            return []
    
    def ask_question(self, question: str, context: str = None) -> Dict[str, Any]:
        """
        Answer a research question using RAG
        
        Args:
            question: Research question
            context: Optional context
            
        Returns:
            Answer with sources
        """
        self.logger.info(f"Answering question: {question}")
        
        # Use RAG system if available
        if self.rag_system.vectorstore:
            return self.rag_system.answer_question(question)
        else:
            # Fallback to direct LLM
            answer = self.groq_processor.answer_question(question, context or "")
            return {
                'answer': answer,
                'sources': [],
                'method': 'direct_llm'
            }
    
    def process_pdf(self, file_path: str) -> Dict[str, Any]:
        """
        Process a PDF file
        
        Args:
            file_path: Path to PDF file
            
        Returns:
            Processing result
        """
        self.logger.info(f"Processing PDF: {file_path}")
        
        # Extract text
        extraction_result = self.pdf_processor.extract_text_from_file(file_path)
        
        if extraction_result.get('error'):
            return {'success': False, 'error': extraction_result['error']}
        
        text = extraction_result.get('text', '')
        
        # Extract basic information
        title = self._extract_title_from_text(text)
        abstract = self._extract_abstract_from_text(text)
        
        # Generate summary using Groq
        summary = self.groq_processor.summarize_paper(title, abstract, text)
        
        # Create paper object
        paper = {
            'title': title,
            'abstract': abstract,
            'content': text,
            'summary': summary,
            'source': 'uploaded_pdf',
            'file_path': file_path,
            'processed_at': datetime.now().isoformat(),
            'metadata': extraction_result.get('metadata', {})
        }
        
        # Try to add to RAG system (don't fail if RAG is not initialized)
        try:
            self.rag_system.add_papers([paper])
        except Exception as e:
            self.logger.warning(f"Could not add paper to RAG system: {e}")
        
        # Return formatted response with all expected fields
        return {
            'success': True,
            'title': title,
            'abstract': abstract,
            'text_length': len(text),
            'processed_at': datetime.now().isoformat(),
            'summary': summary,
            'paper': paper,
            'word_count': extraction_result.get('word_count', 0),
            'pages': extraction_result.get('metadata', {}).get('pages', 0)
        }
    
    def analyze_trends(self, topic: str, max_papers: int = 50) -> Dict[str, Any]:
        """
        Analyze research trends for a topic using advanced trend monitoring
        
        Args:
            topic: Research topic
            max_papers: Maximum papers to analyze
            
        Returns:
            Advanced trend analysis
        """
        self.logger.info(f"Analyzing trends for: {topic}")
        print(f"📊 Starting advanced trend analysis for '{topic}'")
        
        # Get papers from multiple sources for comprehensive analysis
        papers = self.search_papers(topic, max_papers)
        
        if not papers:
            return {'error': 'No papers found for trend analysis'}
        
        print(f"📊 Found {len(papers)} papers for trend analysis")
        
        # Use advanced trend monitor for comprehensive analysis
        trend_report = self.trend_monitor.generate_trend_report(papers)
        
        # Add metadata
        trend_report['query_metadata'] = {
            'topic': topic,
            'papers_analyzed': len(papers),
            'analysis_date': datetime.now().isoformat(),
            'analysis_type': 'advanced_trend_monitoring'
        }
        
        return trend_report
    
    def create_project(self, name: str, research_question: str, keywords: List[str], user_id: str) -> str:
        """Create a new research project"""
        return self.project_manager.create_project(name, research_question, keywords, user_id)
    
    def get_project(self, project_id: str, user_id: str = None) -> Optional[Dict[str, Any]]:
        """Get a project by ID"""
        return self.project_manager.get_project(project_id, user_id)
    
    def list_projects(self, user_id: str = None) -> List[Dict[str, Any]]:
        """List projects"""
        return self.project_manager.list_projects(user_id)
    
    def conduct_literature_search(self, project_id: str, max_papers: int = 20, user_id: str = None) -> Dict[str, Any]:
        """
        Conduct literature search for a project
        
        Args:
            project_id: Project ID
            max_papers: Maximum papers to find
            user_id: User ID to check ownership
            
        Returns:
            Search results
        """
        project = self.project_manager.get_project(project_id, user_id)
        if not project:
            return {'error': 'Project not found or access denied'}
        
        # Build search query
        query = f"{project['research_question']} {' '.join(project['keywords'])}"
        
        # Search for papers
        papers = self.search_papers(query, max_papers)
        
        # Add papers to project
        for paper in papers:
            self.project_manager.add_paper_to_project(project_id, paper, user_id)
        
        return {
            'project_id': project_id,
            'papers_found': len(papers),
            'papers': papers
        }
    
    def generate_literature_review(self, project_id: str, user_id: str = None) -> Dict[str, Any]:
        """
        Generate a literature review for a project
        
        Args:
            project_id: Project ID
            user_id: User ID to check ownership
            
        Returns:
            Literature review
        """
        try:
            project = self.project_manager.get_project(project_id, user_id)
            if not project:
                return {'error': 'Project not found or access denied'}
            
            papers = project.get('papers', [])
            if not papers:
                return {'error': 'No papers found in project'}
            
            print(f"Generating review for project {project_id} with {len(papers)} papers...")
            
            # Generate review
            review_content = self.groq_processor.generate_literature_review(
                papers, 
                project['research_question']
            )
            
            print(f"Review generated, length: {len(review_content) if review_content else 0}")
            
            if not review_content or review_content.startswith("Error"):
                return {'error': f'Failed to generate review: {review_content}'}
            
            return {
                'project_id': project_id,
                'review': {
                    'content': review_content,
                    'papers_count': len(papers),
                    'research_question': project['research_question']
                },
                'papers_reviewed': len(papers),
                'generated_at': datetime.now().isoformat()
            }
        except Exception as e:
            print(f"Error in generate_literature_review: {str(e)}")
            return {'error': f'Unexpected error: {str(e)}'}
    
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get system status"""
        return {
            'status': 'operational',
            'components': {
                'groq_processor': 'ready',
                'rag_system': 'ready',
                'arxiv_fetcher': 'ready',
                'pdf_processor': 'ready',
                'project_manager': 'ready'
            },
            'statistics': {
                'rag_documents': self.rag_system.get_database_stats().get('total_chunks', 0),
                'system_version': '2.0.0',
                'status_check_time': datetime.now().isoformat()
            },
            'config': self.config.get_summary()
        }
    
    def _extract_title_from_text(self, text: str) -> str:
        """Extract title from PDF text"""
        lines = text.split('\n')[:20]  # Check first 20 lines
        
        for line in lines:
            line = line.strip()
            if len(line) > 10 and len(line) < 200:
                # Skip lines that look like headers or metadata
                if not any(keyword in line.lower() for keyword in ['page', 'arxiv', 'doi', 'submitted', 'accepted']):
                    return line
        
        return "Unknown Title"
    
    def _extract_abstract_from_text(self, text: str) -> str:
        """Extract abstract from PDF text"""
        text_lower = text.lower()
        
        # Look for abstract section
        abstract_start = text_lower.find('abstract')
        if abstract_start != -1:
            # Find the end of abstract (usually next section)
            abstract_text = text[abstract_start:]
            
            # Look for common section headers that might follow abstract
            section_headers = ['introduction', '1. introduction', '1 introduction', 'keywords', 'key words']
            
            end_pos = len(abstract_text)
            for header in section_headers:
                pos = abstract_text.lower().find(header)
                if pos != -1 and pos < end_pos:
                    end_pos = pos
            
            abstract = abstract_text[:end_pos]
            
            # Clean up
            abstract = abstract.replace('abstract', '', 1).strip()
            if len(abstract) > 1000:
                abstract = abstract[:1000] + "..."
            
            return abstract
        
        return "Abstract not found"


class ResearchMate:
    """
    Main ResearchMate interface
    Simplified wrapper around the research assistant
    """
    
    def __init__(self, config: Config = None):
        self.config = config or Config()
        self.assistant = SimpleResearchAssistant(self.config)
        self.version = "2.0.0"
        self.initialized_at = datetime.now().isoformat()
        
        print(f"ResearchMate {self.version} initialized!")
    
    def search(self, query: str, max_results: int = 10) -> Dict[str, Any]:
        """Search for papers"""
        try:
            papers = self.assistant.search_papers(query, max_results)
            return {
                'success': True,
                'query': query,
                'papers': papers,
                'count': len(papers)
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def ask(self, question: str) -> Dict[str, Any]:
        """Ask a research question"""
        try:
            result = self.assistant.ask_question(question)
            return {
                'success': True,
                'question': question,
                'answer': result['answer'],
                'sources': result.get('sources', [])
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def upload_pdf(self, file_path: str) -> Dict[str, Any]:
        """Process uploaded PDF"""
        try:
            result = self.assistant.process_pdf(file_path)
            return result
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def analyze_trends(self, topic: str) -> Dict[str, Any]:
        """Analyze research trends"""
        try:
            result = self.assistant.analyze_trends(topic)
            return {'success': True, **result}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def create_project(self, name: str, research_question: str, keywords: List[str], user_id: str) -> Dict[str, Any]:
        """Create research project"""
        try:
            project_id = self.assistant.create_project(name, research_question, keywords, user_id)
            return {
                'success': True,
                'project_id': project_id,
                'message': f'Project "{name}" created successfully'
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def get_project(self, project_id: str, user_id: str = None) -> Dict[str, Any]:
        """Get project details"""
        try:
            project = self.assistant.get_project(project_id, user_id)
            if project:
                return {'success': True, 'project': project}
            else:
                return {'success': False, 'error': 'Project not found or access denied'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def list_projects(self, user_id: str = None) -> Dict[str, Any]:
        """List projects"""
        try:
            projects = self.assistant.list_projects(user_id)
            return {'success': True, 'projects': projects}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def search_project_literature(self, project_id: str, max_papers: int = 20, user_id: str = None) -> Dict[str, Any]:
        """Search literature for a project"""
        try:
            result = self.assistant.conduct_literature_search(project_id, max_papers, user_id)
            return {'success': True, **result}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def generate_review(self, project_id: str, user_id: str = None) -> Dict[str, Any]:
        """Generate literature review for a project"""
        try:
            result = self.assistant.generate_literature_review(project_id, user_id)
            return {'success': True, **result}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def get_status(self) -> Dict[str, Any]:
        """Get system status"""
        try:
            status = self.assistant.get_system_status()
            return {'success': True, **status}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def analyze_project(self, project_id: str, user_id: str = None) -> Dict[str, Any]:
        """Analyze project literature"""
        try:
            project = self.assistant.get_project(project_id, user_id)
            if not project:
                return {'success': False, 'error': 'Project not found or access denied'}
            
            # Basic project analysis
            papers = project.get('papers', [])
            if not papers:
                return {'success': False, 'error': 'No papers found in project'}
            
            # Helper function to safely extract year
            def safe_year(paper):
                year = paper.get('year')
                if year is None:
                    return None
                try:
                    if isinstance(year, str):
                        year = int(year)
                    if isinstance(year, int) and 1900 <= year <= 2030:
                        return year
                except (ValueError, TypeError):
                    pass
                return None
            
            # Analyze papers
            total_papers = len(papers)
            
            # Process years more safely
            years = [safe_year(p) for p in papers]
            years = [y for y in years if y is not None]
            
            authors = []
            for p in papers:
                if p.get('authors'):
                    if isinstance(p.get('authors'), list):
                        authors.extend(p.get('authors'))
                    elif isinstance(p.get('authors'), str):
                        authors.append(p.get('authors'))
            
            # Extract key topics from keywords and titles
            all_keywords = []
            for p in papers:
                if p.get('keywords'):
                    if isinstance(p.get('keywords'), list):
                        all_keywords.extend(p.get('keywords'))
                    elif isinstance(p.get('keywords'), str):
                        all_keywords.extend(p.get('keywords').split(','))
            
            # Calculate year range safely
            year_range = "Unknown"
            if years:
                min_year = min(years)
                max_year = max(years)
                year_range = f"{min_year} - {max_year}" if min_year != max_year else str(min_year)
            
            # Count recent papers safely
            recent_papers_count = len([p for p in papers if safe_year(p) is not None and safe_year(p) >= 2020])
            
            # Basic analysis
            analysis = {
                'total_papers': total_papers,
                'year_range': year_range,
                'unique_authors': len(set(authors)) if authors else 0,
                'top_authors': list(set(authors))[:10] if authors else [],
                'key_topics': list(set([k.strip().lower() for k in all_keywords if k.strip()]))[:10] if all_keywords else [],
                'recent_papers': [p for p in papers if safe_year(p) is not None and safe_year(p) >= 2020][:5],
                'trends': f"Based on {total_papers} papers" + (f" spanning {year_range}" if years else ""),
                'insights': f"""## Key Research Insights

**Total Literature:** {total_papers} papers analyzed

**Research Scope:** {"Multi-year analysis spanning " + str(len(set(years))) + " different years" if len(years) > 1 else "Limited temporal scope"}

**Author Collaboration:** {len(set(authors))} unique researchers identified

**Key Themes:** {', '.join(list(set([k.strip().title() for k in all_keywords if k.strip()]))[:5]) if all_keywords else 'No specific themes identified'}

**Research Activity:** {"Active research area" if total_papers > 10 else "Emerging research area"}
""",
                'summary': f"""## Literature Analysis Summary

This project contains **{total_papers} research papers**{f" published between {year_range}" if years else ""}.

**Research Community:** The work involves {len(set(authors))} unique authors{f", with top contributors including {', '.join(list(set(authors))[:3])}" if len(authors) >= 3 else ""}.

**Research Focus:** {"The literature covers diverse topics including " + ', '.join(list(set([k.strip().title() for k in all_keywords if k.strip()]))[:5]) if all_keywords else "The research focus requires further analysis based on paper content"}.

**Temporal Distribution:** {"Recent research activity is strong" if recent_papers_count > total_papers * 0.5 else "Includes both historical and recent contributions"}.

**Research Maturity:** {"Well-established research area" if total_papers > 20 else "Growing research area"} with {"strong" if len(set(authors)) > 15 else "moderate"} community engagement.
"""
            }
            
            return {
                'success': True,
                'project_id': project_id,
                'analysis': analysis,
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def ask_project_question(self, project_id: str, question: str) -> Dict[str, Any]:
        """Ask a question about a specific project"""
        try:
            project = self.assistant.get_project(project_id)
            if not project:
                return {'success': False, 'error': 'Project not found'}
            
            # Context-aware question answering
            context = f"Project: {project.get('name', '')}\n"
            context += f"Research Question: {project.get('research_question', '')}\n"
            context += f"Keywords: {', '.join(project.get('keywords', []))}\n"
            
            # Use RAG system with project context
            full_question = f"Context: {context}\n\nQuestion: {question}"
            result = self.assistant.ask_question(full_question)
            
            return {
                'success': True,
                'project_id': project_id,
                'question': question,
                'answer': result['answer'],
                'sources': result.get('sources', [])
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}

    @property
    def trend_monitor(self):
        """Access to the advanced trend monitor"""
        return self.assistant.trend_monitor
    
    def search_papers(self, query: str, max_results: int = 10):
        """Direct access to paper search"""
        return self.assistant.search_papers(query, max_results)
