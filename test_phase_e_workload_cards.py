import sys
import unittest
from pathlib import Path
from bs4 import BeautifulSoup
sys.path.insert(0,str(Path(__file__).resolve().parent/'python'))
from official_spec_extractor import extract_label_value_blocks

class WorkloadCardTests(unittest.TestCase):
    def extract(self,html):
        specs={};extract_label_value_blocks(BeautifulSoup(html,'html.parser'),specs);return specs
    def test_duration_before_label_is_bound_to_own_workload(self):
        specs=self.extract('''<ul>
        <li><strong>40 Hours</strong><p>Video Playback<sup>3</sup></p></li>
        <li><strong>15.4 Hours</strong><p>Gaming</p></li>
        <li><strong>93 Hours</strong><p>Music Playback<sup>4</sup></p></li>
        <li><strong>14.5 Hours</strong><p>Navigation</p></li></ul>''')
        self.assertEqual({k:v['value'] for k,v in specs.items()},
                         {'video_playback':'40 Hours','gaming':'15.4 Hours',
                          'music_playback':'93 Hours','navigation':'14.5 Hours'})
    def test_missing_duration_does_not_borrow_next_card(self):
        specs=self.extract('<ul><li><p>Video Playback</p></li><li><strong>15.4 Hours</strong><p>Gaming</p></li></ul>')
        self.assertNotIn('video_playback',specs)
        self.assertEqual(specs['gaming']['value'],'15.4 Hours')
    def test_conventional_adjacent_specs_still_work(self):
        specs=self.extract('<div><span>Battery Capacity</span></div><div><span>5000 mAh</span></div>')
        self.assertTrue(any(v['value']=='5000 mAh' for v in specs.values()))

if __name__=='__main__':unittest.main()
