/**
 * Combines multiple class names into a single string
 */
export function cn(...inputs) {
  return inputs.filter(Boolean).join(" ")
}

/**
 * Formats a date string to a localized format
 */
export function formatDate(dateString) {
  if (!dateString) return ""
  
  const date = new Date(dateString)
  return new Intl.DateTimeFormat('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  }).format(date)
}

/**
 * Truncates text to a specified length and adds ellipsis
 */
export function truncateText(text, maxLength = 100) {
  if (!text || text.length <= maxLength) return text
  return `${text.substring(0, maxLength)}...`
}

/**
 * Creates a formatted error message from different error types
 */
export function formatErrorMessage(error) {
  if (!error) return null
  
  // If it's an API error response
  if (error.response?.data?.message) {
    return error.response.data.message
  }
  
  // If it's a regular error object with a message
  if (error.message) {
    return error.message
  }
  
  // If it's a string
  if (typeof error === 'string') {
    return error
  }
  
  // Default error message
  return 'An unexpected error occurred'
}

/**
 * Extracts search params from a URL or location object
 */
export function getSearchParams(location) {
  if (!location) return {}
  
  const searchParams = new URLSearchParams(
    typeof location === 'string' ? location : location.search
  )
  
  return Object.fromEntries(searchParams.entries())
}

/**
 * Creates a debounced function that delays invoking the provided function
 * until after the specified wait time has elapsed since the last invocation
 */
export function debounce(func, wait = 300) {
  let timeout
  
  return function executedFunction(...args) {
    const later = () => {
      clearTimeout(timeout)
      func(...args)
    }
    
    clearTimeout(timeout)
    timeout = setTimeout(later, wait)
  }
}