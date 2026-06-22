// Shared client utilities for Leafy Dash

function getAuthHeader() {
    const token = localStorage.getItem('user_token');
    return token ? { 'Authorization': `Bearer ${token}` } : {};
}

// Redirect client to login if unauthorized
function checkUserAuth() {
    const token = localStorage.getItem('user_token');
    const role = localStorage.getItem('user_role');
    
    if (!token || role !== 'user') {
        localStorage.clear();
        window.location.href = '/login';
        return false;
    }
    return true;
}

// Format currency dynamically based on regional settings
function formatCurrency(amount) {
    const currency = localStorage.getItem('intl_base_currency') || 'USD';
    const locales = {
        'USD': 'en-US',
        'GBP': 'en-GB',
        'EUR': 'de-DE'
    };
    const locale = locales[currency] || 'en-US';
    return new Intl.NumberFormat(locale, {
        style: 'currency',
        currency: currency
    }).format(amount);
}

// Get the currency symbol corresponding to the active regional currency
function getCurrencySymbol() {
    const currency = localStorage.getItem('intl_base_currency') || 'USD';
    const symbols = {
        'USD': '$',
        'GBP': '£',
        'EUR': '€'
    };
    return symbols[currency] || '$';
}

// Dynamic regional date formatting
function formatDate(dateString) {
    if (!dateString) return 'N/A';
    const date = new Date(dateString);
    const format = localStorage.getItem('intl_date_format') || 'MM/DD/YYYY';
    
    const dd = String(date.getDate()).padStart(2, '0');
    const mm = String(date.getMonth() + 1).padStart(2, '0');
    const yyyy = date.getFullYear();
    
    if (format === 'DD/MM/YYYY') {
        return `${dd}/${mm}/${yyyy}`;
    } else if (format === 'YYYY-MM-DD') {
        return `${yyyy}-${mm}-${dd}`;
    } else {
        return `${mm}/${dd}/${yyyy}`;
    }
}

// Dynamic regional datetime formatting
function formatDateTime(dateString) {
    if (!dateString) return 'N/A';
    const date = new Date(dateString);
    const datePart = formatDate(dateString);
    const timePart = date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    return `${datePart} ${timePart}`;
}

// Escape HTML utility to prevent XSS
function escapeHtml(text) {
    if (text === null || text === undefined) return '';
    const map = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#039;'
    };
    return String(text).replace(/[&<>"']/g, function(m) { return map[m]; });
}

// Validate email format using RFC 5322 regex
function isValidEmail(email) {
    const trimmed = String(email || '').trim();
    if (!trimmed) return false;
    const re = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;
    return re.test(trimmed);
}

// Validate password strength based on backend rules:
// - At least 8 characters long
// - At least one uppercase letter
// - At least one lowercase letter
// - At least one digit
// - At least one special character from @$!%*?&_#-
function getPasswordStrengthError(password) {
    if (!password) {
        return "Password is required.";
    }
    if (password.length < 8) {
        return "Password must be at least 8 characters long.";
    }
    if (!/[A-Z]/.test(password)) {
        return "Password must contain at least one uppercase letter.";
    }
    if (!/[a-z]/.test(password)) {
        return "Password must contain at least one lowercase letter.";
    }
    if (!/[0-9]/.test(password)) {
        return "Password must contain at least one digit.";
    }
    const specialChars = "@$!%*?&_#-";
    const hasSpecial = password.split('').some(char => specialChars.includes(char));
    if (!hasSpecial) {
        return `Password must contain at least one special character from: ${specialChars}`;
    }
    return null;
}

// Check if string is empty or contains only spaces after trimming
function validateRequiredString(value, fieldName) {
    const trimmed = String(value || '').trim();
    if (!trimmed) {
        return `${fieldName} cannot be empty or only whitespace.`;
    }
    return null;
}

