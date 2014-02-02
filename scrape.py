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

import json

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

def plot_data(job):
    AZ = []
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
                bid = re.search('data="(\d+)"', str(cells[1])).group(1)
                time = re.search('data="(\d+)"', str(cells[2])).group(1)
                cloud = re.search('devstack-precise-([\w\-]+)-', str(cells[3])).group(1)
                if cloud not in AZ:
                    AZ.append(cloud)
                print "Found cloud %s => %s" % (cloud, time)
                if int(time) < (30 * 60 * 1000):
                    print "Suspect run time"

                data.append(dict(
                    buildid=bid,
                    time=time,
                    cloud=cloud
                ))

    # you need very specific datastructures for matplotlib
    AZ = sorted(AZ)
    with open(job + ".json", "w") as f:
        f.write(json.dumps({"AZ": AZ, "data": data}, indent=4))

    mpdata = {x: {'x': [], 'y': [], 'num': 0} for x in AZ}

    for d in data:
        mpdata[d['cloud']]['x'].append(COUNT)
        mpdata[d['cloud']]['y'].append(int(d['time']) / 60000)
        mpdata[d['cloud']]['num'] += 1
        COUNT += 1

    pl.figure(figsize=(12, 9))

    axes = []
    for az in AZ:
        axes.append(mpdata[az]['x'])
        axes.append(mpdata[az]['y'])
    p = pl.plot(*axes)

    pl.ylim(0)
    pl.ylabel("Minutes to Complete Job")
    pl.xlabel("Run #")
    pl.title("Timing to complete job %s" % job)
    legs = map(lambda x: "%s (%s)" % (x, mpdata[x]['num']), AZ)
    pl.legend(p, legs, loc=3)

    pl.savefig(job + ".png")


def main():
    plot_data("check-tempest-dsvm-full")
    plot_data("check-tempest-dsvm-postgres-full")


if __name__ == "__main__":
    main()
