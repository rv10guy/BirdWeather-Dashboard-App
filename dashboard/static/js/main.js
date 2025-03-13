// BirdWeather Dashboard JavaScript

document.addEventListener('DOMContentLoaded', function() {
    console.log('BirdWeather Dashboard initialized');
    
    // Set current year in the footer
    const currentYearElement = document.querySelector('footer .container p');
    if (currentYearElement) {
        const currentYear = new Date().getFullYear();
        currentYearElement.innerHTML = currentYearElement.innerHTML.replace('{{ current_year }}', currentYear);
    }
    
    // Initialize dashboard components
    initializeFilters();
    setupEventListeners();
});

/**
 * Initialize filter functionality
 */
function initializeFilters() {
    // Hide common birds toggle
    const hideCommonToggle = document.getElementById('hideCommonBird');
    if (hideCommonToggle) {
        hideCommonToggle.addEventListener('change', function() {
            toggleCommonBirds(this.checked);
        });
    }
    
    // Search functionality
    const searchInput = document.querySelector('.search-input input');
    if (searchInput) {
        searchInput.addEventListener('input', function() {
            filterBirdsByName(this.value.trim().toLowerCase());
        });
    }
}

/**
 * Toggle visibility of common birds in the table
 */
function toggleCommonBirds(hideCommon) {
    console.log(`${hideCommon ? 'Hiding' : 'Showing'} common birds`);
    
    // This is a simplified implementation that would be enhanced in a real app
    // In a real implementation, we would check a 'common' property on each bird
    const birdRows = document.querySelectorAll('.bird-table tbody tr');
    
    birdRows.forEach(row => {
        const birdName = row.querySelector('.bird-name').textContent.trim();
        
        // Example: Mark Sparrows as common (would be replaced with actual data in real app)
        const isCommon = birdName.toLowerCase().includes('sparrow');
        
        if (hideCommon && isCommon) {
            row.style.display = 'none';
        } else {
            row.style.display = '';
        }
    });
}

/**
 * Filter birds in the table by name
 */
function filterBirdsByName(searchTerm) {
    console.log(`Filtering birds by: ${searchTerm}`);
    
    const birdRows = document.querySelectorAll('.bird-table tbody tr');
    
    birdRows.forEach(row => {
        const birdName = row.querySelector('.bird-name').textContent.trim().toLowerCase();
        
        if (searchTerm === '' || birdName.includes(searchTerm)) {
            row.style.display = '';
        } else {
            row.style.display = 'none';
        }
    });
}

/**
 * Set up event listeners for interactive elements
 */
function setupEventListeners() {
    // Time filter dropdown
    const dropdownItems = document.querySelectorAll('.dropdown-menu .dropdown-item');
    const dropdownButton = document.getElementById('timeFilterDropdown');
    
    if (dropdownItems.length && dropdownButton) {
        dropdownItems.forEach(item => {
            item.addEventListener('click', function(e) {
                e.preventDefault();
                const selectedTime = this.textContent.trim();
                dropdownButton.textContent = selectedTime;
                filterByTimeRange(selectedTime);
            });
        });
    }
    
    // Bird row selection
    const birdRows = document.querySelectorAll('.bird-table tbody tr');
    birdRows.forEach(row => {
        row.addEventListener('click', function() {
            const birdName = this.querySelector('.bird-name').textContent.trim();
            console.log(`Selected bird: ${birdName}`);
            // In a real app, this would load detailed information about the selected bird
            highlightSelectedRow(this);
        });
    });
}

/**
 * Highlight the selected row and remove highlight from others
 */
function highlightSelectedRow(selectedRow) {
    const birdRows = document.querySelectorAll('.bird-table tbody tr');
    birdRows.forEach(row => {
        row.classList.remove('bg-light');
    });
    selectedRow.classList.add('bg-light');
}

/**
 * Filter bird data by time range
 */
function filterByTimeRange(timeRange) {
    console.log(`Filtering by time range: ${timeRange}`);
    // This would be implemented with actual time-based filtering in a real app
    // For now, we just log the selected time range
}

/**
 * Handle image loading diagnostics
 * This function is kept for reference but not used as we're handling errors in HTML
 */
function handleImageErrors() {
    const images = document.querySelectorAll('img');
    images.forEach(img => {
        img.onerror = function() {
            // Use a more reliable placeholder with bird silhouette
            this.src = 'https://placehold.co/400x300/4A90E2/FFFFFF?text=Bird';
            this.alt = 'Bird placeholder image';
            this.style.backgroundColor = '#4A90E2';
            this.style.padding = '5px';
            
            // Log the error for debugging
            console.warn(`Failed to load image: ${this.src}`);
        };
    });
} 