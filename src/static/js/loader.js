// Simple loader utility functions for inline use
window.showInlineLoader = function(element) {
  if (!element) return;
  const loader = document.createElement('div');
  loader.className = 'inline-loader';
  loader.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Loading...';
  element.appendChild(loader);
};

window.hideInlineLoader = function(element) {
  if (!element) return;
  const loader = element.querySelector('.inline-loader');
  if (loader) loader.remove();
};

// Check if we're on a page that needs initialization check
if (window.location.pathname !== '/loading' && window.location.pathname !== '/login') {
  // For protected pages, check initialization status
  fetch('/api/init-status')
    .then(response => response.json())
    .then(data => {
      if (!data.initialized) {
        window.location.href = '/loading';
      }
    })
    .catch(error => {
      console.error('Error checking init status:', error);
    });
}
