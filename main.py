import os
import time
import shutil
import tempfile
import logging
import threading
from urllib.parse import urlparse
from concurrent.futures import ThreadPoolExecutor
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException

try:
    from colorama import init, Fore, Back, Style
    init(autoreset=True)  # Initialize colorama
    COLORS_AVAILABLE = True
except ImportError:
    # Fallback if colorama is not installed
    class MockColor:
        def __getattr__(self, name):
            return ''
    Fore = Back = Style = MockColor()
    COLORS_AVAILABLE = False

# Custom formatter for beautiful console output
class BeautifulFormatter(logging.Formatter):
    def __init__(self):
        super().__init__()
        
    def format(self, record):
        # Color mapping for different log levels
        colors = {
            'DEBUG': Fore.CYAN,
            'INFO': Fore.GREEN,
            'WARNING': Fore.YELLOW,
            'ERROR': Fore.RED,
            'CRITICAL': Fore.MAGENTA
        }
        
        # Icons for different log levels
        icons = {
            'DEBUG': '🔍',
            'INFO': '✅',
            'WARNING': '⚠️',
            'ERROR': '❌',
            'CRITICAL': '💥'
        }
        
        color = colors.get(record.levelname, '')
        icon = icons.get(record.levelname, '•')
        
        # Format the message without timestamp for console
        if record.levelname == 'DEBUG':
            return f"{Fore.CYAN}   {icon} {record.getMessage()}{Style.RESET_ALL}"
        else:
            return f"{color}{icon} {record.getMessage()}{Style.RESET_ALL}"

# Setup logging with beautiful formatting
file_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
console_formatter = BeautifulFormatter()

# File handler (keeps detailed logs)
file_handler = logging.FileHandler('chrome_automation.log')
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(file_formatter)

# Console handler (beautiful output)
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)  # Only show INFO and above in console
console_handler.setFormatter(console_formatter)

# Configure logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logger.addHandler(file_handler)
logger.addHandler(console_handler)

# Enhanced utility functions for beautiful output
def print_header(title):
    """Print a beautiful section header"""
    width = max(60, len(title) + 8)
    border = "═" * width
    padding = (width - len(title) - 2) // 2
    print(f"\n{Fore.BLUE}{Style.BRIGHT}{border}")
    print(f"║{' ' * padding}{title}{' ' * (width - len(title) - padding - 2)}║")
    print(f"{border}{Style.RESET_ALL}\n")

def print_account_header(account_id, email):
    """Print account-specific header"""
    title = f"ACCOUNT {account_id}: {email}"
    width = max(50, len(title) + 4)
    border = "─" * width
    print(f"\n{Fore.MAGENTA}{Style.BRIGHT}┌{border}┐")
    print(f"│ {title:<{width-2}} │")
    print(f"└{border}┘{Style.RESET_ALL}")

def print_step(step_num, total_steps, description, account_id=None):
    """Print a step with enhanced progress indicator"""
    progress_bar = "█" * step_num + "░" * (total_steps - step_num)
    progress_percent = f"{(step_num/total_steps)*100:.0f}%"
    
    if account_id:
        account_prefix = f"{Fore.MAGENTA}[Account {account_id}]{Style.RESET_ALL} "
    else:
        account_prefix = ""
    
    print(f"{Fore.YELLOW}🚀 {account_prefix}Step {step_num}/{total_steps} ({progress_percent}) {Fore.CYAN}[{progress_bar}]{Style.RESET_ALL}")
    print(f"   {Fore.WHITE}{description}{Style.RESET_ALL}")

def print_success(message, account_id=None):
    """Print an enhanced success message"""
    if account_id:
        account_prefix = f"{Fore.MAGENTA}[Account {account_id}]{Style.RESET_ALL} "
    else:
        account_prefix = ""
    print(f"{Fore.GREEN}✅ {account_prefix}{Style.BRIGHT}{message}{Style.RESET_ALL}")

def print_error(message, account_id=None):
    """Print an enhanced error message"""
    if account_id:
        account_prefix = f"{Fore.MAGENTA}[Account {account_id}]{Style.RESET_ALL} "
    else:
        account_prefix = ""
    print(f"{Fore.RED}❌ {account_prefix}{Style.BRIGHT}{message}{Style.RESET_ALL}")

def print_warning(message, account_id=None):
    """Print a warning message"""
    if account_id:
        account_prefix = f"{Fore.MAGENTA}[Account {account_id}]{Style.RESET_ALL} "
    else:
        account_prefix = ""
    print(f"{Fore.YELLOW}⚠️  {account_prefix}{message}{Style.RESET_ALL}")

def print_info(message, account_id=None):
    """Print an enhanced info message"""
    if account_id:
        account_prefix = f"{Fore.MAGENTA}[Account {account_id}]{Style.RESET_ALL} "
    else:
        account_prefix = ""
    print(f"{Fore.CYAN}ℹ️  {account_prefix}{message}{Style.RESET_ALL}")

def print_health_status(account_id, health, uptime, is_good=True):
    """Print health status with enhanced formatting"""
    status_icon = "🟢" if is_good else "🔴"
    status_color = Fore.GREEN if is_good else Fore.RED
    
    print(f"{status_icon} {Fore.MAGENTA}[Account {account_id}]{Style.RESET_ALL} "
          f"{status_color}{Style.BRIGHT}Health: {health}{Style.RESET_ALL} │ "
          f"{Fore.BLUE}Uptime: {uptime}{Style.RESET_ALL}")

def print_proxy_info(account_id, host, port):
    """Print proxy information with enhanced formatting"""
    print(f"{Fore.CYAN}🌐 {Fore.MAGENTA}[Account {account_id}]{Style.RESET_ALL} "
          f"Proxy: {Fore.YELLOW}{Style.BRIGHT}{host}:{port}{Style.RESET_ALL}")

def print_separator():
    """Print a visual separator"""
    print(f"{Fore.BLUE}{'─' * 60}{Style.RESET_ALL}")

def print_retry_header(account_id, email, retry_count, max_retries):
    """Print retry-specific header"""
    title = f"RETRY {retry_count}/{max_retries} - ACCOUNT {account_id}: {email}"
    width = max(60, len(title) + 4)
    border = "═" * width
    print(f"\n{Fore.YELLOW}{Style.BRIGHT}┌{border}┐")
    print(f"│ 🔄 {title:<{width-5}} │")
    print(f"└{border}┘{Style.RESET_ALL}")

def print_summary_table(accounts_data, proxies_data):
    """Print a summary table of accounts and proxies"""
    print(f"\n{Fore.BLUE}{Style.BRIGHT}📊 SETUP SUMMARY{Style.RESET_ALL}")
    print(f"{Fore.BLUE}{'─' * 60}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{'Account':<10} {'Email':<25} {'Proxy':<20}{Style.RESET_ALL}")
    print(f"{Fore.BLUE}{'─' * 60}{Style.RESET_ALL}")
    
    for i, (account, proxy) in enumerate(zip(accounts_data, proxies_data), 1):
        proxy_parsed = urlparse(proxy)
        proxy_display = f"{proxy_parsed.hostname}:{proxy_parsed.port}"
        print(f"{Fore.MAGENTA}{i:<10}{Style.RESET_ALL} "
              f"{Fore.WHITE}{account['email']:<25}{Style.RESET_ALL} "
              f"{Fore.YELLOW}{proxy_display:<20}{Style.RESET_ALL}")
    
    print(f"{Fore.BLUE}{'─' * 60}{Style.RESET_ALL}\n")

class ChromeProxyAutomation:
    def __init__(self, account_id=1, account_data=None, proxy_line=None):
        self.account_id = account_id
        self.driver = None
        self.temp_profile_path = None
        self.proxy_data = None
        self.proxy_line = proxy_line
        self.gradient_data = account_data
        self.wait_timeout = 10
        self.health_monitoring_active = False
        self.setup_complete = False
        self.was_good_before = False
        self.retry_count = 0
        self.max_retries = 3
        self.consecutive_disconnects = 0
        self.max_consecutive_disconnects = 3
        
    def parse_proxy_data(self, proxy_line):
        """Parse proxy data from a single proxy line"""
        try:
            logger.debug(f"[Account {self.account_id}] Parsing proxy line: {proxy_line}")
            
            # Parse proxy URL: http://username:password@host:port
            parsed = urlparse(proxy_line)
            
            self.proxy_data = {
                'host': parsed.hostname,
                'port': str(parsed.port),
                'username': parsed.username,
                'password': parsed.password
            }
            
            logger.info(f"[Account {self.account_id}] Parsed proxy data: {self.proxy_data['host']}:{self.proxy_data['port']}")
            return True
            
        except Exception as e:
            logger.error(f"[Account {self.account_id}] Error parsing proxy data: {e}")
            return False
    
    @staticmethod
    def parse_all_proxies(proxy_file_path="proxy.txt"):
        """Parse all proxies from proxy.txt file"""
        proxies = []
        try:
            logger.debug(f"Reading proxy file: {proxy_file_path}")
            with open(proxy_file_path, 'r') as f:
                lines = f.readlines()
            
            for i, line in enumerate(lines, 1):
                line = line.strip()
                if line:
                    try:
                        # Validate proxy format
                        parsed = urlparse(line)
                        if parsed.hostname and parsed.port:
                            proxies.append(line)
                            logger.debug(f"Parsed proxy {i}: {parsed.hostname}:{parsed.port}")
                        else:
                            logger.warning(f"Invalid proxy format on line {i}: {line}")
                    except Exception as e:
                        logger.warning(f"Error parsing proxy on line {i}: {e}")
            
            logger.info(f"Parsed {len(proxies)} proxies from proxy file")
            return proxies
                
        except Exception as e:
            logger.error(f"Error parsing proxy file: {e}")
            return []
    
    @staticmethod
    def parse_all_accounts(data_file_path="data.txt"):
        """Parse all accounts from data.txt file"""
        accounts = []
        try:
            logger.debug(f"Reading data file: {data_file_path}")
            with open(data_file_path, 'r') as f:
                lines = f.readlines()
            
            for i, line in enumerate(lines, 1):
                line = line.strip()
                if line and ':' in line:
                    email, password = line.split(':', 1)
                    account_data = {
                        'email': email.strip(),
                        'password': password.strip()
                    }
                    accounts.append(account_data)
                    logger.debug(f"Parsed account {i}: {account_data['email']}")
                elif line:
                    logger.warning(f"Invalid data format on line {i}: {line}")
            
            logger.info(f"Parsed {len(accounts)} accounts from data file")
            return accounts
                
        except Exception as e:
            logger.error(f"Error parsing data file: {e}")
            return []
    
    def setup_gradient_extension(self):
        """Setup gradient extension by logging in through extension URL"""
        try:
            print_info("🔗 Opening Gradient extension", self.account_id)
            
            # Navigate directly to gradient extension in current tab
            self.driver.get("chrome-extension://caacbgbklghmpodbdafajbgdnegacfmo/popup.html")
            time.sleep(5)  # Increased wait time for page load
            
            print_info("🖱️  Clicking login button", self.account_id)
            
            # Click the specific login button on extension page with retry logic
            login_success = self.robust_click(
                By.XPATH, 
                '//div[@class="mt-[50px] h-[48px] w-full rounded-[125px] bg-[#FFFFFF] px-[32px] py-[7.5px] flex justify-center items-center select-none text-[16px] cursor-pointer"]//div[@class="Helveticae" and text()="Log in"]',
                "Extension login button",
                max_attempts=3,
                wait_time=3
            )
            
            if not login_success:
                print_error("Failed to click extension login button", self.account_id)
                return False
            
            print_info("⏳ Waiting for redirect to web app", self.account_id)
            
            # Wait for new tab to open and switch to it
            WebDriverWait(self.driver, self.wait_timeout).until(
                lambda driver: len(driver.window_handles) > 1
            )
            
            # Switch to the new tab (web app)
            self.driver.switch_to.window(self.driver.window_handles[-1])
            time.sleep(5)  # Increased wait time for web app load
            
            print_info("📝 Filling login credentials", self.account_id)
            
            # Find and fill email field with retry logic
            for attempt in range(3):
                try:
                    email_input = WebDriverWait(self.driver, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, 'input[placeholder="Enter Email"]'))
                    )
                    email_input.clear()
                    time.sleep(1)
                    email_input.send_keys(self.gradient_data['email'])
                    print_info("✅ Email entered successfully", self.account_id)
                    break
                except Exception as e:
                    if attempt < 2:
                        print_info(f"🔄 Retrying email input (attempt {attempt + 1})", self.account_id)
                        time.sleep(2)
                    else:
                        print_error("Failed to enter email", self.account_id)
                        return False
            
            # Find and fill password field with retry logic
            for attempt in range(3):
                try:
                    password_input = WebDriverWait(self.driver, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, 'input[placeholder="Enter Password"][type="password"]'))
                    )
                    password_input.clear()
                    time.sleep(1)
                    password_input.send_keys(self.gradient_data['password'])
                    print_info("✅ Password entered successfully", self.account_id)
                    break
                except Exception as e:
                    if attempt < 2:
                        print_info(f"🔄 Retrying password input (attempt {attempt + 1})", self.account_id)
                        time.sleep(2)
                    else:
                        print_error("Failed to enter password", self.account_id)
                        return False
            
            print_info("🔐 Submitting login form", self.account_id)
            
            # Click login button on web app with retry logic
            web_login_success = self.robust_click(
                By.XPATH,
                '//button[contains(text(), "Log In")]',
                "Web app login button",
                max_attempts=3,
                wait_time=2
            )
            
            if not web_login_success:
                print_error("Failed to click web app login button", self.account_id)
                return False
            
            # Wait for login to complete
            time.sleep(8)  # Increased wait time for login processing
            
            print_info("🔄 Returning to extension", self.account_id)
            
            # Close current tab and return to extension
            self.driver.close()
            self.driver.switch_to.window(self.driver.window_handles[0])
            self.driver.refresh()
            time.sleep(5)  # Increased wait time for extension refresh
            
            # Handle post-login dialogs
            self.handle_extension_dialogs()
            
            return True
            
        except TimeoutException as e:
            print_error(f"Timeout during extension setup: {str(e)[:100]}", self.account_id)
            return False
        except Exception as e:
            print_error(f"Error during extension setup: {str(e)[:100]}", self.account_id)
            return False
    
    def handle_extension_dialogs(self):
        """Handle post-login dialogs in Gradient extension with robust retry logic"""
        try:
            print_info("🔧 Handling extension dialogs", self.account_id)
            
            # Wait for page to fully load
            time.sleep(3)
            
            # Try to click "Close" button with retry logic
            close_success = self.robust_click(
                By.XPATH, 
                '//button[contains(@class, "w-full") and contains(@class, "h-[48px]") and contains(@class, "bg-black") and contains(@class, "text-white") and text()="Close"]',
                "Close dialog button",
                max_attempts=3,
                wait_time=2
            )
            
            if close_success:
                time.sleep(2)  # Wait after successful click
            
            # Try to click "I got it" button with retry logic
            got_it_success = self.robust_click(
                By.XPATH,
                '//button[contains(@class, "w-full") and contains(@class, "h-[48px]") and contains(@class, "bg-black") and contains(@class, "text-white") and text()="I got it"]',
                "I got it dialog button",
                max_attempts=3,
                wait_time=2
            )
            
            if got_it_success:
                time.sleep(2)  # Wait after successful click
            
            # If neither dialog was found, that's also okay
            if not close_success and not got_it_success:
                print_info("ℹ️ No dialogs found to dismiss", self.account_id)
            
            print_info("✅ Dialog handling completed", self.account_id)
                
        except Exception as e:
            print_warning(f"Dialog handling error: {str(e)[:100]}", self.account_id)
    
    def monitor_extension_health(self):
        """Monitor Gradient extension health status every minute with retry logic"""
        try:
            self.health_monitoring_active = True
            print_info("🔄 Health monitoring started (60s intervals)", self.account_id)
            
            while self.health_monitoring_active:
                try:
                    # Refresh the extension page
                    self.driver.refresh()
                    time.sleep(5)  # Wait for page to load
                    
                    # Check health status
                    health_status = self.get_extension_health()
                    uptime = self.get_extension_uptime()
                    
                    # Determine if status is good
                    is_good = health_status.lower() == "good"
                    
                    # Track status changes
                    if is_good:
                        self.was_good_before = True
                        self.consecutive_disconnects = 0
                    else:
                        self.consecutive_disconnects += 1
                    
                    # Display status with enhanced formatting
                    print_health_status(self.account_id, health_status, uptime, is_good)
                    
                    # Check if we need to retry (was good before but now disconnected)
                    if (self.was_good_before and not is_good and 
                        self.consecutive_disconnects >= self.max_consecutive_disconnects and
                        self.retry_count < self.max_retries):
                        
                        print_warning(f"🔄 Account was good but now disconnected for {self.consecutive_disconnects} checks. Initiating retry...", self.account_id)
                        self.initiate_retry()
                        return  # Exit current monitoring loop
                    
                    # Wait 60 seconds before next check
                    time.sleep(60)
                    
                except Exception as e:
                    print_error(f"Health check error: {e}", self.account_id)
                    time.sleep(60)  # Continue monitoring even if there's an error
                    
        except Exception as e:
            logger.error(f"[Account {self.account_id}] Error in health monitoring: {e}")
        finally:
            self.health_monitoring_active = False
    
    def get_extension_health(self):
        """Extract health status from extension page"""
        try:
            health_element = self.driver.find_element(By.XPATH, 
                '//div[contains(@class, "flex") and contains(@class, "flex-row") and contains(@class, "items-center") and contains(@class, "ml-1.5")]//span[contains(@class, "Helveticae") and contains(@class, "text-[12px]") and contains(@class, "text-theme-gray-60") and contains(@class, "select-none")]')
            return health_element.text
        except NoSuchElementException:
            return "Unknown"
        except Exception as e:
            logger.error(f"[Account {self.account_id}] Error getting health status: {e}")
            return "Error"
    
    def get_extension_uptime(self):
        """Extract uptime from extension page"""
        try:
            uptime_element = self.driver.find_element(By.XPATH, 
                '//div[contains(@class, "Helveticae") and contains(@class, "font-bold") and contains(@class, "flex") and contains(@class, "justify-center") and contains(@class, "items-center") and contains(@class, "select-none") and contains(@class, "mt-[2px]")]')
            return uptime_element.text
        except NoSuchElementException:
            return "00:00"
        except Exception as e:
            logger.error(f"[Account {self.account_id}] Error getting uptime: {e}")
            return "Error"
    
    def create_temp_profile(self, source_profile_path="chrome_user_profile"):
        """Create temporary Chrome profile in current directory"""
        try:
            logger.debug(f"[Account {self.account_id}] Creating temporary profile from: {source_profile_path}")
            
            # Create temp_profiles directory in current working directory
            temp_base_dir = os.path.join(os.getcwd(), "temp_profiles")
            if not os.path.exists(temp_base_dir):
                os.makedirs(temp_base_dir)
                logger.debug(f"Created temp_profiles directory: {temp_base_dir}")
            
            # Create account-specific temporary directory
            self.temp_profile_path = os.path.join(temp_base_dir, f"chrome_account_{self.account_id}")
            
            # Remove existing temp profile if it exists
            if os.path.exists(self.temp_profile_path):
                shutil.rmtree(self.temp_profile_path, ignore_errors=True)
                logger.debug(f"[Account {self.account_id}] Removed existing temp profile")
            
            # Create the temp profile directory
            os.makedirs(self.temp_profile_path)
            logger.debug(f"[Account {self.account_id}] Temporary profile path: {self.temp_profile_path}")
            
            # Copy existing profile to temp location
            profile_dest = os.path.join(self.temp_profile_path, "profile")
            if os.path.exists(source_profile_path):
                shutil.copytree(source_profile_path, profile_dest, dirs_exist_ok=True)
                logger.info(f"[Account {self.account_id}] Successfully copied existing profile to temporary location")
            else:
                logger.warning(f"[Account {self.account_id}] Source profile not found: {source_profile_path}")
                os.makedirs(profile_dest)
                logger.info(f"[Account {self.account_id}] Created new empty profile directory")
            
            return True
            
        except Exception as e:
            logger.error(f"[Account {self.account_id}] Error creating temporary profile: {e}")
            return False
    
    def start_chrome(self):
        """Start Chrome instance with safe memory optimization using undetected-chromedriver"""
        try:
            logger.debug(f"[Account {self.account_id}] Starting Chrome instance with safe memory optimization")
            
            # Configure Chrome options for undetected-chromedriver
            chrome_options = uc.ChromeOptions()
            
            # Essential configuration (unchanged)
            chrome_options.add_argument(f"--user-data-dir={os.path.join(self.temp_profile_path, 'profile')}")
            chrome_options.add_argument("--no-first-run")
            chrome_options.add_argument("--disable-default-apps")
            chrome_options.add_argument("--disable-extensions-file-access-check")
            chrome_options.add_argument("--enable-extensions")
            chrome_options.add_argument("--headless")  # Run in headless mode
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument(f"--remote-debugging-port={9222 + self.account_id}")  # Unique port per account
            
            # Safe memory optimization flags (won't break functionality)
            chrome_options.add_argument("--memory-pressure-off")  # Disable memory pressure notifications
            chrome_options.add_argument("--disable-background-timer-throttling")  # Reduce background processing
            chrome_options.add_argument("--disable-renderer-backgrounding")  # Prevent renderer backgrounding
            chrome_options.add_argument("--disable-backgrounding-occluded-windows")  # Disable background window optimization
            chrome_options.add_argument("--disable-background-networking")  # Disable background network requests
            chrome_options.add_argument("--disable-sync")  # Disable Chrome sync
            chrome_options.add_argument("--disable-translate")  # Disable translation service
            chrome_options.add_argument("--disable-ipc-flooding-protection")  # Reduce IPC overhead
            chrome_options.add_argument("--disable-hang-monitor")  # Disable hang monitor
            chrome_options.add_argument("--disable-prompt-on-repost")  # Disable repost prompts
            chrome_options.add_argument("--disable-domain-reliability")  # Disable domain reliability
            chrome_options.add_argument("--disable-component-update")  # Disable component updates
            chrome_options.add_argument("--disable-client-side-phishing-detection")  # Disable phishing detection
            chrome_options.add_argument("--disable-default-apps")  # Disable default apps
            chrome_options.add_argument("--aggressive-cache-discard")  # Aggressively discard cached data
            
            # Cache size limits (safe)
            chrome_options.add_argument("--disk-cache-size=67108864")  # Limit disk cache to 64MB
            chrome_options.add_argument("--media-cache-size=33554432")  # Limit media cache to 32MB
            
            # Start Chrome with undetected-chromedriver
            self.driver = uc.Chrome(options=chrome_options, version_main=None)
            
            logger.info(f"[Account {self.account_id}] Chrome started successfully with safe memory optimization")
            return True
            
        except Exception as e:
            logger.error(f"[Account {self.account_id}] Error starting Chrome: {e}")
            return False
    
    def wait_for_element(self, by, value, timeout=None):
        """Wait for element with error handling"""
        if timeout is None:
            timeout = self.wait_timeout
            
        try:
            wait = WebDriverWait(self.driver, timeout)
            element = wait.until(EC.presence_of_element_located((by, value)))
            logger.debug(f"Found element: {by}={value}")
            return element
        except TimeoutException:
            logger.warning(f"Element not found within {timeout}s: {by}={value}")
            return None
    
    def safe_clear_and_send_keys(self, element, text):
        """Safely clear input field and enter new text"""
        try:
            # Clear existing text
            element.clear()
            time.sleep(0.5)
            
            # Send new text
            element.send_keys(text)
            logger.debug(f"Successfully entered text: {text}")
            return True
            
        except Exception as e:
            logger.error(f"Error entering text: {e}")
            return False
    
    def robust_click(self, by, value, description, max_attempts=3, wait_time=2):
        """Robust click method with retry logic for UI interactions"""
        for attempt in range(max_attempts):
            try:
                # Wait for element to be present and clickable
                element = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((by, value))
                )
                
                # Scroll element into view
                self.driver.execute_script("arguments[0].scrollIntoView(true);", element)
                time.sleep(1)
                
                # Try regular click first
                try:
                    element.click()
                    print_info(f"✅ {description} (attempt {attempt + 1})", self.account_id)
                    return True
                except Exception as click_error:
                    # If regular click fails, try JavaScript click
                    print_info(f"🔄 Retrying {description} with JS click (attempt {attempt + 1})", self.account_id)
                    self.driver.execute_script("arguments[0].click();", element)
                    print_info(f"✅ {description} via JS (attempt {attempt + 1})", self.account_id)
                    return True
                    
            except TimeoutException:
                if attempt < max_attempts - 1:
                    print_info(f"⏳ {description} not ready, waiting {wait_time}s (attempt {attempt + 1})", self.account_id)
                    time.sleep(wait_time)
                else:
                    print_warning(f"⚠️ {description} not found after {max_attempts} attempts", self.account_id)
                    return False
            except Exception as e:
                if attempt < max_attempts - 1:
                    print_warning(f"🔄 {description} failed, retrying in {wait_time}s (attempt {attempt + 1}): {str(e)[:100]}", self.account_id)
                    time.sleep(wait_time)
                else:
                    print_warning(f"❌ {description} failed after {max_attempts} attempts: {str(e)[:100]}", self.account_id)
                    return False
        
        return False
    
    def setup_proxy(self):
        """Navigate to proxy settings and configure proxy"""
        try:
            logger.info(f"[Account {self.account_id}] Setting up proxy configuration")
            
            # Navigate to proxy settings page
            proxy_url = "chrome-extension://pfnededegaaopdmhkdmcofjmoldfiped/options.html#!/profile/proxy"
            logger.debug(f"[Account {self.account_id}] Navigating to: {proxy_url}")
            self.driver.get(proxy_url)
            time.sleep(3)
            
            # Wait for page to load
            logger.debug(f"[Account {self.account_id}] Waiting for proxy settings page to load")
            time.sleep(5)
            
            # Input proxy host
            logger.debug(f"[Account {self.account_id}] Looking for proxy host input field")
            host_input = self.wait_for_element(By.CSS_SELECTOR, 'input[ng-model="proxyEditors[scheme].host"]')
            if host_input:
                if self.safe_clear_and_send_keys(host_input, self.proxy_data['host']):
                    logger.info(f"[Account {self.account_id}] Entered proxy host: {self.proxy_data['host']}")
                else:
                    logger.error(f"[Account {self.account_id}] Failed to enter proxy host")
                    return False
            else:
                logger.error(f"[Account {self.account_id}] Proxy host input field not found")
                return False
            
            # Input proxy port
            logger.debug(f"[Account {self.account_id}] Looking for proxy port input field")
            port_input = self.wait_for_element(By.CSS_SELECTOR, 'input[ng-model="proxyEditors[scheme].port"]')
            if port_input:
                if self.safe_clear_and_send_keys(port_input, self.proxy_data['port']):
                    logger.info(f"[Account {self.account_id}] Entered proxy port: {self.proxy_data['port']}")
                else:
                    logger.error(f"[Account {self.account_id}] Failed to enter proxy port")
                    return False
            else:
                logger.error(f"[Account {self.account_id}] Proxy port input field not found")
                return False
            
            # Click auth button
            logger.debug(f"[Account {self.account_id}] Looking for auth button")
            auth_button = self.wait_for_element(By.CSS_SELECTOR, 'button.proxy-auth-toggle')
            if auth_button:
                auth_button.click()
                logger.info(f"[Account {self.account_id}] Clicked auth button")
                time.sleep(2)
            else:
                logger.error(f"[Account {self.account_id}] Auth button not found")
                return False
            
            # Input username
            logger.debug(f"[Account {self.account_id}] Looking for username input field")
            username_input = self.wait_for_element(By.CSS_SELECTOR, 'input[placeholder="Username"]')
            if username_input:
                if self.safe_clear_and_send_keys(username_input, self.proxy_data['username']):
                    logger.info(f"[Account {self.account_id}] Entered username: {self.proxy_data['username']}")
                else:
                    logger.error(f"[Account {self.account_id}] Failed to enter username")
                    return False
            else:
                logger.error(f"[Account {self.account_id}] Username input field not found")
                return False
            
            # Input password
            logger.debug(f"[Account {self.account_id}] Looking for password input field")
            password_input = self.wait_for_element(By.CSS_SELECTOR, 'input[name="password"]')
            if password_input:
                if self.safe_clear_and_send_keys(password_input, self.proxy_data['password']):
                    logger.info(f"[Account {self.account_id}] Entered password")
                else:
                    logger.error(f"[Account {self.account_id}] Failed to enter password")
                    return False
            else:
                logger.error(f"[Account {self.account_id}] Password input field not found")
                return False
            
            # Click save button
            logger.debug(f"[Account {self.account_id}] Looking for save button")
            save_button = self.wait_for_element(By.CSS_SELECTOR, 'button[type="submit"].btn-primary')
            if save_button:
                save_button.click()
                logger.info(f"[Account {self.account_id}] Clicked save button")
                time.sleep(2)
            else:
                logger.error(f"[Account {self.account_id}] Save button not found")
                return False
            
            # Click apply button
            logger.debug(f"[Account {self.account_id}] Looking for apply button")
            apply_button = self.wait_for_element(By.CSS_SELECTOR, 'a[ng-click="applyOptions()"]')
            if apply_button:
                apply_button.click()
                logger.info(f"[Account {self.account_id}] Clicked apply button")
                time.sleep(3)
            else:
                logger.error(f"[Account {self.account_id}] Apply button not found")
                return False
            
            logger.info(f"[Account {self.account_id}] Proxy configuration completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"[Account {self.account_id}] Error setting up proxy: {e}")
            return False
    
    def connect_to_proxy(self):
        """Connect to proxy through extension popup"""
        try:
            print_info("🔗 Connecting to proxy", self.account_id)
            
            # Store the main window handle
            main_window = self.driver.current_window_handle
            
            # Open new tab
            self.driver.execute_script("window.open('');")
            self.driver.switch_to.window(self.driver.window_handles[-1])
            
            # Navigate to extension popup
            popup_url = "chrome-extension://pfnededegaaopdmhkdmcofjmoldfiped/popup/index.html"
            self.driver.get(popup_url)
            time.sleep(5)  # Increased wait time for popup load
            
            # Click connect button with retry logic
            connect_success = self.robust_click(
                By.CSS_SELECTOR,
                '#js-profile-1',
                "Proxy connect button",
                max_attempts=3,
                wait_time=3
            )
            
            if connect_success:
                time.sleep(8)  # Wait longer for connection to establish
                
                # Switch back to main window after connection
                try:
                    self.driver.switch_to.window(main_window)
                    print_info("✅ Returned to main window", self.account_id)
                except Exception as switch_error:
                    print_warning(f"Window switch issue, using first available: {str(switch_error)[:50]}", self.account_id)
                    # Try to switch to the first available window
                    if self.driver.window_handles:
                        self.driver.switch_to.window(self.driver.window_handles[0])
                
                return True
            else:
                print_error("Failed to click proxy connect button", self.account_id)
                return False
                
        except Exception as e:
            print_error(f"Error connecting to proxy: {str(e)[:100]}", self.account_id)
            return False
    

    
    def initiate_retry(self):
        """Initiate retry process for disconnected account"""
        try:
            self.retry_count += 1
            print_warning(f"🔄 Starting retry attempt {self.retry_count}/{self.max_retries}", self.account_id)
            
            # Stop current health monitoring
            self.health_monitoring_active = False
            
            # Clean up current resources
            self.cleanup_for_retry()
            
            # Wait a bit before retry
            print_info("⏳ Waiting 30 seconds before retry", self.account_id)
            time.sleep(30)
            
            # Reset status tracking
            self.consecutive_disconnects = 0
            self.setup_complete = False
            
            # Start retry in a new thread
            retry_thread = threading.Thread(target=self.retry_setup, daemon=True)
            retry_thread.start()
            
        except Exception as e:
            print_error(f"Error initiating retry: {e}", self.account_id)
    
    def cleanup_for_retry(self):
        """Clean up resources specifically for retry (keeps account data)"""
        try:
            print_info("🧹 Cleaning up for retry", self.account_id)
            
            # Stop health monitoring
            self.health_monitoring_active = False
            
            # Close browser
            if self.driver:
                try:
                    self.driver.quit()
                    print_info("✅ Browser closed", self.account_id)
                except Exception as e:
                    print_warning(f"Browser cleanup issue: {e}", self.account_id)
                finally:
                    self.driver = None
            
            # Remove temp profile folder
            if self.temp_profile_path and os.path.exists(self.temp_profile_path):
                try:
                    shutil.rmtree(self.temp_profile_path, ignore_errors=True)
                    print_info("✅ Temp profile deleted", self.account_id)
                except Exception as e:
                    print_warning(f"Temp profile cleanup issue: {e}", self.account_id)
                finally:
                    self.temp_profile_path = None
            
            # Reset proxy data (will be re-parsed)
            self.proxy_data = None
            
            print_success("🧹 Cleanup completed for retry", self.account_id)
            
        except Exception as e:
            print_error(f"Error during retry cleanup: {e}", self.account_id)
    
    def retry_setup(self):
        """Retry the complete setup process"""
        try:
            print_retry_header(self.account_id, self.gradient_data['email'], self.retry_count, self.max_retries)
            print_info(f"🔄 Attempting full reconnection", self.account_id)
            
            # Run the complete setup again
            success = self.run_account_setup_internal()
            
            if success:
                print_success(f"🎯 Retry {self.retry_count} successful! Account reconnected.", self.account_id)
                print_separator()
                # Start health monitoring again
                health_thread = threading.Thread(target=self.monitor_extension_health, daemon=True)
                health_thread.start()
            else:
                print_error(f"💥 Retry {self.retry_count} failed", self.account_id)
                if self.retry_count < self.max_retries:
                    print_info(f"🔄 Will attempt retry {self.retry_count + 1} if disconnected again", self.account_id)
                else:
                    print_error(f"❌ Max retries ({self.max_retries}) reached. Account disabled.", self.account_id)
                print_separator()
            
        except Exception as e:
            print_error(f"Error during retry setup: {e}", self.account_id)
    
    def run_account_setup_internal(self):
        """Internal setup method without threading (used for retries)"""
        try:
            # Parse proxy data
            print_step(1, 6, "Parsing proxy configuration", self.account_id)
            if self.proxy_line:
                if not self.parse_proxy_data(self.proxy_line):
                    print_error("Failed to parse proxy data", self.account_id)
                    return False
                print_proxy_info(self.account_id, self.proxy_data['host'], self.proxy_data['port'])
                print_success("Proxy configuration loaded", self.account_id)
            else:
                print_error("No proxy assigned to this account", self.account_id)
                return False
            
            # Create temporary profile
            print_step(2, 6, "Creating temporary Chrome profile", self.account_id)
            if not self.create_temp_profile():
                print_error("Failed to create temporary profile", self.account_id)
                return False
            print_success("Temporary profile created", self.account_id)
            
            # Start Chrome
            print_step(3, 6, "Starting Chrome browser", self.account_id)
            if not self.start_chrome():
                print_error("Failed to start Chrome", self.account_id)
                return False
            print_success("Chrome browser started in headless mode", self.account_id)
            
            # Setup proxy
            print_step(4, 6, "Configuring proxy settings", self.account_id)
            if not self.setup_proxy():
                print_warning("Failed to setup proxy, continuing without proxy", self.account_id)
            else:
                print_success("Proxy settings configured", self.account_id)
            
            # Connect to proxy
            print_step(5, 6, "Connecting to proxy server", self.account_id)
            if not self.connect_to_proxy():
                print_warning("Failed to connect to proxy, continuing without connection", self.account_id)
            else:
                print_success("Connected to proxy server", self.account_id)
            
            # Setup gradient extension
            print_step(6, 6, "Setting up Gradient extension", self.account_id)
            if not self.setup_gradient_extension():
                print_error("Failed to setup gradient extension", self.account_id)
                return False
            else:
                print_success("Gradient extension configured successfully", self.account_id)
            
            self.setup_complete = True
            return True
            
        except Exception as e:
            print_error(f"Unexpected error during internal setup: {e}", self.account_id)
            return False
    
    def cleanup(self):
        """Clean up resources for this account"""
        try:
            self.health_monitoring_active = False
            
            if self.driver:
                logger.debug(f"[Account {self.account_id}] Closing Chrome driver")
                try:
                    self.driver.quit()
                except Exception as e:
                    logger.warning(f"[Account {self.account_id}] Error closing driver: {e}")
            
            if self.temp_profile_path and os.path.exists(self.temp_profile_path):
                logger.debug(f"[Account {self.account_id}] Removing temporary profile: {self.temp_profile_path}")
                try:
                    shutil.rmtree(self.temp_profile_path, ignore_errors=True)
                    logger.debug(f"[Account {self.account_id}] Successfully removed temp profile")
                except Exception as e:
                    logger.warning(f"[Account {self.account_id}] Error removing temp profile: {e}")
                
            logger.info(f"[Account {self.account_id}] Cleanup completed")
            
        except Exception as e:
            logger.error(f"[Account {self.account_id}] Error during cleanup: {e}")
    
    def run_account_setup(self):
        """Setup method for individual account"""
        try:
            print_account_header(self.account_id, self.gradient_data['email'])
            
            # Run internal setup
            success = self.run_account_setup_internal()
            
            if success:
                print_success(f"🎯 Setup completed for {self.gradient_data['email']}", self.account_id)
                
                # Start health monitoring in a separate thread
                health_thread = threading.Thread(target=self.monitor_extension_health, daemon=True)
                health_thread.start()
                
                return True
            else:
                return False
            
        except Exception as e:
            print_error(f"Unexpected error during setup: {e}", self.account_id)
            return False

class MultiAccountManager:
    def __init__(self):
        self.accounts = []
        self.active_automations = []
        self.setup_delay = 30  # 30 seconds delay between account setups
        
        # Clean up any existing temp profiles from previous runs
        self.cleanup_existing_temp_profiles()
    
    @staticmethod
    def cleanup_existing_temp_profiles():
        """Clean up any existing temp profiles from previous runs"""
        try:
            temp_base_dir = os.path.join(os.getcwd(), "temp_profiles")
            if os.path.exists(temp_base_dir):
                shutil.rmtree(temp_base_dir, ignore_errors=True)
                print_info("🧹 Cleaned up existing temp profiles from previous runs")
        except Exception as e:
            print_warning(f"Could not clean up existing temp profiles: {e}")
        
    def run_all_accounts(self):
        """Main method to run all accounts concurrently"""
        try:
            print_header("🤖 MULTI-ACCOUNT CHROME PROXY AUTOMATION")
            print_info("🚀 Initializing automated setup for multiple accounts...")
            
            # Parse all accounts from data.txt
            accounts_data = ChromeProxyAutomation.parse_all_accounts()
            if not accounts_data:
                print_error("❌ No valid accounts found in data.txt")
                return False
            
            # Parse all proxies from proxy.txt
            proxies_data = ChromeProxyAutomation.parse_all_proxies()
            if not proxies_data:
                print_error("❌ No valid proxies found in proxy.txt")
                return False
            
            # Check if we have enough proxies for all accounts
            if len(proxies_data) < len(accounts_data):
                print_error(f"❌ Insufficient proxies! Found {len(proxies_data)} proxies for {len(accounts_data)} accounts")
                print_info("💡 Each account requires its own proxy. Please add more proxies to proxy.txt")
                return False
            
            # Display summary table
            print_summary_table(accounts_data, proxies_data)
            
            # Use ThreadPoolExecutor to manage concurrent account setups
            with ThreadPoolExecutor(max_workers=len(accounts_data)) as executor:
                futures = []
                
                for i, account_data in enumerate(accounts_data, 1):
                    # Get corresponding proxy for this account (same line number)
                    proxy_line = proxies_data[i-1] if i-1 < len(proxies_data) else None
                    
                    # Create automation instance for each account with its proxy
                    automation = ChromeProxyAutomation(
                        account_id=i, 
                        account_data=account_data,
                        proxy_line=proxy_line
                    )
                    self.active_automations.append(automation)
                    
                    # Submit account setup with delay
                    future = executor.submit(self.setup_account_with_delay, automation, i-1)
                    futures.append(future)
                
                print_header("🚀 DEPLOYMENT STATUS")
                print_info("⏱️  Accounts deploy with 30-second staggered intervals")
                print_info("🔄 Health monitoring starts automatically after each setup")
                print_info("⚡ Press Ctrl+C to stop all operations")
                print_separator()
                
                # Wait for all setups to complete
                try:
                    for future in futures:
                        future.result()  # This will raise any exceptions that occurred
                        
                    print_header("🎉 DEPLOYMENT COMPLETE")
                    print_success("✅ All account setups have been initiated!")
                    print_info("🔄 Health monitoring is active for all configured accounts")
                    print_separator()
                    
                    # Keep the main thread alive to maintain health monitoring
                    self.keep_alive()
                    
                except KeyboardInterrupt:
                    print_info("🛑 Operation interrupted by user")
                    self.cleanup_all()
                    return False
                    
        except Exception as e:
            print_error(f"💥 Critical error in multi-account manager: {e}")
            self.cleanup_all()
            return False
    
    def setup_account_with_delay(self, automation, account_index):
        """Setup account with appropriate delay"""
        try:
            # Add delay for accounts after the first one
            if account_index > 0:
                delay_time = account_index * self.setup_delay
                print_info(f"⏳ Waiting {delay_time}s before deployment", automation.account_id)
                time.sleep(delay_time)
            
            # Run the account setup
            success = automation.run_account_setup()
            
            if success:
                print_success("🎯 Account deployment successful", automation.account_id)
                print_separator()
            else:
                print_error("💥 Account deployment failed", automation.account_id)
                print_separator()
                
            return success
            
        except Exception as e:
            print_error(f"💥 Error during deployment: {e}", automation.account_id)
            return False
    
    def keep_alive(self):
        """Keep the main thread alive while health monitoring runs"""
        try:
            print_header("🔄 HEALTH MONITORING ACTIVE")
            print_info("🖥️  Main process running - monitoring all accounts")
            print_info("⚡ Press Ctrl+C to stop all operations")
            print_separator()
            
            while True:
                time.sleep(60)  # Check every minute
                
                # Check if any automations are still active
                active_count = sum(1 for auto in self.active_automations if auto.health_monitoring_active)
                if active_count == 0:
                    print_info("🔚 All health monitoring stopped. Exiting...")
                    break
                    
        except KeyboardInterrupt:
            print_info("🛑 Stopping all operations...")
            self.cleanup_all()
    
    def cleanup_all(self):
        """Cleanup all automation instances and remove temp profiles directory"""
        try:
            print_header("🧹 CLEANUP IN PROGRESS")
            print_info("🔄 Shutting down all automation instances...")
            
            for automation in self.active_automations:
                try:
                    automation.cleanup()
                    print_success(f"Cleaned up successfully", automation.account_id)
                except Exception as e:
                    print_error(f"Cleanup error: {e}", automation.account_id)
            
            # Remove the entire temp_profiles directory
            temp_base_dir = os.path.join(os.getcwd(), "temp_profiles")
            if os.path.exists(temp_base_dir):
                try:
                    shutil.rmtree(temp_base_dir, ignore_errors=True)
                    print_success("🗂️ Removed temp_profiles directory")
                except Exception as e:
                    print_warning(f"Could not remove temp_profiles directory: {e}")
            
            print_separator()
            print_success("🎉 Cleanup completed for all accounts")
            
        except Exception as e:
            print_error(f"💥 Error during cleanup: {e}")

if __name__ == "__main__":
    manager = MultiAccountManager()
    manager.run_all_accounts()