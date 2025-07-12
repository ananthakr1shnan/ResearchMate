import networkx as nx
import json
from datetime import datetime
from typing import List, Dict, Any
import matplotlib.pyplot as plt
from collections import defaultdict

class CitationNetworkAnalyzer:
    """Analyze citation networks and author collaborations - Web App Version"""

    def __init__(self):
        self.reset()
        print("✅ Citation network analyzer initialized (web app version)!")

    def reset(self):
        """Reset all data structures"""
        self.citation_graph = nx.DiGraph()
        self.author_graph = nx.Graph()
        self.paper_data = {}
        self.author_data = {}
        print("🔄 Citation network analyzer reset")

    def _safe_get_authors(self, paper: Dict) -> List[str]:
        """Safely extract and normalize author list from paper"""
        authors = paper.get('authors', [])

        # Handle None
        if authors is None:
            return []

        # Handle string (comma-separated)
        if isinstance(authors, str):
            if not authors.strip():
                return []
            return [a.strip() for a in authors.split(',') if a.strip()]

        # Handle list
        if isinstance(authors, list):
            result = []
            for author in authors:
                if isinstance(author, str) and author.strip():
                    result.append(author.strip())
                elif isinstance(author, dict):
                    # Handle author objects with 'name' field
                    name = author.get('name', '') or author.get('authorId', '')
                    if name and isinstance(name, str):
                        result.append(name.strip())
            return result

        # Unknown format
        return []

    def _safe_add_author(self, author_name: str, paper_id: str, citation_count: int = 0):
        """Safely add author to the graph"""
        try:
            # Initialize author data if not exists
            if author_name not in self.author_data:
                self.author_data[author_name] = {
                    'papers': [],
                    'total_citations': 0
                }

            # Add to NetworkX graph if not exists
            if not self.author_graph.has_node(author_name):
                self.author_graph.add_node(author_name)

            # Update author data
            if paper_id not in self.author_data[author_name]['papers']:
                self.author_data[author_name]['papers'].append(paper_id)
                self.author_data[author_name]['total_citations'] += citation_count

            return True

        except Exception as e:
            print(f"⚠️  Error adding author {author_name}: {e}")
            return False

    def _safe_add_collaboration(self, author1: str, author2: str, paper_id: str):
        """Safely add collaboration edge between authors"""
        try:
            # Ensure both authors exist
            if not self.author_graph.has_node(author1):
                self.author_graph.add_node(author1)
            if not self.author_graph.has_node(author2):
                self.author_graph.add_node(author2)

            # Add or update edge
            if self.author_graph.has_edge(author1, author2):
                # Update existing edge
                edge_data = self.author_graph.edges[author1, author2]
                edge_data['weight'] = edge_data.get('weight', 0) + 1
                if 'papers' not in edge_data:
                    edge_data['papers'] = []
                if paper_id not in edge_data['papers']:
                    edge_data['papers'].append(paper_id)
            else:
                # Add new edge
                self.author_graph.add_edge(author1, author2, weight=1, papers=[paper_id])

            return True

        except Exception as e:
            print(f"⚠️  Error adding collaboration {author1}-{author2}: {e}")
            return False

    def add_papers(self, papers: List[Dict]):
        """Add papers to the citation network"""
        if not papers:
            print("⚠️  No papers provided to add_papers")
            return

        processed_count = 0
        error_count = 0

        print(f"📝 Processing {len(papers)} papers...")

        for paper_idx, paper in enumerate(papers):
            try:
                # Validate paper input
                if not isinstance(paper, dict):
                    print(f"⚠️  Paper {paper_idx} is not a dict: {type(paper)}")
                    error_count += 1
                    continue

                # Generate paper ID
                paper_id = paper.get('paper_id')
                if not paper_id:
                    paper_id = paper.get('url', '')
                    if not paper_id:
                        title = paper.get('title', f'Unknown_{paper_idx}')
                        paper_id = f"paper_{abs(hash(title)) % 1000000}"

                # Store paper data
                self.paper_data[paper_id] = {
                    'title': paper.get('title', ''),
                    'authors': self._safe_get_authors(paper),
                    'year': paper.get('year'),
                    'venue': paper.get('venue', ''),
                    'citation_count': paper.get('citation_count', 0),
                    'source': paper.get('source', ''),
                    'url': paper.get('url', ''),
                    'abstract': paper.get('abstract', '')
                }

                # Add to citation graph
                self.citation_graph.add_node(paper_id, **self.paper_data[paper_id])

                # Process authors
                authors = self._safe_get_authors(paper)
                citation_count = paper.get('citation_count', 0)

                # Validate citation count
                if not isinstance(citation_count, (int, float)):
                    citation_count = 0

                # Add authors
                valid_authors = []
                for author in authors:
                    if self._safe_add_author(author, paper_id, citation_count):
                        valid_authors.append(author)

                # Add collaborations
                for i, author1 in enumerate(valid_authors):
                    for j, author2 in enumerate(valid_authors):
                        if i < j:  # Avoid duplicates and self-loops
                            self._safe_add_collaboration(author1, author2, paper_id)

                processed_count += 1

            except Exception as e:
                print(f"⚠️  Error processing paper {paper_idx}: {e}")
                error_count += 1
                continue

        print(f"✅ Successfully processed {processed_count} papers ({error_count} errors)")

    def analyze_author_network(self) -> Dict:
        """Analyze author collaboration network"""
        try:
            if len(self.author_graph.nodes) == 0:
                return {'error': 'No authors in network'}

            # Basic network metrics
            metrics = {
                'total_authors': len(self.author_graph.nodes),
                'total_collaborations': len(self.author_graph.edges),
                'network_density': nx.density(self.author_graph),
                'number_of_components': nx.number_connected_components(self.author_graph),
                'largest_component_size': len(max(nx.connected_components(self.author_graph), key=len)) if nx.number_connected_components(self.author_graph) > 0 else 0
            }

            # Most collaborative authors
            collaboration_counts = {node: self.author_graph.degree(node) for node in self.author_graph.nodes}
            top_collaborators = sorted(collaboration_counts.items(), key=lambda x: x[1], reverse=True)[:10]

            # Most productive authors
            productivity = {}
            for author, data in self.author_data.items():
                productivity[author] = len(data.get('papers', []))
            top_productive = sorted(productivity.items(), key=lambda x: x[1], reverse=True)[:10]

            # Most cited authors
            citation_counts = {}
            for author, data in self.author_data.items():
                citation_counts[author] = data.get('total_citations', 0)
            top_cited = sorted(citation_counts.items(), key=lambda x: x[1], reverse=True)[:10]

            return {
                'network_metrics': metrics,
                'top_collaborators': top_collaborators,
                'top_productive_authors': top_productive,
                'top_cited_authors': top_cited,
                'analysis_timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            return {
                'error': str(e),
                'analysis_timestamp': datetime.now().isoformat()
            }

    def analyze_paper_network(self) -> Dict:
        """Analyze paper citation network"""
        try:
            if len(self.citation_graph.nodes) == 0:
                return {'error': 'No papers in network'}

            # Basic network metrics
            metrics = {
                'total_papers': len(self.citation_graph.nodes),
                'total_citations': len(self.citation_graph.edges),
                'network_density': nx.density(self.citation_graph),
                'number_of_components': nx.number_weakly_connected_components(self.citation_graph),
                'largest_component_size': len(max(nx.weakly_connected_components(self.citation_graph), key=len)) if nx.number_weakly_connected_components(self.citation_graph) > 0 else 0
            }

            # Most cited papers
            in_degree = dict(self.citation_graph.in_degree())
            most_cited = sorted(in_degree.items(), key=lambda x: x[1], reverse=True)[:10]

            # Most citing papers
            out_degree = dict(self.citation_graph.out_degree())
            most_citing = sorted(out_degree.items(), key=lambda x: x[1], reverse=True)[:10]

            # Convert paper IDs to titles for readability
            most_cited_titles = []
            for paper_id, count in most_cited:
                if paper_id in self.paper_data:
                    most_cited_titles.append((self.paper_data[paper_id]['title'], count))
                else:
                    most_cited_titles.append((paper_id, count))

            most_citing_titles = []
            for paper_id, count in most_citing:
                if paper_id in self.paper_data:
                    most_citing_titles.append((self.paper_data[paper_id]['title'], count))
                else:
                    most_citing_titles.append((paper_id, count))

            return {
                'network_metrics': metrics,
                'most_cited_papers': most_cited_titles,
                'most_citing_papers': most_citing_titles,
                'analysis_timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            return {
                'error': str(e),
                'analysis_timestamp': datetime.now().isoformat()
            }

    def get_network_summary(self) -> Dict:
        """Get comprehensive network summary"""
        try:
            author_analysis = self.analyze_author_network()
            paper_analysis = self.analyze_paper_network()

            return {
                'author_network': author_analysis,
                'paper_network': paper_analysis,
                'overall_stats': {
                    'total_papers': len(self.paper_data),
                    'total_authors': len(self.author_data),
                    'papers_per_author': len(self.paper_data) / max(len(self.author_data), 1),
                    'collaborations_per_author': len(self.author_graph.edges) / max(len(self.author_graph.nodes), 1)
                },
                'analysis_timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            return {
                'error': str(e),
                'analysis_timestamp': datetime.now().isoformat()
            }