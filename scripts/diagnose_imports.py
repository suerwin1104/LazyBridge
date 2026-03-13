import browser_use
print(f"Version: {getattr(browser_use, '__version__', 'unknown')}")
print(f"Dir: {dir(browser_use)}")

try:
    from browser_use.browser.browser import BrowserConfig
    print("Found BrowserConfig in browser_use.browser.browser")
except ImportError:
    print("NOT in browser_use.browser.browser")

try:
    from browser_use import BrowserConfig
    print("Found BrowserConfig in browser_use")
except ImportError:
    print("NOT in browser_use")

# Find where BrowserConfig is defined
import pkgutil
for loader, module_name, is_pkg in pkgutil.walk_packages(browser_use.__path__, browser_use.__name__ + '.'):
    try:
        mod = __import__(module_name, fromlist=['BrowserConfig'])
        if hasattr(mod, 'BrowserConfig'):
            print(f"BrowserConfig FOUND in {module_name}")
    except:
        continue
