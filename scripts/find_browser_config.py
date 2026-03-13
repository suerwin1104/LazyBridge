import browser_use
import pkgutil
import inspect

def find_class_in_package(package, class_name):
    for loader, module_name, is_pkg in pkgutil.walk_packages(package.__path__, package.__name__ + '.'):
        try:
            module = __import__(module_name, fromlist=[class_name])
            for name, obj in inspect.getmembers(module):
                if inspect.isclass(obj) and name == class_name:
                    return module_name
        except Exception:
            continue
    return None

location = find_class_in_package(browser_use, "BrowserConfig")
if location:
    print(f"BrowserConfig found in: {location}")
else:
    print("BrowserConfig not found in any submodule.")
    
# Let's also check for similar names
for loader, module_name, is_pkg in pkgutil.walk_packages(browser_use.__path__, browser_use.__name__ + '.'):
    try:
        module = __import__(module_name, fromlist=[''])
        for name, obj in inspect.getmembers(module):
            if inspect.isclass(obj) and "Config" in name:
                print(f"Found class: {name} in {module_name}")
    except:
        continue
