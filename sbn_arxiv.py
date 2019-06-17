
import arxiv
import os
import time, datetime


'''
	list the arxiv classifiers of interest
	the full list is available at
	https://arxiv.org/help/subscribe#archive-list
'''
subjects = ['math.na', 'math.fa', 'math.gm', 'math.ho', 'math.oc', \
			'cs.ai', 'cs.lg', 'cs.cc', 'cs.cv', 'cs.et', 'cs.it', 'cs.na', \
			'stat.ml', 'stat.ap', 'stat.co']


''' search arxiv and parse the result '''
# form the search query
search_query = 'cat:' + ' OR cat:'.join(subjects)
result = arxiv.query(search_query=search_query, sort_by='lastUpdatedDate', max_results=1000)

# extract the update dates
dates_utc = list(map(lambda t: time.strftime('%Y-%m-%d', t), \
	[paper['updated_parsed'] for paper in result]))
# get yesterday's date
yesterday_utc = datetime.date.today() - datetime.timedelta(days=3)
# find the number of new submissions
num_submit = dates_utc.count(str(yesterday_utc))


''' report new submissions and form html file '''
if num_submit > 0:

	# create 'html_files' directory if it does not exist
	if not os.path.exists('html_files'):
		os.makedirs('html_files')

	# create the html file
	f_html = open('./html_files/arXiv submissions from ' + str(yesterday_utc) + '.html', 'w+')
	f_html.write('<html>\n')

	# create title
	print('{:d} new arXiv submissions from {:s}:\n'\
		.format(num_submit, yesterday_utc.strftime('%d %B %Y')))
	f_html.write('<p>{0} new arXiv submissions from {1} from {2}:</p>\n'\
		.format(num_submit, yesterday_utc.strftime('%d %B %Y'), ', '.join(subjects)))

	# iterate over the new submissions
	for paper in result[:num_submit]:

		# display new papers
		print('Title:    {:s}'.format(paper['title'].replace('\n', '')))
		print('Authors:  {:s}\n'.format(', '.join(paper['authors'])))

		# write parsed data to the html file
		f_html.write('<br><a href={:s}>\n'.format(paper['pdf_url']))
		f_html.write('<b>{:s}</b></a>\n'.format(paper['title'].replace('\n', '')))
		f_html.write('<br>{:s}\n'.format(', '.join([tag['term'] for tag in paper['tags']])))
		f_html.write('<br>{:s}\n'.format(', '.join(paper['authors'])))
		f_html.write('<br>\n')

	# close the html file
	f_html.write('</html>')
	f_html.close()

else:
	print('No new arXiv submissions from {:s}.\n'.format(yesterday_utc.strftime('%d %B %Y')))
