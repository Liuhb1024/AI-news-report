import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime
import time
import random
import os
from config import get_config

class XinwenliboScraper:
    def __init__(self, config=None):
        """
        初始化爬虫
        
        参数：
            config: 配置对象（可选，默认使用全局配置）
        """
        self.config = config or get_config()
        
        # 从配置读取参数
        self.base_url = self.config.get("scraper.base_url", "https://tv.cctv.com/lm/xwlb/")
        self.timeout = self.config.get("scraper.timeout", 15)
        self.max_retry = self.config.get("scraper.max_retry", 3)
        self.delay = self.config.get("scraper.delay_between_requests", 1.5)
        self.user_agents = self.config.get("scraper.user_agents", [])
        
        # 随机选择User-Agent
        user_agent = random.choice(self.user_agents) if self.user_agents else 'Mozilla/5.0'
        
        self.headers = {
            'User-Agent': user_agent,
            'Referer': 'https://tv.cctv.com/',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8'
        }
    
    def get_news_list(self, date_str):
        """
        获取指定日期的新闻列表
        date_str: 格式 YYYYMMDD，如 '20241104'
        """
        url = f"{self.base_url}day/{date_str}.shtml"
        print(f"正在访问: {url}")
        
        try:
            response = requests.get(url, headers=self.headers, timeout=self.timeout)
            response.encoding = 'utf-8'
            
            if response.status_code != 200:
                print(f"请求失败，状态码: {response.status_code}")
                return []
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 查找新闻列表（可能需要根据实际页面结构调整）
            news_items = []
            
            # 方法1：查找所有包含链接的新闻项
            links = soup.find_all('a', href=True)
            
            for link in links:
                href = link.get('href', '')
                title = link.get_text(strip=True)
                
                # 过滤出新闻详情页链接
                if 'tv.cctv.com' in href and len(title) > 5:
                    news_items.append({
                        'title': title,
                        'url': href if href.startswith('http') else f"https:{href}"
                    })
            
            print(f"找到 {len(news_items)} 条新闻链接")
            return news_items
            
        except Exception as e:
            print(f"获取新闻列表失败: {e}")
            return []
    
    def get_news_content(self, news_url):
        """
        获取单条新闻的详细内容
        """
        try:
            print(f"  正在获取: {news_url}")
            response = requests.get(news_url, headers=self.headers, timeout=self.timeout)
            response.encoding = 'utf-8'
            
            if response.status_code != 200:
                return None
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 尝试多种可能的内容容器
            content = None
            
            # 方法1：查找常见的内容区域
            content_areas = [
                soup.find('div', class_='content_area'),
                soup.find('div', class_='cnt_bd'),
                soup.find('div', id='content_area'),
                soup.find('div', class_='text'),
                soup.find('article')
            ]
            
            for area in content_areas:
                if area:
                    paragraphs = area.find_all('p')
                    if paragraphs:
                        content = '<br />'.join([p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True)])
                        break
            
            # 如果上面都没找到，尝试直接找所有p标签
            if not content:
                paragraphs = soup.find_all('p')
                content = '<br />'.join([p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True)])
            
            return content if content else "未能提取到内容"
            
        except Exception as e:
            print(f"  获取内容失败: {e}")
            return None
    
    def scrape_date(self, date_str, max_retry=None):
        """
        爬取指定日期的所有新闻
        max_retry: 失败重试次数（默认从配置读取）
        """
        max_retry = max_retry or self.max_retry
        print(f"<br />开始爬取 {date_str} 的新闻联播内容<br />" + "="*50)
        
        # 获取新闻列表
        news_list = self.get_news_list(date_str)
        
        if not news_list:
            print("未找到新闻列表，尝试备用方法...")
            return self.scrape_alternative(date_str)
        
        # 获取每条新闻的详细内容
        all_news = []
        total_count = len(news_list)
        failed_items = []
        
        print(f"<br />共找到 {total_count} 条新闻，开始逐条获取内容...<br />")
        
        for i, news in enumerate(news_list, 1):
            print(f"[{i}/{total_count}] {news['title']}")
            
            # 尝试获取内容，支持重试
            content = None
            for attempt in range(max_retry):
                content = self.get_news_content(news['url'])
                if content:
                    break
                if attempt < max_retry - 1:
                    print(f"  重试 {attempt + 1}/{max_retry}...")
                    time.sleep(2)
            
            if content:
                all_news.append({
                    'index': i,
                    'title': news['title'],
                    'url': news['url'],
                    'content': content
                })
                print(f"  ✓ 获取成功 (内容长度: {len(content)} 字符)")
            else:
                failed_items.append(news)
                print(f"  ✗ 获取失败")
            
            # 礼貌延迟，避免请求过快
            time.sleep(self.delay)
        
        # 显示统计信息
        print(f"<br />{'='*60}")
        print(f"爬取完成统计：")
        print(f"  总计: {total_count} 条")
        print(f"  成功: {len(all_news)} 条")
        print(f"  失败: {len(failed_items)} 条")
        print(f"{'='*60}<br />")
        
        if failed_items:
            print("失败的新闻：")
            for item in failed_items:
                print(f"  - {item['title']}")
            print()
        
        return all_news
    
    def scrape_alternative(self, date_str):
        """
        备用方案：直接从主页面提取内容
        """
        url = f"{self.base_url}day/{date_str}.shtml"
        
        try:
            response = requests.get(url, headers=self.headers, timeout=self.timeout)
            response.encoding = 'utf-8'
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 保存HTML用于调试
            import os
            from utils.path_helper import get_output_paths
            paths = get_output_paths(self.config, date_str)
            debug_file = os.path.join(paths['logs_dir'], f'xinwenlianbo_{date_str}_debug.html')
            with open(debug_file, 'w', encoding='utf-8') as f:
                f.write(response.text)
            print(f"已保存原始HTML到 {debug_file}，请手动检查页面结构")
            
            return []
        except Exception as e:
            print(f"备用方案也失败: {e}")
            return []
    
    def save_to_file(self, news_data, date_str):
        """保存到文件"""
        if not news_data:
            print("\n没有数据可保存")
            return
        
        from utils.path_helper import get_output_paths
        paths = get_output_paths(self.config, date_str)
        data_dir = paths['data_dir']
        
        # 保存为JSON
        json_filename = os.path.join(data_dir, f'xinwenlianbo_{date_str}.json')
        with open(json_filename, 'w', encoding='utf-8') as f:
            json.dump(news_data, f, ensure_ascii=False, indent=2)
        print(f"已保存JSON到: {json_filename}")
        
        # 保存为易读的文本
        txt_filename = os.path.join(data_dir, f'xinwenlianbo_{date_str}.txt')
        with open(txt_filename, 'w', encoding='utf-8') as f:
            f.write(f"新闻联播文字稿 - {date_str}\n")
            f.write("="*60 + "\n\n")
            
            for news in news_data:
                # 清理内容中的<br />标签，替换为换行符
                content = news['content'].replace('<br />', '\n')
                f.write(f"【新闻 {news['index']}】{news['title']}\n")
                f.write(f"链接: {news['url']}\n")
                f.write(f"\n{content}\n")
                f.write("\n" + "-"*60 + "\n\n")
        
        print(f"已保存文本到: {txt_filename}")
        
        # 保存为Markdown格式（更适合AI分析）
        md_filename = os.path.join(data_dir, f'xinwenlianbo_{date_str}.md')
        with open(md_filename, 'w', encoding='utf-8') as f:
            f.write(f"# 新闻联播文字稿 - {date_str}\n\n")
            f.write(f"**共 {len(news_data)} 条新闻**\n\n")
            f.write("---\n\n")
            
            for news in news_data:
                # 清理内容中的<br />标签，替换为换行符
                content = news['content'].replace('<br />', '\n')
                f.write(f"## {news['index']}. {news['title']}\n\n")
                f.write(f"🔗 [{news['url']}]({news['url']})\n\n")
                f.write(f"{content}\n\n")
                f.write("---\n\n")
        
        print(f"已保存Markdown到: {md_filename}")
        
        # 打印摘要
        print(f"\n{'='*60}")
        print(f"文件保存完成！共 {len(news_data)} 条新闻")
        print(f"{'='*60}\n")
        
        # 显示所有新闻标题
        print("所有新闻标题列表：")
        for news in news_data:
            print(f"{news['index']}. {news['title']}")
        
        # 统计总字数
        total_chars = sum(len(news['content']) for news in news_data)
        print(f"<br />总字数: {total_chars:,} 字符")

def main():
    scraper = XinwenliboScraper()
    
    # 可以设置日期
    date_str = "20251104"  # 格式：YYYYMMDD
    
    # 也可以自动获取今天的日期
    # from datetime import date
    # date_str = date.today().strftime("%Y%m%d")
    
    print(f"准备爬取日期: {date_str}")
    print("注意：完整爬取可能需要几分钟时间...<br />")
    
    # 开始爬取（爬取所有新闻）
    news_data = scraper.scrape_date(date_str)
    
    # 保存结果
    scraper.save_to_file(news_data, date_str)

if __name__ == "__main__":
    main()