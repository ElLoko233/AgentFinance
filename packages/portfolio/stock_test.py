import datetime
import os
import shutil

from stock import Stock
from unittest import TestCase, main
from unittest.mock import patch, call

class TestStock(TestCase):
    test_env_dir = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "TestDir"))
    
    ticker = "MSFT"
    stock_test_dir = os.path.normpath(os.path.join(test_env_dir, ticker))
    
    def setUp(self):
        # Relocating to the testing environment
        if os.path.exists(self.test_env_dir) and os.getcwd() != self.test_env_dir:
            os.chdir(self.test_env_dir)
            
        else:
          # Create the test directory
          os.mkdir(self.test_env_dir)
          
          # Relocate to test environment
          os.chdir(self.test_env_dir)
                      
    
    def tearDown(self):
        # Deleting the entire testing environment
        if os.path.exists(self.test_env_dir) and os.getcwd() != self.test_env_dir:
            shutil.rmtree(self.test_env_dir)
            
        else:
          os.chdir(os.path.normpath(os.path.abspath(os.path.join(os.getcwd(), ".."))))
          shutil.rmtree(self.test_env_dir)
          
          
    def test_loadDirectories_function(self):
        """Tests the loadDirectories function if it successfully operates as expected
        """     
           
        # List of directories expected to be called in the specified order
        directory_creation_list_in_order = [call(self.stock_test_dir),
                                         call(os.path.normpath(os.path.join(self.stock_test_dir, "cashflow"))),
                                         call(os.path.normpath(os.path.join(self.stock_test_dir, "incomestatement"))),
                                         call(os.path.normpath(os.path.join(self.stock_test_dir, "balancesheet")))]
        
        # Test if ValueError is raised when object does not have a baseSaveDirectory
        with self.assertRaises(ValueError):
            no_base_directory_stock = Stock(ticker=self.ticker)
            no_base_directory_stock.loadDirectories()
            
        # Test if os.makedirs is called with proper arguments
        with patch("stock.os.makedirs") as mocked_os_makedirs:
            has_base_directory_stock = Stock(ticker=self.ticker, baseSaveDirectory=self.stock_test_dir)
            has_base_directory_stock.loadDirectories()
            mocked_os_makedirs.assert_has_calls(directory_creation_list_in_order, any_order=True)    


if __name__ == '__main__':
    main()