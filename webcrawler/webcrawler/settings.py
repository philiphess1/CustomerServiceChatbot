# Scrapy settings for webcrawler project

BOT_NAME = "webcrawler"

SPIDER_MODULES = ["webcrawler.spiders"]
NEWSPIDER_MODULE = "webcrawler.spiders"

# Crawl responsibly by identifying yourself (and your website) on the user-agent
#USER_AGENT = "webcrawler (+http://www.yourdomain.com)"

# Obey robots.txt rules
ROBOTSTXT_OBEY = True

# Configure maximum concurrent requests performed by Scrapy (default: 16)
CONCURRENT_REQUESTS = 1

# Configure a delay for requests for the same website (default: 0)
DOWNLOAD_DELAY = 3

# Disable cookies (enabled by default)
COOKIES_ENABLED = False

# Disable Telnet Console (enabled by default)
#TELNETCONSOLE_ENABLED = False

# Override the default request headers:
#DEFAULT_REQUEST_HEADERS = {
#    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
#    "Accept-Language": "en",
#}

# Enable or disable spider middlewares
#SPIDER_MIDDLEWARES = {
#    "webcrawler.middlewares.WebcrawlerSpiderMiddleware": 543,
#}

# Enable or disable downloader middlewares
#DOWNLOADER_MIDDLEWARES = {
#    "webcrawler.middlewares.WebcrawlerDownloaderMiddleware": 543,
#}

# Enable or disable extensions
#EXTENSIONS = {
#    "scrapy.extensions.telnet.TelnetConsole": None,
#}

# Configure item pipelines
#ITEM_PIPELINES = {
#    "webcrawler.pipelines.WebcrawlerPipeline": 300,
#}

# Enable and configure HTTP caching (disabled by default)
#HTTPCACHE_ENABLED = True
#HTTPCACHE_EXPIRATION_SECS = 0
#HTTPCACHE_DIR = "httpcache"
#HTTPCACHE_IGNORE_HTTP_CODES = []
#HTTPCACHE_STORAGE = "scrapy.extensions.httpcache.FilesystemCacheStorage"

# Set settings whose default value is deprecated to a future-proof value
REQUEST_FINGERPRINTER_IMPLEMENTATION = "2.7"
TWISTED_REACTOR = "twisted.internet.asyncioreactor.AsyncioSelectorReactor"
FEED_EXPORT_ENCODING = "utf-8"

# Playwright settings
DOWNLOAD_HANDLERS = {
    "http": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
    "https": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
}

# Playwright settings
TWISTED_REACTOR = "twisted.internet.asyncioreactor.AsyncioSelectorReactor"

# Enable Playwright
PLAYWRIGHT_BROWSER_TYPE = "chromium"

# Launch options for Playwright browser
PLAYWRIGHT_LAUNCH_OPTIONS = {
    "headless": True,
    "timeout": 20 * 1000,  # 20 seconds
}

# Configure item pipelines
ITEM_PIPELINES = {
    'webcrawler.pipelines.WebcrawlerPipeline': 300,
    'webcrawler.pipelines.CollectItemsPipeline': 400,
}
LOG_ENABLED = True
LOG_LEVEL = 'DEBUG'