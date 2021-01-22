from selenium import webdriver
import requests
from sys import exit

""" Basic DOM manipulation through Python + Requests library to download images off of https://facesoftheriot.com """


class Scrape:
    def __init__(self):
        self.driver = webdriver.Chrome()
        self.driver.get('https://facesoftheriot.com')
        self.imageTags = None
        self.filenameCounter = 0
        self.getImageTagsOnPage()

    def __del__(self):
        print(f'Downloaded {self.filenameCounter} images!')

    # Start off getting each <img> on the HTML page, then pass to next function
    def getImageTagsOnPage(self):
        self.imageTags = self.driver.find_elements_by_tag_name('img')
        if len(self.imageTags) == 0:
            exit(0)
        self.downloadImages()

    # For each image, go and download it to a file
    def downloadImages(self):
        for tag in self.imageTags:
            src = tag.get_attribute('src')

            # Fill in userAgent from https://www.whatismybrowser.com/detect/what-is-my-user-agent
            # I was getting 406 errors without the user agent
            userAgent = 'YourUserAgent'
            r = requests.get(src, headers={'User-Agent': userAgent}, stream=True)

            # Write data from GET request to file
            with open("./images/" + str(self.filenameCounter) + '.jpg', "wb") as f:
                if not r.ok:
                    print(r)
                    continue

                # Write from stream block by block
                for dataBlock in r.iter_content(1024):
                    if not dataBlock:
                        break
                    f.write(dataBlock)
                self.filenameCounter += 1

        self.getNextPage()

    # Click the 'Next' button to get to the next page, then repeat cycle
    def getNextPage(self):
        self.driver.find_element_by_link_text('Next').click()
        self.getImageTagsOnPage()


# Just instantiate a new Scrape Object, init() takes care of the rest
if __name__ == "__main__":
    Scrape()

