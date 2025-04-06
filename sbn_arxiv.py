
import os
import arxiv
import requests
import logging, configparser
import time, datetime, calendar
import re


''' configure the logger '''
# #logger = logging.getLogger(logging.INFO)
logging.basicConfig(
    level = logging.INFO,
    handlers = [logging.FileHandler('./sbn_arxiv.log'), logging.StreamHandler()],
    format = '{:s} {:s} {:s}: {:s}'\
        .format('%(asctime)s', '%(levelname)s', '%(module)s', '%(message)s'),
    datefmt='%Y-%m-%d %H:%M:%S')


''' read the provided settings '''
# read settings.ini
config = configparser.ConfigParser(comment_prefixes='/', allow_no_value=True)
if os.path.exists('./settings.ini'):
    config.read('./settings.ini')
    logging.debug('"settings.ini" file is processed')
else:
    logging.error('"settings.ini" file is not found')
    raise SystemExit(0)

# extract the parameters
try:
    subjects = config.get('settings', 'subjects').replace('\n', ' ').split()
    subjects = [s.lower() for s in subjects]
    date_range = config.get('settings', 'date_range').split('-')
    max_results = int(config.get('settings', 'max_results'))
    font_face = config.get('settings', 'font_face')
    font_size = config.get('settings', 'font_size')
    display_papers = int(config.get('settings', 'display_papers'))
    keywords = config.get('settings', 'keywords').split(', ')
    logging.debug('parameter values are extracted')
except:
    logging.error('parameters are not extracted: error in the "settings.ini" file')
    raise SystemExit(0)


''' parse the date range '''
try:
    # retrieve the previous check time
    last_check = int(config.get('settings', 'last_check'))
    if date_range == ['since','last','check'] and last_check == 0:
        date_range = ['1']

    # if date_range is a single day
    if len(date_range) == 1:
        # if today is Monday, get submissions from last Friday
        if (date_range == ['1']) and (datetime.date.today().strftime('%A') == 'Monday'):
            date_range[0] = '3'
        # parse the date
        date_range = [str(datetime.date.today() - datetime.timedelta(days=int(date_range[0])))]
        date_title = datetime.datetime.strptime(date_range[0], '%Y-%m-%d').strftime('%d %B %Y')
        date_name = date_range[0]

    # if date_range is a range of days
    elif len(date_range) == 2:
        # parse the date
        date_range = [str(datetime.date.today() - datetime.timedelta(days=n))\
                        for n in range(int(date_range[0]), 1+int(date_range[-1]))][::-1]
        date_title = datetime.datetime.strptime(date_range[0], '%Y-%m-%d').strftime('%d %B %Y')\
            + ' -- ' + datetime.datetime.strptime(date_range[-1], '%Y-%m-%d').strftime('%d %B %Y')
        date_name = date_range[0] + ' to ' + date_range[-1]

    # if date_range is since the last check
    elif len(date_range) == 3:
        # parse the date
        date_range = [str(datetime.date.today())]
        date_title = datetime.datetime.strptime(date_range[0], '%Y-%m-%d').strftime('%d %B %Y')
        date_name = date_range[0]

    # other cases
    else:
        raise Exception

except:
    logging.error('"date_range" parameter from the "settings.ini" file is in a wrong format')
    raise SystemExit(0)


''' search arxiv and parse the search_result '''
# form the search query
search_query = 'cat:' + ' OR cat:'.join(subjects)
# check the connection
try:
    requests.head('https://arxiv.org/')
except requests.ConnectionError:
    logging.error('failed to connect to arxiv.org')
    raise SystemExit(0)
# submit the search query
search_result = arxiv.query(search_query, sort_by='lastUpdatedDate', max_results=max_results)
# filter results by date
if date_range == [str(datetime.date.today())]:
    search_result = list(filter(lambda s:\
        calendar.timegm(s['updated_parsed']) > last_check, search_result))
else:
    search_result = list(filter(lambda s:\
        time.strftime('%Y-%m-%d', s['updated_parsed']) in date_range, search_result))


''' prepare submissions '''
# extract papers with matching date and main subject
papers = [search_result[i] for i in range(len(search_result)) \
    if search_result[i]['arxiv_primary_category']['term'].lower() in subjects]
# update the timestamp of the last check
if len(papers) > 0:
    last_check = calendar.timegm(papers[0]['updated_parsed'])
try:
    config.set('settings', 'last_check', str(last_check))
    with open('./settings.ini', 'w') as f:
        config.write(f)
    logging.debug('"last_check" is updated in "settings.ini"')
except:
    logging.warning('"last_check" could not be updated in "settings.ini"')
# sort the papers by priority
papers.sort(key=lambda p: subjects.index(p['arxiv_primary_category']['term'].lower()))


''' generate the html file '''
# create 'html_files' directory if it does not exist
if not os.path.exists('html_files'):
    os.makedirs('html_files')
logging.debug('submissions are processed')

# process selected papers
if len(papers) > 0:
    # create the html file
    html_file = open('./html_files/arXiv submissions from ' + date_name + '.html', 'w+')
    html_file.write('<html>\n')
    # adjust font style and size
    html_file.write('<span style="font-family: {:s}; font-size: {:s};">\n'\
        .format(font_face, font_size))

    # create the title
    date_tags = '{:s} from {:s}'.format(date_title,\
        ', '.join([s[0] + s[1] + s[2].upper() for s in map(lambda x: x.partition('.'), subjects)]))
    html_file.write('<p>{:d} arXiv submissions from {:s}:</p>\n'.format(len(papers), date_tags))

    # iterate over the relevant submissions
    for paper in papers:

        # get paper info
        title = ' '.join(paper['title'].split())
        authors = ', '.join(paper['authors'])
        tags = ', '.join([tag['term'] for tag in paper['tags']])
        for keyword in keywords:
            k = re.compile(re.escape(keyword), re.IGNORECASE)
            title = k.sub('<b><i>{:s}</i></b>'.format(keyword), title)
            authors = k.sub('<b><i>{:s}</i></b>'.format(keyword), authors)

        # write parsed data to the html file
        html_file.write('<br><a href={:s}>\n'.format(paper['pdf_url']))
        html_file.write('<b>{:s}</b></a>\n'.format(title))
        html_file.write('[{:s}]\n'.format(tags))
        html_file.write('<br>{:s}\n'.format(authors))
        html_file.write('<br>\n')

        # display the papers in the console
        if display_papers == 1:
            print('Title:    {:s}'.format(title))
            print('Authors:  {:s}'.format(authors))
            print('Subjects: {:s}'.format(tags))
            print()

    # close the html file
    html_file.write('</span>\n')
    html_file.write('</html>')
    html_file.close()
    logging.info('{:d} arXiv submissions from {:s}.\n'.format(len(papers), date_tags))

else:
    logging.info('No relevant arXiv submissions from {:s}.\n'.format(date_title))

