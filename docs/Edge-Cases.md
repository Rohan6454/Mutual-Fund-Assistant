# Edge Cases for Mutual Fund FAQ Assistant

## Overview

This document outlines comprehensive edge cases for evaluating the Mutual Fund FAQ Assistant project. These edge cases cover all system components, from data ingestion to user-facing responses, ensuring robust testing across various scenarios.

---

## 1. Data Ingestion & Processing Edge Cases

### 1.1 Scraping Failures
- **Network timeouts**: URLs that don't respond within timeout limits
- **HTTP error codes**: 404, 500, 503, 429 (rate limiting)
- **Authentication required**: URLs behind login walls
- **Blocked by robots.txt**: URLs that disallow scraping
- **Malformed URLs**: Invalid URL formats in sources.json
- **Redirect loops**: URLs that create infinite redirects
- **Large file downloads**: PDFs exceeding size limits
- **Corrupted downloads**: Incomplete or damaged files
- **SSL certificate errors**: Expired or invalid certificates
- **Content type mismatches**: URLs claiming to be HTML but returning binary data

### 1.2 Content Extraction Issues
- **Empty HTML pages**: Pages with no meaningful content
- **JavaScript-rendered content**: Pages requiring JS for content loading
- **Protected PDFs**: Password-protected or encrypted PDFs
- **Scanned PDFs**: Image-based PDFs without text layer
- **Malformed HTML**: Broken HTML structure causing parsing errors
- **Unicode issues**: Special characters, emojis, non-UTF8 content
- **Table extraction failures**: Complex tables not parsed correctly
- **Multi-language content**: Hindi/regional language content mixed with English
- **Dynamic content**: Content that changes based on user interactions
- **Cookie-gated content**: Content requiring cookies for access

### 1.3 Data Quality Issues
- **Duplicate content**: Same information across multiple sources
- **Conflicting information**: Different sources providing contradictory data
- **Outdated information**: Old factsheets with stale data
- **Incomplete data**: Missing key fields (expense ratio, NAV, etc.)
- **Inconsistent formats**: Different date formats, number formats
- **Typographical errors**: Misspelled scheme names, incorrect values
- **Ambiguous scheme names**: Similar scheme names across AMCs
- **Broken internal links**: References to non-existent sections

---

## 2. RAG Retrieval Edge Cases

### 2.1 Query Processing
- **Empty queries**: Blank or whitespace-only input
- **Very long queries**: Queries exceeding token limits
- **Special characters**: Queries with emojis, symbols, non-ASCII
- **Multiple questions**: Queries containing multiple questions
- **Ambiguous scheme names**: "flexi cap" without AMC specification
- **Typo-heavy queries**: "expens ratio hdfl flexcap" (multiple typos)
- **Mixed language queries**: Hindi + English combinations
- **Code-like queries**: Queries resembling programming syntax
- **Mathematical expressions**: Queries with formulas or calculations
- **URLs in queries**: Queries containing web links

### 2.2 Intent Classification
- **Borderline advisory**: "What are the risks of investing in..." (factual vs advisory)
- **Implicit comparisons**: "Tell me about HDFC vs ICICI" (without explicit comparison words)
- **Procedural vs factual**: "How to check" vs "What is"
- **PII edge cases**: Numbers that look like PAN/Aadhaar but aren't
- **Context-dependent queries**: Queries that require previous conversation context
- **Sarcastic or metaphorical language**: Non-literal user intent
- **Conditional questions**: "If I invest X, what happens to Y"
- **Hypothetical scenarios**: "What would happen if..."

### 2.3 Vector Search Failures
- **No matching chunks**: Queries with no relevant content in corpus
- **Low similarity scores**: All results below threshold
- **High similarity but irrelevant**: Semantic similarity without factual relevance
- **Scheme name mismatches**: Correct scheme, wrong name in metadata
- **Embedding dimension mismatches**: Different embedding models
- **Qdrant connection failures**: Database unavailable
- **Index corruption**: Damaged vector index
- **Timeout during search**: Slow database responses
- **Empty result sets**: Search returns no results
- **Too many results**: Search returns excessive results

### 2.4 Re-ranking Issues
- **MMR algorithm failures**: Errors in diversity calculations
- **All chunks from same source**: No diversity possible
- **Identical chunks**: Duplicate content affecting re-ranking
- **Score ties**: Multiple chunks with identical scores
- **Negative scores**: Unexpected negative similarity scores
- **Overflow errors**: Numerical issues in calculations

---

## 3. LLM Generation Edge Cases

### 3.1 Input Guardrails
- **Context injection failures**: Malformed context templates
- **Context too long**: Retrieved chunks exceed token limits
- **Empty context**: No relevant chunks found
- **Malformed context**: Invalid JSON or structure
- **Context with PII**: Retrieved chunks containing personal information
- **Context with advice**: Retrieved chunks containing advisory content
- **Multiple conflicting contexts**: Chunks with contradictory information

### 3.2 LLM API Issues
- **Rate limiting**: Exceeding Gemini API limits
- **API key exhaustion**: Quota exceeded
- **Network failures**: Connection timeouts to Gemini
- **Model unavailability**: Gemini service downtime
- **Invalid responses**: Malformed or empty LLM responses
- **Safety filter triggers**: Content flagged by Gemini safety
- **Token limit exceeded**: Input/output too long
- **Model hallucination**: LLM generating incorrect information
- **Response truncation**: Incomplete responses due to limits

### 3.3 Output Guardrails
- **Sentence count violations**: Responses exceeding 3 sentences
- **Advice language detection**: Subtle advisory phrases
- **PII in responses**: Generated responses containing personal data
- **URL validation**: Invalid or malformed source URLs
- **Missing citations**: Responses without source links
- **Multiple citations**: Responses with multiple source links
- **Citation formatting**: Incorrect citation format
- **Footer generation**: Missing or incorrect last-updated dates

---

## 4. Backend API Edge Cases

### 4.1 Request Handling
- **Malformed JSON**: Invalid request body format
- **Missing required fields**: Empty thread_id or message
- **Invalid data types**: Numbers instead of strings
- **Unicode issues**: Non-UTF8 characters in requests
- **Oversized requests**: Requests exceeding size limits
- **Concurrent requests**: Multiple simultaneous requests
- **Session management**: Thread state corruption
- **Memory leaks**: Unbounded memory growth
- **Database connection issues**: Qdrant connection failures
- **Service dependencies**: Downstream service failures

### 4.2 Response Generation
- **Serialization failures**: Unable to convert response to JSON
- **Timeout during generation**: LLM calls taking too long
- **Partial responses**: Incomplete response data
- **Encoding issues**: Response encoding problems
- **Status code errors**: Incorrect HTTP status codes
- **Header issues**: Missing or invalid response headers
- **CORS violations**: Cross-origin request failures

### 4.3 Rate Limiting & Security
- **Rate limit bypass**: Clients circumventing rate limits
- **DDOS attacks**: High-volume request floods
- **Injection attacks**: Malicious input in queries
- **Authentication bypass**: Unauthorized access attempts
- **Session hijacking**: Thread ID manipulation
- **Data exfiltration**: Attempts to extract system data

---

## 5. Frontend UI Edge Cases

### 5.1 User Interface
- **Browser compatibility**: Different browser rendering issues
- **Mobile responsiveness**: UI breaking on small screens
- **JavaScript disabled**: Functionality without JS
- **Network connectivity**: Offline behavior
- **Session persistence**: Page refresh handling
- **Multiple tabs**: Conflicts between browser tabs
- **Accessibility**: Screen reader compatibility
- **Keyboard navigation**: Keyboard-only usage
- **High contrast mode**: Visual accessibility
- **Text scaling**: Large font size handling

### 5.2 Chat Interface
- **Message history**: Long conversation handling
- **Message formatting**: Special characters in messages
- **Scroll behavior**: Chat window scrolling issues
- **Input validation**: Empty or invalid user input
- **Real-time updates**: Live response streaming
- **Error display**: User-friendly error messages
- **Loading states**: Indicators for processing
- **Message timestamps**: Time zone handling
- **Character limits**: Input length restrictions

---

## 6. System Integration Edge Cases

### 6.1 Scheduled Operations
- **Scheduler failures**: Daily scrape not triggering
- **Partial updates**: Some sources updated, others failed
- **Concurrent operations**: Overlapping scrape and query operations
- **Resource exhaustion**: Memory/CPU during peak loads
- **Storage issues**: Disk space running out
- **Backup failures**: Data backup not working
- **Rollback scenarios**: Failed update recovery
- **Version conflicts**: Incompatible data versions

### 6.2 Configuration Management
- **Missing environment variables**: Required config not set
- **Invalid configuration**: Wrong format or values
- **Configuration hot-reload**: Runtime config changes
- **Default value handling**: Missing config defaults
- **Security credentials**: Exposed API keys or passwords
- **Multi-environment**: Dev/staging/prod config conflicts

### 6.3 Monitoring & Logging
- **Log file rotation**: Disk space from logs
- **Performance monitoring**: Metrics collection failures
- **Error tracking**: Incomplete error reporting
- **Audit trails**: Missing action logs
- **Health checks**: False positive/negative health status
- **Alert fatigue**: Too many false alarms

---

## 7. Data Consistency Edge Cases

### 7.1 Synchronization Issues
- **Race conditions**: Concurrent data modifications
- **Eventual consistency**: Temporary data inconsistencies
- **Stale data**: Outdated information in responses
- **Partial updates**: Incomplete data propagation
- **Replication lag**: Database sync delays
- **Cache invalidation**: Stale cache entries

### 7.2 Data Integrity
- **Corrupted chunks**: Damaged text chunks in database
- **Metadata mismatches**: Chunk metadata not matching content
- **Orphaned records**: Chunks without source references
- **Duplicate detection**: Identical content across sources
- **Version conflicts**: Multiple versions of same information

---

## 8. Performance Edge Cases

### 8.1 Load Testing
- **High concurrency**: Multiple simultaneous users
- **Memory pressure**: High memory usage scenarios
- **CPU spikes**: Intensive computation periods
- **I/O bottlenecks**: Disk/network performance limits
- **Database performance**: Qdrant query optimization
- **API response times**: Slow response scenarios

### 8.2 Scalability Issues
- **Horizontal scaling**: Multiple instance coordination
- **Resource allocation**: CPU/memory distribution
- **Cache efficiency**: Hit/miss ratios
- **Connection pooling**: Database connection management
- **Queue management**: Request queue overflow

---

## 9. Security & Compliance Edge Cases

### 9.1 Data Privacy
- **PII detection failures**: Personal information slipping through
- **Data retention**: Storing user queries longer than required
- **Data anonymization**: Insufficient data anonymization
- **Access control**: Unauthorized data access
- **Audit compliance**: Regulatory requirement violations

### 9.2 Financial Compliance
- **Investment advice**: System providing prohibited advice
- **Performance claims**: Unverified performance statements
- **Risk disclosures**: Missing risk information
- **Regulatory updates**: Changes in compliance requirements
- **Disclaimer enforcement**: Missing required disclaimers

---

## 10. Disaster Recovery Edge Cases

### 10.1 System Failures
- **Complete system outage**: Total service unavailability
- **Partial system failure**: Some components working
- **Data corruption**: Database corruption scenarios
- **Network partitions**: Split-brain scenarios
- **Power failures**: Unexpected shutdowns
- **Hardware failures**: Disk/memory/CPU failures

### 10.2 Recovery Procedures
- **Backup restoration**: Restoring from backups
- **Data reconciliation**: Fixing inconsistent data
- **Service restart**: Recovery sequence procedures
- **Graceful degradation**: Reduced functionality modes
- **Manual overrides**: Emergency intervention procedures

---

## 11. User Experience Edge Cases

### 11.1 Error Handling
- **Graceful failures**: User-friendly error messages
- **Recovery guidance**: Helping users recover from errors
- **Alternative suggestions**: Providing fallback options
- **Context preservation**: Maintaining conversation context
- **Progressive disclosure**: Revealing complexity gradually

### 11.2 Accessibility
- **Screen readers**: Voice-over compatibility
- **Keyboard navigation**: Tab order and shortcuts
- **Color blindness**: Color-independent information
- **Motor impairments**: Large click targets
- **Cognitive disabilities**: Simple language and structure

---

## 12. Third-Party Dependencies

### 12.1 External Service Failures
- **Gemini API outage**: LLM service unavailable
- **Qdrant failures**: Vector database issues
- **Hugging Face models**: Model download failures
- **AMC website changes**: Source structure modifications
- **CDN failures**: Static resource delivery issues

### 12.2 Dependency Updates
- **Breaking changes**: Library version incompatibilities
- **Security patches**: Urgent dependency updates
- **Feature deprecation**: Removed functionality
- **License changes**: Compliance issues
- **Performance regressions**: Updated library performance

---

## Evaluation Framework

### Severity Classification
- **Critical**: System completely non-functional
- **High**: Core functionality severely impacted
- **Medium**: Partial functionality affected
- **Low**: Minor issues with workarounds

### Test Categories
- **Unit Tests**: Individual component testing
- **Integration Tests**: Component interaction testing
- **End-to-End Tests**: Complete user journey testing
- **Performance Tests**: Load and stress testing
- **Security Tests**: Vulnerability assessment

### Success Criteria
- **Functional Correctness**: Accurate responses to valid queries
- **Robustness**: Graceful handling of edge cases
- **Performance**: Response times within acceptable limits
- **Security**: No data breaches or compliance violations
- **Usability**: Positive user experience under all conditions

---

## Implementation Priority

### Phase 1: Critical Edge Cases
1. PII detection and handling
2. Investment advice prevention
3. Core functionality failures
4. Data corruption scenarios

### Phase 2: High Priority Edge Cases
1. Performance under load
2. Network failures
3. Data consistency issues
4. User experience problems

### Phase 3: Medium Priority Edge Cases
1. Accessibility compliance
2. Advanced security scenarios
3. Disaster recovery
4. Optimization opportunities

### Phase 4: Low Priority Edge Cases
1. Edge case UI polish
2. Advanced monitoring
3. Performance optimization
4. Future-proofing scenarios

---

## Conclusion

This comprehensive edge case document provides a framework for thorough testing of the Mutual Fund FAQ Assistant. Regular testing against these edge cases ensures system reliability, compliance, and user satisfaction across all operational scenarios.
