// ResearchMate Main JavaScript

// Global variables
let currentToast = null;

// Authentication utilities with enhanced security
let sessionTimeout = null;
let lastActivityTime = Date.now();
const SESSION_TIMEOUT_MINUTES = 480; // 8 hours for prototype (less aggressive)
const ACTIVITY_CHECK_INTERVAL = 300000; // Check every 5 minutes

function getAuthToken() {
    // Check both sessionStorage (preferred) and localStorage (fallback)
    return sessionStorage.getItem('authToken') || localStorage.getItem('authToken');
}

function setAuthToken(token) {
    // Store in sessionStorage for better security (clears on browser close)
    sessionStorage.setItem('authToken', token);
    // Also store in localStorage for compatibility, but with shorter expiry
    localStorage.setItem('authToken', token);
    localStorage.setItem('tokenTimestamp', Date.now().toString());
    
    // Set cookie with HttpOnly equivalent behavior
    document.cookie = `authToken=${token}; path=/; SameSite=Strict; Secure=${location.protocol === 'https:'}`;
    
    // Reset activity tracking
    lastActivityTime = Date.now();
    startSessionTimeout();
}

function clearAuthToken() {
    sessionStorage.removeItem('authToken');
    sessionStorage.removeItem('userId');
    localStorage.removeItem('authToken');
    localStorage.removeItem('userId');
    localStorage.removeItem('tokenTimestamp');
    
    // Clear cookie
    document.cookie = 'authToken=; path=/; expires=Thu, 01 Jan 1970 00:00:00 GMT; SameSite=Strict';
    
    clearTimeout(sessionTimeout);
}

function isTokenExpired() {
    const timestamp = localStorage.getItem('tokenTimestamp');
    if (!timestamp) return true;
    
    const tokenAge = Date.now() - parseInt(timestamp);
    const maxAge = 24 * 60 * 60 * 1000; // 24 hours
    
    return tokenAge > maxAge;
}

function startSessionTimeout() {
    clearTimeout(sessionTimeout);
    sessionTimeout = setTimeout(() => {
        const inactivityTime = Date.now() - lastActivityTime;
        if (inactivityTime >= SESSION_TIMEOUT_MINUTES * 60 * 1000) {
            // Session expired due to inactivity
            showToast('Session expired due to inactivity. Please log in again.', 'warning');
            logout();
        } else {
            // Still active, reset timer
            startSessionTimeout();
        }
    }, ACTIVITY_CHECK_INTERVAL);
}

function trackActivity() {
    lastActivityTime = Date.now();
}

function setAuthHeaders(headers = {}) {
    const token = getAuthToken();
    if (token && !isTokenExpired()) {
        headers['Authorization'] = `Bearer ${token}`;
    }
    return headers;
}

function makeAuthenticatedRequest(url, options = {}) {
    const headers = setAuthHeaders(options.headers || {});
    return fetch(url, {
        ...options,
        headers: headers
    });
}

// Check if user is authenticated
function isAuthenticated() {
    const token = getAuthToken();
    return !!(token && !isTokenExpired());
}

// Redirect to login if not authenticated
function requireAuth() {
    if (!isAuthenticated()) {
        clearAuthToken();
        window.location.href = '/login';
        return false;
    }
    return true;
}

// Document ready with enhanced security
document.addEventListener('DOMContentLoaded', function() {
    // Check authentication on protected pages
    if (window.location.pathname !== '/login' && !isAuthenticated()) {
        clearAuthToken();
        window.location.href = '/login';
        return;
    }
    
    // Start session timeout if authenticated
    if (isAuthenticated()) {
        startSessionTimeout();
    }
    
    // Track user activity for session timeout
    document.addEventListener('click', trackActivity);
    document.addEventListener('keypress', trackActivity);
    document.addEventListener('scroll', trackActivity);
    document.addEventListener('mousemove', trackActivity);
    
    // Initialize tooltips
    initializeTooltips();
    
    // Handle page visibility changes (user switches tabs or minimizes browser)
    document.addEventListener('visibilitychange', function() {
        if (document.hidden) {
            // Page is hidden, reduce activity tracking
            clearTimeout(sessionTimeout);
        } else {
            // Page is visible again, resume activity tracking
            if (isAuthenticated()) {
                trackActivity();
                startSessionTimeout();
            }
        }
    });
    
    // Handle beforeunload event (browser/tab closing)
    window.addEventListener('beforeunload', function() {
        // Clear sessionStorage on page unload (but keep localStorage for potential restoration)
        sessionStorage.clear();
    });
    
    // Periodically validate token with server (disabled for prototype)
    // if (isAuthenticated()) {
    //     setInterval(async function() {
    //         try {
    //             const response = await makeAuthenticatedRequest('/api/user/status');
    //             if (!response.ok) {
    //                 // Token is invalid or expired
    //                 showToast('Session expired. Please log in again.', 'warning');
    //                 logout();
    //             }
    //         } catch (error) {
    //             console.log('Token validation failed:', error);
    //         }
    //     }, 5 * 60 * 1000); // Check every 5 minutes
    // }
    
    // Initialize smooth scrolling
    initializeSmoothScrolling();
    
    // Initialize animations
    initializeAnimations();
    
    // Initialize keyboard shortcuts
    initializeKeyboardShortcuts();
    
    // Theme toggle removed
    
    // Initialize upload
    initializeUpload();
    
    // Initialize search page (if on search page)
    initializeSearchPage();
    
    console.log('ResearchMate initialized successfully!');
});

// Initialize tooltips
function initializeTooltips() {
    const tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]');
    const tooltipList = [...tooltipTriggerList].map(tooltipTriggerEl => new bootstrap.Tooltip(tooltipTriggerEl));
}

// Initialize smooth scrolling
function initializeSmoothScrolling() {
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });
}

// Initialize animations
function initializeAnimations() {
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('fade-in');
            }
        });
    }, {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    });

    document.querySelectorAll('.card, .alert').forEach(el => {
        observer.observe(el);
    });
}

// Initialize keyboard shortcuts
function initializeKeyboardShortcuts() {
    document.addEventListener('keydown', function(e) {
        // Ctrl/Cmd + K: Focus search
        if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
            e.preventDefault();
            const searchInput = document.querySelector('#query, #question, #topic');
            if (searchInput) {
                searchInput.focus();
            }
        }
        
        // Ctrl/Cmd + Enter: Submit form
        if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
            e.preventDefault();
            const form = document.querySelector('form');
            if (form) {
                form.dispatchEvent(new Event('submit'));
            }
        }
        
        // Escape: Close modals
        if (e.key === 'Escape') {
            const modals = document.querySelectorAll('.modal.show');
            modals.forEach(modal => {
                const bsModal = bootstrap.Modal.getInstance(modal);
                if (bsModal) {
                    bsModal.hide();
                }
            });
        }
    });
}

// Theme toggle removed: always use dark theme

// Enhanced Upload functionality
function initializeUpload() {
    const uploadArea = document.getElementById('upload-area');
    const fileInput = document.getElementById('pdf-file');
    const uploadBtn = document.getElementById('upload-btn');
    
    if (!uploadArea || !fileInput || !uploadBtn) return;
    
    // Restore previous upload results if they exist
    restoreUploadResults();
    
    // Click to browse files
    uploadArea.addEventListener('click', () => {
        fileInput.click();
    });
    
    // Drag and drop functionality
    uploadArea.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadArea.classList.add('dragover');
    });
    
    uploadArea.addEventListener('dragleave', () => {
        uploadArea.classList.remove('dragover');
    });
    
    uploadArea.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadArea.classList.remove('dragover');
        
        const files = e.dataTransfer.files;
        if (files.length > 0 && files[0].type === 'application/pdf') {
            fileInput.files = files;
            handleFileSelection(files[0]);
        } else {
            showToast('Please select a valid PDF file', 'danger');
        }
    });
    
    // File input change
    fileInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) {
            handleFileSelection(e.target.files[0]);
        }
    });
    
    function handleFileSelection(file) {
        uploadBtn.disabled = false;
        uploadBtn.innerHTML = `<i class="fas fa-upload me-2"></i>Upload "${file.name}"`;
        
        // Update upload area
        uploadArea.innerHTML = `
            <i class="fas fa-file-pdf text-danger"></i>
            <h5 class="mt-2 text-success">File Selected</h5>
            <p class="text-muted">${file.name} (${formatFileSize(file.size)})</p>
        `;
    }
}

// Format file size
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

// Toggle upload area visibility
function toggleUploadArea() {
    const uploadArea = document.getElementById('upload-area');
    if (uploadArea) {
        uploadArea.classList.toggle('d-none');
    }
}

// Upload result persistence functions
function saveUploadResults(data) {
    try {
        const uploadData = {
            ...data,
            savedAt: new Date().toISOString(),
            pageUrl: window.location.pathname
        };
        saveToLocalStorage('researchmate_upload_results', uploadData);
        console.log('Upload results saved to localStorage');
    } catch (error) {
        console.error('Failed to save upload results:', error);
    }
}

function restoreUploadResults() {
    try {
        const resultsContainer = document.getElementById('results-container');
        if (!resultsContainer) return;
        
        const savedData = loadFromLocalStorage('researchmate_upload_results');
        if (savedData && savedData.pageUrl === window.location.pathname) {
            // Check if data is recent (within 24 hours)
            const savedTime = new Date(savedData.savedAt);
            const now = new Date();
            const hoursDiff = (now - savedTime) / (1000 * 60 * 60);
            
            if (hoursDiff < 24) {
                console.log('Restoring upload results from localStorage');
                displayUploadResults(savedData);
                showToast('Previous PDF analysis restored', 'info', 3000);
            } else {
                // Clean up old data
                clearUploadResults();
            }
        }
    } catch (error) {
        console.error('Failed to restore upload results:', error);
    }
}

function clearUploadResults() {
    try {
        localStorage.removeItem('researchmate_upload_results');
        const resultsContainer = document.getElementById('results-container');
        if (resultsContainer) {
            resultsContainer.innerHTML = '';
        }
    } catch (error) {
        console.error('Failed to clear upload results:', error);
    }
}

function displayUploadResults(data) {
    const resultsContainer = document.getElementById('results-container');
    if (!resultsContainer) return;
    
    const summary = data.summary || {};
    
    // Utility: Render markdown using a JS markdown parser (marked.js)
    function renderMarkdown(text) {
        if (typeof marked !== 'undefined') {
            return marked.parseInline(text || '');
        }
        return text || '';
    }
    
    const html = `
        <div class="card">
            <div class="card-header d-flex justify-content-between align-items-center">
                <h5 class="mb-0">
                    <i class="fas fa-file-pdf me-2"></i>PDF Analysis Results
                </h5>
                <button class="btn btn-sm btn-outline-secondary" onclick="clearUploadResults()" title="Clear results">
                    <i class="fas fa-times"></i>
                </button>
            </div>
            <div class="card-body">
                <!-- Paper Info -->
                <div class="row mb-4">
                    <div class="col-md-8">
                        <h6 class="text-primary">📄 Paper Information</h6>
                        <h5 class="mb-2">${renderMarkdown(data.title || 'Unknown Title')}</h5>
                        <p class="text-muted small mb-2">
                            <i class="fas fa-clock me-1"></i>
                            Processed: ${data.processed_at ? new Date(data.processed_at).toLocaleString() : 'N/A'}
                        </p>
                        <p class="text-muted small">
                            <i class="fas fa-file-alt me-1"></i>
                            Text Length: ${data.text_length ? data.text_length.toLocaleString() : 'N/A'} characters
                        </p>
                    </div>
                    <div class="col-md-4 text-end">
                        <div class="badge bg-success p-2">
                            <i class="fas fa-check-circle me-1"></i>
                            Analysis Complete
                        </div>
                        ${data.savedAt ? `
                            <div class="badge bg-info p-2 mt-2 d-block">
                                <i class="fas fa-history me-1"></i>
                                Restored
                            </div>
                        ` : ''}
                    </div>
                </div>

                <!-- Abstract -->
                <div class="mb-4">
                    <h6 class="text-info">📝 Abstract</h6>
                    <div class="border-start border-info ps-3">
                        <div class="mb-0">${renderMarkdown(data.abstract || 'Abstract not found')}</div>
                    </div>
                </div>

                <!-- AI Analysis -->
                <div class="row">
                    <!-- Main Summary -->
                    <div class="col-md-6 mb-4">
                        <div class="card h-100 border-primary">
                            <div class="card-header bg-primary text-white">
                                <h6 class="mb-0">
                                    <i class="fas fa-brain me-2"></i>Main Summary
                                </h6>
                            </div>
                            <div class="card-body">
                                <div class="mb-0">${renderMarkdown(summary.summary || 'Summary not available')}</div>
                            </div>
                        </div>
                    </div>

                    <!-- Key Contributions -->
                    <div class="col-md-6 mb-4">
                        <div class="card h-100 border-success">
                            <div class="card-header bg-success text-white">
                                <h6 class="mb-0">
                                    <i class="fas fa-star me-2"></i>Key Contributions
                                </h6>
                            </div>
                            <div class="card-body">
                                <div class="contributions-text">
                                    ${summary.contributions ? summary.contributions.split('\n').map(line => line.trim()).filter(line => line).map(line => `<div class="mb-1">${renderMarkdown(line)}</div>`).join('') : 'Contributions not available'}
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- Methodology -->
                    <div class="col-md-6 mb-4">
                        <div class="card h-100 border-info">
                            <div class="card-header bg-info text-white">
                                <h6 class="mb-0">
                                    <i class="fas fa-cogs me-2"></i>Methodology
                                </h6>
                            </div>
                            <div class="card-body">
                                <div class="mb-0">${renderMarkdown(summary.methodology || 'Methodology not available')}</div>
                            </div>
                        </div>
                    </div>

                    <!-- Key Findings -->
                    <div class="col-md-6 mb-4">
                        <div class="card h-100 border-warning">
                            <div class="card-header bg-warning text-dark">
                                <h6 class="mb-0">
                                    <i class="fas fa-lightbulb me-2"></i>Key Findings
                                </h6>
                            </div>
                            <div class="card-body">
                                <div class="findings-text">
                                    ${summary.findings ? summary.findings.split('\n').map(line => line.trim()).filter(line => line).map(line => `<div class="mb-1">${renderMarkdown(line)}</div>`).join('') : 'Findings not available'}
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- Limitations -->
                    <div class="col-12 mb-4">
                        <div class="card border-danger">
                            <div class="card-header bg-danger text-white">
                                <h6 class="mb-0">
                                    <i class="fas fa-exclamation-triangle me-2"></i>Limitations
                                </h6>
                            </div>
                            <div class="card-body">
                                <div class="mb-0">${renderMarkdown(summary.limitations || 'Limitations not identified')}</div>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Actions -->
                <div class="d-flex justify-content-between align-items-center">
                    <div>
                        <button class="btn btn-success me-2" onclick="addToKnowledgeBase()">
                            <i class="fas fa-database me-1"></i>Add to Knowledge Base
                        </button>
                        <button class="btn btn-info" onclick="askAboutPaper()">
                            <i class="fas fa-question-circle me-1"></i>Ask Questions
                        </button>
                    </div>
                    <div class="text-muted">
                        <small>
                            <i class="fas fa-check me-1"></i>
                            Paper analyzed and ready for questions
                        </small>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    resultsContainer.innerHTML = html;
}

// Utility functions
function showToast(message, type = 'info', duration = 5000) {
    // Remove existing toast
    if (currentToast) {
        currentToast.remove();
    }
    
    const toast = document.createElement('div');
    toast.className = `toast align-items-center text-bg-${type} border-0 position-fixed top-0 end-0 m-3`;
    toast.style.zIndex = '9999';
    toast.setAttribute('role', 'alert');
    toast.setAttribute('aria-live', 'assertive');
    toast.setAttribute('aria-atomic', 'true');
    
    toast.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">
                <i class="fas fa-${getIconForType(type)} me-2"></i>
                ${message}
            </div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
        </div>
    `;
    
    document.body.appendChild(toast);
    currentToast = toast;
    
    const bsToast = new bootstrap.Toast(toast, {
        autohide: true,
        delay: duration
    });
    
    bsToast.show();
    
    // Clean up after toast is hidden
    toast.addEventListener('hidden.bs.toast', function() {
        toast.remove();
        if (currentToast === toast) {
            currentToast = null;
        }
    });
}

function getIconForType(type) {
    const icons = {
        'success': 'check-circle',
        'danger': 'exclamation-triangle',
        'warning': 'exclamation-triangle',
        'info': 'info-circle',
        'primary': 'info-circle',
        'secondary': 'info-circle'
    };
    return icons[type] || 'info-circle';
}

function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

function formatNumber(num) {
    if (num >= 1000000) {
        return (num / 1000000).toFixed(1) + 'M';
    } else if (num >= 1000) {
        return (num / 1000).toFixed(1) + 'K';
    }
    return num.toString();
}

function truncateText(text, maxLength) {
    if (text.length <= maxLength) {
        return text;
    }
    return text.substring(0, maxLength) + '...';
}

function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(() => {
        showToast('Copied to clipboard!', 'success', 2000);
    }).catch(err => {
        showToast('Failed to copy to clipboard', 'danger', 3000);
    });
}

function downloadText(text, filename) {
    const element = document.createElement('a');
    element.setAttribute('href', 'data:text/plain;charset=utf-8,' + encodeURIComponent(text));
    element.setAttribute('download', filename);
    element.style.display = 'none';
    document.body.appendChild(element);
    element.click();
    document.body.removeChild(element);
}

function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

function throttle(func, limit) {
    let inThrottle;
    return function() {
        const args = arguments;
        const context = this;
        if (!inThrottle) {
            func.apply(context, args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    };
}

// API helper functions
async function apiRequest(url, options = {}) {
    try {
        const response = await fetch(url, {
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            },
            ...options
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        return await response.json();
    } catch (error) {
        console.error('API request failed:', error);
        throw error;
    }
}

// Search functionality
function highlightSearchTerms(text, terms) {
    if (!terms || terms.length === 0) return text;
    
    let highlightedText = text;
    terms.forEach(term => {
        const regex = new RegExp(`(${term})`, 'gi');
        highlightedText = highlightedText.replace(regex, '<mark>$1</mark>');
    });
    
    return highlightedText;
}

// Search page functionality
function initializeSearchPage() {
    const searchForm = document.getElementById('search-form');
    const questionForm = document.getElementById('question-form');
    const resultsContainer = document.getElementById('results-container');
    const loadingDiv = document.getElementById('loading');

    console.log('Main.js: initializeSearchPage called');
    console.log('Search form found:', !!searchForm);
    console.log('Results container found:', !!resultsContainer);
    
    if (!searchForm || !resultsContainer) {
        console.log('Not on search page or missing elements');
        return; // Not on search page
    }

    console.log('Main.js: Initializing search page...');

    // Search form handler
    searchForm.addEventListener('submit', function(e) {
        e.preventDefault();
        
        console.log('Main.js: Search form submitted!');
        
        const query = document.getElementById('query').value;
        const maxResults = parseInt(document.getElementById('max_results').value);
        
        console.log('Main.js: Query:', query, 'Max results:', maxResults);
        
        if (!query.trim()) {
            console.error('Main.js: Empty query');
            showToast('Please enter a search query', 'warning');
            return;
        }
        
        console.log('Main.js: Starting search...');
        searchPapers(query, maxResults);
    });

    // Question form handler (if exists)
    if (questionForm) {
        questionForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const question = document.getElementById('question').value;
            if (!question.trim()) {
                showToast('Please enter a question', 'warning');
                return;
            }
            askQuestion(question);
        });
    }

    function showLoading(type = 'search') {
        if (!loadingDiv) return;
        
        const loadingTitle = document.getElementById('loading-title');
        const loadingMessage = document.getElementById('loading-message');
        const loadingProgress = document.getElementById('loading-progress');
        
        loadingDiv.style.display = 'block';
        resultsContainer.innerHTML = '';
        
        if (loadingTitle) {
            loadingTitle.textContent = type === 'search' ? 'Searching Research Papers...' : 'Processing Your Question...';
        }
        if (loadingMessage) {
            loadingMessage.innerHTML = '<i class="fas fa-info-circle me-1 text-info"></i>First search may take 30-60 seconds for initialization...';
        }
        if (loadingProgress) {
            loadingProgress.style.width = '10%';
        }
    }

    function hideLoading() {
        if (loadingDiv) {
            loadingDiv.style.display = 'none';
        }
    }

    function searchPapers(query, maxResults) {
        console.log('Starting search for:', query);
        showLoading('search');
        
        // Show helpful message about first-time search
        const loadingMessage = document.getElementById('loading-message');
        const loadingProgress = document.getElementById('loading-progress');
        
        if (loadingMessage) {
            loadingMessage.innerHTML = '<i class="fas fa-info-circle me-1 text-info"></i>Searching across multiple databases...';
        }
        if (loadingProgress) {
            loadingProgress.style.width = '10%';
        }
        
        // Update progress periodically
        let progressInterval = setInterval(() => {
            if (loadingProgress) {
                const currentWidth = parseInt(loadingProgress.style.width) || 10;
                if (currentWidth < 80) {
                    loadingProgress.style.width = (currentWidth + 2) + '%';
                }
            }
        }, 1000);
        
        // Set a timeout for very long searches
        const timeoutId = setTimeout(() => {
            if (loadingMessage) {
                loadingMessage.innerHTML = '<i class="fas fa-exclamation-triangle me-1 text-warning"></i>Search is taking longer than expected. Please wait...';
            }
        }, 30000); // 30 seconds
        
        fetch('/api/search', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ query: query, max_results: maxResults })
        })
        .then(response => {
            clearTimeout(timeoutId);
            clearInterval(progressInterval);
            console.log('Search response status:', response.status);
            return response.json();
        })
        .then(data => {
            hideLoading();
            
            console.log('Search API response:', data);
            console.log('Response success:', data.success);
            console.log('Response papers:', data.papers);
            
            if (data.success) {
                displaySearchResults(data);
            } else {
                console.error('Search failed with error:', data.error);
                displayError(data.error || 'Search failed');
            }
        })
        .catch(error => {
            clearTimeout(timeoutId);
            clearInterval(progressInterval);
            hideLoading();
            
            console.error('Search request failed:', error);
            displayError('Network error: ' + error.message);
        });
    }

    function askQuestion(question) {
        showLoading('question');
        
        fetch('/api/ask', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ question: question })
        })
        .then(response => response.json())
        .then(data => {
            hideLoading();
            
            if (data.success) {
                displayQuestionAnswer(data);
            } else {
                displayError(data.error || 'Question failed');
            }
        })
        .catch(error => {
            hideLoading();
            displayError('Network error: ' + error.message);
        });
    }

    function displaySearchResults(data) {
        console.log('displaySearchResults called with:', data);
        
        const papers = data.papers || [];
        console.log('Papers array:', papers);
        console.log('Papers count:', papers.length);
        
        // Simple fallback for testing
        if (papers.length === 0) {
            const html = `
                <div class="alert alert-info" role="alert">
                    <i class="fas fa-info-circle me-2"></i>
                    No papers found for your search query "${data.query}". Try different keywords.
                </div>
            `;
            resultsContainer.innerHTML = html;
            return;
        }
        
        // Try to render papers with error handling
        try {
            const html = `
                <div class="card shadow-sm">
                    <div class="card-header">
                        <h5 class="mb-0">
                            <i class="fas fa-search me-2"></i>Search Results
                            <span class="badge bg-primary ms-2">${data.count || papers.length} papers found</span>
                        </h5>
                    </div>
                    <div class="card-body">
                        <div class="row">
                            ${papers.map((paper, index) => {
                                try {
                                    const title = paper.title || 'Untitled';
                                    const authors = Array.isArray(paper.authors) ? paper.authors.join(', ') : (paper.authors || 'Unknown authors');
                                    const year = paper.year || paper.published_year || 'Unknown year';
                                    const source = paper.source || 'ArXiv';
                                    const abstract = paper.abstract ? (paper.abstract.length > 200 ? paper.abstract.substring(0, 200) + '...' : paper.abstract) : 'No abstract available';
                                    const url = paper.url || paper.arxiv_url || '#';
                                    
                                    return `
                                        <div class="col-md-6 mb-3">
                                            <div class="card h-100 shadow-sm result-item">
                                                <div class="card-body">
                                                    <h6 class="card-title">
                                                        <a href="${url}" target="_blank" class="text-decoration-none">
                                                            ${title}
                                                        </a>
                                                    </h6>
                                                    <p class="text-muted mb-2">
                                                        <small>
                                                            <i class="fas fa-users me-1"></i>
                                                            ${authors}
                                                        </small>
                                                    </p>
                                                    <p class="text-muted mb-2">
                                                        <small>
                                                            <i class="fas fa-calendar me-1"></i>
                                                            ${year}
                                                            <i class="fas fa-database ms-2 me-1"></i>
                                                            ${source}
                                                        </small>
                                                    </p>
                                                    <p class="card-text">
                                                        <small>${abstract}</small>
                                                    </p>
                                                    <div class="d-flex justify-content-between align-items-center">
                                                        <a href="${url}" target="_blank" class="btn btn-sm btn-outline-primary">
                                                            <i class="fas fa-external-link-alt me-1"></i>View Paper
                                                        </a>
                                                        ${paper.pdf_url ? `
                                                            <a href="${paper.pdf_url}" target="_blank" class="btn btn-sm btn-outline-danger">
                                                                <i class="fas fa-file-pdf me-1"></i>PDF
                                                            </a>
                                                        ` : ''}
                                                    </div>
                                                </div>
                                            </div>
                                        </div>
                                    `;
                                } catch (paperError) {
                                    console.error('Error rendering paper', index, paperError);
                                    return `
                                        <div class="col-md-6 mb-3">
                                            <div class="card h-100 shadow-sm result-item">
                                                <div class="card-body">
                                                    <p class="text-danger">Error rendering paper ${index + 1}</p>
                                                </div>
                                            </div>
                                        </div>
                                    `;
                                }
                            }).join('')}
                        </div>
                    </div>
                </div>
            `;
            
            console.log('Generated HTML length:', html.length);
            console.log('Results container:', resultsContainer);
            
            resultsContainer.innerHTML = html;
            
            console.log('Results displayed, container content length:', resultsContainer.innerHTML.length);
            
            // Show success toast
            showToast(`Found ${papers.length} papers for "${data.query}"`, 'success', 3000);
            
        } catch (error) {
            console.error('Error rendering search results:', error);
            resultsContainer.innerHTML = `
                <div class="alert alert-danger" role="alert">
                    <i class="fas fa-exclamation-triangle me-2"></i>
                    Error rendering search results: ${error.message}
                </div>
            `;
        }
    }

    function displayQuestionAnswer(data) {
         // Deduplicate sources based on URL to avoid showing the same source multiple times
        const uniqueSources = data.sources ? data.sources.filter((source, index, array) => 
            array.findIndex(s => s.url === source.url) === index
        ) : [];
        
        const html = `
            <div class="card">
                <div class="card-header">
                    <h5 class="mb-0">
                        <i class="fas fa-question-circle me-2"></i>Question & Answer
                    </h5>
                </div>
                <div class="card-body">
                    <div class="mb-3">
                        <h6 class="text-primary">Question:</h6>
                        <p class="border-start border-primary ps-3">${data.question}</p>
                    </div>
                    <div class="mb-3">
                        <h6 class="text-success">Answer:</h6>
                        <div class="border-start border-success ps-3">
                            ${marked.parse(data.answer)}
                        </div>
                    </div>
                    ${uniqueSources.length > 0 ? `
                        <div class="mb-3">
                            <h6 class="text-info">Sources:</h6>
                            <div class="row">
                                ${uniqueSources.map(source => `
                                    <div class="col-md-6 mb-2">
                                        <div class="card border-info">
                                            <div class="card-body p-2">
                                                <h6 class="card-title small mb-1">
                                                    <a href="${source.url}" target="_blank" class="text-decoration-none">
                                                        ${source.title}
                                                    </a>
                                                </h6>
                                                <p class="text-muted small mb-0">
                                                    <i class="fas fa-users me-1"></i>${source.authors}
                                                </p>
                                            </div>
                                        </div>
                                    </div>
                                `).join('')}
                            </div>
                        </div>
                    ` : ''}
                </div>
            </div>
        `;
        
        resultsContainer.innerHTML = html;
    }

    function displayError(message) {
        const html = `
            <div class="alert alert-danger" role="alert">
                <i class="fas fa-exclamation-triangle me-2"></i>
                <strong>Error:</strong> ${message}
            </div>
        `;
        
        resultsContainer.innerHTML = html;
        showToast('Search error: ' + message, 'danger', 5000);
    }

    console.log('Search page initialized successfully!');
}

// Form validation
function validateForm(formElement) {
    const requiredFields = formElement.querySelectorAll('[required]');
    let isValid = true;
    
    requiredFields.forEach(field => {
        if (!field.value.trim()) {
            field.classList.add('is-invalid');
            isValid = false;
        } else {
            field.classList.remove('is-invalid');
        }
    });
    
    return isValid;
}

// Loading states
function setLoadingState(element, isLoading) {
    if (isLoading) {
        element.disabled = true;
        element.dataset.originalText = element.innerHTML;
        element.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Loading...';
    } else {
        element.disabled = false;
        element.innerHTML = element.dataset.originalText || element.innerHTML;
    }
}

// Error handling
function handleError(error, context = '') {
    console.error(`Error in ${context}:`, error);
    
    let message = 'An unexpected error occurred';
    if (error.message) {
        message = error.message;
    }
    
    showToast(message, 'danger', 8000);
}

// Local storage helpers
function saveToLocalStorage(key, value) {
    try {
        localStorage.setItem(key, JSON.stringify(value));
    } catch (error) {
        console.error('Failed to save to localStorage:', error);
    }
}

function loadFromLocalStorage(key, defaultValue = null) {
    try {
        const value = localStorage.getItem(key);
        return value ? JSON.parse(value) : defaultValue;
    } catch (error) {
        console.error('Failed to load from localStorage:', error);
        return defaultValue;
    }
}

// Enhanced logout function with security cleanup
function logout() {
    // Clear all authentication data
    clearAuthToken();
    
    // Clear all session data
    sessionStorage.clear();
    
    // Clear specific localStorage items but keep non-sensitive data
    const keysToRemove = ['authToken', 'userId', 'tokenTimestamp', 'userSession'];
    keysToRemove.forEach(key => localStorage.removeItem(key));
    
    // Call logout API
    fetch('/api/auth/logout', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        }
    })
    .then(() => {
        // Redirect to login page
        window.location.href = '/login';
    })
    .catch(() => {
        // Even if API call fails, redirect to login
        window.location.href = '/login';
    });
}

// Make logout function globally available
window.logout = logout;

// Make makeAuthenticatedRequest globally available
window.makeAuthenticatedRequest = makeAuthenticatedRequest;

// Export functions for global use
window.ResearchMate = {
    showToast,
    formatDate,
    formatNumber,
    truncateText,
    copyToClipboard,
    downloadText,
    debounce,
    throttle,
    apiRequest,
    highlightSearchTerms,
    validateForm,
    setLoadingState,
    handleError,
    saveToLocalStorage,
    loadFromLocalStorage,
    saveUploadResults,
    restoreUploadResults,
    clearUploadResults,
    displayUploadResults
};

// Make clearUploadResults globally available for onclick handlers
window.clearUploadResults = clearUploadResults;

console.log('ResearchMate JavaScript loaded successfully with upload persistence!');
