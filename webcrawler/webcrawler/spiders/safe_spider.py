import scrapy
from scrapy_playwright.page import PageMethod
import logging

class SafeSpider(scrapy.Spider):
    name = 'safe_spider'
    
    def start_requests(self):
        for url in self.start_urls:
            self.logger.info(f"Starting request for URL: {url}")
            yield scrapy.Request(url, 
                                 meta=dict(
                                     playwright=True,
                                     playwright_include_page=True,
                                     playwright_page_methods=[
                                         PageMethod('wait_for_selector', 'body'),
                                     ],
                                 ),
                                 callback=self.parse,
                                 errback=self.errback_httpbin)

    async def parse(self, response):
        page = response.meta["playwright_page"]
        
        try:
            self.logger.info(f"Parsing response from {response.url}")
            # Extract text content
            content = await page.evaluate("() => document.body.innerText")
            
            self.logger.info(f"Extracted content length: {len(content)}")
            
            # Process the content
            yield {
                'url': response.url,
                'content': content,
            }
            
        except Exception as e:
            self.logger.error(f"Error processing {response.url}: {str(e)}")
        
        finally:
            # Close the page to free up resources
            await page.close()

    async def errback_httpbin(self, failure):
        page = failure.request.meta["playwright_page"]
        await page.close()
        self.logger.error(f"Error occurred: {str(failure)}")