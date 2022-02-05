import unittest
from numpy import random, isclose
from math import log2
from location_entropy import population_entropy

class TestQuadratureMethods(unittest.TestCase):

    def test_pop_entropy(self):
        my_dict = {}
        my_dict['a']=int(random.rand(1)*100)
        my_dict['b']=int(random.rand(1)*100)
        my_dict['c']=int(random.rand(1)*100)
        x,y,z = population_entropy(my_dict)
        self.assertEqual(x,(my_dict['a']+my_dict['b']+my_dict['c']),"The total population number didn't line up")
        self.assertEqual(y,3,"The number of options didn't line up")
        n = 10
        p = int(random.rand(1)*100)
        my_unif_dict = {i:p for i in range(n)}
        x,y,z = population_entropy(my_unif_dict)
        self.assertEqual(x,p*n,f"The total population number didn't line up")
        self.assertEqual(y,n,"The number of options didn't line up")
        self.assertTrue(isclose(z,log2(n)),"Should maximize entropy")
 
if __name__ == '__main__':
    unittest.main()