# Selenium-Interceptor

* Modifying or **adding headers**(#Change-headers)
* Modify response

### Feel free to test my code!

## Getting Started

### Dependencies

* [Python >= 3.7](https://www.python.org/downloads/)
* [Chrome-Browser](https://www.google.de/chrome/) installed
* Selenium

### Installing

* [Windows] Install [Chrome-Browser](https://www.google.de/chrome/)
* ```pip install selenium-interceptor```


### Change-headers
```python

from selenium_profiles.scripts.cdp_tools import cdp_listener

# Note: driver allready initialized

cdp_listener = cdp_listener(driver=driver)
cdp_listener.specify_headers({"sec-ch-ua-platform":"Android"})
thread = cdp_listener.start_threaded(listeners= {
                                                "header_mod":{"listener":cdp_listener.all_requests,"at_event":cdp_listener.modify_headers},
                                                 })
driver.get("https://modheader.com/headers?product=ModHeader")
```
Don't forget to execute
```driver.quit()```
in the End. Else-wise your temporary folder will get flooded! (Windows)

## Help

Please feel free to open an issue or fork!

## Todo



## Deprecated

## Authors

[Aurin Aegerter](mailto:aurinliun@gmx.ch)

## License

Shield: [![CC BY-NC-SA 4.0][cc-by-nc-sa-shield]][cc-by-nc-sa]

This work is licensed under a
[Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License][cc-by-nc-sa].

[![CC BY-NC-SA 4.0][cc-by-nc-sa-image]][cc-by-nc-sa]

[cc-by-nc-sa]: http://creativecommons.org/licenses/by-nc-sa/4.0/
[cc-by-nc-sa-image]: https://licensebuttons.net/l/by-nc-sa/4.0/88x31.png
[cc-by-nc-sa-shield]: https://img.shields.io/badge/License-CC%20BY--NC--SA%204.0-lightgrey.svg

## Disclaimer

I am not responsible what you use the code for!!! Also no warranty!

## Acknowledgments

Inspiration, code snippets, etc.
* [Selenium-Profiles](https://github.com/kaliiiiiiiiii/Selenium-Profiles)
* [Chromedriver-Options List](https://peter.sh/experiments/chromium-command-line-switches/)
* [cdp_event_listeners](https://stackoverflow.com/questions/66227508/selenium-4-0-0-beta-1-how-add-event-listeners-in-cdp)
