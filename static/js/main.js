document.addEventListener('DOMContentLoaded', () => {
    // DOM elements
    const searchForm = document.getElementById('search-form');
    const searchTermInput = document.getElementById('search-term-input');
    const addTermBtn = document.getElementById('add-term-btn');
    const searchTermsContainer = document.getElementById('search-terms-container');
    const minSalaryInput = document.getElementById('min-salary');
    const timePeriodSelect = document.getElementById('time-period');
    const remoteOnlyCheckbox = document.getElementById('remote-only');
    const fulltimeOnlyCheckbox = document.getElementById('fulltime-only');
    const refreshBtn = document.getElementById('refresh-btn');
    const jobsContainer = document.getElementById('jobs-container');
    const jobCountElement = document.getElementById('job-count');
    const loadingElement = document.getElementById('loading');
    const noJobsElement = document.getElementById('no-jobs');
    
    // State
    let searchTerms = [];
    let lastFetchTime = null;
    let jobsData = [];
    
    // Initialize
    init();
    
    // Event listeners
    searchForm.addEventListener('submit', handleSearch);
    addTermBtn.addEventListener('click', addSearchTerm);
    searchTermInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            e.preventDefault();
            addSearchTerm();
        }
    });
    refreshBtn.addEventListener('click', refreshJobs);
    
    // Functions
    async function init() {
        try {
            // Load default search terms
            const response = await fetch('/api/search-terms');
            const terms = await response.json();
            searchTerms = terms;
            renderSearchTerms();
            
            // Load initial jobs
            fetchJobs();
            
            // Set up auto-refresh every 5 minutes
            setInterval(fetchJobs, 5 * 60 * 1000);
        } catch (error) {
            console.error('Initialization error:', error);
        }
    }
    
    function addSearchTerm() {
        const term = searchTermInput.value.trim();
        if (term && !searchTerms.includes(term)) {
            searchTerms.push(term);
            searchTermInput.value = '';
            renderSearchTerms();
        }
    }
    
    function removeSearchTerm(term) {
        searchTerms = searchTerms.filter(t => t !== term);
        renderSearchTerms();
    }
    
    function renderSearchTerms() {
        searchTermsContainer.innerHTML = '';
        searchTerms.forEach(term => {
            const pill = document.createElement('div');
            pill.className = 'search-term-pill';
            pill.innerHTML = `
                ${term}
                <span class="close-btn" data-term="${term}">&times;</span>
            `;
            searchTermsContainer.appendChild(pill);
            
            // Add event listener to close button
            pill.querySelector('.close-btn').addEventListener('click', () => {
                removeSearchTerm(term);
            });
        });
    }
    
    async function handleSearch(e) {
        e.preventDefault();
        await fetchJobs();
    }
    
    async function fetchJobs() {
        showLoading();
        
        try {
            // Build query params
            const params = new URLSearchParams();
            if (searchTerms.length > 0) {
                params.append('query', searchTerms.join(','));
            }
            params.append('min_salary', minSalaryInput.value);
            params.append('remote_only', remoteOnlyCheckbox.checked);
            params.append('fulltime_only', fulltimeOnlyCheckbox.checked);
            params.append('time_period', timePeriodSelect.value);
            
            // Fetch jobs
            const response = await fetch(`/api/jobs?${params.toString()}`);
            const newJobs = await response.json();
            
            // Update jobs data
            const oldJobIds = new Set(jobsData.map(job => job.id));
            jobsData = newJobs;
            
            // Render jobs
            renderJobs(jobsData, oldJobIds);
            
            // Update last fetch time
            lastFetchTime = new Date();
            updateLastFetchTime();
        } catch (error) {
            console.error('Error fetching jobs:', error);
            showNoJobs();
        }
    }
    
    async function refreshJobs() {
        try {
            const response = await fetch('/api/update-jobs', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    search_terms: searchTerms,
                    min_salary: parseInt(minSalaryInput.value),
                    remote_only: remoteOnlyCheckbox.checked,
                    fulltime_only: fulltimeOnlyCheckbox.checked,
                    days_ago: parseInt(timePeriodSelect.value)
                })
            });
            
            const result = await response.json();
            console.log(result.message);
            
            // Refresh the jobs list
            fetchJobs();
        } catch (error) {
            console.error('Error refreshing jobs:', error);
        }
    }
    
    function renderJobs(jobs, oldJobIds) {
        // Update job count
        jobCountElement.textContent = `${jobs.length} jobs found`;
        
        // Show/hide loading and no jobs messages
        if (jobs.length === 0) {
            showNoJobs();
            return;
        }
        
        // Clear loading and no jobs messages
        loadingElement.classList.add('d-none');
        noJobsElement.classList.add('d-none');
        
        // Clear jobs container (except for loading and no jobs elements)
        const jobCards = jobsContainer.querySelectorAll('.job-card-container');
        jobCards.forEach(card => card.remove());
        
        // Get job card template
        const template = document.getElementById('job-card-template');
        
        // Sort jobs by date (newest first)
        jobs.sort((a, b) => new Date(b.date_posted) - new Date(a.date_posted));
        
        // Render each job
        jobs.forEach(job => {
            const isNew = !oldJobIds.has(job.id);
            const jobElement = template.content.cloneNode(true);
            const jobCard = jobElement.querySelector('.col-md-6');
            jobCard.classList.add('job-card-container');
            
            // Add new badge if job is new
            if (isNew) {
                const newBadge = document.createElement('div');
                newBadge.className = 'badge bg-danger new-job-badge pulse-animation';
                newBadge.textContent = 'NEW';
                jobCard.querySelector('.job-card').appendChild(newBadge);
            }
            
            // Fill in job details
            jobCard.querySelector('.job-title').textContent = job.title;
            jobCard.querySelector('.company-name').textContent = job.company;
            jobCard.querySelector('.location-badge').textContent = job.location;
            jobCard.querySelector('.salary-badge').textContent = job.salary;
            
            // Format date
            const datePosted = new Date(job.date_posted);
            const timeAgo = getTimeAgo(datePosted);
            jobCard.querySelector('.date-badge').textContent = timeAgo;
            
            // Set description
            jobCard.querySelector('.job-description').textContent = job.description;
            
            // Set link
            const link = jobCard.querySelector('.job-link');
            link.href = job.url;
            
            // Add to jobs container
            jobsContainer.appendChild(jobElement);
        });
    }
    
    function showLoading() {
        loadingElement.classList.remove('d-none');
        noJobsElement.classList.add('d-none');
    }
    
    function showNoJobs() {
        loadingElement.classList.add('d-none');
        noJobsElement.classList.remove('d-none');
    }
    
    function updateLastFetchTime() {
        if (lastFetchTime) {
            const timeAgo = getTimeAgo(lastFetchTime);
            console.log(`Last updated: ${timeAgo}`);
        }
    }
    
    function getTimeAgo(date) {
        const now = new Date();
        const diffMs = now - date;
        const diffSec = Math.floor(diffMs / 1000);
        const diffMin = Math.floor(diffSec / 60);
        const diffHour = Math.floor(diffMin / 60);
        const diffDay = Math.floor(diffHour / 24);
        
        if (diffDay > 0) {
            return `${diffDay} day${diffDay > 1 ? 's' : ''} ago`;
        } else if (diffHour > 0) {
            return `${diffHour} hour${diffHour > 1 ? 's' : ''} ago`;
        } else if (diffMin > 0) {
            return `${diffMin} minute${diffMin > 1 ? 's' : ''} ago`;
        } else {
            return 'Just now';
        }
    }
});
