"""
Groq Llama 3.3 70B integration component
"""

import os
from typing import Dict, List, Optional, Any
from datetime import datetime
import re

from groq import Groq
from langchain.llms.base import LLM
from langchain.schema import Document
from pydantic import Field

from .config import config


class GroqLlamaLLM(LLM):
    """LangChain-compatible wrapper for Groq Llama 3.3 70B"""

    api_key: str = Field(...)
    groq_client: Any = Field(default=None)
    model_name: str = Field(default="llama-3.3-70b-versatile")
    temperature: float = Field(default=0.7)
    max_tokens: int = Field(default=2000)
    top_p: float = Field(default=0.9)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.groq_client = Groq(api_key=self.api_key)

    class Config:
        arbitrary_types_allowed = True

    @property
    def _llm_type(self) -> str:
        return "groq_llama"

    def _call(self, prompt: str, stop: Optional[List[str]] = None) -> str:
        try:
            response = self.groq_client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}],
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                top_p=self.top_p,
                stop=stop
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Error: {str(e)}"

    @property
    def _identifying_params(self) -> Dict[str, Any]:
        return {
            "model_name": self.model_name,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "top_p": self.top_p
        }


class GroqProcessor:
    """Enhanced Groq Llama processor with research capabilities"""

    def __init__(self, config_obj=None):
        # Use passed config or default config
        self.config = config_obj if config_obj else config
        
        if not self.config.GROQ_API_KEY:
            raise ValueError("Groq API key not found! Please set GROQ_API_KEY environment variable.")

        self.groq_client = Groq(api_key=self.config.GROQ_API_KEY)
        self.llm = GroqLlamaLLM(
            api_key=self.config.GROQ_API_KEY,
            model_name=self.config.LLAMA_MODEL,
            temperature=self.config.TEMPERATURE,
            max_tokens=self.config.MAX_OUTPUT_TOKENS,
            top_p=self.config.TOP_P
        )
        print("Groq Llama 3.3 70B initialized successfully!")

    def generate_response(self, prompt: str, max_tokens: int = 2000) -> str:
        """Generate response using Groq Llama"""
        try:
            response = self.groq_client.chat.completions.create(
                model=self.config.LLAMA_MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=self.config.TEMPERATURE,
                max_tokens=max_tokens,
                top_p=self.config.TOP_P
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            return f"Error: {str(e)}"

    def summarize_paper(self, title: str, abstract: str, content: str) -> Dict[str, str]:
        """Generate comprehensive paper summary"""
        try:
            if len(content) > self.config.MAX_PAPER_LENGTH:
                content = content[:self.config.MAX_PAPER_LENGTH] + "..."

            prompt = f"""Analyze this research paper and provide a structured summary:

Title: {title}
Abstract: {abstract}
Content: {content[:8000]}

Provide a comprehensive summary with these sections:
1. **MAIN SUMMARY** (2-3 sentences)
2. **KEY CONTRIBUTIONS** (3-5 bullet points)
3. **METHODOLOGY** (brief description)
4. **KEY FINDINGS** (3-5 bullet points)
5. **LIMITATIONS** (if mentioned)

Format your response clearly with section headers."""

            response = self.generate_response(prompt, max_tokens=self.config.MAX_SUMMARY_LENGTH)
            return self._parse_summary_response(response, title, abstract)
        except Exception as e:
            return {
                'summary': f'Error generating summary: {str(e)}',
                'contributions': 'N/A',
                'methodology': 'N/A',
                'findings': 'N/A',
                'limitations': 'N/A',
                'title': title,
                'abstract': abstract
            }

    def _parse_summary_response(self, response: str, title: str, abstract: str) -> Dict[str, str]:
        """Parse AI response into structured summary"""
        sections = {
            'summary': '',
            'contributions': '',
            'methodology': '',
            'findings': '',
            'limitations': '',
            'title': title,
            'abstract': abstract
        }

        if "Error:" in response:
            return sections

        lines = response.split('\n')
        current_section = 'summary'

        for line in lines:
            line = line.strip()
            if not line:
                continue

            line_lower = line.lower()
            if any(keyword in line_lower for keyword in ['main summary', '1.', '**main']):
                current_section = 'summary'
                continue
            elif any(keyword in line_lower for keyword in ['key contributions', '2.', '**key contrib']):
                current_section = 'contributions'
                continue
            elif any(keyword in line_lower for keyword in ['methodology', '3.', '**method']):
                current_section = 'methodology'
                continue
            elif any(keyword in line_lower for keyword in ['key findings', 'findings', '4.', '**key find']):
                current_section = 'findings'
                continue
            elif any(keyword in line_lower for keyword in ['limitations', '5.', '**limit']):
                current_section = 'limitations'
                continue

            if not line.startswith(('1.', '2.', '3.', '4.', '5.', '**', '#')):
                sections[current_section] += line + ' '

        return sections

    def analyze_trends(self, texts: List[str]) -> Dict:
        """Analyze research trends from multiple texts"""
        try:
            combined_text = ' '.join(texts[:10])  # Limit to avoid token limits

            prompt = f"""Analyze research trends in this collection of texts:

{combined_text[:5000]}

Identify:
1. Key research themes and topics
2. Emerging trends and directions
3. Frequently mentioned technologies/methods
4. Research gaps or opportunities

Provide analysis as structured points."""

            response = self.generate_response(prompt, max_tokens=1500)

            return {
                'trend_analysis': response,
                'texts_analyzed': len(texts),
                'analysis_date': datetime.now().isoformat(),
                'keywords': self._extract_keywords(combined_text)
            }
        except Exception as e:
            return {
                'trend_analysis': f'Error: {str(e)}',
                'texts_analyzed': 0,
                'analysis_date': datetime.now().isoformat(),
                'keywords': []
            }

    def _extract_keywords(self, text: str) -> List[str]:
        """Extract keywords from text"""
        words = re.findall(r'\b[a-zA-Z]+\b', text.lower())
        stop_words = {'the', 'and', 'for', 'are', 'with', 'this', 'that', 'from', 'they', 'have'}
        keywords = [w for w in words if len(w) > 3 and w not in stop_words]

        # Count frequency and return top keywords
        word_counts = {}
        for word in keywords:
            word_counts[word] = word_counts.get(word, 0) + 1

        return [word for word, count in sorted(word_counts.items(), key=lambda x: x[1], reverse=True)[:20]]

    def answer_question(self, question: str, context: str = "") -> str:
        """Answer a question with optional context"""
        try:
            prompt = f"""Answer this research question based on the provided context:

Question: {question}

Context: {context[:4000] if context else 'No specific context provided'}

Provide a clear, informative answer based on the context and your knowledge."""

            return self.generate_response(prompt, max_tokens=1000)
        except Exception as e:
            return f"Error answering question: {str(e)}"

    def generate_literature_review(self, papers: List[Dict], research_question: str) -> str:
        """Generate literature review from papers"""
        try:
            papers_text = "\n".join([
                f"Title: {paper.get('title', '')}\nAbstract: {paper.get('abstract', '')}\n"
                for paper in papers[:10]
            ])

            prompt = f"""Generate a comprehensive literature review for the research question: "{research_question}"

Based on these papers:
{papers_text}

Provide a structured review with:
1. Introduction to the research area
2. Key themes and methodologies
3. Major findings and contributions
4. Research gaps and limitations
5. Future research directions
6. Conclusion

Keep it academic and well-structured."""

            return self.generate_response(prompt, max_tokens=3000)
        except Exception as e:
            return f"Error generating literature review: {str(e)}"

    def classify_paper(self, title: str, abstract: str) -> Dict[str, Any]:
        """Classify a paper into research categories"""
        try:
            prompt = f"""Classify this research paper:

Title: {title}
Abstract: {abstract}

Provide classification in JSON format:
{{
    "primary_field": "field name",
    "subfields": ["subfield1", "subfield2"],
    "methodology": "methodology type",
    "application_area": "application area",
    "novelty_score": 1-10,
    "impact_potential": "high/medium/low"
}}"""

            response = self.generate_response(prompt, max_tokens=500)
            
            # Try to parse as JSON, fallback to structured text
            try:
                import json
                return json.loads(response)
            except:
                return {
                    "classification": response,
                    "title": title,
                    "processed_at": datetime.now().isoformat()
                }
        except Exception as e:
            return {
                "error": f"Classification error: {str(e)}",
                "title": title,
                "processed_at": datetime.now().isoformat()
            }

    def get_research_recommendations(self, interests: List[str], recent_papers: List[Dict]) -> str:
        """Get personalized research recommendations"""
        try:
            interests_text = ", ".join(interests)
            papers_text = "\n".join([
                f"- {paper.get('title', '')}"
                for paper in recent_papers[:10]
            ])

            prompt = f"""Based on these research interests: {interests_text}

And these recent papers:
{papers_text}

Provide personalized research recommendations including:
1. Trending topics to explore
2. Potential research gaps
3. Collaboration opportunities
4. Methodological approaches to consider
5. Future research directions

Keep recommendations specific and actionable."""

            return self.generate_response(prompt, max_tokens=1500)
        except Exception as e:
            return f"Error generating recommendations: {str(e)}"
