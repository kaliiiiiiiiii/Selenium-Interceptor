import time
import unittest


def return_driver():
    from selenium_profiles import driver as mydriver
    from selenium_profiles.profiles import profiles

    mydriver = mydriver()
    profile = profiles.Windows()

    driver = mydriver.start(profile, uc_driver=False)
    return driver


class Driver(unittest.TestCase):
    def test_headers(self):
        from selenium.webdriver.common.by import By  # locate elements
        from selenium_interceptor.interceptor import cdp_listener

        my_platform = "Test_Platform"
        driver = return_driver()
        cdp_listener = cdp_listener(driver=driver)
        cdp_listener.specify_headers({"sec-ch-ua-platform": my_platform})
        thread = cdp_listener.start_threaded(listeners={
            "continue": {"listener": cdp_listener.all_requests, "at_event": cdp_listener.modify_headers},
        })

        driver.get('https://modheader.com/headers?product=ModHeader')
        time.sleep(3)
        driver.refresh()
        time.sleep(1)
        platform = driver.find_element(By.XPATH, '/html/body/div[1]/main/div[1]/div/div/div/table[1]/tbody/tr[19]/td[2]').accessible_name

        driver.quit()

        self.assertEqual(platform, my_platform)  # add assertion here


if __name__ == '__main__':
    unittest.main()
