#!/usr/bin/env python

from datetime import date, timedelta
import math
import numpy
import os
import requests
import sys

QUERY = ('select * from yahoo.finance.historicaldata where '
         'symbol = "{symbol}" and startDate = "{start_date}" '
         'and endDate = "{end_date}"')
BASE = 'http://query.yahooapis.com/v1/public/yql'


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


def main(symbol, N=20, K=2):
    end_date = date.today()
    start_date = end_date - timedelta(days=int(N * 2 * 1.5))
    qu = QUERY.format(**{'symbol': symbol,
                         'start_date': start_date,
                         'end_date': end_date})
    payload = {
        'q': qu,
        'format': 'json',
        'env': 'store://datatables.org/alltableswithkeys',
        'diagnostics': 'true'
    }
    req = requests.get(BASE, params=payload)
    if req.status_code != 200:
        raise Exception("Error {}".format(req.status_code))
    if not req.json['query']['results']:
        raise Exception(
            req.json['query']['diagnostics']['javascript']['content'])
    quotes = list(reversed(req.json['query']['results']['quote']))
    closes = [float(q['Close']) for q in quotes]

    mas, sigmas = moving_avgs(closes, N)
    upper_bollinger = [x + (K * sigmas[i]) for i, x in enumerate(mas)]

    for i, q in enumerate(quotes[N:]):
        print q['Date'], q['Close'], upper_bollinger[i]


def usage(name):
    print "Usage: {} symbol".format(os.path.basename(name))

if __name__ == '__main__':
    if len(sys.argv) < 2:
        usage(sys.argv[0])
        sys.exit(1)
    sym = sys.argv[1]
    N = 20
    if len(sys.argv) > 2:
        N = int(sys.argv)[2]
    main(sym, N=N)
