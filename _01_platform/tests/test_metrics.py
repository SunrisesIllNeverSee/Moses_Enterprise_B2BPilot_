import math, unittest
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'src'))
from metrics import leverage, yield_metric, token_snr, log_leverage, construction

class TestCanonicalMetrics(unittest.TestCase):
    def test_leverage(self): self.assertEqual(leverage(10, 200), 20)
    def test_yield_identity(self):
        I,O,R=10,5,200
        self.assertAlmostEqual(yield_metric(I,O,R), leverage(I,R)*(O/I))
    def test_snr(self): self.assertAlmostEqual(token_snr(9,1), .1)
    def test_log_leverage(self): self.assertAlmostEqual(log_leverage(10,1000),2)
    def test_construction(self): self.assertAlmostEqual(construction(100,20),.2)
    def test_domains(self):
        self.assertIsNone(leverage(0,10)); self.assertIsNone(yield_metric(0,1,1))
        self.assertIsNone(token_snr(0,0)); self.assertIsNone(construction(0,1))

if __name__ == '__main__': unittest.main()
