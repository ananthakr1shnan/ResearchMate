"""
Advanced Research Trend Monitor - Web App Version
Based on the notebook implementation with enhanced features
"""

import json
import time
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from collections import defaultdict, Counter
import re

# Optional imports for advanced features
try:
    import networkx as nx
    HAS_NETWORKX = True
except ImportError:
    HAS_NETWORKX = False
    print("⚠️  NetworkX not available - some advanced features disabled")

try:
    import matplotlib.pyplot as plt
    import seaborn as sns
    HAS_PLOTTING = True
except ImportError:
    HAS_PLOTTING = False
    print("⚠️  Matplotlib/Seaborn not available - plotting features disabled")

try:
    from wordcloud import WordCloud
    HAS_WORDCLOUD = True
except ImportError:
    HAS_WORDCLOUD = False
    print("⚠️  WordCloud not available - word cloud features disabled")

try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False
    print("⚠️  NumPy not available - some numerical features disabled")

class AdvancedTrendMonitor:
    """Advanced research trend monitoring with temporal analysis and gap detection"""

    def __init__(self, groq_processor=None):
        self.groq_processor = groq_processor
        self.trend_data = {}
        self.keyword_trends = defaultdict(list)
        self.temporal_data = defaultdict(list)
        self.gap_analysis_cache = {}
        print("✅ Advanced Research Trend Monitor initialized!")

    def analyze_temporal_trends(self, papers: List[Dict], timeframe: str = "yearly") -> Dict:
        """Analyze trends over time with sophisticated temporal analysis"""
        try:
            if not papers:
                return {'error': 'No papers provided for temporal analysis'}

            # Group papers by time period
            temporal_groups = defaultdict(list)
            year_counts = defaultdict(int)
            keyword_evolution = defaultdict(lambda: defaultdict(int))
            
            for paper in papers:
                year = paper.get('year')
                if not year:
                    continue
                
                # Handle different year formats
                if isinstance(year, str):
                    try:
                        year = int(year)
                    except ValueError:
                        continue
                
                if year < 1990 or year > 2030:  # Filter unrealistic years
                    continue
                
                temporal_groups[year].append(paper)
                year_counts[year] += 1
                
                # Track keyword evolution
                title = paper.get('title', '').lower()
                abstract = paper.get('abstract', '').lower()
                content = f"{title} {abstract}"
                
                # Extract keywords (simple approach)
                keywords = self._extract_keywords(content)
                for keyword in keywords:
                    keyword_evolution[year][keyword] += 1

            # Calculate trends
            trends = {
                'publication_trend': dict(sorted(year_counts.items())),
                'keyword_evolution': dict(keyword_evolution),
                'temporal_analysis': {},
                'growth_analysis': {},
                'emerging_topics': {},
                'declining_topics': {}
            }

            # Analyze publication growth
            years = sorted(year_counts.keys())
            if len(years) >= 2:
                recent_years = years[-3:]  # Last 3 years
                earlier_years = years[:-3] if len(years) > 3 else years[:-1]
                
                recent_avg = sum(year_counts[y] for y in recent_years) / len(recent_years)
                earlier_avg = sum(year_counts[y] for y in earlier_years) / len(earlier_years) if earlier_years else 0
                
                growth_rate = ((recent_avg - earlier_avg) / earlier_avg * 100) if earlier_avg > 0 else 0
                
                trends['growth_analysis'] = {
                    'recent_average': recent_avg,
                    'earlier_average': earlier_avg,
                    'growth_rate_percent': growth_rate,
                    'trend_direction': 'growing' if growth_rate > 5 else 'declining' if growth_rate < -5 else 'stable'
                }

            # Analyze emerging vs declining topics
            if len(years) >= 2:
                recent_year = years[-1]
                previous_year = years[-2] if len(years) > 1 else years[-1]
                
                recent_keywords = set(keyword_evolution[recent_year].keys())
                previous_keywords = set(keyword_evolution[previous_year].keys())
                
                emerging = recent_keywords - previous_keywords
                declining = previous_keywords - recent_keywords
                
                trends['emerging_topics'] = {
                    'topics': list(emerging)[:10],  # Top 10 emerging
                    'count': len(emerging)
                }
                
                trends['declining_topics'] = {
                    'topics': list(declining)[:10],  # Top 10 declining
                    'count': len(declining)
                }

            # Temporal analysis summary
            trends['temporal_analysis'] = {
                'total_years': len(years),
                'year_range': f"{min(years)}-{max(years)}" if years else "N/A",
                'peak_year': max(year_counts.items(), key=lambda x: x[1])[0] if year_counts else None,
                'total_papers': sum(year_counts.values()),
                'average_per_year': sum(year_counts.values()) / len(years) if years else 0
            }

            return trends

        except Exception as e:
            return {
                'error': f'Temporal trend analysis failed: {str(e)}',
                'analysis_timestamp': datetime.now().isoformat()
            }

    def detect_research_gaps(self, papers: List[Dict]) -> Dict:
        """Detect research gaps using advanced analysis"""
        try:
            if not papers:
                return {'error': 'No papers provided for gap analysis'}

            # Analyze methodologies
            methodologies = defaultdict(int)
            research_areas = defaultdict(int)
            data_types = defaultdict(int)
            evaluation_methods = defaultdict(int)
            
            # Common research area keywords
            area_keywords = {
                'natural_language_processing': ['nlp', 'language', 'text', 'linguistic'],
                'computer_vision': ['vision', 'image', 'visual', 'cv'],
                'machine_learning': ['ml', 'learning', 'algorithm', 'model'],
                'deep_learning': ['deep', 'neural', 'network', 'cnn', 'rnn'],
                'reinforcement_learning': ['reinforcement', 'rl', 'agent', 'policy'],
                'robotics': ['robot', 'robotic', 'manipulation', 'control'],
                'healthcare': ['medical', 'health', 'clinical', 'patient'],
                'finance': ['financial', 'trading', 'market', 'economic'],
                'security': ['security', 'privacy', 'attack', 'defense']
            }

            # Methodology keywords
            method_keywords = {
                'supervised_learning': ['supervised', 'classification', 'regression'],
                'unsupervised_learning': ['unsupervised', 'clustering', 'dimensionality'],
                'semi_supervised': ['semi-supervised', 'few-shot', 'zero-shot'],
                'transfer_learning': ['transfer', 'domain adaptation', 'fine-tuning'],
                'federated_learning': ['federated', 'distributed', 'decentralized'],
                'meta_learning': ['meta', 'learning to learn', 'few-shot'],
                'explainable_ai': ['explainable', 'interpretable', 'explanation'],
                'adversarial': ['adversarial', 'robust', 'attack']
            }

            # Analyze papers
            for paper in papers:
                content = f"{paper.get('title', '')} {paper.get('abstract', '')}".lower()
                
                # Count research areas
                for area, keywords in area_keywords.items():
                    if any(keyword in content for keyword in keywords):
                        research_areas[area] += 1
                
                # Count methodologies
                for method, keywords in method_keywords.items():
                    if any(keyword in content for keyword in keywords):
                        methodologies[method] += 1
                
                # Identify data types
                if 'dataset' in content or 'data' in content:
                    if any(word in content for word in ['text', 'corpus', 'language']):
                        data_types['text'] += 1
                    elif any(word in content for word in ['image', 'visual', 'video']):
                        data_types['image'] += 1
                    elif any(word in content for word in ['audio', 'speech', 'sound']):
                        data_types['audio'] += 1
                    elif any(word in content for word in ['sensor', 'iot', 'time series']):
                        data_types['sensor'] += 1
                    else:
                        data_types['tabular'] += 1

            # Identify gaps
            gaps = {
                'methodology_gaps': [],
                'research_area_gaps': [],
                'data_type_gaps': [],
                'interdisciplinary_gaps': [],
                'emerging_gaps': []
            }

            # Find underexplored methodologies
            total_papers = len(papers)
            for method, count in methodologies.items():
                coverage = (count / total_papers) * 100
                if coverage < 5:  # Less than 5% coverage
                    gaps['methodology_gaps'].append({
                        'method': method.replace('_', ' ').title(),
                        'coverage_percent': coverage,
                        'papers_count': count
                    })

            # Find underexplored research areas
            for area, count in research_areas.items():
                coverage = (count / total_papers) * 100
                if coverage < 10:  # Less than 10% coverage
                    gaps['research_area_gaps'].append({
                        'area': area.replace('_', ' ').title(),
                        'coverage_percent': coverage,
                        'papers_count': count
                    })

            # Find underexplored data types
            for dtype, count in data_types.items():
                coverage = (count / total_papers) * 100
                if coverage < 15:  # Less than 15% coverage
                    gaps['data_type_gaps'].append({
                        'data_type': dtype.replace('_', ' ').title(),
                        'coverage_percent': coverage,
                        'papers_count': count
                    })

            # Generate AI-powered gap analysis
            if self.groq_processor:
                ai_analysis = self._generate_ai_gap_analysis(papers, gaps)
                gaps['ai_analysis'] = ai_analysis

            gaps['analysis_summary'] = {
                'total_papers_analyzed': total_papers,
                'methodology_gaps_found': len(gaps['methodology_gaps']),
                'research_area_gaps_found': len(gaps['research_area_gaps']),
                'data_type_gaps_found': len(gaps['data_type_gaps']),
                'analysis_timestamp': datetime.now().isoformat()
            }

            return gaps

        except Exception as e:
            return {
                'error': f'Gap detection failed: {str(e)}',
                'analysis_timestamp': datetime.now().isoformat()
            }

    def generate_trend_report(self, papers: List[Dict]) -> Dict:
        """Generate comprehensive trend report"""
        try:
            if not papers:
                return {'error': 'No papers provided for trend report'}

            print(f"📊 Generating trend report for {len(papers)} papers...")

            # Run all analyses
            temporal_trends = self.analyze_temporal_trends(papers)
            research_gaps = self.detect_research_gaps(papers)
            
            # Generate keyword trends
            keyword_analysis = self._analyze_keyword_trends(papers)
            
            # Generate emerging topics
            emerging_topics = self._detect_emerging_topics(papers)
            
            # Generate AI-powered executive summary
            executive_summary = self._generate_executive_summary(papers, temporal_trends, research_gaps)

            # Compile comprehensive report
            report = {
                'executive_summary': executive_summary,
                'temporal_trends': temporal_trends,
                'research_gaps': research_gaps,
                'keyword_analysis': keyword_analysis,
                'emerging_topics': emerging_topics,
                'report_metadata': {
                    'papers_analyzed': len(papers),
                    'analysis_date': datetime.now().isoformat(),
                    'report_version': '2.0'
                }
            }

            return report

        except Exception as e:
            return {
                'error': f'Trend report generation failed: {str(e)}',
                'analysis_timestamp': datetime.now().isoformat()
            }

    def _extract_keywords(self, content: str) -> List[str]:
        """Extract keywords from content using simple NLP"""
        # Remove common words and extract meaningful terms
        stop_words = {'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'must', 'shall', 'can', 'this', 'that', 'these', 'those', 'we', 'they', 'our', 'their', 'using', 'based', 'approach', 'method', 'model', 'paper', 'study', 'research', 'work', 'results', 'show', 'propose', 'present'}
        
        # Extract words (simple tokenization)
        words = re.findall(r'\b[a-zA-Z]+\b', content.lower())
        
        # Filter keywords
        keywords = [word for word in words if len(word) > 3 and word not in stop_words]
        
        # Return top keywords
        return list(Counter(keywords).keys())[:20]

    def _analyze_keyword_trends(self, papers: List[Dict]) -> Dict:
        """Analyze keyword trends over time"""
        try:
            keyword_by_year = defaultdict(lambda: defaultdict(int))
            
            for paper in papers:
                year = paper.get('year')
                if not year:
                    continue
                
                content = f"{paper.get('title', '')} {paper.get('abstract', '')}".lower()
                keywords = self._extract_keywords(content)
                
                for keyword in keywords[:10]:  # Top 10 keywords per paper
                    keyword_by_year[year][keyword] += 1
            
            # Find trending keywords
            trending_keywords = {}
            for keyword in set().union(*[keywords.keys() for keywords in keyword_by_year.values()]):
                years = sorted(keyword_by_year.keys())
                if len(years) >= 2:
                    recent_count = keyword_by_year[years[-1]][keyword]
                    previous_count = keyword_by_year[years[-2]][keyword]
                    
                    if previous_count > 0:
                        trend = ((recent_count - previous_count) / previous_count) * 100
                        trending_keywords[keyword] = trend
            
            # Get top trending keywords
            top_trending = sorted(trending_keywords.items(), key=lambda x: x[1], reverse=True)[:10]
            
            return {
                'keyword_evolution': dict(keyword_by_year),
                'trending_keywords': top_trending,
                'analysis_timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                'error': f'Keyword trend analysis failed: {str(e)}',
                'analysis_timestamp': datetime.now().isoformat()
            }

    def _detect_emerging_topics(self, papers: List[Dict]) -> Dict:
        """Detect emerging research topics"""
        try:
            # Group papers by recent years
            recent_papers = []
            older_papers = []
            
            current_year = datetime.now().year
            
            for paper in papers:
                year = paper.get('year')
                if not year:
                    continue
                
                if isinstance(year, str):
                    try:
                        year = int(year)
                    except ValueError:
                        continue
                
                if year >= current_year - 2:  # Last 2 years
                    recent_papers.append(paper)
                else:
                    older_papers.append(paper)
            
            # Extract topics from recent vs older papers
            recent_topics = set()
            older_topics = set()
            
            for paper in recent_papers:
                content = f"{paper.get('title', '')} {paper.get('abstract', '')}".lower()
                topics = self._extract_keywords(content)
                recent_topics.update(topics[:5])  # Top 5 topics per paper
            
            for paper in older_papers:
                content = f"{paper.get('title', '')} {paper.get('abstract', '')}".lower()
                topics = self._extract_keywords(content)
                older_topics.update(topics[:5])
            
            # Find emerging topics (in recent but not in older)
            emerging = recent_topics - older_topics
            
            return {
                'emerging_topics': list(emerging)[:15],  # Top 15 emerging topics
                'recent_papers_count': len(recent_papers),
                'older_papers_count': len(older_papers),
                'analysis_timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                'error': f'Emerging topic detection failed: {str(e)}',
                'analysis_timestamp': datetime.now().isoformat()
            }

    def _generate_ai_gap_analysis(self, papers: List[Dict], gaps: Dict) -> str:
        """Generate AI-powered gap analysis"""
        try:
            if not self.groq_processor:
                return "AI analysis not available - Groq processor not initialized"
            
            # Prepare summary for AI analysis
            summary = f"""
            Research Gap Analysis Summary:
            - Total Papers Analyzed: {len(papers)}
            - Methodology Gaps Found: {len(gaps['methodology_gaps'])}
            - Research Area Gaps Found: {len(gaps['research_area_gaps'])}
            - Data Type Gaps Found: {len(gaps['data_type_gaps'])}
            
            Top Methodology Gaps:
            {', '.join([gap['method'] for gap in gaps['methodology_gaps'][:5]])}
            
            Top Research Area Gaps:
            {', '.join([gap['area'] for gap in gaps['research_area_gaps'][:5]])}
            """
            
            prompt = f"""Based on this research gap analysis, provide insights on:

{summary}

Please provide:
1. **Key Research Gaps**: Most significant gaps and why they matter
2. **Opportunities**: Potential research opportunities in underexplored areas
3. **Recommendations**: Specific recommendations for future research
4. **Priority Areas**: Which gaps should be prioritized and why

Format as a structured analysis."""

            response = self.groq_processor.generate_response(prompt, max_tokens=1500)
            return response

        except Exception as e:
            return f"AI gap analysis failed: {str(e)}"

    def _generate_executive_summary(self, papers: List[Dict], temporal_trends: Dict, research_gaps: Dict) -> str:
        """Generate executive summary of trend analysis"""
        try:
            if not self.groq_processor:
                return "Executive summary not available - Groq processor not initialized"
            
            # Prepare data for summary
            growth_info = temporal_trends.get('growth_analysis', {})
            gap_summary = research_gaps.get('analysis_summary', {})
            
            prompt = f"""Generate an executive summary for this research trend analysis:

Papers Analyzed: {len(papers)}
Publication Growth: {growth_info.get('trend_direction', 'unknown')} ({growth_info.get('growth_rate_percent', 0):.1f}%)
Research Gaps Found: {gap_summary.get('methodology_gaps_found', 0)} methodology gaps, {gap_summary.get('research_area_gaps_found', 0)} area gaps

Temporal Analysis:
- Year Range: {temporal_trends.get('temporal_analysis', {}).get('year_range', 'N/A')}
- Peak Year: {temporal_trends.get('temporal_analysis', {}).get('peak_year', 'N/A')}
- Average Papers/Year: {temporal_trends.get('temporal_analysis', {}).get('average_per_year', 0):.1f}

Provide a 3-paragraph executive summary covering:
1. Overall research landscape and trends
2. Key findings and patterns
3. Implications and future directions"""

            response = self.groq_processor.generate_response(prompt, max_tokens=1000)
            return response

        except Exception as e:
            return f"Executive summary generation failed: {str(e)}"

    def get_trend_summary(self) -> Dict:
        """Get summary of all trend data"""
        return {
            'total_trends_tracked': len(self.trend_data),
            'keyword_trends_count': len(self.keyword_trends),
            'temporal_data_points': sum(len(data) for data in self.temporal_data.values()),
            'last_analysis': datetime.now().isoformat()
        }
