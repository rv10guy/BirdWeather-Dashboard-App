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
    initializeWeatherRefresh();
    initializeCharts();
    
    // Add event listeners for UI interactions
    addEventListeners();
});

/**
 * Set up periodic weather data refresh
 */
function initializeWeatherRefresh() {
    // This would normally fetch fresh weather data from the server
    // For now, we'll just simulate it with a console log
    console.log('Weather data refresh initialized');
    
    // Refresh weather data every 10 minutes
    setInterval(() => {
        console.log('Refreshing weather data...');
        // fetchWeatherData();
    }, 600000); // 10 minutes
}

/**
 * Initialize data visualization charts
 */
function initializeCharts() {
    const visualizationContainer = document.getElementById('visualization');
    
    if (visualizationContainer) {
        visualizationContainer.innerHTML = `
            <p class="text-center">
                <em>This is a placeholder for the data visualization chart.</em><br>
                In a real implementation, this would include a chart showing the relationship 
                between bird activity and weather conditions.
            </p>
        `;
    }
}

/**
 * Add event listeners for UI interactions
 */
function addEventListeners() {
    // Make navbar items active on click
    const navLinks = document.querySelectorAll('.navbar-nav .nav-link');
    
    navLinks.forEach(link => {
        link.addEventListener('click', function() {
            // Remove active class from all links
            navLinks.forEach(l => l.classList.remove('active'));
            // Add active class to clicked link
            this.classList.add('active');
        });
    });
    
    // Example: Add click event to refresh weather manually
    const weatherCard = document.querySelector('#weather-data').closest('.card');
    if (weatherCard) {
        weatherCard.addEventListener('click', function() {
            console.log('Manual weather refresh requested');
            // Implementation would go here
        });
    }
} 