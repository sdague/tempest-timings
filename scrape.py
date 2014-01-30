#!/usr/bin/python

#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import bs4
import urllib2
import pprint
import re
import pylab as pl

pp = pprint.PrettyPrinter()

JENKINS = (
    'jenkins01',
    'jenkins02',
    'jenkins03',
    'jenkins04',
    'jenkins05',
    'jenkins06',
    'jenkins07',
)


def plot_data(job, fname):
    COUNT = 1
    template = "https://%s.openstack.org/job/" + job + "/buildTimeTrend"

    urls = map(lambda x: template % x, JENKINS)
    data = []
    for url in urls:
        print "scraping %s" % url
        page = urllib2.urlopen(url)

        soup = bs4.BeautifulSoup(page.read())
        builds = soup.select("table.sortable tr")

        for build in builds:
            tmp = bs4.BeautifulSoup("<html>" + str(build) + "</html>")
            cells = tmp.findAll('td')
            if not cells:
                continue

            if re.search('data="4"', str(cells[0])):
                bid = re.search('data="(\d+)"', str(cells[1]))
                time = re.search('data="(\d+)"', str(cells[2]))
                cloud = re.search('devstack-precise-([\w\-]+)-', str(cells[3]))
                print "Found cloud %s => %s" % (cloud.group(1), time.group(1))
                data.append(dict(
                    buildid=bid.group(1),
                    time=time.group(1),
                    cloud=cloud.group(1)
                ))

    mpdata = {
        'hpcloud-az1': {'x': [], 'y': []},
        'hpcloud-az2': {'x': [], 'y': []},
        'hpcloud-az3': {'x': [], 'y': []},
        'rax-iad': {'x': [], 'y': []},
        'rax-dfw': {'x': [], 'y': []},
        'rax-ord': {'x': [], 'y': []},
    }

    for d in data:
        mpdata[d['cloud']]['x'].append(COUNT)
        mpdata[d['cloud']]['y'].append(int(d['time']) / 60000)
        COUNT += 1

    pl.figure(figsize=(8, 6))

    p = pl.plot(mpdata['hpcloud-az1']['x'], mpdata['hpcloud-az1']['y'],
                mpdata['hpcloud-az2']['x'], mpdata['hpcloud-az2']['y'],
                mpdata['hpcloud-az3']['x'], mpdata['hpcloud-az3']['y'],
                mpdata['rax-iad']['x'], mpdata['rax-iad']['y'],
                mpdata['rax-dfw']['x'], mpdata['rax-dfw']['y'],
                mpdata['rax-ord']['x'], mpdata['rax-ord']['y'],
                )
    pl.ylim(0)
    pl.ylabel("Minutes to Complete Job")
    pl.xlabel("Run #")
    pl.title("Timing to complete job %s" % job)
    pl.legend([p[0], p[1], p[2], p[3], p[4], p[5]],
              ['hpcloud-az1', 'hpcloud-az2', 'hpcloud-az3',
               'rax-iad', 'rax-dfw', 'rax-ord'],
              loc=3
              )

    pl.savefig(fname)

plot_data("gate-tempest-dsvm-full", 'tempest-full.png')
plot_data("gate-tempest-dsvm-postgres-full", 'tempest-pg-full.png')
