# fetch and parse
import requests
from bs4 import BeautifulSoup

# io
from getpass import getpass

# date time
from datetime import datetime, timedelta, timezone
from pytimeparse import parse

# ics generator
from ics import Calendar, Event

URL = 'https://exams.unimelb.edu.au/timetable/personal.php?db=8'

class Exam():
    def __init__(self, init_dict):
        """expected format: {'Building': 'REBW',
            'Date': 'Tuesday 18/06/2019',
            'Duration': '3 hours plus 15 minutes reading',
            'Exam': 'CHEM10009 Chemistry for BioSciences',
            'Exam Conditions': 'CLOSED book exam',
            'Reading Time': '15 minutes',
            'Time': '1:15pm',
            'Venue': 'Royal Exhibition Building West',
            'Writing Time': '3 hours',
            'Your Seat': '695'}"""
        self.start = datetime.strptime('{} @ {} +1000'.format(init_dict['Date'], init_dict['Time']), '%A %d/%m/%Y @ %I:%M%p %z')
        subject = init_dict['Exam'].split()
        self.unit = subject[0]
        self.subject = ' '.join(subject[1:])
        self.duration = (parse(init_dict['Writing Time']) + parse(init_dict['Reading Time'])) / 60
        td_dur = timedelta(minutes=self.duration)
        self.end = self.start + td_dur
        self.venue = init_dict['Venue']
        self.seat = init_dict['Your Seat']
        self.conditions = init_dict['Exam Conditions']
        # self.raw_dict = init_dict
        
    def __repr__(self):
        return '{} from {} to {} for {} mins'.format(
            self.unit,
            self.start,
            self.end,
            self.duration
        )

    def ics_event(self):
        e = Event()
        e.name = '{} {} Exam'.format(self.unit, self.subject)
        e.begin = self.start
        e.end = self.end
        e.location = self.venue
        e.url = URL
        e.description = 'Seat: {} \r\nConditions: {} \r\nDuration: {} minutes \r\nVenue: {}'.format(
            self.seat, self.conditions, self.duration, self.venue)
        return e

def main():
    username, password = get_login()
    form_data = build_form_data(get_token(), username, password)
    raw_text = requests.post(URL, data = form_data).text
    
    # Convert list of dictionaries into list of Exam instances
    exams = [Exam(d) for d in parse_page(raw_text)]
    # Create calendar events
    c = Calendar(events=[exam.ics_event() for exam in exams], creator='UNIMELB EXAM TIMETABLE GENERATOR')
    # Write to file
    with open('outfile.ics', 'w') as f:
        f.writelines(c)

def get_token():
    """Get login token from homepage"""
    r = requests.get(URL)
    s = BeautifulSoup(r.text, 'html.parser')
    token = s.form.input.get('value')
    return token

def get_login():
    """Get login info from user"""
    username = input('Username: ')
    password = getpass('Password: ')
    return username, password

def build_form_data(token, username, password):
    """Build POST dictionary"""
    return {
        '_token': token,
        'tAccountName': username,
        'tWebPassword': password,
        'action': 'login'
    }

def parse_page(raw_text):
    s = BeautifulSoup(raw_text, 'html.parser')
    table = s.table
    rows = table.find_all('tr')
    elist = [tuple([d. get_text() for d in row.find_all('td')]) for row in rows]
    new_list = [elist[i:i+11][1:] for i in range(0, len(elist), 11)] # split at every 11
    dict_list = [dict(x) for x in new_list]
    return dict_list

if __name__ == "__main__":
    main()