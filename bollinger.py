#!/usr/bin/env python

import csv
from datetime import date, timedelta
import math
import os
import requests
import sys

import matplotlib
matplotlib.use('AGG')

import matplotlib.pyplot as plt
plt.ioff()

YQL_QUERY = ('select * from yahoo.finance.historicaldata where '
         'symbol = "{symbol}" and startDate = "{start_date}" '
         'and endDate = "{end_date}"')
YQL_BASE = 'http://query.yahooapis.com/v1/public/yql'

CSV_HIST_BASE = 'http://ichart.yahoo.com/table.csv'

CSV_CUR_BASE = 'http://download.finance.yahoo.com/d/quotes.csv'


def moving_avgs(seq, N):
    mas = []
    std_devs = []
    ma = sum(seq[:N]) / N
    mas.append(ma)
    std_devs.append(pop_std_dev(seq[:N]))
    for i, c in enumerate(seq[N:]):
        ma = mas[-1]
        ma -= seq[i] / N
        ma += c / N
        mas.append(ma)
        std_devs.append(pop_std_dev(seq[i + 1:N + i]))
    return mas, std_devs


def pop_std_dev(seq):
    '''
    Calculates the population standard deviation for a sequence.
    '''
    mean = sum(seq) / len(seq)
    variances_sq = [(x - mean) ** 2 for x in seq]
    sigma = math.sqrt(sum(variances_sq) / len(seq))
    return sigma


def _get_quotes_yql(symbol, start_date, end_date):
    qu = YQL_QUERY.format(**{'symbol': symbol,
                             'start_date': start_date,
                             'end_date': end_date})
    payload = {
        'q': qu,
        'format': 'json',
        'env': 'store://datatables.org/alltableswithkeys',
        'diagnostics': 'true'
    }
    req = requests.get(YQL_BASE, params=payload)
    if req.status_code != 200:
        raise Exception("Error {}".format(req.status_code))
    if not req.json['query']['results']:
        raise Exception(
            req.json['query']['diagnostics']['javascript']['content'])
    quotes = list(reversed(req.json['query']['results']['quote']))
    return quotes


def _get_quotes_csv(symbol, start_date, end_date):
    # Historical data
    payload = {
        's': symbol,
        'a': start_date.month - 1,
        'b': start_date.day,
        'c': start_date.year,
        'd': end_date.month - 1,
        'e': end_date.day,
        'f': end_date.year,
        'g': 'd', # trading periods: https://code.google.com/p/yahoo-finance-managed/wiki/enumHistQuotesInterval
        'ignore': 'csv',
    }
    req = requests.get(CSV_HIST_BASE, params=payload)
    quotes = list(reversed([q for q in csv.DictReader(req.content.splitlines(),
                                                      delimiter=',')]))

    # Today's data
    payload = {
        's': symbol,
        # Quote properties: https://code.google.com/p/yahoo-finance-managed/wiki/enumQuoteProperty
        'f': 'nsl1d1',
    }
    req = requests.get(CSV_CUR_BASE, params=payload)
    reader = csv.reader(req.content.splitlines(),
                        delimiter=',')
    # TODO: how can I get the header so I can use DictReader?
    name, _, close, quote_date = reader.next()
    # Date is in mon/day/year format
    mon, day, year = quote_date.split('/')
    quote_date = '-'.join([year, '%.02d' % int(mon), '%.02d' % int(day)])
    if quote_date != quotes[-1]['Date']:
        # Fake today's quote
        quote = {
            'Close': close,
            'Date': quote_date
        }
        quotes.append(quote)
    return quotes


def get_quotes(symbol, start_date, end_date, mode='yql'):
    if mode == 'yql':
        closes = _get_quotes_yql(symbol, start_date, end_date)
    elif mode == 'csv':
        closes = _get_quotes_csv(symbol, start_date, end_date)
    else:
        raise Exception('Unknown mode {}'.format(mode))
    return closes

def render(symbol, quotes, upper, lower):
    closes = [float(q['Close']) for q in quotes]
    dates = [date(*map(int, q['Date'].split('-'))) for q in quotes]

    fig, ax = plt.subplots(1)

    fig.autofmt_xdate()

    plt.title(symbol)
    plt.ylabel('Closes')

    ax.plot(dates, closes)
    ax.plot(dates, upper, 'r--')
    ax.plot(dates, lower, 'r--')

    # ax.fill_between(dates, lower, upper, facecolor='red', alpha=0.3)

    for var, color in zip((lower, closes, upper), ('red', 'blue', 'red')):
        plt.annotate('%0.2f' % var[-1], xy=(1, var[-1]), xytext=(8, 0),
                     xycoords=('axes fraction', 'data'),
                     textcoords='offset points',
                     color=color,
        )
    # second_axis = plt.twinx()
    # second_axis.set_yticks([lower[-1], closes[-1], upper[-1]])

    plt.savefig('output.png')


def main(symbol, N=20, K=2, days=90):
    end_date = date.today()
    start_date = end_date - timedelta(days=days + N)

    quotes = get_quotes(symbol, start_date, end_date, mode='csv')
    closes = [float(q['Close']) for q in quotes]

    mas, sigmas = moving_avgs(closes, N)
    upper_bollinger = [x + (K * sigmas[i]) for i, x in enumerate(mas)]
    lower_bollinger = [x - (K * sigmas[i]) for i, x in enumerate(mas)]
    render(symbol, quotes[N-1:], upper_bollinger, lower_bollinger)

    for i, q in enumerate(quotes[N-1:]):
        print '{date}, {close}, {upper}, {lower}, {signal}'.format(**{
            'date': q['Date'],
            'close': q['Close'],
            'upper': '%.02f' % upper_bollinger[i],
            'lower': '%.02f' % lower_bollinger[i],
            'signal': ('+' if float(q['Close']) > upper_bollinger[i] else
                       '-' if float(q['Close']) < lower_bollinger[i] else
                       ' '),
        })


def usage(name):
    print "Usage: {} symbol".format(os.path.basename(name))

if __name__ == '__main__':
    if len(sys.argv) < 2:
        usage(sys.argv[0])
        sys.exit(1)
    sym = sys.argv[1]
    N = 20
    if len(sys.argv) > 2:
        N = int(sys.argv[2])
    main(sym, N=N)
