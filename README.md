# Scrape_Produthunt_Selenium
A modular Selenium-based web scraper to extract product details across all categories from ProductHunt. Easily configurable and extensible for various scraping needs.

## Key Features ✨
- 🧩 Modular architecture for easy maintenance
- 🕶️ Headless browsing support
- ⏳ Smart waiting mechanisms for dynamic content
- 📂 Category-based data organization


## Setup 🛠️

### Prerequisites
- Python 3.11
- Chrome browser

### Installation
1. Clone repository:
```bash
git clone https://github.com/yourusername/Scrape_Produthunt_Selenium.git
cd Scrape_Produthunt_Selenium
```
2. Configure virtual environment (Recommended)
```bash
python -m venv venv
source venv/bin/activate  # Linux/MacOS
venv\Scripts\activate    # Windows
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

### Config Params
--CATE_URL:目标URL地址
--MAX_TRY:每个分类所获取的产品数量


## Usage 🚀
```bash
python ScrapePH.py --CATE_URL https://www.producthunt.com/categories --MAX_TRY 100
```

## ToDo
- Add Parallel scraping capability

