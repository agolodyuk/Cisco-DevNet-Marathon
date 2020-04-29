import logging
import argparse
import sys
import time
import pathlib
import re

from pyats import aetest
from pyats.log.utils import banner
from genie.testbed import load

# global for generator
TESTBED = None
RESULTS = {}

class Result:
    def __init__(self,name):
        self.name = name
        self.is_cdp = 'OFF'
        self.nbrs = 0
        self.clock_state = 'unsync'
        self.is_npe = "PE"

    def __str__(self):
        return f'{self.name}; {self.hw}; {self.sw}; {self.is_npe}; CDP is {self.is_cdp}, {self.nbrs} peers; Clock is {self.clock_state}'

def ping_percent(ping_result):
  pattern = '(\d+) percent'
  result = re.search(pattern, ping_result)
  return int(result[1])

def is_alive(dev, ip):
  try:
    result = dev.ping(ip)
  except Exception:
    return False
  else:
    percent = ping_percent(result)
    if percent == 0:
      return False
  return True

def generator():
    for key,value in TESTBED.devices.items():
        yield key

@aetest.loop(uids=generator(),name=generator())
class TestDay1(aetest.Testcase):
    @aetest.setup
    def connect(self, testbed):
        self.ne = testbed.devices[self.uid]
        try:
            self.ne.connect()
        except Exception:
            self.errored('connect to device error, abandoning script', goto = ['exit'])

    @aetest.test
    def make_backup(self):
        try:
            # get conf
            conf = self.ne.execute('show run')

            # save conf
            pathlib.Path('./backup').mkdir(exist_ok=True)
            path = './backup/' + self.ne.name + '_' + time.strftime('%d%m%Y_%H%M') + '.txt'
            with open(path, 'w') as file:
                file.write(conf)
        except Exception:
            self.failed("failed to backup")

    @aetest.test
    def test_cdp(self):
        RESULTS[self.ne.name] = Result(self.ne.name)
        try:
            cdp = self.ne.parse('show cdp neighbors')
        except Exception:
            self.failed('CDP not enabled')

        nbrs_count = len(cdp['cdp']['index'])
        RESULTS[self.ne.name].is_cdp = 'ON'
        RESULTS[self.ne.name].nbrs = nbrs_count
        self.passed(f'CDP is ON, nbrs={nbrs_count}')

    @aetest.test
    def test_software(self):
        soft = self.ne.parse('show version')
        RESULTS[self.ne.name].hw = soft['version']['platform']
        RESULTS[self.ne.name].sw = soft['version']['image_id']
        if 'NPE' in soft['version']['image_id']:
            RESULTS[self.ne.name].is_npe = "NPE"
            self.passed(f"{soft['version']['version']} image={soft['version']['image_id']} with NPE")
        self.passed(f"{soft['version']['version']} image={soft['version']['image_id']} PE")

    @aetest.test
    def test_ntp(self, ntp):
        # set NTP-server IP & TZ
        if not is_alive(self.ne, ntp):
            self.failed('NTP-server unreacheable')
        try:
            self.ne.configure(f'ntp server {ntp}\n'
                              'clock timezone GMT 0 0')
            self.ne.execute('wr')
        except Exception:
            self.failed('something goes wrong when try to set NTP-server')

        # check is clock - sync
        try:
            ntp = self.ne.parse('show ntp status')
        except Exception:
            self.failed()
        else:
            if not 'clock_state' in ntp or not 'system_status' in ntp['clock_state']:
                self.failed()
            status = ntp['clock_state']['system_status']
            if status['status'] != 'synchronized':
                self.failed(f'ntp status={status["status"]}')

        RESULTS[self.ne.name].clock_state = 'sync'

    @aetest.cleanup
    def disconnect(self):
        self.ne.disconnect()

if __name__ == '__main__':
  logging.getLogger(__name__).setLevel(logging.DEBUG)
  logging.getLogger('pyats.aetest').setLevel(logging.DEBUG)

  parser = argparse.ArgumentParser(description='DevNet Marathon day1')
  parser.add_argument('--ntp', type=str, dest='ntp',help='provide NTP-server ip', metavar='A.B.C.D')
  args,sys.argv[1:] = parser.parse_known_args(sys.argv[1:])

  tb = load('test_tb.yaml')
  TESTBED = tb
  aetest.main(testbed=tb, ntp = args.ntp)

  logger = logging.getLogger(__name__)
  logger.info(banner('Step (5). Results'))
  for dev_name, result in RESULTS.items():
      print(result)