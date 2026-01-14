"""
Google Trends ATH Detector - Core Analysis Script

Fetches Google Trends data using Selenium with human-like behavior to avoid detection.
Detects ATH (All-Time High) and anomalies, classifies signal types.

Based on: design-human-like-crawler.md
"""

import json
import time
import random
import argparse
import asyncio
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
from loguru import logger

# ========== Configuration ==========

USER_AGENTS = [
    # Windows Chrome
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    # macOS Chrome
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    # Windows Firefox
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
    # macOS Safari
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15',
    # Linux Chrome
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
]

GOOGLE_TRENDS_BASE = "https://trends.google.com/trends/explore"


@dataclass
class AnalysisParams:
    """Analysis parameters with defaults"""
    topic: str
    geo: str
    timeframe: str
    granularity: str = "weekly"
    smoothing_window: int = 4
    anomaly_method: str = "zscore"
    anomaly_threshold: float = 2.5
    compare_terms: Optional[List[str]] = None
    related_queries: bool = True


class GoogleTrendsCrawler:
    """Human-like Google Trends crawler using Selenium"""

    def __init__(self, headless: bool = True, debug: bool = False):
        self.headless = headless
        self.debug = debug
        self.driver = None

    def _create_driver(self) -> webdriver.Chrome:
        """Create Chrome driver with anti-detection options"""
        chrome_options = Options()

        # Basic settings
        if self.headless:
            chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')

        # Anti-detection settings
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_experimental_option('excludeSwitches', ['enable-automation'])
        chrome_options.add_experimental_option('useAutomationExtension', False)

        # Random User-Agent
        user_agent = random.choice(USER_AGENTS)
        chrome_options.add_argument(f'user-agent={user_agent}')
        logger.debug(f"Using User-Agent: {user_agent[:50]}...")

        # Create driver
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        driver.set_page_load_timeout(60)

        # Remove webdriver flag
        driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
            'source': '''
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                })
            '''
        })

        return driver

    def _human_delay(self, min_sec: float = 0.5, max_sec: float = 2.0):
        """Add human-like random delay"""
        delay = random.uniform(min_sec, max_sec)
        logger.debug(f"Waiting {delay:.2f}s...")
        time.sleep(delay)

    def _build_trends_url(
        self,
        topic: str,
        geo: str = "US",
        timeframe: str = "today 5-y"
    ) -> str:
        """Build Google Trends explore URL"""
        # Convert timeframe to Google Trends format
        # "2004-01-01 2025-12-31" -> "2004-01-01 2025-12-31"
        # "today 5-y" stays as is

        import urllib.parse
        params = {
            "q": topic,
            "geo": geo,
            "date": timeframe.replace(" ", " ")  # Keep as-is for now
        }
        query_string = urllib.parse.urlencode(params)
        return f"{GOOGLE_TRENDS_BASE}?{query_string}"

    def _wait_for_chart(self, driver: webdriver.Chrome, timeout: int = 20):
        """Wait for Google Trends chart to load"""
        wait = WebDriverWait(driver, timeout)

        # Multiple selector strategies
        selectors = [
            (By.CSS_SELECTOR, "div[class*='line-chart']"),
            (By.CSS_SELECTOR, "svg"),
            (By.CSS_SELECTOR, "div.trends-chart"),
            (By.CSS_SELECTOR, "div[data-ng-if*='chart']"),
        ]

        for by, value in selectors:
            try:
                wait.until(EC.presence_of_element_located((by, value)))
                logger.info(f"Chart loaded (found: {value})")
                return True
            except:
                continue

        logger.warning("Chart element not found, continuing anyway...")
        return False

    def _extract_timeseries_data(self, html: str) -> Dict[str, Any]:
        """Extract time series data from page"""
        soup = BeautifulSoup(html, 'lxml')

        # Look for data in various formats
        result = {
            "dates": [],
            "values": [],
            "raw_html_length": len(html)
        }

        # Method 1: Look for script tags with data
        scripts = soup.find_all('script')
        for script in scripts:
            if script.string and 'timelineData' in script.string:
                try:
                    # Extract JSON-like data
                    text = script.string
                    start = text.find('[')
                    end = text.rfind(']') + 1
                    if start != -1 and end > start:
                        data_str = text[start:end]
                        # This is a simplified extraction - actual implementation
                        # may need more sophisticated parsing
                        logger.debug("Found timelineData in script")
                except:
                    pass

        # Method 2: Look for CSV download link and use that
        csv_links = soup.select('a[href*="csv"]')
        if csv_links:
            logger.debug(f"Found {len(csv_links)} CSV download links")

        return result

    def _save_debug_html(self, html: str, filename: str = "debug_page.html"):
        """Save HTML for debugging"""
        try:
            debug_path = Path(filename)
            debug_path.write_text(html, encoding='utf-8')
            logger.warning(f"Saved debug HTML to: {debug_path.absolute()}")
        except Exception as e:
            logger.error(f"Failed to save debug HTML: {e}")

    def fetch_trends_via_api(
        self,
        topic: str,
        geo: str = "US",
        timeframe: str = "2004-01-01 2025-12-31"
    ) -> Dict[str, Any]:
        """
        Fetch Google Trends data using internal API with Selenium session.

        This method:
        1. Opens Google Trends page to establish cookies
        2. Extracts API tokens from page
        3. Makes API requests with proper headers
        """
        driver = None
        try:
            driver = self._create_driver()

            # Step 1: Visit homepage first (establish session)
            logger.info("Initializing session...")
            self._human_delay(1, 2)
            driver.get("https://trends.google.com/trends/")
            self._human_delay(2, 3)

            # Step 2: Visit explore page
            logger.info(f"Fetching trends for '{topic}' in {geo}...")

            # Parse timeframe
            try:
                start_date, end_date = timeframe.split(" ")
                date_param = f"{start_date} {end_date}"
            except ValueError:
                date_param = "today 5-y"

            # Build explore URL
            import urllib.parse
            explore_url = f"https://trends.google.com/trends/explore?q={urllib.parse.quote(topic)}&geo={geo}&date={urllib.parse.quote(date_param)}"

            self._human_delay(1, 2)
            driver.get(explore_url)

            # Wait for page to load
            self._wait_for_chart(driver)
            self._human_delay(3, 5)  # Extra wait for JS execution

            # Step 3: Extract data from page
            page_source = driver.page_source

            if self.debug:
                self._save_debug_html(page_source)

            # Try to extract timeline data from the page
            # Google Trends embeds data in window.__DATA__ or similar
            try:
                # Execute JavaScript to get data
                data_script = """
                    // Try to find timeline data
                    if (typeof window.__INIT_WIDGET_DATA__ !== 'undefined') {
                        return JSON.stringify(window.__INIT_WIDGET_DATA__);
                    }
                    // Alternative: look for data in page
                    var scripts = document.querySelectorAll('script');
                    for (var i = 0; i < scripts.length; i++) {
                        var text = scripts[i].textContent;
                        if (text && text.indexOf('timelineData') !== -1) {
                            return text;
                        }
                    }
                    return null;
                """
                js_data = driver.execute_script(data_script)

                if js_data:
                    logger.debug("Found embedded data via JavaScript")
                    # Parse the data - this will be page-specific
                    return self._parse_embedded_data(js_data, topic, geo, timeframe)

            except Exception as e:
                logger.debug(f"JS data extraction failed: {e}")

            # Step 4: Fallback - extract from internal API
            return self._fetch_via_internal_api(driver, topic, geo, timeframe)

        except Exception as e:
            logger.error(f"Fetch failed: {e}")
            return {"error": str(e)}

        finally:
            if driver:
                driver.quit()

    def _fetch_via_internal_api(
        self,
        driver: webdriver.Chrome,
        topic: str,
        geo: str,
        timeframe: str
    ) -> Dict[str, Any]:
        """Fetch data via Google Trends internal API"""
        try:
            start_date, end_date = timeframe.split(" ")
        except ValueError:
            start_date = "2004-01-01"
            end_date = datetime.now().strftime("%Y-%m-%d")

        # Build API request payload
        req_payload = json.dumps({
            "comparisonItem": [{
                "keyword": topic,
                "geo": geo,
                "time": f"{start_date} {end_date}"
            }],
            "category": 0,
            "property": ""
        })

        # Use Selenium to make the API request
        import urllib.parse
        api_url = f"https://trends.google.com/trends/api/explore?hl=en-US&tz=360&req={urllib.parse.quote(req_payload)}"

        self._human_delay(1, 2)
        driver.get(api_url)
        self._human_delay(1, 2)

        # Get the raw response
        body = driver.find_element(By.TAG_NAME, "body").text

        # Parse Google's response (remove XSS protection prefix)
        if body.startswith(")]}'"):
            body = body[5:]

        try:
            explore_data = json.loads(body)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse explore API response: {e}")
            return {"error": "Failed to parse explore response"}

        # Find TIMESERIES widget token
        widgets = explore_data.get("widgets", [])
        timeseries_token = None
        timeseries_req = None

        for widget in widgets:
            if widget.get("id") == "TIMESERIES":
                timeseries_token = widget.get("token")
                timeseries_req = widget.get("request")
                break

        if not timeseries_token:
            logger.error("Could not find TIMESERIES widget")
            return {"error": "Could not find TIMESERIES widget token"}

        # Fetch actual timeseries data
        multiline_url = f"https://trends.google.com/trends/api/widgetdata/multiline?hl=en-US&tz=360&req={urllib.parse.quote(json.dumps(timeseries_req))}&token={timeseries_token}"

        self._human_delay(1, 3)
        driver.get(multiline_url)
        self._human_delay(1, 2)

        body = driver.find_element(By.TAG_NAME, "body").text
        if body.startswith(")]}'"):
            body = body[5:]

        try:
            multiline_data = json.loads(body)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse multiline response: {e}")
            return {"error": "Failed to parse timeline data"}

        # Extract timeline data
        timeline_data = multiline_data.get("default", {}).get("timelineData", [])
        if not timeline_data:
            return {"error": "No timeline data returned"}

        dates = []
        values = []
        for point in timeline_data:
            time_str = point.get("formattedTime", "") or point.get("time", "")
            val = point.get("value", [0])[0]
            dates.append(time_str)
            values.append(val)

        logger.info(f"Successfully fetched {len(values)} data points")

        return {
            "topic": topic,
            "geo": geo,
            "timeframe": timeframe,
            "dates": dates,
            "values": values,
            "data_points": len(values),
            "fetched_at": datetime.now().isoformat()
        }

    def _parse_embedded_data(
        self,
        js_data: str,
        topic: str,
        geo: str,
        timeframe: str
    ) -> Dict[str, Any]:
        """Parse embedded data from page JavaScript"""
        # This is a simplified parser - actual implementation
        # depends on the exact format Google uses
        try:
            if isinstance(js_data, str):
                data = json.loads(js_data)
            else:
                data = js_data

            # Navigate to timeline data
            # Structure varies, this is a common path
            timeline_data = []
            if isinstance(data, dict):
                # Try common paths
                for path in [
                    ["default", "timelineData"],
                    ["widgets", 0, "request", "timelineData"],
                ]:
                    current = data
                    for key in path:
                        if isinstance(current, dict) and key in current:
                            current = current[key]
                        elif isinstance(current, list) and isinstance(key, int) and len(current) > key:
                            current = current[key]
                        else:
                            break
                    if isinstance(current, list) and current:
                        timeline_data = current
                        break

            if timeline_data:
                dates = [p.get("formattedTime", "") for p in timeline_data]
                values = [p.get("value", [0])[0] for p in timeline_data]

                return {
                    "topic": topic,
                    "geo": geo,
                    "timeframe": timeframe,
                    "dates": dates,
                    "values": values,
                    "data_points": len(values),
                    "fetched_at": datetime.now().isoformat()
                }

        except Exception as e:
            logger.debug(f"Failed to parse embedded data: {e}")

        return {"error": "Could not parse embedded data"}

    def fetch_related_queries(
        self,
        topic: str,
        geo: str = "US",
        timeframe: str = "2004-01-01 2025-12-31"
    ) -> Dict[str, Any]:
        """
        Fetch related queries (top and rising) using Selenium.
        """
        driver = None
        try:
            driver = self._create_driver()

            # Visit homepage first
            logger.info("Fetching related queries...")
            self._human_delay(1, 2)
            driver.get("https://trends.google.com/trends/")
            self._human_delay(2, 3)

            try:
                start_date, end_date = timeframe.split(" ")
            except ValueError:
                start_date = "2004-01-01"
                end_date = datetime.now().strftime("%Y-%m-%d")

            # Build explore API request
            req_payload = json.dumps({
                "comparisonItem": [{
                    "keyword": topic,
                    "geo": geo,
                    "time": f"{start_date} {end_date}"
                }],
                "category": 0,
                "property": ""
            })

            import urllib.parse
            api_url = f"https://trends.google.com/trends/api/explore?hl=en-US&tz=360&req={urllib.parse.quote(req_payload)}"

            self._human_delay(1, 2)
            driver.get(api_url)
            self._human_delay(1, 2)

            body = driver.find_element(By.TAG_NAME, "body").text
            if body.startswith(")]}'"):
                body = body[5:]

            explore_data = json.loads(body)

            # Find RELATED_QUERIES widget
            widgets = explore_data.get("widgets", [])
            related_token = None
            related_req = None

            for widget in widgets:
                if widget.get("id") == "RELATED_QUERIES":
                    related_token = widget.get("token")
                    related_req = widget.get("request")
                    break

            if not related_token:
                return {"top": [], "rising": []}

            # Fetch related queries
            related_url = f"https://trends.google.com/trends/api/widgetdata/relatedsearches?hl=en-US&tz=360&req={urllib.parse.quote(json.dumps(related_req))}&token={related_token}"

            self._human_delay(1, 3)
            driver.get(related_url)
            self._human_delay(1, 2)

            body = driver.find_element(By.TAG_NAME, "body").text
            if body.startswith(")]}'"):
                body = body[5:]

            related_data = json.loads(body)

            result = {"top": [], "rising": []}

            # Parse queries
            top_list = related_data.get("default", {}).get("rankedList", [])
            for ranked in top_list:
                keyword_type = ranked.get("rankedKeyword", [])
                for item in keyword_type[:10]:
                    query_info = item.get("query", "")
                    value = item.get("value", 0)
                    formatted = item.get("formattedValue", str(value))

                    if "%" in formatted or formatted == "Breakout":
                        result["rising"].append({
                            "term": query_info,
                            "value": formatted,
                            "type": "rising"
                        })
                    else:
                        result["top"].append({
                            "term": query_info,
                            "value": value,
                            "type": "top"
                        })

            logger.info(f"Found {len(result['top'])} top queries, {len(result['rising'])} rising queries")
            return result

        except Exception as e:
            logger.error(f"Failed to fetch related queries: {e}")
            return {"top": [], "rising": [], "error": str(e)}

        finally:
            if driver:
                driver.quit()


# ========== Public API Functions ==========

def fetch_trends(
    topic: str,
    geo: str = "US",
    timeframe: str = "2004-01-01 2025-12-31",
    headless: bool = True,
    debug: bool = False
) -> Dict[str, Any]:
    """
    Fetch Google Trends interest over time using Selenium.

    Args:
        topic: Search topic or keyword
        geo: Geographic region code (e.g., 'US', 'TW', 'JP')
        timeframe: Time range (e.g., '2004-01-01 2025-12-31')
        headless: Run browser in headless mode
        debug: Save debug HTML on failure

    Returns:
        Dict with 'dates', 'values', and metadata
    """
    crawler = GoogleTrendsCrawler(headless=headless, debug=debug)
    return crawler.fetch_trends_via_api(topic, geo, timeframe)


def fetch_related_queries(
    topic: str,
    geo: str = "US",
    timeframe: str = "2004-01-01 2025-12-31",
    headless: bool = True
) -> Dict[str, Any]:
    """
    Fetch related queries (top and rising).

    Returns:
        Dict with 'top' and 'rising' lists
    """
    crawler = GoogleTrendsCrawler(headless=headless)
    return crawler.fetch_related_queries(topic, geo, timeframe)


def analyze_ath(
    data: Dict[str, Any],
    threshold: float = 2.5,
    include_related: bool = True
) -> Dict[str, Any]:
    """
    Analyze if the trend is at ATH and calculate anomaly score.

    Args:
        data: Data from fetch_trends()
        threshold: Z-score threshold for anomaly detection
        include_related: Whether to fetch and include related queries

    Returns:
        Complete analysis result
    """
    if "error" in data:
        return data

    values = data.get("values", [])
    dates = data.get("dates", [])

    if not values:
        return {"error": "No values to analyze"}

    # Basic statistics
    latest = values[-1]
    hist_max = max(values)
    hist_min = min(values)
    mean_val = sum(values) / len(values)

    # Standard deviation
    variance = sum((v - mean_val) ** 2 for v in values) / len(values)
    std_val = variance ** 0.5

    # Z-score
    zscore = (latest - mean_val) / std_val if std_val > 0 else 0

    # ATH detection (with 2% tolerance)
    is_ath = latest >= hist_max * 0.98

    # Anomaly detection
    is_anomaly = abs(zscore) >= threshold

    # Find max date
    max_idx = values.index(hist_max)
    max_date = dates[max_idx] if max_idx < len(dates) else "unknown"

    # Trend direction (last 12 vs previous 12 periods)
    if len(values) >= 24:
        recent_avg = sum(values[-12:]) / 12
        prev_avg = sum(values[-24:-12]) / 12
        if recent_avg > prev_avg * 1.1:
            trend_direction = "rising"
        elif recent_avg < prev_avg * 0.9:
            trend_direction = "falling"
        else:
            trend_direction = "stable"
    else:
        trend_direction = "insufficient_data"

    # Signal classification
    if is_ath and is_anomaly:
        signal_type = "regime_shift" if trend_direction == "rising" else "event_driven_shock"
    elif is_ath and not is_anomaly:
        signal_type = "seasonal_spike"
    elif is_anomaly:
        signal_type = "event_driven_shock"
    else:
        signal_type = "normal"

    result = {
        "topic": data.get("topic"),
        "geo": data.get("geo"),
        "timeframe": data.get("timeframe"),
        "analysis": {
            "latest_value": latest,
            "latest_date": dates[-1] if dates else "unknown",
            "historical_max": hist_max,
            "historical_max_date": max_date,
            "historical_min": hist_min,
            "mean": round(mean_val, 2),
            "std": round(std_val, 2),
            "zscore": round(zscore, 2),
            "is_all_time_high": is_ath,
            "is_anomaly": is_anomaly,
            "signal_type": signal_type,
            "trend_direction": trend_direction,
            "data_points": len(values)
        },
        "recommendation": _get_recommendation(is_ath, is_anomaly),
        "analyzed_at": datetime.now().isoformat()
    }

    # Fetch related queries if requested
    if include_related:
        related = fetch_related_queries(
            data.get("topic", ""),
            data.get("geo", "US"),
            data.get("timeframe", "")
        )
        drivers = []
        for item in related.get("rising", [])[:10]:
            drivers.append(item)
        for item in related.get("top", [])[:5]:
            drivers.append(item)
        result["drivers_from_related_queries"] = drivers

    return result


def compare_trends(
    topic: str,
    compare_terms: List[str],
    geo: str = "US",
    timeframe: str = "2004-01-01 2025-12-31"
) -> Dict[str, Any]:
    """
    Compare multiple topics and calculate correlations.

    Args:
        topic: Main topic to compare
        compare_terms: List of terms to compare with
        geo: Geographic region
        timeframe: Time range

    Returns:
        Correlation analysis results
    """
    crawler = GoogleTrendsCrawler(headless=True)

    # Fetch main topic
    main_data = crawler.fetch_trends_via_api(topic, geo, timeframe)
    if "error" in main_data:
        return main_data

    main_values = main_data.get("values", [])

    correlations = {}
    for term in compare_terms:
        logger.info(f"Fetching comparison term: {term}")
        # Add longer delay between requests to avoid rate limiting
        time.sleep(random.uniform(3, 6))

        compare_data = crawler.fetch_trends_via_api(term, geo, timeframe)

        if "error" not in compare_data:
            compare_values = compare_data.get("values", [])

            # Calculate correlation (simple Pearson)
            if len(main_values) == len(compare_values) and len(main_values) > 10:
                n = len(main_values)
                mean_x = sum(main_values) / n
                mean_y = sum(compare_values) / n

                cov = sum((main_values[i] - mean_x) * (compare_values[i] - mean_y) for i in range(n)) / n
                std_x = (sum((v - mean_x) ** 2 for v in main_values) / n) ** 0.5
                std_y = (sum((v - mean_y) ** 2 for v in compare_values) / n) ** 0.5

                if std_x > 0 and std_y > 0:
                    corr = cov / (std_x * std_y)
                    correlations[term] = round(corr, 3)
                else:
                    correlations[term] = 0.0
            else:
                correlations[term] = None

    return {
        "topic": topic,
        "geo": geo,
        "timeframe": timeframe,
        "compare_correlations": correlations,
        "interpretation": _interpret_correlations(correlations),
        "analyzed_at": datetime.now().isoformat()
    }


def _get_recommendation(is_ath: bool, is_anomaly: bool) -> str:
    """Generate recommendation based on analysis."""
    if is_ath and is_anomaly:
        return "搜尋趨勢創下歷史新高且異常飆升，建議進一步分析驅動因素（相關查詢、新聞事件等）"
    elif is_ath:
        return "搜尋趨勢接近歷史高點，可能為季節性因素，建議觀察後續走勢"
    elif is_anomaly:
        return "搜尋趨勢異常波動但非歷史新高，可能為局部事件影響"
    else:
        return "搜尋趨勢在正常範圍內波動"


def _interpret_correlations(correlations: Dict[str, float]) -> str:
    """Interpret correlation results."""
    high_corr = [k for k, v in correlations.items() if v and v > 0.7]
    if high_corr:
        return f"與 {', '.join(high_corr)} 高度相關（>0.7），可能為系統性焦慮而非單點焦慮"
    return "與其他主題相關性不高，可能為獨立的單點焦慮"


# ========== Async Wrapper ==========

async def fetch_trends_async(
    topic: str,
    geo: str = "US",
    timeframe: str = "2004-01-01 2025-12-31"
) -> Dict[str, Any]:
    """Async wrapper for fetch_trends"""
    # Add random pre-request delay
    delay = random.uniform(0.5, 2.0)
    await asyncio.sleep(delay)

    # Run in thread pool to avoid blocking
    return await asyncio.to_thread(fetch_trends, topic, geo, timeframe)


# ========== CLI Interface ==========

def main():
    """CLI interface"""
    parser = argparse.ArgumentParser(
        description="Google Trends ATH Detector (Selenium-based)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic analysis
  python trend_fetcher.py --topic "Health Insurance" --geo US

  # Compare multiple topics
  python trend_fetcher.py --topic "Health Insurance" --compare "Unemployment,Inflation" --geo US

  # Skip related queries (faster)
  python trend_fetcher.py --topic "Health Insurance" --no-related

  # Debug mode (saves HTML on failure)
  python trend_fetcher.py --topic "Health Insurance" --debug
        """
    )
    parser.add_argument("--topic", type=str, required=True, help="Search topic")
    parser.add_argument("--geo", type=str, default="US", help="Geographic region")
    parser.add_argument("--timeframe", type=str, default="2004-01-01 2025-12-31", help="Time range")
    parser.add_argument("--threshold", type=float, default=2.5, help="Anomaly z-score threshold")
    parser.add_argument("--compare", type=str, default="", help="Comma-separated compare terms")
    parser.add_argument("--no-related", action="store_true", help="Skip related queries")
    parser.add_argument("--no-headless", action="store_true", help="Show browser window")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    parser.add_argument("--output", type=str, help="Output JSON file")

    args = parser.parse_args()

    # Configure logger
    if args.debug:
        logger.add("trend_fetcher.log", rotation="10 MB")

    print(f"Fetching Google Trends data for '{args.topic}' in {args.geo}...")
    print("Using Selenium with anti-detection measures...")

    # Fetch data
    data = fetch_trends(
        args.topic,
        args.geo,
        args.timeframe,
        headless=not args.no_headless,
        debug=args.debug
    )

    if "error" in data:
        print(f"Error: {data['error']}")
        return

    print(f"Fetched {len(data.get('values', []))} data points")

    # Analyze
    result = analyze_ath(data, args.threshold, include_related=not args.no_related)

    # Compare if requested
    if args.compare:
        compare_terms = [t.strip() for t in args.compare.split(",") if t.strip()]
        if compare_terms:
            print(f"Comparing with: {', '.join(compare_terms)}")
            compare_result = compare_trends(args.topic, compare_terms, args.geo, args.timeframe)
            result["compare_correlations"] = compare_result.get("compare_correlations", {})
            result["compare_interpretation"] = compare_result.get("interpretation", "")

    output_json = json.dumps(result, indent=2, ensure_ascii=False)

    if args.output:
        Path(args.output).write_text(output_json, encoding='utf-8')
        print(f"Results written to: {args.output}")
    else:
        print(output_json)


if __name__ == "__main__":
    main()
