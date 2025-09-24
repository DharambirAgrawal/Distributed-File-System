"""
Search algorithms for the AI Research Assistant
Implements BFS, DFS, and A* search for document retrieval
"""

import re
import time
from collections import deque
from difflib import SequenceMatcher
from db.database import get_db_cursor


class SearchResult:
    """Represents a search result with metadata"""
    def __init__(self, document_id, file_name, tags, summary, full_text_content, 
                 match_score=0.0, match_context="", match_type=""):
        self.document_id = document_id
        self.file_name = file_name
        self.tags = tags or []
        self.summary = summary or ""
        self.full_text_content = full_text_content or ""
        self.match_score = match_score
        self.match_context = match_context
        self.match_type = match_type
    
    def to_dict(self):
        return {
            'document_id': self.document_id,
            'file_name': self.file_name,
            'tags': self.tags,
            'summary': self.summary,
            'match_score': self.match_score,
            'match_context': self.match_context,
            'match_type': self.match_type
        }


class DocumentSearcher:
    """Main search engine class"""
    
    def __init__(self):
        self.algorithms = {
            'bfs': self.breadth_first_search,
            'dfs': self.depth_first_search,
            'astar': self.a_star_search
        }
    
    def search(self, user_id, query, algorithm='bfs', limit=50):
        """
        Main search interface
        
        Args:
            user_id: ID of the user performing the search
            query: Search query string
            algorithm: Search algorithm to use ('bfs', 'dfs', 'astar')
            limit: Maximum number of results to return
            
        Returns:
            List of SearchResult objects
        """
        start_time = time.time()
        
        # Get user's documents from database
        documents = self._get_user_documents(user_id)
        
        # Perform search using selected algorithm
        if algorithm in self.algorithms:
            results = self.algorithms[algorithm](documents, query, limit)
        else:
            raise ValueError(f"Unknown algorithm: {algorithm}")
        
        # Calculate execution time
        execution_time = int((time.time() - start_time) * 1000)  # in milliseconds
        
        # Log the search
        self._log_search(user_id, query, algorithm, len(results), execution_time)
        
        return results
    
    def _get_user_documents(self, user_id):
        """Retrieve all documents for a user from the database"""
        try:
            with get_db_cursor() as cursor:
                cursor.execute("""
                    SELECT d.id, d.file_name, d.summary, d.full_text_content
                    FROM documents d
                    WHERE d.user_id = %s
                    ORDER BY d.created_at DESC
                """, (user_id,))

                documents = []
                for row in cursor.fetchall() or []:
                    doc = {
                        'id': row['id'],
                        'file_name': row['file_name'],
                        'summary': row.get('summary') or '',
                        'full_text_content': row.get('full_text_content') or '',
                        'tags': []
                    }

                    cursor.execute(
                        "SELECT tag FROM tags WHERE document_id = %s ORDER BY id",
                        (doc['id'],)
                    )
                    tag_rows = cursor.fetchall() or []
                    doc['tags'] = [tag_row['tag'] for tag_row in tag_rows if tag_row.get('tag') is not None]

                    documents.append(doc)

                return documents
        except Exception as e:
            print(f"Error retrieving documents: {e}")
            return []
    
    def breadth_first_search(self, documents, query, limit):
        """
        BFS: Search documents level by level
        Priority: file_name -> tags -> summary -> full_text_content
        """
        results = []
        query_lower = query.lower()
        
        # Level 1: Search in file names
        for doc in documents:
            if query_lower in doc['file_name'].lower():
                context = self._get_context_snippet(doc['file_name'], query, 50)
                score = self._calculate_similarity_score(query, doc['file_name'])
                results.append(SearchResult(
                    doc['id'], doc['file_name'], doc['tags'], doc['summary'],
                    doc['full_text_content'], score, context, "filename"
                ))
        
        # Level 2: Search in tags
        if len(results) < limit:
            for doc in documents:
                if any(query_lower in tag.lower() for tag in doc['tags']):
                    # Skip if already found in filename
                    if not any(r.document_id == doc['id'] for r in results):
                        matching_tags = [tag for tag in doc['tags'] if query_lower in tag.lower()]
                        context = f"Tags: {', '.join(matching_tags)}"
                        score = max(self._calculate_similarity_score(query, tag) for tag in matching_tags)
                        results.append(SearchResult(
                            doc['id'], doc['file_name'], doc['tags'], doc['summary'],
                            doc['full_text_content'], score, context, "tags"
                        ))
        
        # Level 3: Search in summary
        if len(results) < limit:
            for doc in documents:
                if doc['summary'] and query_lower in doc['summary'].lower():
                    # Skip if already found
                    if not any(r.document_id == doc['id'] for r in results):
                        context = self._get_context_snippet(doc['summary'], query, 100)
                        score = self._calculate_similarity_score(query, doc['summary'])
                        results.append(SearchResult(
                            doc['id'], doc['file_name'], doc['tags'], doc['summary'],
                            doc['full_text_content'], score, context, "summary"
                        ))
        
        # Level 4: Search in full text content
        if len(results) < limit:
            for doc in documents:
                if doc['full_text_content'] and query_lower in doc['full_text_content'].lower():
                    # Skip if already found
                    if not any(r.document_id == doc['id'] for r in results):
                        context = self._get_context_snippet(doc['full_text_content'], query, 150)
                        score = self._calculate_similarity_score(query, doc['full_text_content'])
                        results.append(SearchResult(
                            doc['id'], doc['file_name'], doc['tags'], doc['summary'],
                            doc['full_text_content'], score, context, "content"
                        ))
        
        return sorted(results, key=lambda x: x.match_score, reverse=True)[:limit]
    
    def depth_first_search(self, documents, query, limit):
        """
        DFS: Search deeply in each document before moving to next
        For each document, search: file_name -> tags -> summary -> full_text_content
        """
        results = []
        query_lower = query.lower()
        
        for doc in documents:
            if len(results) >= limit:
                break
            
            # Search filename first
            if query_lower in doc['file_name'].lower():
                context = self._get_context_snippet(doc['file_name'], query, 50)
                score = self._calculate_similarity_score(query, doc['file_name'])
                results.append(SearchResult(
                    doc['id'], doc['file_name'], doc['tags'], doc['summary'],
                    doc['full_text_content'], score, context, "filename"
                ))
                continue
            
            # Search tags
            matching_tags = [tag for tag in doc['tags'] if query_lower in tag.lower()]
            if matching_tags:
                context = f"Tags: {', '.join(matching_tags)}"
                score = max(self._calculate_similarity_score(query, tag) for tag in matching_tags)
                results.append(SearchResult(
                    doc['id'], doc['file_name'], doc['tags'], doc['summary'],
                    doc['full_text_content'], score, context, "tags"
                ))
                continue
            
            # Search summary
            if doc['summary'] and query_lower in doc['summary'].lower():
                context = self._get_context_snippet(doc['summary'], query, 100)
                score = self._calculate_similarity_score(query, doc['summary'])
                results.append(SearchResult(
                    doc['id'], doc['file_name'], doc['tags'], doc['summary'],
                    doc['full_text_content'], score, context, "summary"
                ))
                continue
            
            # Search full text content
            if doc['full_text_content'] and query_lower in doc['full_text_content'].lower():
                context = self._get_context_snippet(doc['full_text_content'], query, 150)
                score = self._calculate_similarity_score(query, doc['full_text_content'])
                results.append(SearchResult(
                    doc['id'], doc['file_name'], doc['tags'], doc['summary'],
                    doc['full_text_content'], score, context, "content"
                ))
        
        return sorted(results, key=lambda x: x.match_score, reverse=True)[:limit]
    
    def a_star_search(self, documents, query, limit):
        """
        A* Search: Uses heuristic function to prioritize documents
        Heuristic: combination of similarity score and content relevance
        """
        query_lower = query.lower()
        query_words = set(query_lower.split())
        
        # Calculate heuristic score for each document
        document_scores = []
        
        for doc in documents:
            # Calculate heuristic score (f = g + h)
            g_score = 0  # Cost so far (inverse of document position)
            h_score = self._calculate_heuristic(doc, query, query_words)
            f_score = g_score + h_score
            
            document_scores.append((f_score, doc))
        
        # Sort by f_score (highest first)
        document_scores.sort(key=lambda x: x[0], reverse=True)
        
        results = []
        for f_score, doc in document_scores[:limit]:
            if len(results) >= limit:
                break
            
            # Find the best match within this document
            best_match = self._find_best_match_in_document(doc, query, query_lower)
            if best_match:
                results.append(best_match)
        
        return results
    
    def _calculate_heuristic(self, doc, query, query_words):
        """Calculate heuristic score for A* search"""
        score = 0
        
        # Filename relevance (highest weight)
        filename_words = set(doc['file_name'].lower().split())
        filename_overlap = len(query_words.intersection(filename_words))
        score += filename_overlap * 10
        
        # Tag relevance
        tag_words = set()
        for tag in doc['tags']:
            tag_words.update(tag.lower().split())
        tag_overlap = len(query_words.intersection(tag_words))
        score += tag_overlap * 8
        
        # Summary relevance
        if doc['summary']:
            summary_words = set(doc['summary'].lower().split())
            summary_overlap = len(query_words.intersection(summary_words))
            score += summary_overlap * 5
        
        # Content relevance (word frequency)
        if doc['full_text_content']:
            content_words = doc['full_text_content'].lower().split()
            for word in query_words:
                word_count = content_words.count(word)
                score += word_count * 2
        
        # Length penalty (shorter documents are often more relevant)
        if doc['full_text_content']:
            length_penalty = len(doc['full_text_content']) / 10000  # Normalize
            score -= length_penalty
        
        return score
    
    def _find_best_match_in_document(self, doc, query, query_lower):
        """Find the best match within a document for A* search"""
        matches = []
        
        # Check filename
        if query_lower in doc['file_name'].lower():
            context = self._get_context_snippet(doc['file_name'], query, 50)
            score = self._calculate_similarity_score(query, doc['file_name'])
            matches.append(('filename', score, context))
        
        # Check tags
        matching_tags = [tag for tag in doc['tags'] if query_lower in tag.lower()]
        if matching_tags:
            context = f"Tags: {', '.join(matching_tags)}"
            score = max(self._calculate_similarity_score(query, tag) for tag in matching_tags)
            matches.append(('tags', score, context))
        
        # Check summary
        if doc['summary'] and query_lower in doc['summary'].lower():
            context = self._get_context_snippet(doc['summary'], query, 100)
            score = self._calculate_similarity_score(query, doc['summary'])
            matches.append(('summary', score, context))
        
        # Check content
        if doc['full_text_content'] and query_lower in doc['full_text_content'].lower():
            context = self._get_context_snippet(doc['full_text_content'], query, 150)
            score = self._calculate_similarity_score(query, doc['full_text_content'])
            matches.append(('content', score, context))
        
        if matches:
            # Return the best match
            best_match = max(matches, key=lambda x: x[1])
            return SearchResult(
                doc['id'], doc['file_name'], doc['tags'], doc['summary'],
                doc['full_text_content'], best_match[1], best_match[2], best_match[0]
            )
        
        return None
    
    def _calculate_similarity_score(self, query, text):
        """Calculate similarity score between query and text"""
        if not text:
            return 0.0
        
        # Use SequenceMatcher for similarity
        similarity = SequenceMatcher(None, query.lower(), text.lower()).ratio()
        
        # Boost score for exact matches
        if query.lower() in text.lower():
            similarity += 0.5
        
        # Boost score for exact word matches
        query_words = set(query.lower().split())
        text_words = set(text.lower().split())
        word_overlap = len(query_words.intersection(text_words))
        if query_words:
            word_ratio = word_overlap / len(query_words)
            similarity += word_ratio * 0.3
        
        return min(similarity, 1.0)
    
    def _get_context_snippet(self, text, query, max_length=100):
        """Extract a context snippet around the matching text"""
        if not text:
            return ""
        
        query_lower = query.lower()
        text_lower = text.lower()
        
        # Find the position of the query in the text
        match_pos = text_lower.find(query_lower)
        if match_pos == -1:
            # Return beginning of text if no exact match
            return text[:max_length] + ("..." if len(text) > max_length else "")
        
        # Calculate context window
        context_start = max(0, match_pos - max_length // 2)
        context_end = min(len(text), match_pos + len(query) + max_length // 2)
        
        snippet = text[context_start:context_end]
        
        # Add ellipsis if needed
        if context_start > 0:
            snippet = "..." + snippet
        if context_end < len(text):
            snippet = snippet + "..."
        
        return snippet
    
    def _log_search(self, user_id, query, algorithm, results_count, execution_time):
        """Log search query to database"""
        try:
            with get_db_cursor() as cursor:
                cursor.execute("""
                    INSERT INTO search_logs (user_id, query, algorithm_used, results_count, execution_time_ms)
                    VALUES (%s, %s, %s, %s, %s)
                """, (user_id, query, algorithm, results_count, execution_time))
        except Exception as e:
            print(f"Error logging search: {e}")


# Global searcher instance
searcher = DocumentSearcher()