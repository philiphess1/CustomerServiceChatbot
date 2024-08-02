import scrapy
from scrapy_playwright.page import PageMethod
import json
import time

class SafeSpider(scrapy.Spider):
    name = 'safe_spider'
    
    def start_requests(self):
        urls = [
            self.start_urls[0],  # Use the URL passed from the scrape_url function
        ]
        for url in urls:
            yield scrapy.Request(url, 
                                 meta=dict(
                                     playwright=True,
                                     playwright_include_page=True,
                                     playwright_page_methods=[
                                         PageMethod('wait_for_selector', 'body'),
                                     ],
                                 ),
                                 callback=self.parse)

    def parse(self, response):
        page = response.meta["playwright_page"]
        
        # Extract text content
        content = yield page.evaluate("() => document.body.innerText")
        
        # Process the content
        yield {
            'url': response.url,
            'content': content,
        }
        
        # Find and follow links
        links = yield page.evaluate("() => Array.from(document.links).map(link => link.href)")
        for link in links:
            if link.startswith(response.url):  # Only follow internal links
                yield scrapy.Request(link, 
                                     meta=dict(
                                         playwright=True,
                                         playwright_include_page=True,
                                         playwright_page_methods=[
                                             PageMethod('wait_for_selector', 'body'),
                                         ],
                                     ),
                                     callback=self.parse)
        
        # Close the page to free up resources
        yield page.close()
        
        # Add a delay between requests
        time.sleep(2)  # Adjust this value as needed