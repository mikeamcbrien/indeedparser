# Indeed Job Parser

A microsite that polls Indeed for new job listings and displays them immediately based on your custom criteria.

## Features

- **Real-time Job Listings**: Automatically polls for new job listings every hour
- **Custom Search Terms**: Add or remove search terms like "Web Developer", "CraftCMS", "DevOps", etc.
- **Advanced Filtering**:
  - Remote-only positions
  - Minimum salary threshold (default: $200k annually)
  - Time period filter (last 24 hours, week, or month)
  - Full-time positions only
- **Responsive UI**: Modern, mobile-friendly interface
- **Job Details**: View salary, location, posting date, and job description
- **Direct Links**: Quick access to the original job posting

## Getting Started

### Prerequisites

- Python 3.8+
- pip (Python package manager)

### Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/indeedparser.git
   cd indeedparser
   ```

2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Run the application:
   ```
   python app.py
   ```

4. Open your browser and navigate to:
   ```
   http://localhost:5000
   ```

## Usage

1. **Search Terms**: Add or remove job titles or skills to search for
2. **Filters**:
   - Set minimum salary (default: $200,000)
   - Choose time period (last 24 hours, week, month)
   - Toggle remote-only and full-time-only options
3. **Refresh Data**: Click the "Refresh Data" button to manually trigger a new search
4. **View Jobs**: Click "View Job" to open the original posting on Indeed

## Important Notes

- This application uses a simulated Indeed API for demonstration purposes
- In a production environment, you would need to use Indeed's official API or implement proper web scraping techniques
- Web scraping Indeed may violate their terms of service, so use at your own risk

## Customization

You can modify the default search terms and filters in the `app.py` file:

- Default search terms: Edit the `search_terms` list in the `update_jobs` function
- Default minimum salary: Modify the `min_salary` parameter in the `scrape_indeed` function
- Default time period: Change the `days_ago` parameter in the `scrape_indeed` function

## License

This project is licensed under the MIT License - see the LICENSE file for details.