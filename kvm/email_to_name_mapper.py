#!/usr/bin/env python3
"""
Email to Name Mapping Utility
Converts email addresses to full names for PowerPoint presentations
"""

# Email to full name mapping
EMAIL_TO_NAME = {
    "dmfreim@us.ibm.com": "Douglas M Freimuth",
    "Will.Bezenah@ibm.com": "Will Bezenah",
    "Aaron.M.Brown@ibm.com": "Aaron M Brown",
    "Zhuoying.Cai@ibm.com": "Joy Cai",
    "melissa.howland@us.ibm.com": "Melissa Carlson",
    "jdaley@ibm.com": "Joshua Daley",
    "Omar.Elghoul@ibm.com": "Omar Elghoul",
    "Ramesh.Errabolu@ibm.com": "Ramesh Errabolu",
    "farman@us.ibm.com": "Eric R Farman",
    "jjherne@us.ibm.com": "Jason Herne",
    "Peter.Jin@ibm.com": "Peter Jin",
    "dmjudkov@us.ibm.com": "David M Judkovics",
    "jh.kim@ibm.com": "Jaehoon Kim",
    "aekrowia@us.ibm.com": "Anthony E Krowiak",
    "cam@ibm.com": "Cameron Miller",
    "rreyes@us.ibm.com": "Rorie p Reyes",
    "mjrosato@us.ibm.com": "Matthew Rosato",
    "jaredros@us.ibm.com": "Jared Rossi",
    "Konstantin.Shkolnyy@ibm.com": "Konstantin Shkolnyy",
    "Collin.Walling@ibm.com": "Collin Walling",
    "mjwebber@us.ibm.com": "Matthew J Webber",
    "hanli11@ibm.com": "Han Li",
    "Farhan.Ali4@ibm.com": "Farhan Ali"
}

def convert_email_to_name(email_text):
    """
    Convert email address(es) to full name(s)
    
    Args:
        email_text: Email address or comma-separated list of emails
        
    Returns:
        Full name(s) or original text if not found
    """
    if not email_text or not isinstance(email_text, str):
        return email_text or "N/A"
    
    # If it doesn't contain @, it's probably already a name
    if "@" not in email_text:
        return email_text
    
    # Handle multiple emails separated by commas
    if "," in email_text:
        emails = [e.strip() for e in email_text.split(",")]
        names = []
        for email in emails:
            name = EMAIL_TO_NAME.get(email, email.split("@")[0].replace(".", " ").title())
            names.append(name)
        return ", ".join(names)
    
    # Single email
    email = email_text.strip()
    if email in EMAIL_TO_NAME:
        return EMAIL_TO_NAME[email]
    
    # Fallback: extract username and format it
    username = email.split("@")[0]
    return username.replace(".", " ").title()

# Made with Bob
