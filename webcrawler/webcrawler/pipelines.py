from itemadapter import ItemAdapter

    
# Global variable to store scraped items
global_items = []

class CollectItemsPipeline:
    def process_item(self, item, spider):
        global global_items
        global_items.append(item)
        return item

    def close_spider(self, spider):
        # You can add any final processing here if needed
        pass

# Explicitly export global_items
__all__ = ['global_items', 'CollectItemsPipeline']