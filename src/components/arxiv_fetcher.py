"""
ArXiv Fetcher Component
Fetches and processes research papers from ArXiv
"""

import re
import time
import requests
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
import arxiv


class ArxivFetcher:
    """
    Fetches research papers from ArXiv
    Provides search, download, and metadata extraction capabilities
    """
    
    def __init__(self, config = None):
        # Import Config only when needed to avoid dependency issues
        if config is None:
            try:
                from .config import Config
                self.config = Config()
            except ImportError:
                # Fallback to None if Config cannot be imported
                self.config = None
        else:
            self.config = config
        self.client = arxiv.Client()
    
    def search_papers(self, 
                     query: str, 
                     max_results: int = 10,
                     sort_by: str = "relevance",
                     category: str = None,
                     date_range: int = None) -> List[Dict[str, Any]]:
        """
        Search for papers on ArXiv
        
        Args:
            query: Search query
            max_results: Maximum number of results
            sort_by: Sort criteria ('relevance', 'lastUpdatedDate', 'submittedDate')
            category: ArXiv category filter (e.g., 'cs.AI', 'cs.LG')
            date_range: Days back to search (e.g., 7, 30, 365)
            
        Returns:
            List of paper dictionaries
        """
        try:
            print(f"Searching ArXiv for: '{query}'")
            
            # Build search query
            search_query = query
            if category:
                search_query = f"cat:{category} AND {query}"
            
            # Set sort criteria
            sort_criteria = {
                "relevance": arxiv.SortCriterion.Relevance,
                "lastUpdatedDate": arxiv.SortCriterion.LastUpdatedDate,
                "submittedDate": arxiv.SortCriterion.SubmittedDate
            }.get(sort_by, arxiv.SortCriterion.Relevance)
            
            # Create search
            search = arxiv.Search(
                query=search_query,
                max_results=max_results,
                sort_by=sort_criteria,
                sort_order=arxiv.SortOrder.Descending
            )
            
            papers = []
            for result in self.client.results(search):
                # Date filtering
                if date_range:
                    cutoff_date = datetime.now() - timedelta(days=date_range)
                    if result.published.replace(tzinfo=None) < cutoff_date:
                        continue
                
                # Extract paper information
                paper = self._extract_paper_info(result)
                papers.append(paper)
            
            print(f"Found {len(papers)} papers")
            return papers
            
        except Exception as e:
            print(f"Error searching ArXiv: {e}")
            return []
    
    def get_paper_by_id(self, arxiv_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific paper by ArXiv ID
        
        Args:
            arxiv_id: ArXiv paper ID (e.g., '2301.12345')
            
        Returns:
            Paper dictionary or None
        """
        try:
            print(f"Fetching paper: {arxiv_id}")
            
            search = arxiv.Search(id_list=[arxiv_id])
            results = list(self.client.results(search))
            
            if results:
                paper = self._extract_paper_info(results[0])
                print(f"Retrieved paper: {paper['title']}")
                return paper
            else:
                print(f"Paper not found: {arxiv_id}")
                return None
                
        except Exception as e:
            print(f"Error fetching paper {arxiv_id}: {e}")
            return None
    
    def search_by_author(self, author: str, max_results: int = 20) -> List[Dict[str, Any]]:
        """
        Search for papers by author
        
        Args:
            author: Author name
            max_results: Maximum number of results
            
        Returns:
            List of paper dictionaries
        """
        query = f"au:{author}"
        return self.search_papers(query, max_results=max_results, sort_by="lastUpdatedDate")
    
    def search_by_category(self, category: str, max_results: int = 20) -> List[Dict[str, Any]]:
        """
        Search for papers by category
        
        Args:
            category: ArXiv category (e.g., 'cs.AI', 'cs.LG', 'stat.ML')
            max_results: Maximum number of results
            
        Returns:
            List of paper dictionaries
        """
        query = f"cat:{category}"
        return self.search_papers(query, max_results=max_results, sort_by="lastUpdatedDate")
    
    def get_trending_papers(self, category: str = "cs.AI", days: int = 7, max_results: int = 10) -> List[Dict[str, Any]]:
        """
        Get trending papers in a category
        
        Args:
            category: ArXiv category
            days: Days back to look for papers
            max_results: Maximum number of results
            
        Returns:
            List of paper dictionaries
        """
        return self.search_by_category(category, max_results=max_results)
    
    def _extract_paper_info(self, result) -> Dict[str, Any]:
        """
        Extract paper information from ArXiv result
        
        Args:
            result: ArXiv search result
            
        Returns:
            Paper dictionary
        """
        try:
            # Extract ArXiv ID
            arxiv_id = result.entry_id.split('/')[-1]
            
            # Clean and format data
            paper = {
                'arxiv_id': arxiv_id,
                'title': result.title.strip(),
                'authors': [author.name for author in result.authors],
                'summary': result.summary.strip(),
                'published': result.published.isoformat(),
                'updated': result.updated.isoformat(),
                'categories': result.categories,
                'primary_category': result.primary_category,
                'pdf_url': result.pdf_url,
                'entry_id': result.entry_id,
                'journal_ref': result.journal_ref,
                'doi': result.doi,
                'comment': result.comment,
                'links': [{'title': link.title, 'href': link.href} for link in result.links],
                'fetched_at': datetime.now().isoformat()
            }
            
            # Add formatted metadata
            paper['authors_str'] = ', '.join(paper['authors'][:3]) + ('...' if len(paper['authors']) > 3 else '')
            paper['categories_str'] = ', '.join(paper['categories'][:3]) + ('...' if len(paper['categories']) > 3 else '')
            paper['year'] = result.published.year
            paper['month'] = result.published.month
            
            return paper
            
        except Exception as e:
            print(f"Error extracting paper info: {e}")
            return {
                'arxiv_id': 'unknown',
                'title': 'Error extracting title',
                'authors': [],
                'summary': 'Error extracting summary',
                'error': str(e)
            }
    
    def download_pdf(self, paper: Dict[str, Any], download_dir: str = "downloads") -> Optional[str]:
        """
        Download PDF for a paper
        
        Args:
            paper: Paper dictionary
            download_dir: Directory to save PDF
            
        Returns:
            Path to downloaded PDF or None
        """
        try:
            import os
            os.makedirs(download_dir, exist_ok=True)
            
            pdf_url = paper.get('pdf_url')
            if not pdf_url:
                print(f"No PDF URL for paper: {paper.get('title', 'Unknown')}")
                return None
            
            arxiv_id = paper.get('arxiv_id', 'unknown')
            filename = f"{arxiv_id}.pdf"
            filepath = os.path.join(download_dir, filename)
            
            if os.path.exists(filepath):
                print(f"PDF already exists: {filepath}")
                return filepath
            
            print(f"Downloading PDF: {paper.get('title', 'Unknown')}")
            
            response = requests.get(pdf_url, timeout=30)
            response.raise_for_status()
            
            with open(filepath, 'wb') as f:
                f.write(response.content)
            
            print(f"PDF downloaded: {filepath}")
            return filepath
            
        except Exception as e:
            print(f"Error downloading PDF: {e}")
            return None
    
    def get_paper_recommendations(self, paper_id: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """
        Get paper recommendations based on a paper's content
        
        Args:
            paper_id: ArXiv ID of the base paper
            max_results: Number of recommendations
            
        Returns:
            List of recommended papers
        """
        try:
            # Get the base paper
            base_paper = self.get_paper_by_id(paper_id)
            if not base_paper:
                return []
            
            # Extract key terms from title and summary
            title = base_paper.get('title', '')
            summary = base_paper.get('summary', '')
            categories = base_paper.get('categories', [])
            
            # Simple keyword extraction (can be improved with NLP)
            keywords = self._extract_keywords(title + ' ' + summary)
            
            # Search for related papers
            query = ' '.join(keywords[:5])  # Use top 5 keywords
            
            related_papers = self.search_papers(
                query=query,
                max_results=max_results + 5,  # Get more to filter out the original
                sort_by="relevance"
            )
            
            # Filter out the original paper
            recommendations = [p for p in related_papers if p.get('arxiv_id') != paper_id]
            
            return recommendations[:max_results]
            
        except Exception as e:
            print(f"Error getting recommendations: {e}")
            return []
    
    def _extract_keywords(self, text: str) -> List[str]:
        """
        Simple keyword extraction from text
        
        Args:
            text: Input text
            
        Returns:
            List of keywords
        """
        # Simple implementation - can be improved with NLP libraries
        import re
        from collections import Counter
        
        # Remove common stop words
        stop_words = {'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'a', 'an', 'as', 'is', 'was', 'are', 'were', 'be', 'been', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'must', 'can', 'this', 'that', 'these', 'those', 'we', 'us', 'our', 'you', 'your', 'he', 'him', 'his', 'she', 'her', 'it', 'its', 'they', 'them', 'their'}
        
        # Extract words
        words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
        
        # Filter and count
        filtered_words = [word for word in words if word not in stop_words]
        word_counts = Counter(filtered_words)
        
        # Return most common words
        return [word for word, count in word_counts.most_common(20)]
    
    def get_categories(self) -> Dict[str, str]:
        """
        Get available ArXiv categories
        
        Returns:
            Dictionary of category codes and descriptions
        """
        return {
            'cs.AI': 'Artificial Intelligence',
            'cs.LG': 'Machine Learning',
            'cs.CV': 'Computer Vision',
            'cs.CL': 'Computation and Language',
            'cs.NE': 'Neural and Evolutionary Computing',
            'cs.RO': 'Robotics',
            'cs.CR': 'Cryptography and Security',
            'cs.DC': 'Distributed, Parallel, and Cluster Computing',
            'cs.DB': 'Databases',
            'cs.DS': 'Data Structures and Algorithms',
            'cs.HC': 'Human-Computer Interaction',
            'cs.IR': 'Information Retrieval',
            'cs.IT': 'Information Theory',
            'cs.MM': 'Multimedia',
            'cs.NI': 'Networking and Internet Architecture',
            'cs.OS': 'Operating Systems',
            'cs.PL': 'Programming Languages',
            'cs.SE': 'Software Engineering',
            'cs.SY': 'Systems and Control',
            'stat.ML': 'Machine Learning (Statistics)',
            'stat.AP': 'Applications (Statistics)',
            'stat.CO': 'Computation (Statistics)',
            'stat.ME': 'Methodology (Statistics)',
            'stat.TH': 'Statistics Theory',
            'math.ST': 'Statistics Theory (Mathematics)',
            'math.PR': 'Probability (Mathematics)',
            'math.OC': 'Optimization and Control',
            'math.NA': 'Numerical Analysis',
            'eess.AS': 'Audio and Speech Processing',
            'eess.IV': 'Image and Video Processing',
            'eess.SP': 'Signal Processing',
            'eess.SY': 'Systems and Control',
            'q-bio.QM': 'Quantitative Methods',
            'q-bio.NC': 'Neurons and Cognition',
            'physics.data-an': 'Data Analysis, Statistics and Probability'
        }
