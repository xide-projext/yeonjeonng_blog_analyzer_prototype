"""
SEO Analysis Service for Blog SEO Analyzer.

This module provides comprehensive SEO analysis including keyword density,
meta data optimization, heading structure, link analysis, and technical SEO.
"""

import logging
import re
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup, Comment
from textstat import flesch_reading_ease, flesch_kincaid_grade

from backend.shared.models import CrawlResult


logger = logging.getLogger(__name__)


class KeywordAnalyzer:
    """Analyzes keyword density and distribution."""
    
    def __init__(self, content: str, title: str = "", meta_description: str = ""):
        self.content = content.lower() if content else ""
        self.title = title.lower() if title else ""
        self.meta_description = meta_description.lower() if meta_description else ""
        self.word_count = len(self.content.split()) if self.content else 0
    
    def analyze_keyword_density(self, target_keywords: List[str] = None) -> Dict[str, Any]:
        """
        Analyze keyword density in content.
        
        Args:
            target_keywords: List of keywords to analyze specifically
            
        Returns:
            Dictionary with keyword density analysis
        """
        if not self.content:
            return {"error": "No content to analyze"}
        
        # Extract all words (2+ characters)
        words = re.findall(r'\b\w{2,}\b', self.content)
        total_words = len(words)
        
        if total_words == 0:
            return {"error": "No words found in content"}
        
        # Count word frequencies
        word_freq = {}
        for word in words:
            word_freq[word] = word_freq.get(word, 0) + 1
        
        # Calculate density for most common words
        keyword_density = {}
        for word, count in sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:20]:
            density = (count / total_words) * 100
            keyword_density[word] = {
                "count": count,
                "density": round(density, 2)
            }
        
        # Analyze target keywords if provided
        target_analysis = {}
        if target_keywords:
            for keyword in target_keywords:
                keyword_lower = keyword.lower()
                count = self.content.count(keyword_lower)
                density = (count / total_words) * 100 if total_words > 0 else 0
                
                # Check keyword placement
                in_title = keyword_lower in self.title
                in_meta = keyword_lower in self.meta_description
                
                target_analysis[keyword] = {
                    "count": count,
                    "density": round(density, 2),
                    "in_title": in_title,
                    "in_meta_description": in_meta,
                    "placement_score": self._calculate_placement_score(
                        keyword_lower, in_title, in_meta, density
                    )
                }
        
        return {
            "total_words": total_words,
            "unique_words": len(word_freq),
            "keyword_density": keyword_density,
            "target_keywords": target_analysis,
            "recommendations": self._get_keyword_recommendations(keyword_density, target_analysis)
        }
    
    def _calculate_placement_score(self, keyword: str, in_title: bool, 
                                   in_meta: bool, density: float) -> int:
        """Calculate keyword placement score (0-100)."""
        score = 0
        
        # Title placement (40 points)
        if in_title:
            score += 40
        
        # Meta description placement (20 points)
        if in_meta:
            score += 20
        
        # Density score (40 points)
        if 0.5 <= density <= 3.0:  # Optimal density range
            score += 40
        elif density > 3.0:  # Over-optimization penalty
            score += max(0, 40 - (density - 3.0) * 5)
        else:  # Under-optimization
            score += density * 20
        
        return min(100, int(score))
    
    def _get_keyword_recommendations(self, density: Dict[str, Any], 
                                     target: Dict[str, Any]) -> List[str]:
        """Generate keyword optimization recommendations."""
        recommendations = []
        
        # Check for keyword stuffing
        high_density_words = [
            word for word, data in density.items() 
            if data["density"] > 3.0
        ]
        if high_density_words:
            recommendations.append(
                f"Consider reducing density of: {', '.join(high_density_words[:3])}"
            )
        
        # Check target keyword optimization
        for keyword, data in target.items():
            if data["density"] < 0.5:
                recommendations.append(f"Consider increasing usage of '{keyword}'")
            if not data["in_title"]:
                recommendations.append(f"Consider adding '{keyword}' to title")
            if not data["in_meta_description"]:
                recommendations.append(f"Consider adding '{keyword}' to meta description")
        
        return recommendations


class MetaDataAnalyzer:
    """Analyzes meta data optimization."""
    
    def analyze_meta_data(self, soup: BeautifulSoup, crawl_result: CrawlResult) -> Dict[str, Any]:
        """
        Analyze meta data optimization.
        
        Args:
            soup: BeautifulSoup object of the page
            crawl_result: Crawling result with extracted data
            
        Returns:
            Dictionary with meta data analysis
        """
        analysis = {
            "title": self._analyze_title(crawl_result.title),
            "meta_description": self._analyze_meta_description(crawl_result.meta_description),
            "open_graph": self._analyze_open_graph(soup),
            "twitter_cards": self._analyze_twitter_cards(soup),
            "schema_markup": self._analyze_schema_markup(soup),
            "overall_score": 0
        }
        
        # Calculate overall meta score
        scores = []
        for key, value in analysis.items():
            if isinstance(value, dict) and "score" in value:
                scores.append(value["score"])
        
        analysis["overall_score"] = int(sum(scores) / len(scores)) if scores else 0
        
        return analysis
    
    def _analyze_title(self, title: str) -> Dict[str, Any]:
        """Analyze title tag optimization."""
        if not title:
            return {
                "score": 0,
                "length": 0,
                "issues": ["Missing title tag"],
                "recommendations": ["Add a descriptive title tag"]
            }
        
        length = len(title)
        score = 0
        issues = []
        recommendations = []
        
        # Length analysis
        if 30 <= length <= 60:
            score += 40
        elif length < 30:
            score += max(0, 40 - (30 - length) * 2)
            issues.append(f"Title too short ({length} chars)")
            recommendations.append("Consider expanding title to 30-60 characters")
        else:
            score += max(0, 40 - (length - 60) * 1)
            issues.append(f"Title too long ({length} chars)")
            recommendations.append("Consider shortening title to under 60 characters")
        
        # Content analysis
        if any(char.isupper() for char in title):
            score += 20
        else:
            issues.append("No capital letters in title")
            recommendations.append("Use proper capitalization")
        
        # Uniqueness (basic check)
        word_count = len(set(title.lower().split()))
        if word_count >= 3:
            score += 40
        else:
            issues.append("Title appears too generic")
            recommendations.append("Make title more specific and descriptive")
        
        return {
            "score": min(100, score),
            "length": length,
            "word_count": word_count,
            "issues": issues,
            "recommendations": recommendations
        }
    
    def _analyze_meta_description(self, description: str) -> Dict[str, Any]:
        """Analyze meta description optimization."""
        if not description:
            return {
                "score": 0,
                "length": 0,
                "issues": ["Missing meta description"],
                "recommendations": ["Add a compelling meta description"]
            }
        
        length = len(description)
        score = 0
        issues = []
        recommendations = []
        
        # Length analysis
        if 120 <= length <= 160:
            score += 50
        elif length < 120:
            score += max(0, 50 - (120 - length) * 0.5)
            issues.append(f"Meta description too short ({length} chars)")
            recommendations.append("Expand meta description to 120-160 characters")
        else:
            score += max(0, 50 - (length - 160) * 1)
            issues.append(f"Meta description too long ({length} chars)")
            recommendations.append("Shorten meta description to under 160 characters")
        
        # Content analysis
        if any(word in description.lower() for word in ['how', 'why', 'what', 'best', 'guide']):
            score += 25
        else:
            recommendations.append("Consider adding action words or benefits")
        
        if '.' in description or '!' in description or '?' in description:
            score += 25
        else:
            recommendations.append("Consider adding punctuation for better readability")
        
        return {
            "score": min(100, score),
            "length": length,
            "issues": issues,
            "recommendations": recommendations
        }
    
    def _analyze_open_graph(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Analyze Open Graph meta tags."""
        og_tags = {}
        for tag in soup.find_all("meta", property=lambda x: x and x.startswith("og:")):
            property_name = tag.get("property", "").replace("og:", "")
            og_tags[property_name] = tag.get("content", "")
        
        score = 0
        issues = []
        recommendations = []
        
        required_tags = ["title", "description", "url", "type"]
        for tag in required_tags:
            if tag in og_tags and og_tags[tag]:
                score += 25
            else:
                issues.append(f"Missing og:{tag}")
                recommendations.append(f"Add og:{tag} meta tag")
        
        return {
            "score": score,
            "tags": og_tags,
            "issues": issues,
            "recommendations": recommendations
        }
    
    def _analyze_twitter_cards(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Analyze Twitter Card meta tags."""
        twitter_tags = {}
        for tag in soup.find_all("meta", attrs={"name": lambda x: x and x.startswith("twitter:")}):
            name = tag.get("name", "").replace("twitter:", "")
            twitter_tags[name] = tag.get("content", "")
        
        score = 0
        if "card" in twitter_tags:
            score += 50
        if "title" in twitter_tags:
            score += 25
        if "description" in twitter_tags:
            score += 25
        
        return {
            "score": score,
            "tags": twitter_tags
        }
    
    def _analyze_schema_markup(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Analyze structured data markup."""
        schema_types = []
        
        # JSON-LD
        for script in soup.find_all("script", type="application/ld+json"):
            schema_types.append("JSON-LD")
        
        # Microdata
        for elem in soup.find_all(attrs={"itemtype": True}):
            schema_types.append("Microdata")
        
        # RDFa
        for elem in soup.find_all(attrs={"typeof": True}):
            schema_types.append("RDFa")
        
        score = min(100, len(schema_types) * 50)
        
        return {
            "score": score,
            "types": list(set(schema_types)),
            "count": len(schema_types)
        }


class HeadingAnalyzer:
    """Analyzes heading structure and hierarchy."""
    
    def analyze_headings(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """
        Analyze heading structure.
        
        Args:
            soup: BeautifulSoup object of the page
            
        Returns:
            Dictionary with heading analysis
        """
        headings = []
        for i in range(1, 7):
            heading_tags = soup.find_all(f"h{i}")
            for tag in heading_tags:
                headings.append({
                    "level": i,
                    "text": tag.get_text(strip=True),
                    "length": len(tag.get_text(strip=True))
                })
        
        analysis = {
            "headings": headings,
            "structure": self._analyze_structure(headings),
            "h1_analysis": self._analyze_h1(headings),
            "hierarchy_score": self._calculate_hierarchy_score(headings),
            "recommendations": []
        }
        
        analysis["recommendations"] = self._get_heading_recommendations(analysis)
        
        return analysis
    
    def _analyze_structure(self, headings: List[Dict]) -> Dict[str, Any]:
        """Analyze heading structure."""
        structure = {}
        for heading in headings:
            level = f"h{heading['level']}"
            if level not in structure:
                structure[level] = 0
            structure[level] += 1
        
        return structure
    
    def _analyze_h1(self, headings: List[Dict]) -> Dict[str, Any]:
        """Analyze H1 tags specifically."""
        h1_tags = [h for h in headings if h["level"] == 1]
        
        analysis = {
            "count": len(h1_tags),
            "score": 0,
            "issues": []
        }
        
        if len(h1_tags) == 1:
            analysis["score"] = 100
            h1 = h1_tags[0]
            if h1["length"] < 20:
                analysis["issues"].append("H1 tag is too short")
                analysis["score"] -= 20
            elif h1["length"] > 70:
                analysis["issues"].append("H1 tag is too long")
                analysis["score"] -= 10
        elif len(h1_tags) == 0:
            analysis["score"] = 0
            analysis["issues"].append("Missing H1 tag")
        else:
            analysis["score"] = 30
            analysis["issues"].append("Multiple H1 tags found")
        
        return analysis
    
    def _calculate_hierarchy_score(self, headings: List[Dict]) -> int:
        """Calculate heading hierarchy score."""
        if not headings:
            return 0
        
        score = 0
        
        # Check for logical hierarchy
        levels = [h["level"] for h in headings]
        
        # H1 should come first
        if levels and levels[0] == 1:
            score += 30
        
        # No skipped levels
        unique_levels = sorted(set(levels))
        if all(unique_levels[i] - unique_levels[i-1] <= 1 for i in range(1, len(unique_levels))):
            score += 40
        
        # Good distribution
        if len(unique_levels) >= 2:
            score += 30
        
        return score
    
    def _get_heading_recommendations(self, analysis: Dict) -> List[str]:
        """Generate heading recommendations."""
        recommendations = []
        
        if analysis["h1_analysis"]["count"] == 0:
            recommendations.append("Add an H1 tag to your page")
        elif analysis["h1_analysis"]["count"] > 1:
            recommendations.append("Use only one H1 tag per page")
        
        if analysis["hierarchy_score"] < 70:
            recommendations.append("Improve heading hierarchy structure")
        
        if not any(h["level"] == 2 for h in analysis["headings"]):
            recommendations.append("Consider adding H2 subheadings for better structure")
        
        return recommendations


class LinkAnalyzer:
    """Analyzes internal and external links."""
    
    def analyze_links(self, soup: BeautifulSoup, base_url: str) -> Dict[str, Any]:
        """
        Analyze link structure and quality.
        
        Args:
            soup: BeautifulSoup object of the page
            base_url: Base URL for relative link resolution
            
        Returns:
            Dictionary with link analysis
        """
        links = []
        base_domain = urlparse(base_url).netloc
        
        for link in soup.find_all("a", href=True):
            href = link["href"]
            text = link.get_text(strip=True)
            
            # Resolve relative URLs
            if href.startswith("/"):
                full_url = urljoin(base_url, href)
            else:
                full_url = href
            
            link_domain = urlparse(full_url).netloc
            is_internal = link_domain == base_domain or not link_domain
            
            links.append({
                "url": full_url,
                "text": text,
                "is_internal": is_internal,
                "has_text": bool(text),
                "is_nofollow": "nofollow" in link.get("rel", []),
                "opens_new_tab": link.get("target") == "_blank"
            })
        
        analysis = {
            "total_links": len(links),
            "internal_links": len([l for l in links if l["is_internal"]]),
            "external_links": len([l for l in links if not l["is_internal"]]),
            "links_with_text": len([l for l in links if l["has_text"]]),
            "nofollow_links": len([l for l in links if l["is_nofollow"]]),
            "links": links,
            "score": self._calculate_link_score(links),
            "recommendations": []
        }
        
        analysis["recommendations"] = self._get_link_recommendations(analysis)
        
        return analysis
    
    def _calculate_link_score(self, links: List[Dict]) -> int:
        """Calculate link optimization score."""
        if not links:
            return 50
        
        score = 0
        
        # Good ratio of internal to external links
        internal_count = len([l for l in links if l["is_internal"]])
        external_count = len([l for l in links if not l["is_internal"]])
        
        if internal_count > 0:
            score += 30
        
        if external_count > 0:
            score += 20
        
        # Links have descriptive text
        links_with_text = len([l for l in links if l["has_text"] and len(l["text"]) > 3])
        text_ratio = links_with_text / len(links) if links else 0
        score += int(text_ratio * 50)
        
        return min(100, score)
    
    def _get_link_recommendations(self, analysis: Dict) -> List[str]:
        """Generate link recommendations."""
        recommendations = []
        
        if analysis["internal_links"] == 0:
            recommendations.append("Add internal links to improve site navigation")
        
        if analysis["external_links"] == 0:
            recommendations.append("Consider adding relevant external links for authority")
        
        text_ratio = analysis["links_with_text"] / analysis["total_links"] if analysis["total_links"] else 0
        if text_ratio < 0.8:
            recommendations.append("Ensure all links have descriptive anchor text")
        
        return recommendations


class ReadabilityAnalyzer:
    """Analyzes content readability."""
    
    def analyze_readability(self, content: str) -> Dict[str, Any]:
        """
        Analyze content readability.
        
        Args:
            content: Text content to analyze
            
        Returns:
            Dictionary with readability analysis
        """
        if not content:
            return {"error": "No content to analyze"}
        
        # Basic statistics
        sentences = len(re.findall(r'[.!?]+', content))
        words = len(content.split())
        characters = len(content)
        
        # Readability scores
        flesch_score = flesch_reading_ease(content)
        fk_grade = flesch_kincaid_grade(content)
        
        # Paragraph analysis
        paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]
        avg_paragraph_length = sum(len(p.split()) for p in paragraphs) / len(paragraphs) if paragraphs else 0
        
        # Sentence analysis
        sentence_lengths = []
        for sentence in re.split(r'[.!?]+', content):
            if sentence.strip():
                sentence_lengths.append(len(sentence.split()))
        
        avg_sentence_length = sum(sentence_lengths) / len(sentence_lengths) if sentence_lengths else 0
        
        analysis = {
            "flesch_reading_ease": round(flesch_score, 1),
            "flesch_kincaid_grade": round(fk_grade, 1),
            "reading_level": self._get_reading_level(flesch_score),
            "statistics": {
                "characters": characters,
                "words": words,
                "sentences": sentences,
                "paragraphs": len(paragraphs),
                "avg_words_per_sentence": round(words / sentences, 1) if sentences else 0,
                "avg_words_per_paragraph": round(avg_paragraph_length, 1),
                "avg_sentence_length": round(avg_sentence_length, 1)
            },
            "score": self._calculate_readability_score(flesch_score, avg_sentence_length, avg_paragraph_length),
            "recommendations": []
        }
        
        analysis["recommendations"] = self._get_readability_recommendations(analysis)
        
        return analysis
    
    def _get_reading_level(self, flesch_score: float) -> str:
        """Convert Flesch score to reading level."""
        if flesch_score >= 90:
            return "Very Easy"
        elif flesch_score >= 80:
            return "Easy"
        elif flesch_score >= 70:
            return "Fairly Easy"
        elif flesch_score >= 60:
            return "Standard"
        elif flesch_score >= 50:
            return "Fairly Difficult"
        elif flesch_score >= 30:
            return "Difficult"
        else:
            return "Very Difficult"
    
    def _calculate_readability_score(self, flesch_score: float, 
                                     avg_sentence_length: float, 
                                     avg_paragraph_length: float) -> int:
        """Calculate overall readability score."""
        score = 0
        
        # Flesch Reading Ease score (50 points)
        if 60 <= flesch_score <= 80:  # Standard to Easy
            score += 50
        elif flesch_score > 80:  # Very easy
            score += 40
        elif flesch_score >= 50:  # Fairly difficult
            score += 35
        else:  # Difficult
            score += 20
        
        # Sentence length (25 points)
        if 15 <= avg_sentence_length <= 25:  # Optimal
            score += 25
        elif avg_sentence_length < 15:  # Too short
            score += 15
        else:  # Too long
            score += max(0, 25 - (avg_sentence_length - 25))
        
        # Paragraph length (25 points)
        if 50 <= avg_paragraph_length <= 150:  # Optimal
            score += 25
        elif avg_paragraph_length < 50:  # Too short
            score += 15
        else:  # Too long
            score += max(0, 25 - (avg_paragraph_length - 150) // 10)
        
        return min(100, score)
    
    def _get_readability_recommendations(self, analysis: Dict) -> List[str]:
        """Generate readability recommendations."""
        recommendations = []
        
        if analysis["flesch_reading_ease"] < 50:
            recommendations.append("Simplify language and use shorter sentences")
        
        avg_sentence = analysis["statistics"]["avg_sentence_length"]
        if avg_sentence > 25:
            recommendations.append("Break down long sentences for better readability")
        
        avg_paragraph = analysis["statistics"]["avg_words_per_paragraph"]
        if avg_paragraph > 150:
            recommendations.append("Break down long paragraphs into smaller ones")
        
        return recommendations


class SEOAnalyzer:
    """Main SEO analyzer that combines all analysis modules."""
    
    def __init__(self):
        self.keyword_analyzer = None
        self.meta_analyzer = MetaDataAnalyzer()
        self.heading_analyzer = HeadingAnalyzer()
        self.link_analyzer = LinkAnalyzer()
        self.readability_analyzer = ReadabilityAnalyzer()
    
    def analyze(self, crawl_result: CrawlResult, target_keywords: List[str] = None) -> Dict[str, Any]:
        """
        Perform comprehensive SEO analysis.
        
        Args:
            crawl_result: Result from web crawling
            target_keywords: Optional list of target keywords
            
        Returns:
            Dictionary with complete SEO analysis
        """
        if not crawl_result.success:
            return {"error": f"Crawling failed: {crawl_result.error_message}"}
        
        # Parse HTML for detailed analysis
        soup = BeautifulSoup(crawl_result.content or "", "html.parser") if crawl_result.content else None
        
        if not soup:
            return {"error": "No content to analyze"}
        
        # Initialize keyword analyzer
        self.keyword_analyzer = KeywordAnalyzer(
            crawl_result.content or "",
            crawl_result.title or "",
            crawl_result.meta_description or ""
        )
        
        # Perform all analyses
        analysis = {
            "url": crawl_result.url,
            "timestamp": crawl_result,
            "keyword_analysis": self.keyword_analyzer.analyze_keyword_density(target_keywords),
            "meta_analysis": self.meta_analyzer.analyze_meta_data(soup, crawl_result),
            "heading_analysis": self.heading_analyzer.analyze_headings(soup),
            "link_analysis": self.link_analyzer.analyze_links(soup, crawl_result.url),
            "readability_analysis": self.readability_analyzer.analyze_readability(crawl_result.content or ""),
            "technical_seo": self._analyze_technical_seo(soup, crawl_result),
            "overall_score": 0,
            "recommendations": []
        }
        
        # Calculate overall score
        analysis["overall_score"] = self._calculate_overall_score(analysis)
        
        # Generate recommendations
        analysis["recommendations"] = self._generate_recommendations(analysis)
        
        return analysis
    
    def _analyze_technical_seo(self, soup: BeautifulSoup, crawl_result: CrawlResult) -> Dict[str, Any]:
        """Analyze technical SEO factors."""
        analysis = {
            "page_speed": {"score": 85, "issues": []},  # Placeholder - would integrate with PageSpeed API
            "mobile_friendly": {"score": 90, "issues": []},  # Placeholder - would check viewport etc.
            "ssl": {"enabled": crawl_result.url.startswith("https://"), "score": 100 if crawl_result.url.startswith("https://") else 0},
            "url_structure": self._analyze_url_structure(crawl_result.url),
            "images": self._analyze_images(soup)
        }
        
        return analysis
    
    def _analyze_url_structure(self, url: str) -> Dict[str, Any]:
        """Analyze URL structure."""
        parsed = urlparse(url)
        path = parsed.path
        
        score = 0
        issues = []
        
        # Length check
        if len(url) <= 100:
            score += 30
        else:
            issues.append("URL too long")
        
        # Readable structure
        if re.match(r'^/[\w\-/]*$', path):
            score += 30
        else:
            issues.append("URL contains special characters")
        
        # Keyword presence (basic check)
        if len([p for p in path.split('/') if len(p) > 2]) >= 1:
            score += 40
        
        return {
            "score": score,
            "length": len(url),
            "issues": issues
        }
    
    def _analyze_images(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Analyze image optimization."""
        images = soup.find_all("img")
        total_images = len(images)
        
        if total_images == 0:
            return {"score": 100, "total_images": 0, "issues": []}
        
        images_with_alt = len([img for img in images if img.get("alt")])
        alt_ratio = images_with_alt / total_images
        
        score = int(alt_ratio * 100)
        issues = []
        
        if alt_ratio < 1.0:
            issues.append(f"{total_images - images_with_alt} images missing alt text")
        
        return {
            "score": score,
            "total_images": total_images,
            "images_with_alt": images_with_alt,
            "alt_ratio": round(alt_ratio, 2),
            "issues": issues
        }
    
    def _calculate_overall_score(self, analysis: Dict[str, Any]) -> int:
        """Calculate overall SEO score."""
        scores = []
        weights = {
            "meta_analysis": 0.25,
            "heading_analysis": 0.15,
            "keyword_analysis": 0.20,
            "link_analysis": 0.15,
            "readability_analysis": 0.15,
            "technical_seo": 0.10
        }
        
        for key, weight in weights.items():
            if key in analysis and isinstance(analysis[key], dict):
                if "score" in analysis[key]:
                    scores.append(analysis[key]["score"] * weight)
                elif "overall_score" in analysis[key]:
                    scores.append(analysis[key]["overall_score"] * weight)
                elif key == "heading_analysis" and "hierarchy_score" in analysis[key]:
                    scores.append(analysis[key]["hierarchy_score"] * weight)
        
        return int(sum(scores)) if scores else 0
    
    def _generate_recommendations(self, analysis: Dict[str, Any]) -> List[str]:
        """Generate overall recommendations."""
        recommendations = []
        
        # Collect recommendations from all modules
        for module_name, module_data in analysis.items():
            if isinstance(module_data, dict) and "recommendations" in module_data:
                recommendations.extend(module_data["recommendations"])
        
        # Add overall recommendations based on score
        if analysis["overall_score"] < 50:
            recommendations.insert(0, "Focus on improving meta tags and content structure")
        elif analysis["overall_score"] < 70:
            recommendations.insert(0, "Good foundation - focus on keyword optimization and readability")
        elif analysis["overall_score"] < 90:
            recommendations.insert(0, "Strong SEO - fine-tune technical aspects for perfection")
        
        return recommendations[:10]  # Limit to top 10 recommendations 