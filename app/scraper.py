import csv
from jobspy import scrape_jobs

def test_scrape():
    jobs = scrape_jobs(
        site_name=["indeed", "linkedin", "glassdoor"],
        search_term="software engineer",
        location="India",
        results_wanted=10,
        hours_old=72,
        country_indeed='India',
    )
    print(f"Found {len(jobs)} jobs")
    print(jobs.head())
    jobs.to_csv("jobs.csv", quoting=csv.QUOTE_NONNUMERIC, escapechar="\\", index=False)

if __name__ == "__main__":
    test_scrape()
