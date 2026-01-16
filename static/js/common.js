/**
 * Common JavaScript functions shared across the application
 */

/**
 * Escape HTML to prevent XSS attacks
 * @param {string} text - The text to escape
 * @returns {string} HTML-escaped text
 */
function escapeHtml(text) {
  if (text === null || text === undefined) {
    return '';
  }
  var map = {
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    '"': '&quot;',
    "'": '&#039;'
  };
  return String(text).replace(/[&<>"']/g, function(m) { return map[m]; });
}

/**
 * Load printer media sizes from the API and update the label size dropdown
 * @param {string} printerName - The name of the printer
 * @param {function} onSuccess - Optional callback function to run after successful load
 */
function loadPrinterMedia(printerName, onSuccess) {
  if (!printerName) return;

  $.ajax({
    type: 'GET',
    url: '/api/printer/' + encodeURIComponent(printerName) + '/media',
    dataType: 'json',
    success: function(data) {
      if (data.success) {
        // Update label sizes dropdown
        $('#labelSize').empty();

        for (var key in data.label_sizes) {
          $('#labelSize').append($('<option>', {
            value: key,
            text: data.label_sizes[key]
          }));
        }

        // When switching printers, always use the printer's default media
        // This ensures each printer's default is selected when switching
        if (data.default_size && data.label_sizes[data.default_size]) {
          $('#labelSize').val(data.default_size);
        }

        // Call optional success callback
        if (onSuccess && typeof onSuccess === 'function') {
          onSuccess(data);
        }
      }
    },
    error: function(xhr, status, error) {
      console.error('Error loading printer media:', error);
    }
  });
}

/**
 * Check if there are configuration errors
 * @returns {Promise<boolean>} Promise that resolves to true if no errors, false if errors exist
 */
function checkConfigErrors() {
  return fetch('/api/config-errors')
    .then(r => r.json())
    .then(data => {
      if (data.has_errors && data.errors && data.errors.length > 0) {
        return false;
      }
      return true;
    })
    .catch(err => {
      console.error('Error checking configuration:', err);
      return true; // Allow operation if we can't check
    });
}

