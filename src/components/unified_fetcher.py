"""
Unified Research Paper Fetcher
Fetches papers from multiple sources: ArXiv, Semantic Scholar, Crossref, and PubMed
Replaces all previous fetcher components for maximum minimalism
"""

import re
import time
import requests
import xml.etree.ElementTree as ET
from typing import List, Dict, Optional, Any, Union
from datetime import datetime, timedelta
import arxiv
import json
from collections import Counter


class UnifiedPaperFetcher:
    """
    Unified fetcher for research papers from multiple academic databases
    Supports: ArXiv, Semantic Scholar, Crossref, PubMed
    """
    
    def __init__(self, config=None):
        # Import Config only when needed to avoid dependency issues
        if config is None:
            try:
                from .config import Config
                self.config = Config()
            except ImportError:
                self.config = None
        else:
            self.config = config
            
        # Initialize clients
        self.arxiv_client = arxiv.Client()
        
        # API endpoints
        self.semantic_scholar_base = "https://api.semanticscholar.org/graph/v1"
        self.crossref_base = "https://api.crossref.org/works"
        self.pubmed_base = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
        
        # Rate limiting
        self.last_request_time = {}
        self.min_request_interval = {
            'semantic_scholar': 5.0,  # 5 seconds between requests
            'crossref': 0.1,  # 100ms between requests (polite)
            'pubmed': 0.34,   # ~3 requests per second
            'arxiv': 3.0      # 3 seconds between requests
        }
    
    def search_papers(self, 
                     query: str, 
                     max_results: int = 10,
                     sources: List[str] = None,
                     sort_by: str = "relevance") -> List[Dict[str, Any]]:
        """
        Search for papers across multiple sources
        
        Args:
            query: Search query
            max_results: Maximum number of results per source
            sources: List of sources ['arxiv', 'semantic_scholar', 'crossref', 'pubmed']
            sort_by: Sort criteria
            
        Returns:
            List of paper dictionaries with unified format
        """
        if sources is None:
            sources = ['arxiv', 'semantic_scholar', 'crossref', 'pubmed']
        
        all_papers = []
        results_per_source = max(1, max_results // len(sources))
        
        print(f"Searching for: '{query}' across sources: {sources}")
        
        for source in sources:
            try:
                print(f"Searching {source}...")
                
                if source == 'arxiv':
                    papers = self._search_arxiv(query, results_per_source)
                elif source == 'semantic_scholar':
                    papers = self._search_semantic_scholar(query, results_per_source)
                elif source == 'crossref':
                    papers = self._search_crossref(query, results_per_source)
                elif source == 'pubmed':
                    papers = self._search_pubmed(query, results_per_source)
                else:
                    print(f"Unknown source: {source}")
                    continue
                
                print(f"Found {len(papers)} papers from {source}")
                all_papers.extend(papers)
                
            except Exception as e:
                print(f"Error searching {source}: {e}")
                continue
        
        # Remove duplicates and sort
        unique_papers = self._deduplicate_papers(all_papers)
        
        # Sort by relevance/date
        if sort_by == "date":
            unique_papers.sort(key=lambda x: x.get('published_date', ''), reverse=True)
        
        print(f"Total unique papers found: {len(unique_papers)}")
        return unique_papers[:max_results]
    
    def _search_arxiv(self, query: str, max_results: int) -> List[Dict[str, Any]]:
        """Search ArXiv"""
        self._rate_limit('arxiv')
        
        try:
            search = arxiv.Search(
                query=query,
                max_results=max_results,
                sort_by=arxiv.SortCriterion.Relevance,
                sort_order=arxiv.SortOrder.Descending
            )
            
            papers = []
            for result in self.arxiv_client.results(search):
                paper = {
                    'title': result.title,
                    'authors': [author.name for author in result.authors],
                    'abstract': result.summary,
                    'published_date': result.published.strftime('%Y-%m-%d'),
                    'year': result.published.year,
                    'url': result.entry_id,
                    'pdf_url': result.pdf_url,
                    'source': 'ArXiv',
                    'arxiv_id': result.entry_id.split('/')[-1],
                    'categories': [cat for cat in result.categories],
                    'doi': result.doi
                }
                papers.append(paper)
            
            return papers
            
        except Exception as e:
            print(f"ArXiv search error: {e}")
            return []
    
    def _search_semantic_scholar(self, query: str, max_results: int) -> List[Dict[str, Any]]:
        """Search Semantic Scholar"""
        self._rate_limit('semantic_scholar')
        
        try:
            url = f"{self.semantic_scholar_base}/paper/search"
            params = {
                'query': query,
                'limit': min(max_results, 100),
                'fields': 'title,authors,abstract,year,url,venue,citationCount,referenceCount,publicationDate,externalIds'
            }
            
            # Retry logic for rate limiting
            max_retries = 3
            data = None
            for attempt in range(max_retries):
                data = self.safe_get(url, params)
                if data and 'data' in data:
                    break
                elif attempt < max_retries - 1:
                    wait_time = (attempt + 1) * 5
                    print(f"Semantic Scholar rate limited, waiting {wait_time} seconds...")
                    time.sleep(wait_time)  # Exponential backoff
                else:
                    print("Semantic Scholar API unavailable after retries")
                    return []
            
            if not data or 'data' not in data:
                return []
            
            papers = []
            for paper_data in data.get('data', []):
                # Handle authors
                authors = []
                if paper_data.get('authors'):
                    authors = [author.get('name', 'Unknown') for author in paper_data['authors']]
                
                # Handle external IDs
                external_ids = paper_data.get('externalIds', {})
                doi = external_ids.get('DOI')
                arxiv_id = external_ids.get('ArXiv')
                
                paper = {
                    'title': paper_data.get('title', 'No title'),
                    'authors': authors,
                    'abstract': paper_data.get('abstract', ''),
                    'published_date': paper_data.get('publicationDate', ''),
                    'year': paper_data.get('year'),
                    'url': paper_data.get('url', ''),
                    'source': 'Semantic Scholar',
                    'venue': paper_data.get('venue', ''),
                    'citation_count': paper_data.get('citationCount', 0),
                    'reference_count': paper_data.get('referenceCount', 0),
                    'doi': doi,
                    'arxiv_id': arxiv_id
                }
                papers.append(paper)
            
            return papers
            
        except Exception as e:
            print(f"Semantic Scholar search error: {e}")
            return []
    
    def _search_crossref(self, query: str, max_results: int) -> List[Dict[str, Any]]:
        """Search Crossref"""
        self._rate_limit('crossref')
        
        try:
            url = self.crossref_base
            params = {
                'query': query,
                'rows': min(max_results, 20),
                'sort': 'relevance',
                'select': 'title,author,abstract,published-print,published-online,URL,DOI,container-title,type'
            }
            
            headers = {
                'User-Agent': 'ResearchMate/2.0 (mailto:research@example.com)'
            }
            
            response = requests.get(url, params=params, headers=headers, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            papers = []
            for item in data.get('message', {}).get('items', []):
                # Handle authors
                authors = []
                if item.get('author'):
                    for author in item['author']:
                        given = author.get('given', '')
                        family = author.get('family', '')
                        name = f"{given} {family}".strip()
                        if name:
                            authors.append(name)
                
                # Handle publication date
                published_date = ''
                year = None
                if item.get('published-print'):
                    date_parts = item['published-print'].get('date-parts', [[]])[0]
                    if date_parts:
                        year = date_parts[0]
                        if len(date_parts) >= 3:
                            published_date = f"{date_parts[0]:04d}-{date_parts[1]:02d}-{date_parts[2]:02d}"
                        elif len(date_parts) >= 2:
                            published_date = f"{date_parts[0]:04d}-{date_parts[1]:02d}-01"
                        else:
                            published_date = f"{date_parts[0]:04d}-01-01"
                
                paper = {
                    'title': item.get('title', ['No title'])[0] if item.get('title') else 'No title',
                    'authors': authors,
                    'abstract': item.get('abstract', ''),
                    'published_date': published_date,
                    'year': year,
                    'url': item.get('URL', ''),
                    'source': 'Crossref',
                    'doi': item.get('DOI', ''),
                    'journal': item.get('container-title', [''])[0] if item.get('container-title') else '',
                    'type': item.get('type', '')
                }
                papers.append(paper)
            
            return papers
            
        except Exception as e:
            print(f"Crossref search error: {e}")
            return []
    
    def _search_pubmed(self, query: str, max_results: int) -> List[Dict[str, Any]]:
        """Search PubMed"""
        self._rate_limit('pubmed')
        
        try:
            # Step 1: Search for PMIDs
            search_url = f"{self.pubmed_base}/esearch.fcgi"
            search_params = {
                'db': 'pubmed',
                'term': query,
                'retmax': min(max_results, 20),
                'retmode': 'json',
                'sort': 'relevance'
            }
            
            response = requests.get(search_url, params=search_params, timeout=30)
            response.raise_for_status()
            search_data = response.json()
            
            pmids = search_data.get('esearchresult', {}).get('idlist', [])
            if not pmids:
                return []
            
            # Step 2: Fetch details for PMIDs
            self._rate_limit('pubmed')
            fetch_url = f"{self.pubmed_base}/efetch.fcgi"
            fetch_params = {
                'db': 'pubmed',
                'id': ','.join(pmids),
                'retmode': 'xml'
            }
            
            response = requests.get(fetch_url, params=fetch_params, timeout=30)
            response.raise_for_status()
            
            # Parse XML
            root = ET.fromstring(response.content)
            papers = []
            
            for article in root.findall('.//PubmedArticle'):
                try:
                    # Extract basic info
                    medline = article.find('.//MedlineCitation')
                    if medline is None:
                        continue
                    
                    article_elem = medline.find('.//Article')
                    if article_elem is None:
                        continue
                    
                    # Title
                    title_elem = article_elem.find('.//ArticleTitle')
                    title = title_elem.text if title_elem is not None else 'No title'
                    
                    # Authors
                    authors = []
                    author_list = article_elem.find('.//AuthorList')
                    if author_list is not None:
                        for author in author_list.findall('.//Author'):
                            last_name = author.find('.//LastName')
                            first_name = author.find('.//ForeName')
                            if last_name is not None and first_name is not None:
                                authors.append(f"{first_name.text} {last_name.text}")
                            elif last_name is not None:
                                authors.append(last_name.text)
                    
                    # Abstract
                    abstract = ''
                    abstract_elem = article_elem.find('.//AbstractText')
                    if abstract_elem is not None:
                        abstract = abstract_elem.text or ''
                    
                    # Publication date
                    pub_date = article_elem.find('.//PubDate')
                    published_date = ''
                    year = None
                    if pub_date is not None:
                        year_elem = pub_date.find('.//Year')
                        month_elem = pub_date.find('.//Month')
                        day_elem = pub_date.find('.//Day')
                        
                        if year_elem is not None:
                            year = int(year_elem.text)
                            month = month_elem.text if month_elem is not None else '01'
                            day = day_elem.text if day_elem is not None else '01'
                            
                            # Convert month name to number if needed
                            month_map = {
                                'Jan': '01', 'Feb': '02', 'Mar': '03', 'Apr': '04',
                                'May': '05', 'Jun': '06', 'Jul': '07', 'Aug': '08',
                                'Sep': '09', 'Oct': '10', 'Nov': '11', 'Dec': '12'
                            }
                            if month in month_map:
                                month = month_map[month]
                            elif not month.isdigit():
                                month = '01'
                            
                            published_date = f"{year}-{month.zfill(2)}-{day.zfill(2)}"
                    
                    # PMID
                    pmid_elem = medline.find('.//PMID')
                    pmid = pmid_elem.text if pmid_elem is not None else ''
                    
                    # Journal
                    journal_elem = article_elem.find('.//Journal/Title')
                    journal = journal_elem.text if journal_elem is not None else ''
                    
                    # DOI
                    doi = ''
                    article_ids = article.findall('.//ArticleId')
                    for article_id in article_ids:
                        if article_id.get('IdType') == 'doi':
                            doi = article_id.text
                            break
                    
                    paper = {
                        'title': title,
                        'authors': authors,
                        'abstract': abstract,
                        'published_date': published_date,
                        'year': year,
                        'url': f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
                        'source': 'PubMed',
                        'pmid': pmid,
                        'journal': journal,
                        'doi': doi
                    }
                    papers.append(paper)
                    
                except Exception as e:
                    print(f"Error parsing PubMed article: {e}")
                    continue
            
            return papers
            
        except Exception as e:
            print(f"PubMed search error: {e}")
            return []
    
    def _rate_limit(self, source: str):
        """Implement rate limiting for API calls"""
        now = time.time()
        last_request = self.last_request_time.get(source, 0)
        interval = self.min_request_interval.get(source, 1.0)
        
        time_since_last = now - last_request
        if time_since_last < interval:
            sleep_time = interval - time_since_last
            time.sleep(sleep_time)
        
        self.last_request_time[source] = time.time()
    
    def safe_get(self, url: str, params: dict = None, headers: dict = None, timeout: int = 30) -> Optional[Dict[str, Any]]:
        """Safe HTTP GET with error handling"""
        try:
            response = requests.get(url, params=params, headers=headers, timeout=timeout)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"HTTP request failed: {e}")
            return None
        except json.JSONDecodeError as e:
            print(f"JSON decode error: {e}")
            return None
    
    def _deduplicate_papers(self, papers: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate papers based on title, DOI, or ArXiv ID"""
        seen = set()
        unique_papers = []
        
        for paper in papers:
            # Create identifier based on available fields
            identifiers = []
            # Use DOI if available
            doi = paper.get('doi')
            if doi is None:
                doi = ''
            doi = str(doi).strip()
            if doi:
                identifiers.append(f"doi:{doi.lower()}")
            # Use ArXiv ID if available
            arxiv_id = paper.get('arxiv_id')
            if arxiv_id is None:
                arxiv_id = ''
            arxiv_id = str(arxiv_id).strip()
            if arxiv_id:
                identifiers.append(f"arxiv:{arxiv_id.lower()}")
            # Use PMID if available
            pmid = paper.get('pmid')
            if pmid is None:
                pmid = ''
            pmid = str(pmid).strip()
            if pmid:
                identifiers.append(f"pmid:{pmid}")
            # Use title as fallback
            title = paper.get('title')
            if title is None:
                title = ''
            title = str(title).strip().lower()
            if title and title != 'no title':
                # Clean title for comparison
                clean_title = re.sub(r'[^\w\s]', '', title)
                clean_title = ' '.join(clean_title.split())
                identifiers.append(f"title:{clean_title}")
            # Check if any identifier has been seen
            found_duplicate = False
            for identifier in identifiers:
                if identifier in seen:
                    found_duplicate = True
                    break
            if not found_duplicate:
                # Add all identifiers to seen set
                for identifier in identifiers:
                    seen.add(identifier)
                unique_papers.append(paper)
        return unique_papers
    
    def get_paper_by_doi(self, doi: str) -> Optional[Dict[str, Any]]:
        """Get paper details by DOI from Crossref"""
        try:
            url = f"{self.crossref_base}/{doi}"
            headers = {
                'User-Agent': 'ResearchMate/2.0 (mailto:research@example.com)'
            }
            
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            item = data.get('message', {})
            if not item:
                return None
            
            # Parse the item (similar to _search_crossref)
            authors = []
            if item.get('author'):
                for author in item['author']:
                    given = author.get('given', '')
                    family = author.get('family', '')
                    name = f"{given} {family}".strip()
                    if name:
                        authors.append(name)
            
            # Handle publication date
            published_date = ''
            year = None
            if item.get('published-print'):
                date_parts = item['published-print'].get('date-parts', [[]])[0]
                if date_parts:
                    year = date_parts[0]
                    if len(date_parts) >= 3:
                        published_date = f"{date_parts[0]:04d}-{date_parts[1]:02d}-{date_parts[2]:02d}"
            
            paper = {
                'title': item.get('title', ['No title'])[0] if item.get('title') else 'No title',
                'authors': authors,
                'abstract': item.get('abstract', ''),
                'published_date': published_date,
                'year': year,
                'url': item.get('URL', ''),
                'source': 'Crossref',
                'doi': item.get('DOI', ''),
                'journal': item.get('container-title', [''])[0] if item.get('container-title') else ''
            }
            
            return paper
            
        except Exception as e:
            print(f"Error fetching DOI {doi}: {e}")
            return None


class PaperFetcher(UnifiedPaperFetcher):
    """
    Consolidated paper fetcher combining all sources
    This is the single fetcher class that replaces all previous fetcher components
    """
    
    def __init__(self, config=None):
        super().__init__(config)
    
    def search_papers(self, 
                     query: str, 
                     max_results: int = 10,
                     sources: List[str] = None,
                     sort_by: str = "relevance",
                     category: str = None,
                     date_range: int = None) -> List[Dict[str, Any]]:
        """
        Enhanced search with additional parameters from original ArxivFetcher
        
        Args:
            query: Search query
            max_results: Maximum number of results
            sources: List of sources ['arxiv', 'semantic_scholar', 'crossref', 'pubmed']
            sort_by: Sort criteria ('relevance', 'date', 'lastUpdatedDate', 'submittedDate')
            category: ArXiv category filter (e.g., 'cs.AI', 'cs.LG')
            date_range: Days back to search (e.g., 7, 30, 365)
            
        Returns:
            List of paper dictionaries with unified format
        """
        # Use all sources by default
        if sources is None:
            sources = ['arxiv', 'semantic_scholar', 'crossref', 'pubmed']
        
        # Apply category filter to ArXiv query if specified
        if category and 'arxiv' in sources:
            enhanced_query = f"cat:{category} AND {query}"
            return self._search_with_enhanced_query(enhanced_query, max_results, sources, sort_by, date_range)
        
        return super().search_papers(query, max_results, sources, sort_by)
    
    def _search_with_enhanced_query(self, query: str, max_results: int, sources: List[str], sort_by: str, date_range: int) -> List[Dict[str, Any]]:
        """Internal method for enhanced search with date filtering"""
        papers = super().search_papers(query, max_results, sources, sort_by)
        
        # Apply date filtering if specified
        if date_range:
            cutoff_date = datetime.now() - timedelta(days=date_range)
            filtered_papers = []
            for paper in papers:
                pub_date_str = paper.get('published_date', '')
                if pub_date_str:
                    try:
                        pub_date = datetime.strptime(pub_date_str, '%Y-%m-%d')
                        if pub_date >= cutoff_date:
                            filtered_papers.append(paper)
                    except ValueError:
                        # If date parsing fails, include the paper
                        filtered_papers.append(paper)
                else:
                    # If no date, include the paper
                    filtered_papers.append(paper)
            return filtered_papers
        
        return papers
    
    def get_paper_by_id(self, paper_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific paper by ID (supports ArXiv ID, DOI, PMID)
        
        Args:
            paper_id: Paper ID (ArXiv ID, DOI, or PMID)
            
        Returns:
            Paper dictionary or None
        """
        # Check if it's an ArXiv ID
        if re.match(r'^\d{4}\.\d{4,5}(v\d+)?$', paper_id):
            return self._get_arxiv_paper_by_id(paper_id)
        
        # Check if it's a DOI
        if '/' in paper_id and ('10.' in paper_id or paper_id.startswith('doi:')):
            doi = paper_id.replace('doi:', '')
            return self.get_paper_by_doi(doi)
        
        # Check if it's a PMID
        if paper_id.isdigit():
            return self._get_pubmed_paper_by_id(paper_id)
        
        # Fallback: search for it
        results = self.search_papers(paper_id, max_results=1)
        return results[0] if results else None
    
    def _get_arxiv_paper_by_id(self, arxiv_id: str) -> Optional[Dict[str, Any]]:
        """Get paper by ArXiv ID"""
        try:
            search = arxiv.Search(id_list=[arxiv_id])
            results = list(self.arxiv_client.results(search))
            
            if results:
                result = results[0]
                return {
                    'title': result.title,
                    'authors': [author.name for author in result.authors],
                    'abstract': result.summary,
                    'published_date': result.published.strftime('%Y-%m-%d'),
                    'year': result.published.year,
                    'url': result.entry_id,
                    'pdf_url': result.pdf_url,
                    'source': 'ArXiv',
                    'arxiv_id': result.entry_id.split('/')[-1],
                    'categories': [cat for cat in result.categories],
                    'doi': result.doi
                }
            return None
        except Exception as e:
            print(f"Error fetching ArXiv paper {arxiv_id}: {e}")
            return None
    
    def _get_pubmed_paper_by_id(self, pmid: str) -> Optional[Dict[str, Any]]:
        """Get paper by PubMed ID"""
        try:
            fetch_url = f"{self.pubmed_base}/efetch.fcgi"
            fetch_params = {
                'db': 'pubmed',
                'id': pmid,
                'retmode': 'xml'
            }
            
            response = requests.get(fetch_url, params=fetch_params, timeout=30)
            response.raise_for_status()
            
            root = ET.fromstring(response.content)
            article = root.find('.//PubmedArticle')
            
            if article is not None:
                # Parse similar to _search_pubmed
                medline = article.find('.//MedlineCitation')
                article_elem = medline.find('.//Article')
                
                title_elem = article_elem.find('.//ArticleTitle')
                title = title_elem.text if title_elem is not None else 'No title'
                
                authors = []
                author_list = article_elem.find('.//AuthorList')
                if author_list is not None:
                    for author in author_list.findall('.//Author'):
                        last_name = author.find('.//LastName')
                        first_name = author.find('.//ForeName')
                        if last_name is not None and first_name is not None:
                            authors.append(f"{first_name.text} {last_name.text}")
                
                abstract = ''
                abstract_elem = article_elem.find('.//AbstractText')
                if abstract_elem is not None:
                    abstract = abstract_elem.text or ''
                
                return {
                    'title': title,
                    'authors': authors,
                    'abstract': abstract,
                    'url': f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
                    'source': 'PubMed',
                    'pmid': pmid
                }
            return None
        except Exception as e:
            print(f"Error fetching PubMed paper {pmid}: {e}")
            return None
    
    def search_by_author(self, author: str, max_results: int = 20) -> List[Dict[str, Any]]:
        """
        Search for papers by author across all sources
        
        Args:
            author: Author name
            max_results: Maximum number of results
            
        Returns:
            List of paper dictionaries
        """
        return self.search_papers(f"author:{author}", max_results=max_results, sort_by="date")
    
    def search_by_category(self, category: str, max_results: int = 20) -> List[Dict[str, Any]]:
        """
        Search for papers by category (primarily ArXiv)
        
        Args:
            category: Category (e.g., 'cs.AI', 'cs.LG', 'stat.ML')
            max_results: Maximum number of results
            
        Returns:
            List of paper dictionaries
        """
        return self.search_papers("", max_results=max_results, category=category, sort_by="date")
    
    def get_trending_papers(self, category: str = "cs.AI", days: int = 7, max_results: int = 10) -> List[Dict[str, Any]]:
        """
        Get trending papers in a category
        
        Args:
            category: Category to search
            days: Days back to look for papers
            max_results: Maximum number of results
            
        Returns:
            List of paper dictionaries
        """
        return self.search_papers(
            query="recent",
            max_results=max_results,
            category=category,
            date_range=days,
            sort_by="date"
        )
    
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
            
            # Generate filename
            paper_id = paper.get('arxiv_id', paper.get('pmid', paper.get('doi', 'unknown')))
            filename = f"{paper_id}.pdf"
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
            paper_id: Paper ID
            max_results: Number of recommendations
            
        Returns:
            List of recommended papers
        """
        try:
            # Get the base paper
            base_paper = self.get_paper_by_id(paper_id)
            if not base_paper:
                return []
            
            # Extract key terms from title and abstract
            title = base_paper.get('title', '')
            abstract = base_paper.get('abstract', '')
            
            # Simple keyword extraction
            keywords = self._extract_keywords(title + ' ' + abstract)
            
            # Search for related papers
            query = ' '.join(keywords[:5])  # Use top 5 keywords
            
            related_papers = self.search_papers(
                query=query,
                max_results=max_results + 5,  # Get more to filter out the original
                sort_by="relevance"
            )
            
            # Filter out the original paper
            recommendations = [p for p in related_papers if p.get('arxiv_id') != paper_id and p.get('pmid') != paper_id]
            
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
        stop_words = {
            'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by',
            'a', 'an', 'as', 'is', 'was', 'are', 'were', 'be', 'been', 'have', 'has', 'had',
            'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'must',
            'can', 'this', 'that', 'these', 'those', 'we', 'us', 'our', 'you', 'your',
            'he', 'him', 'his', 'she', 'her', 'it', 'its', 'they', 'them', 'their'
        }
        
        # Extract words
        words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
        
        # Filter and count
        filtered_words = [word for word in words if word not in stop_words]
        word_counts = Counter(filtered_words)
        
        # Return most common words
        return [word for word, count in word_counts.most_common(20)]
    
    def get_categories(self) -> Dict[str, str]:
        """
        Get available categories (primarily ArXiv)
        
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


# Backward compatibility aliases
class ArxivFetcher(PaperFetcher):
    """Backward compatibility class for ArxivFetcher"""
    
    def __init__(self, config=None):
        super().__init__(config)
    
    def search_papers(self, query: str, max_results: int = 10, **kwargs) -> List[Dict[str, Any]]:
        """Search only ArXiv for backward compatibility"""
        return super().search_papers(query, max_results, sources=['arxiv'], **kwargs)


# Main class alias for the unified fetcher
UnifiedFetcher = PaperFetcher
