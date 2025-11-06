"""
数据补充模块 - 安全版
只使用低风险数据源，加强保护措施
"""

import requests
from bs4 import BeautifulSoup
import json
import time
from datetime import datetime, timedelta
import re
import random
import urllib.robotparser
from urllib.parse import quote, urlparse
from config import get_config

class SafeDataEnrichment:
    """安全的数据补充爬取器"""
    
    def __init__(self, safe_mode=None, config=None, date_str=None):
        """初始化
        
        参数：
            date_str: 日期字符串（用于日志路径）
            safe_mode: 是否启用安全模式（默认从配置读取）
            config: 配置对象（可选，默认使用全局配置）
        """
        # 获取配置
        self.config = config or get_config()
        self.date_str = date_str
        
        # 从配置读取参数
        self.safe_mode = safe_mode if safe_mode is not None else self.config.get("enrichment.safe_mode", True)
        
        # User-Agent列表
        self.user_agents = self.config.get("scraper.user_agents", [])
        
        self.session = requests.Session()
        self._update_headers()
        
        # 白名单：从配置读取
        self.safe_sources = self.config.get("enrichment.safe_sources", {})
        
        # 请求限制：从配置读取
        rate_limit = self.config.get("enrichment.rate_limit", {})
        self.request_count = {}  # 记录每个域名的请求次数
        self.max_requests_per_domain = rate_limit.get("max_requests_per_domain", 10)
        self.min_delay = rate_limit.get("min_delay", 5)
        self.max_delay = rate_limit.get("max_delay", 8)
        
        # 结果数量限制
        self.max_results = self.config.get("enrichment.max_results", {})
        
        # 日志路径（如果有date_str则使用日期分组路径）
        import os
        if self.date_str:
            from utils.path_helper import get_output_paths
            paths = get_output_paths(self.config, self.date_str)
            self.log_file = os.path.join(paths['logs_dir'], "enrichment.log")
        else:
            log_dir = self.config.get("paths.log_dir", "logs")
            os.makedirs(log_dir, exist_ok=True)
            self.log_file = os.path.join(log_dir, "enrichment.log")
        self._init_log()
    
    def _init_log(self):
        """初始化日志文件"""
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(f"<br />{'='*60}<br />")
            f.write(f"新会话开始 - {datetime.now()}<br />")
            f.write(f"安全模式: {'开启' if self.safe_mode else '关闭'}<br />")
            f.write(f"{'='*60}<br />")
    
    def _update_headers(self):
        """更新请求头"""
        self.session.headers.update({
            'User-Agent': random.choice(self.user_agents),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        })
    
    def _log(self, message, level='INFO'):
        """写入日志"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_message = f"[{timestamp}] [{level}] {message}<br />"
        
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(log_message)
        
        # 同时打印到控制台
        if level == 'WARNING':
            print(f"⚠️  {message}")
        elif level == 'ERROR':
            print(f"❌ {message}")
    
    def _is_safe_domain(self, url):
        """检查域名是否在白名单"""
        if not self.safe_mode:
            return True
        
        parsed = urlparse(url)
        domain = parsed.netloc
        
        # 检查是否在白名单
        for safe_domain in self.safe_sources.keys():
            if safe_domain in domain:
                return True
        
        return False
    
    def _check_request_limit(self, domain):
        """检查是否超过请求限制"""
        count = self.request_count.get(domain, 0)
        
        if count >= self.max_requests_per_domain:
            self._log(f"域名 {domain} 已达请求上限 ({self.max_requests_per_domain})", 'WARNING')
            return False
        
        return True
    
    def _increment_request_count(self, domain):
        """增加请求计数"""
        self.request_count[domain] = self.request_count.get(domain, 0) + 1
    
    def safe_request(self, url, method='GET', **kwargs):
        """
        安全的HTTP请求包装
        """
        # 检查域名安全性
        if not self._is_safe_domain(url):
            self._log(f"跳过非白名单域名: {url}", 'WARNING')
            print(f"     ⚠️  [安全模式] 跳过非白名单: {urlparse(url).netloc}")
            return None
        
        # 检查请求限制
        domain = urlparse(url).netloc
        if not self._check_request_limit(domain):
            print(f"     ⚠️  已达请求上限，跳过: {domain}")
            return None
        
        # 随机延迟（反爬保护）
        delay = random.uniform(self.min_delay, self.max_delay)
        print(f"     💤 等待 {delay:.1f} 秒...")
        time.sleep(delay)
        
        # 更新UA（每次请求随机换）
        self._update_headers()
        
        # 发送请求
        try:
            self._log(f"请求: {url}")
            
            if method.upper() == 'GET':
                response = self.session.get(url, timeout=15, **kwargs)
            else:
                response = self.session.post(url, timeout=15, **kwargs)
            
            # 增加计数
            self._increment_request_count(domain)
            
            # 检查状态码
            if response.status_code == 200:
                self._log(f"成功: {url} (状态码: {response.status_code})")
                return response
            else:
                self._log(f"失败: {url} (状态码: {response.status_code})", 'WARNING')
                return None
            
        except requests.exceptions.Timeout:
            self._log(f"超时: {url}", 'ERROR')
            print(f"     ❌ 请求超时")
            return None
        except Exception as e:
            self._log(f"异常: {url} - {str(e)}", 'ERROR')
            print(f"     ❌ 请求失败: {e}")
            return None
    
    # ========== 主流程 ==========
    
    def enrich_all_directions(self, analysis_data):
        """
        为所有投资方向补充数据
        """
        print("<br />" + "="*60)
        print("🔍 开始数据补充（安全模式）...")
        print("="*60)
        
        if self.safe_mode:
            print("<br />🛡️  安全模式已启用")
            print("   允许的数据源:")
            for domain, name in self.safe_sources.items():
                print(f"   ✓ {name} ({domain})")
            print()
        
        directions = analysis_data.get('directions', [])
        
        if not directions:
            print("⚠️  没有投资方向需要补充数据")
            return analysis_data
        
        enriched_directions = []
        
        for i, direction in enumerate(directions, 1):
            print(f"<br />--- 方向 {i}/{len(directions)}: {direction['name']} ---")
            
            enriched = self.enrich_single_direction(direction)
            enriched_directions.append(enriched)
        
        # 更新结果
        result = analysis_data.copy()
        result['directions'] = enriched_directions
        result['_enrichment_metadata'] = {
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'total_directions': len(enriched_directions),
            'safe_mode': self.safe_mode,
            'sources_used': list(self.safe_sources.values()),
            'total_requests': sum(self.request_count.values())
        }
        
        print("<br />✅ 数据补充完成！")
        self._print_request_stats()
        
        return result
    
    def enrich_single_direction(self, direction):
        """
        为单个投资方向补充数据
        """
        enriched = direction.copy()
        
        keywords = direction.get('keywords', [direction['name']])
        main_keyword = keywords[0] if keywords else direction['name']
        
        # 1. 爬取权威资讯
        print("  📰 爬取权威资讯...")
        news = self.scrape_authoritative_news(main_keyword)
        enriched['recent_news'] = news
        print(f"     ✓ 获取到 {len(news)} 条资讯")
        
        # 2. 搜索政策文件
        print("  📋 搜索相关政策...")
        policies = self.scrape_policy_documents(main_keyword)
        enriched['related_policies'] = policies
        print(f"     ✓ 找到 {len(policies)} 条政策")
        
        # 3. 简单热度分析（不需要额外请求）
        print("  📊 分析关键词...")
        stats = self.analyze_keyword_basic(main_keyword, keywords)
        enriched['keyword_analysis'] = stats
        print(f"     ✓ 分析完成")
        
        return enriched
    
    # ========== 具体爬取方法 ==========
    
    def scrape_authoritative_news(self, keyword, max_results=None):
        """
        爬取权威资讯
        只从新华社和人民网获取
        """
        max_results = max_results or self.max_results.get("total_news", 8)
        news_per_source = self.max_results.get("news_per_source", 4)
        
        all_news = []
        
        # 1. 新华社
        try:
            print(f"     • 搜索新华社...")
            xinhua_news = self._scrape_xinhua(keyword, max_results=news_per_source)
            all_news.extend(xinhua_news)
            print(f"       获取: {len(xinhua_news)} 条")
        except Exception as e:
            self._log(f"新华社爬取失败: {e}", 'ERROR')
            print(f"       失败")
        
        # 2. 人民网
        try:
            print(f"     • 搜索人民网...")
            people_news = self._scrape_people(keyword, max_results=news_per_source)
            all_news.extend(people_news)
            print(f"       获取: {len(people_news)} 条")
        except Exception as e:
            self._log(f"人民网爬取失败: {e}", 'ERROR')
            print(f"       失败")
        
        # 去重
        unique_news = self._deduplicate_by_title(all_news)
        
        return unique_news[:max_results]
    
    def _scrape_xinhua(self, keyword, max_results=4):
        """爬取新华社"""
        results = []
        
        # 新华社搜索
        search_url = "https://so.news.cn/"
        params = {
            'keyword': keyword,
            'sortfield': '0'  # 按时间排序
        }
        
        response = self.safe_request(search_url, params=params)
        
        if not response:
            return results
        
        try:
            response.encoding = 'utf-8'
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 查找结果列表
            items = soup.find_all('div', class_='tList')
            
            if not items:
                # 尝试其他可能的结构
                items = soup.find_all('li', class_='clearfix')
            
            for item in items[:max_results]:
                try:
                    # 提取标题和链接
                    link_tag = item.find('a')
                    if not link_tag:
                        continue
                    
                    title = link_tag.get_text(strip=True)
                    link = link_tag.get('href', '')
                    
                    # 确保完整URL
                    if link and not link.startswith('http'):
                        link = 'https://www.news.cn' + link
                    
                    # 提取摘要
                    snippet_tag = item.find('p')
                    snippet = snippet_tag.get_text(strip=True) if snippet_tag else ''
                    
                    # 提取时间
                    time_tag = item.find('span', class_='time')
                    pub_time = time_tag.get_text(strip=True) if time_tag else ''
                    
                    if title and link:
                        results.append({
                            'title': title,
                            'link': link,
                            'snippet': snippet[:200] if snippet else '',
                            'source': '新华社',
                            'pub_time': pub_time,
                            'fetch_time': datetime.now().strftime("%Y-%m-%d %H:%M")
                        })
                
                except Exception as e:
                    continue
        
        except Exception as e:
            self._log(f"解析新华社结果失败: {e}", 'ERROR')
        
        return results
    
    def _scrape_people(self, keyword, max_results=4):
        """爬取人民网"""
        results = []
        
        # 人民网搜索
        search_url = "http://search.people.com.cn/cnpeople/news/getNewsResult.jsp"
        params = {
            'keyword': keyword,
            'pageNum': '1',
            'type': '0'
        }
        
        response = self.safe_request(search_url, params=params)
        
        if not response:
            return results
        
        try:
            response.encoding = 'gbk'  # 人民网使用GBK编码
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 查找结果
            items = soup.find_all('div', class_='item')
            
            for item in items[:max_results]:
                try:
                    # 提取标题
                    title_tag = item.find('h5')
                    if not title_tag:
                        continue
                    
                    link_tag = title_tag.find('a')
                    if not link_tag:
                        continue
                    
                    title = link_tag.get_text(strip=True)
                    link = link_tag.get('href', '')
                    
                    # 提取摘要
                    snippet_tag = item.find('p', class_='text')
                    snippet = snippet_tag.get_text(strip=True) if snippet_tag else ''
                    
                    # 提取时间
                    time_tag = item.find('span', class_='time')
                    pub_time = time_tag.get_text(strip=True) if time_tag else ''
                    
                    if title and link:
                        results.append({
                            'title': title,
                            'link': link,
                            'snippet': snippet[:200] if snippet else '',
                            'source': '人民网',
                            'pub_time': pub_time,
                            'fetch_time': datetime.now().strftime("%Y-%m-%d %H:%M")
                        })
                
                except Exception as e:
                    continue
        
        except Exception as e:
            self._log(f"解析人民网结果失败: {e}", 'ERROR')
        
        return results
    
    def scrape_policy_documents(self, keyword, max_results=None):
        """
        爬取政策文件（中国政府网）
        """
        max_results = max_results or self.max_results.get("policies", 5)
        results = []
        
        # 政府网搜索
        search_url = "http://sousuo.gov.cn/search.htm"
        params = {
            'q': keyword,
            't': 'zhengce',  # 政策类型
            'timetype': 'timeqb',
            'mintime': '2024-01-01',
            'maxtime': datetime.now().strftime("%Y-%m-%d"),
            'sort': 'pubtime'  # 按发布时间排序
        }
        
        print(f"     • 搜索政府网...")
        response = self.safe_request(search_url, params=params)
        
        if not response:
            return results
        
        try:
            response.encoding = 'utf-8'
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 查找结果
            items = soup.find_all('div', class_='res-list')
            
            if not items:
                items = soup.find_all('li', class_='res-list')
            
            for item in items[:max_results]:
                try:
                    # 提取标题
                    title_tag = item.find('h3')
                    if not title_tag:
                        continue
                    
                    link_tag = title_tag.find('a')
                    if not link_tag:
                        continue
                    
                    title = link_tag.get_text(strip=True)
                    link = link_tag.get('href', '')
                    
                    # 提取发文单位
                    dept_tag = item.find('span', class_='from')
                    department = dept_tag.get_text(strip=True).replace('来源：', '') if dept_tag else ''
                    
                    # 提取时间
                    time_tag = item.find('span', class_='time')
                    pub_time = time_tag.get_text(strip=True) if time_tag else ''
                    
                    if title and link:
                        results.append({
                            'title': title,
                            'link': link,
                            'department': department,
                            'pub_time': pub_time,
                            'source': '中国政府网',
                            'fetch_time': datetime.now().strftime("%Y-%m-%d %H:%M")
                        })
                
                except Exception as e:
                    continue
            
            print(f"       获取: {len(results)} 条")
        
        except Exception as e:
            self._log(f"解析政府网结果失败: {e}", 'ERROR')
        
        return results
    
    def analyze_keyword_basic(self, main_keyword, all_keywords):
        """
        关键词基础分析（不需要额外请求）
        """
        return {
            'main_keyword': main_keyword,
            'related_keywords': all_keywords,
            'keyword_count': len(all_keywords),
            'analysis_time': datetime.now().strftime("%Y-%m-%d %H:%M"),
            'note': '基于已有关键词的基础分析'
        }
    
    # ========== 辅助方法 ==========
    
    def _deduplicate_by_title(self, items):
        """根据标题去重"""
        seen = set()
        unique = []
        
        for item in items:
            title = item.get('title', '')
            if title and title not in seen:
                seen.add(title)
                unique.append(item)
        
        return unique
    
    def _print_request_stats(self):
        """打印请求统计"""
        print("<br />📊 请求统计:")
        total = sum(self.request_count.values())
        print(f"   总请求数: {total}")
        
        for domain, count in sorted(self.request_count.items()):
            source_name = self.safe_sources.get(domain, domain)
            print(f"   • {source_name}: {count} 次")
    
    def save_enriched_data(self, enriched_data, date_str):
        """保存补充后的数据"""
        import os
        from utils.path_helper import get_output_paths
        paths = get_output_paths(self.config, date_str)
        
        filename = os.path.join(paths['data_dir'], f"enriched_{date_str}.json")
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(enriched_data, f, ensure_ascii=False, indent=2)
        
        print(f"<br />✅ 补充数据已保存到: {filename}")
        
        # 打印统计
        self._print_enrichment_stats(enriched_data)
        
        # 保存日志摘要
        self._log(f"数据已保存: {filename}")
    
    def _print_enrichment_stats(self, data):
        """打印补充数据统计"""
        print("<br />" + "="*60)
        print("📊 数据补充统计（安全模式）")
        print("="*60)
        
        directions = data.get('directions', [])
        
        total_news = sum(len(d.get('recent_news', [])) for d in directions)
        total_policies = sum(len(d.get('related_policies', [])) for d in directions)
        
        print(f"投资方向数: {len(directions)}")
        print(f"权威资讯: {total_news} 条 （新华社、人民网）")
        print(f"相关政策: {total_policies} 条 （中国政府网）")
        print(f"数据源: {', '.join(data.get('_enrichment_metadata', {}).get('sources_used', []))}")
        print()
        
        for i, direction in enumerate(directions, 1):
            print(f"{i}. {direction['name']}")
            print(f"   ├─ 资讯: {len(direction.get('recent_news', []))} 条")
            print(f"   └─ 政策: {len(direction.get('related_policies', []))} 条")

# ========== 加载函数 ==========

def load_analysis_result(date_str):
    """加载AI分析结果"""
    from config import get_config
    from utils.path_helper import get_output_paths
    import os
    
    config = get_config()
    paths = get_output_paths(config, date_str)
    filename = os.path.join(paths['data_dir'], f"analysis_{date_str}.json")
    
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data
    except FileNotFoundError:
        print(f"❌ 未找到文件: {filename}")
        print("   请先运行 main.py 生成分析结果")
        return None
    except Exception as e:
        print(f"❌ 读取文件失败: {e}")
        return None

# ========== 测试函数 ==========

def test_enrichment(date_str):
    """测试数据补充模块"""
    print("="*60)
    print(f"🧪 测试数据补充模块（安全版）- {date_str}")
    print("="*60)
    
    # 加载分析结果
    analysis_data = load_analysis_result(date_str)
    
    if not analysis_data:
        return
    
    # 初始化补充器（安全模式）
    enricher = SafeDataEnrichment(safe_mode=True)
    
    # 补充数据
    enriched_data = enricher.enrich_all_directions(analysis_data)
    
    # 保存结果
    enricher.save_enriched_data(enriched_data, date_str)
    
    print("<br />✅ 测试完成！")
    print(f"<br />📋 日志已保存到: {enricher.log_file}")

if __name__ == "__main__":
    # 测试时使用今天的日期
    from datetime import date
    today = date.today().strftime("%Y%m%d")
    test_enrichment(today)