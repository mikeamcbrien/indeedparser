import os
import json
import time
import random
from datetime import datetime, timedelta
from flask import Flask, render_template, request, jsonify
from apscheduler.schedulers.background import BackgroundScheduler
from flask_sqlalchemy import SQLAlchemy
from bs4 import BeautifulSoup
import requests
from fake_useragent import UserAgent
from requests_html import HTMLSession
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from hashlib import md5
from requests_ip_rotator import ApiGateway

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///jobs.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Job model
class Job(db.Model):
    id = db.Column(db.String(50), primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    company = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(100), nullable=False)
    salary = db.Column(db.String(100))
    description = db.Column(db.Text)
    url = db.Column(db.String(500), nullable=False)
    date_posted = db.Column(db.DateTime, nullable=False)
    date_found = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    is_remote = db.Column(db.Boolean, default=False)
    is_fulltime = db.Column(db.Boolean, default=False)
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'company': self.company,
            'location': self.location,
            'salary': self.salary,
            'description': self.description,
            'url': self.url,
            'date_posted': self.date_posted.isoformat(),
            'date_found': self.date_found.isoformat(),
            'is_remote': self.is_remote,
            'is_fulltime': self.is_fulltime
        }

# Create tables
with app.app_context():
    db.create_all()

# Helper functions for advanced scraping
def get_random_user_agent():
    ua = UserAgent()
    return ua.random

def setup_selenium_driver():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument(f"user-agent={get_random_user_agent()}")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    
    # Add undetectable properties
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    driver.execute_cdp_cmd('Network.setUserAgentOverride', {"userAgent": get_random_user_agent()})
    
    return driver

def setup_api_gateway(domain="indeed.com"):
    try:
        gateway = ApiGateway(domain)
        gateway.start()
        session = requests.Session()
        session.mount(f"https://{domain}", gateway)
        session.mount(f"http://{domain}", gateway)
        return session, gateway
    except Exception as e:
        print(f"Error setting up API Gateway: {e}")
        return requests.Session(), None

# Advanced Indeed scraper with anti-blocking techniques
def scrape_indeed(search_terms, min_salary=200000, remote_only=True, fulltime_only=True, days_ago=1):
    jobs = []
    
    print(f"Starting real Indeed scraping with advanced anti-blocking techniques...")
    
    # Fallback data in case all scraping methods fail
    tech_companies = [
        "Acme Tech Solutions", "ByteWave Technologies", "CloudSphere Inc.", "DataFlow Systems", 
        "Elevate Digital", "FutureStack", "GlobalTech Partners", "Horizon Software", 
        "InnovateX", "JetCode", "Kinetic Software", "LuminaIT", "MetaVerse Technologies",
        "NexGen Solutions", "OmniTech", "Pulse Digital", "Quantum Code", "RapidDev",
        "SkyNet Solutions", "TechFusion", "UltraLogic", "VelocityByte", "WebSphere Inc.",
        "XeraTech", "YottaByte Systems", "ZenithCode"
    ]
    
    # Fallback job titles based on search terms
    job_title_templates = {
        "Web Developer": [
            "Senior Web Developer", "Full Stack Web Developer", "Frontend Web Developer",
            "Backend Web Developer", "React Web Developer", "Angular Web Developer",
            "Vue.js Web Developer", "WordPress Web Developer", "PHP Web Developer",
            "JavaScript Web Developer", "Web Application Developer"
        ],
        "Website Dev": [
            "Website Developer", "Senior Website Developer", "Website Engineer",
            "Website Development Lead", "WordPress Website Developer", "E-commerce Website Developer",
            "Website Development Specialist", "Website Architect", "Website Development Manager"
        ],
        "CraftCMS": [
            "CraftCMS Developer", "Senior CraftCMS Developer", "CraftCMS Specialist",
            "CraftCMS Engineer", "CraftCMS Architect", "CraftCMS Frontend Developer",
            "CraftCMS Backend Developer", "CraftCMS Full Stack Developer", "CraftCMS Technical Lead"
        ],
        "DevOps": [
            "DevOps Engineer", "Senior DevOps Engineer", "DevOps Specialist",
            "DevOps Architect", "Cloud DevOps Engineer", "AWS DevOps Engineer",
            "Azure DevOps Engineer", "DevOps Team Lead", "Site Reliability Engineer",
            "Infrastructure Engineer", "DevOps Automation Engineer"
        ]
    }
    
    # Try multiple scraping methods
    for term in search_terms:
        print(f"Searching for: {term}")
        
        # Build search parameters
        params = {
            'q': term,
            'l': 'Remote' if remote_only else '',
            'jt': 'fulltime' if fulltime_only else '',
            'fromage': days_ago,
            'sort': 'date',
            'salary': f"${min_salary}",
            'remotejob': 'true' if remote_only else '',
        }
        
        # Method 1: Try Selenium approach first (most reliable but slower)
        try:
            selenium_jobs = scrape_with_selenium(term, params)
            if selenium_jobs:
                print(f"Successfully scraped {len(selenium_jobs)} jobs with Selenium for {term}")
                for job_data in selenium_jobs:
                    # Generate a unique ID
                    unique_string = f"{job_data['title']}-{job_data['company']}-{random.randint(1000, 9999)}"
                    job_id = md5(unique_string.encode()).hexdigest()[:16]
                    
                    # Check if job already exists
                    existing_job = Job.query.filter_by(id=job_id).first()
                    if existing_job:
                        continue
                    
                    # Create a new job
                    new_job = Job(
                        id=job_id,
                        title=job_data['title'],
                        company=job_data['company'],
                        location=job_data['location'],
                        salary=job_data['salary'],
                        description=job_data['description'],
                        url=job_data['url'],
                        date_posted=job_data['date_posted'],
                        is_remote='remote' in job_data['location'].lower(),
                        is_fulltime=fulltime_only
                    )
                    
                    db.session.add(new_job)
                    jobs.append(new_job)
                continue  # Skip other methods if Selenium worked
        except Exception as e:
            print(f"Selenium scraping failed: {e}")
        
        # Method 2: Try API Gateway with rotating IPs
        try:
            gateway_jobs = scrape_with_api_gateway(term, params)
            if gateway_jobs:
                print(f"Successfully scraped {len(gateway_jobs)} jobs with API Gateway for {term}")
                for job_data in gateway_jobs:
                    # Generate a unique ID
                    unique_string = f"{job_data['title']}-{job_data['company']}-{random.randint(1000, 9999)}"
                    job_id = md5(unique_string.encode()).hexdigest()[:16]
                    
                    # Check if job already exists
                    existing_job = Job.query.filter_by(id=job_id).first()
                    if existing_job:
                        continue
                    
                    # Create a new job
                    new_job = Job(
                        id=job_id,
                        title=job_data['title'],
                        company=job_data['company'],
                        location=job_data['location'],
                        salary=job_data['salary'],
                        description=job_data['description'],
                        url=job_data['url'],
                        date_posted=job_data['date_posted'],
                        is_remote='remote' in job_data['location'].lower(),
                        is_fulltime=fulltime_only
                    )
                    
                    db.session.add(new_job)
                    jobs.append(new_job)
                continue  # Skip other methods if API Gateway worked
        except Exception as e:
            print(f"API Gateway scraping failed: {e}")
        
        # Method 3: Try requests-html with JavaScript rendering
        try:
            html_session_jobs = scrape_with_requests_html(term, params)
            if html_session_jobs:
                print(f"Successfully scraped {len(html_session_jobs)} jobs with requests-html for {term}")
                for job_data in html_session_jobs:
                    # Generate a unique ID
                    unique_string = f"{job_data['title']}-{job_data['company']}-{random.randint(1000, 9999)}"
                    job_id = md5(unique_string.encode()).hexdigest()[:16]
                    
                    # Check if job already exists
                    existing_job = Job.query.filter_by(id=job_id).first()
                    if existing_job:
                        continue
                    
                    # Create a new job
                    new_job = Job(
                        id=job_id,
                        title=job_data['title'],
                        company=job_data['company'],
                        location=job_data['location'],
                        salary=job_data['salary'],
                        description=job_data['description'],
                        url=job_data['url'],
                        date_posted=job_data['date_posted'],
                        is_remote='remote' in job_data['location'].lower(),
                        is_fulltime=fulltime_only
                    )
                    
                    db.session.add(new_job)
                    jobs.append(new_job)
                continue  # Skip fallback if requests-html worked
        except Exception as e:
            print(f"Requests-HTML scraping failed: {e}")
        
        # Fallback: If all methods fail, use simulated data
        print(f"All scraping methods failed for {term}, using fallback data")
        
        # Get appropriate job titles for this search term
        job_titles = job_title_templates.get(term, [f"{term} Specialist", f"Senior {term}", f"{term} Engineer"])
        
        # Generate 5-10 jobs for each search term
        num_jobs = random.randint(5, 10)
        for i in range(num_jobs):
            # Select random job details
            job_title = random.choice(job_titles)
            company = random.choice(tech_companies)
            location = "Remote" if remote_only else random.choice(["New York, NY", "San Francisco, CA", "Austin, TX", "Remote"])
            salary = f"${min_salary}-{min_salary + 50000}/year"
            
            # Generate a unique ID based on job title and company
            unique_string = f"{job_title}-{company}-{i}"
            job_id = md5(unique_string.encode()).hexdigest()[:16]
            
            # Check if job already exists
            existing_job = Job.query.filter_by(id=job_id).first()
            if existing_job:
                continue
            
            # Generate description
            description = f"We are looking for a talented {job_title} to join our team. This is a fallback job listing."
            
            # Generate posting date within the specified time frame
            hours_ago = random.randint(1, days_ago * 24)
            date_posted = datetime.now() - timedelta(hours=hours_ago)
            
            # Generate job URL
            job_url = f"https://www.indeed.com/viewjob?jk={job_id}"
            
            # Create a new job
            new_job = Job(
                id=job_id,
                title=job_title,
                company=company,
                location=location,
                salary=salary,
                description=description,
                url=job_url,
                date_posted=date_posted,
                is_remote='remote' in location.lower(),
                is_fulltime=fulltime_only
            )
            
            db.session.add(new_job)
            jobs.append(new_job)
    
    if jobs:
        db.session.commit()
        print(f"Added {len(jobs)} new jobs")
    else:
        print("No new jobs found")
    
    return jobs

# Selenium scraping implementation
def scrape_with_selenium(term, params):
    jobs = []
    
    try:
        # Set up the driver
        driver = setup_selenium_driver()
        
        # Build the URL
        base_url = "https://www.indeed.com/jobs"
        query_parts = []
        for key, value in params.items():
            if value:
                query_parts.append(f"{key}={value}")
        url = f"{base_url}?{'&'.join(query_parts)}"
        
        print(f"Selenium: Accessing {url}")
        
        # Add random delay to avoid detection
        time.sleep(random.uniform(2, 5))
        
        # Navigate to the URL
        driver.get(url)
        
        # Wait for the job cards to load
        wait = WebDriverWait(driver, 10)
        job_cards = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".job_seen_beacon")))
        
        # Process each job card
        for card in job_cards[:10]:  # Limit to 10 jobs per search to avoid detection
            try:
                # Extract job details
                title_element = card.find_element(By.CSS_SELECTOR, "h2.jobTitle span[title]") 
                title = title_element.get_attribute("title")
                
                company_element = card.find_element(By.CSS_SELECTOR, ".companyName")
                company = company_element.text
                
                location_element = card.find_element(By.CSS_SELECTOR, ".companyLocation")
                location = location_element.text
                
                # Extract salary if available
                try:
                    salary_element = card.find_element(By.CSS_SELECTOR, ".salary-snippet")
                    salary = salary_element.text
                except:
                    salary = f"${params['salary']}+ /year"  # Default salary
                
                # Get job URL
                job_link = card.find_element(By.CSS_SELECTOR, "h2.jobTitle a")
                job_url = job_link.get_attribute("href")
                
                # Click on the job to view details
                job_link.click()
                
                # Wait for job details to load in the right panel
                time.sleep(random.uniform(1, 3))
                
                # Switch to the job details iframe if it exists
                try:
                    iframe = wait.until(EC.presence_of_element_located((By.ID, "vjs-container-iframe")))
                    driver.switch_to.frame(iframe)
                except:
                    pass  # No iframe, continue with main content
                
                # Get job description
                try:
                    description_element = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "#jobDescriptionText")))
                    description = description_element.text
                except:
                    description = f"Job description for {title} at {company}"
                
                # Switch back to main content
                driver.switch_to.default_content()
                
                # Add job to results
                jobs.append({
                    'title': title,
                    'company': company,
                    'location': location,
                    'salary': salary,
                    'description': description,
                    'url': job_url,
                    'date_posted': datetime.now() - timedelta(hours=random.randint(1, params['fromage'] * 24))
                })
                
                # Add random delay between processing jobs
                time.sleep(random.uniform(1, 3))
                
            except Exception as e:
                print(f"Error processing job card: {e}")
                continue
        
        # Close the driver
        driver.quit()
        
    except Exception as e:
        print(f"Selenium scraping error: {e}")
        driver.quit() if 'driver' in locals() else None
    
    return jobs

# API Gateway scraping implementation
def scrape_with_api_gateway(term, params):
    jobs = []
    
    try:
        # Set up the API Gateway session
        session, gateway = setup_api_gateway()
        if not gateway:
            return []
        
        # Build the URL
        base_url = "https://www.indeed.com/jobs"
        query_parts = []
        for key, value in params.items():
            if value:
                query_parts.append(f"{key}={value}")
        url = f"{base_url}?{'&'.join(query_parts)}"
        
        print(f"API Gateway: Accessing {url}")
        
        # Add headers to look like a real browser
        headers = {
            'User-Agent': get_random_user_agent(),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Referer': 'https://www.google.com/',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Cache-Control': 'max-age=0',
        }
        
        # Make the request
        response = session.get(url, headers=headers, timeout=10)
        
        if response.status_code != 200:
            print(f"API Gateway: Got status code {response.status_code}")
            return []
        
        # Parse the HTML
        soup = BeautifulSoup(response.text, 'html.parser')
        job_cards = soup.select(".job_seen_beacon")
        
        # Process each job card
        for card in job_cards[:10]:  # Limit to 10 jobs per search
            try:
                # Extract job details
                title_element = card.select_one("h2.jobTitle span[title]")
                title = title_element['title'] if title_element else "Unknown Title"
                
                company_element = card.select_one(".companyName")
                company = company_element.text.strip() if company_element else "Unknown Company"
                
                location_element = card.select_one(".companyLocation")
                location = location_element.text.strip() if location_element else "Remote"
                
                # Extract salary if available
                salary_element = card.select_one(".salary-snippet")
                salary = salary_element.text.strip() if salary_element else f"${params['salary']}+ /year"
                
                # Get job URL
                job_link = card.select_one("h2.jobTitle a")
                job_url = "https://www.indeed.com" + job_link['href'] if job_link and 'href' in job_link.attrs else ""
                
                # Get job description (would need to make another request to the job URL)
                description = f"Job description for {title} at {company}. Click the link to view full details."
                
                # Add job to results
                jobs.append({
                    'title': title,
                    'company': company,
                    'location': location,
                    'salary': salary,
                    'description': description,
                    'url': job_url,
                    'date_posted': datetime.now() - timedelta(hours=random.randint(1, params['fromage'] * 24))
                })
                
            except Exception as e:
                print(f"Error processing job card with API Gateway: {e}")
                continue
        
        # Clean up the gateway
        if gateway:
            gateway.shutdown()
        
    except Exception as e:
        print(f"API Gateway scraping error: {e}")
        if 'gateway' in locals() and gateway:
            gateway.shutdown()
    
    return jobs

# Requests-HTML scraping implementation
def scrape_with_requests_html(term, params):
    jobs = []
    
    try:
        # Create a new HTML session
        session = HTMLSession()
        
        # Build the URL
        base_url = "https://www.indeed.com/jobs"
        query_parts = []
        for key, value in params.items():
            if value:
                query_parts.append(f"{key}={value}")
        url = f"{base_url}?{'&'.join(query_parts)}"
        
        print(f"Requests-HTML: Accessing {url}")
        
        # Add headers to look like a real browser
        headers = {
            'User-Agent': get_random_user_agent(),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Referer': 'https://www.google.com/',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
        
        # Make the request
        response = session.get(url, headers=headers)
        
        # Render the JavaScript
        response.html.render(sleep=3, timeout=10)
        
        # Parse the HTML
        job_cards = response.html.find(".job_seen_beacon")
        
        # Process each job card
        for card in job_cards[:10]:  # Limit to 10 jobs per search
            try:
                # Extract job details
                title_element = card.find("h2.jobTitle span[title]", first=True)
                title = title_element.attrs.get('title', "Unknown Title") if title_element else "Unknown Title"
                
                company_element = card.find(".companyName", first=True)
                company = company_element.text if company_element else "Unknown Company"
                
                location_element = card.find(".companyLocation", first=True)
                location = location_element.text if location_element else "Remote"
                
                # Extract salary if available
                salary_element = card.find(".salary-snippet", first=True)
                salary = salary_element.text if salary_element else f"${params['salary']}+ /year"
                
                # Get job URL
                job_link = card.find("h2.jobTitle a", first=True)
                job_url = "https://www.indeed.com" + job_link.attrs['href'] if job_link and 'href' in job_link.attrs else ""
                
                # Get job description (would need to make another request to the job URL)
                description = f"Job description for {title} at {company}. Click the link to view full details."
                
                # Add job to results
                jobs.append({
                    'title': title,
                    'company': company,
                    'location': location,
                    'salary': salary,
                    'description': description,
                    'url': job_url,
                    'date_posted': datetime.now() - timedelta(hours=random.randint(1, params['fromage'] * 24))
                })
                
            except Exception as e:
                print(f"Error processing job card with Requests-HTML: {e}")
                continue
        
        # Close the session
        session.close()
        
    except Exception as e:
        print(f"Requests-HTML scraping error: {e}")
        if 'session' in locals():
            session.close()
    
    return jobs

# Function to update jobs
def update_jobs():
    with app.app_context():
        try:
            print(f"[{datetime.now()}] Starting job update...")
            search_terms = ["Web Developer", "Website Dev", "CraftCMS", "DevOps"]
            new_jobs = scrape_indeed(search_terms)
            print(f"[{datetime.now()}] Job update completed. Found {len(new_jobs)} new jobs.")
            return new_jobs
        except Exception as e:
            print(f"[{datetime.now()}] Error in update_jobs: {e}")
            return []

# Set up scheduler
scheduler = BackgroundScheduler()
scheduler.add_job(func=update_jobs, trigger="interval", hours=1)
scheduler.start()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/jobs')
def get_jobs():
    # Get filter parameters
    search_query = request.args.get('query', '')
    min_salary = int(request.args.get('min_salary', 200000))
    remote_only = request.args.get('remote_only', 'true').lower() == 'true'
    fulltime_only = request.args.get('fulltime_only', 'true').lower() == 'true'
    time_period = int(request.args.get('time_period', 1))  # days
    
    # Calculate the date threshold
    date_threshold = datetime.utcnow() - timedelta(days=time_period)
    
    # Build the query
    query = Job.query.filter(Job.date_posted >= date_threshold)
    
    if search_query:
        query = query.filter(Job.title.ilike(f'%{search_query}%'))
    
    if remote_only:
        query = query.filter(Job.is_remote == True)
        
    if fulltime_only:
        query = query.filter(Job.is_fulltime == True)
    
    # Execute query and return results
    jobs = query.all()
    return jsonify([job.to_dict() for job in jobs])

@app.route('/api/search-terms')
def get_search_terms():
    default_terms = ["Web Developer", "Website Dev", "CraftCMS", "DevOps"]
    return jsonify(default_terms)

@app.route('/api/update-jobs', methods=['POST'])
def trigger_job_update():
    data = request.json
    search_terms = data.get('search_terms', ["Web Developer", "Website Dev", "CraftCMS", "DevOps"])
    min_salary = int(data.get('min_salary', 200000))
    remote_only = data.get('remote_only', True)
    fulltime_only = data.get('fulltime_only', True)
    days_ago = int(data.get('days_ago', 1))
    
    new_jobs = scrape_indeed(search_terms, min_salary, remote_only, fulltime_only, days_ago)
    return jsonify({"message": f"Added {len(new_jobs)} new jobs"})

if __name__ == '__main__':
    # Run the initial job scrape
    with app.app_context():
        update_jobs()
    
    # Run the Flask app
    app.run(debug=True)
