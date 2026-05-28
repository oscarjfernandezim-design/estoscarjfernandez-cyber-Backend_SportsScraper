import sys
sys.path.insert(0, '.')
from dotenv import load_dotenv; load_dotenv()
from scrapling.fetchers import StealthyFetcher
 
page = StealthyFetcher.fetch('https://us.puma.com/us/en/search?q=running', headless=True, network_idle=True)
 
links = page.css('a[href*="/pd/"]')
print(f'Links /pd/: {len(links)}')
 
for i, link in enumerate(links[:3]):
    print(f'\n--- Link {i+1} ---')
    print('href:', link.css('::attr(href)').get())
    print('textos:', link.css('::text').getall())
    print('img src:', link.css('img::attr(src)').get())
    print('img alt:', link.css('img::attr(alt)').get())
    # Ver atributos del link mismo
    print('aria-label:', link.css('::attr(aria-label)').get())
    print('title:', link.css('::attr(title)').get())
 