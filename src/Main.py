from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import time

chrome_options = Options()
chrome_options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
driver = webdriver.Chrome(options=chrome_options)

# Settings
WAIT_TIME = 10
MAX_CYCLES = 30
JC_INPUT_SELECTOR = "textarea[class*='_sendInput_']"
JC_MESSAGE_SELECTOR = "div._markdownContent_8vtsi_181"

def wait_action(seconds, reason):
    print(f"\n[WAIT {seconds}s] {reason}")
    for i in range(seconds, 0, -1):
        if i % 5 == 0 or i <= 3:
            print(f"  {i}...")
        time.sleep(1)

def switch_to_tab(tab_index, tab_name):
    tabs = driver.window_handles
    if len(tabs) <= tab_index:
        print(f"[ERROR] Tab {tab_index} ({tab_name}) not found!")
        return False
    
    driver.switch_to.window(tabs[tab_index])
    print(f"[OK] Switched to tab {tab_index} ({tab_name})")
    return True

def get_last_message_jc():
    try:
        print("[JC] Looking for messages...")
        all_messages = driver.find_elements(By.CSS_SELECTOR, JC_MESSAGE_SELECTOR)
        
        if not all_messages:
            print("[JC] No messages found")
            return None
        
        print(f"[JC] Found {len(all_messages)} messages")
        last_msg = all_messages[-1]
        
        # Get text
        full_text = driver.execute_script("""
            var element = arguments[0];
            function getText(node) {
                if (node.nodeType === Node.TEXT_NODE) return node.textContent;
                var text = '';
                for (var child of node.childNodes) text += getText(child);
                return text;
            }
            return getText(element).trim();
        """, last_msg)
        
        if not full_text:
            full_text = last_msg.text.strip()
        
        print(f"[JC] Copied message ({len(full_text)} chars)")
        
        # Show preview
        if len(full_text) > 100:
            print(f"      Preview: '{full_text[:100]}...'")
        
        return full_text
        
    except Exception as e:
        print(f"[JC ERROR] Failed to get message: {str(e)[:100]}")
        return None

def get_last_message_ds():
    try:
        print("[DS] Looking for messages...")
        all_messages = driver.find_elements(By.CSS_SELECTOR, "div.ds-message")
        
        if not all_messages:
            print("[DS] No messages found")
            return None
        
        print(f"[DS] Found {len(all_messages)} messages")
        last_msg = all_messages[-1]
        
        # Get text
        full_text = driver.execute_script("""
            var element = arguments[0];
            function getText(node) {
                if (node.nodeType === Node.TEXT_NODE) return node.textContent;
                var text = '';
                for (var child of node.childNodes) text += getText(child);
                return text;
            }
            var result = getText(element);
            result = result.replace(/\\n{3,}/g, '\\n\\n').trim();
            return result;
        """, last_msg)
        
        if not full_text or len(full_text.strip()) < 10:
            full_text = last_msg.text
        
        full_text = full_text.strip()
        
        print(f"[DS] Copied message ({len(full_text)} chars)")
        
        # Show preview
        if len(full_text) > 100:
            print(f"      Preview: '{full_text[:100]}...'")
        
        return full_text
        
    except Exception as e:
        print(f"[DS ERROR] Failed to get message: {str(e)[:100]}")
        return None

def send_to_jc(text):
    """Send text to JuicyChat - FIXED VERSION"""
    try:
        print(f"[JC] Preparing to send {len(text)} chars")
        
        # Find input field
        input_field = driver.find_element(By.CSS_SELECTOR, JC_INPUT_SELECTOR)
        print("[JC] Found input field")
        
        # Focus and clear
        input_field.click()
        time.sleep(0.5)
        
        # Clear field
        driver.execute_script("arguments[0].value = '';", input_field)
        time.sleep(0.5)
        
        # TYPE TEXT (not insert via JS)
        print("[JC] Typing text...")
        input_field.send_keys(text)
        print(f"[JC] Text typed ({len(text)} chars)")
        
        # Add activation (space then backspace)
        print("[JC] Activating field...")
        input_field.send_keys(" ")
        time.sleep(0.3)
        input_field.send_keys(Keys.BACKSPACE)
        time.sleep(0.3)
        
        # SEND WITH ENTER
        print("[JC] Sending with Enter...")
        input_field.send_keys(Keys.ENTER)
        print("[JC] Enter pressed")
        
        # Verify send
        time.sleep(2)
        field_after = input_field.get_attribute('value') or ''
        
        if field_after and len(field_after.strip()) > 10:
            print(f"[JC WARNING] Text still in field ({len(field_after)} chars)")
            
            # Try alternative send method
            print("[JC] Trying alternative send...")
            
            # Method 1: Clear and retry
            input_field.click()
            driver.execute_script("arguments[0].value = '';", input_field)
            time.sleep(0.5)
            input_field.send_keys(text)
            time.sleep(0.5)
            
            # Try Ctrl+Enter
            input_field.send_keys(Keys.CONTROL + Keys.ENTER)
            time.sleep(2)
            
            # Final check
            final_check = input_field.get_attribute('value') or ''
            if final_check and len(final_check.strip()) > 10:
                print(f"[JC ERROR] Not sent. Field has {len(final_check)} chars")
                return False
        
        print("[JC SUCCESS] Message sent!")
        return True
        
    except Exception as e:
        print(f"[JC ERROR] Failed to send: {str(e)[:100]}")
        return False

def insert_text_to_field(input_element, text):
    """Insert text into field without any sending"""
    try:
        # Clear field using JavaScript
        driver.execute_script("arguments[0].value = '';", input_element)
        time.sleep(0.5)
        
        # Insert text using JavaScript
        driver.execute_script("""
            var field = arguments[0];
            var text = arguments[1];
            field.value = text;
            
            var event = new Event('input', { bubbles: true });
            field.dispatchEvent(event);
        """, input_element, text)
        
        time.sleep(0.5)
        
        # Verify insertion
        inserted = driver.execute_script("return arguments[0].value;", input_element)
        return inserted
        
    except Exception as e:
        print(f"[INSERT ERROR] {str(e)[:100]}")
        return ""

def add_dot_and_send(input_field):
    """Add dot and send message in DeepSeek"""
    try:
        print("\n[DS ACTION] Adding dot '.' to activate field...")
        
        # Add dot at the end
        input_field.send_keys(".")
        print("[DS] Dot added")
        time.sleep(1)
        
        # Remove dot
        print("[DS] Removing dot...")
        input_field.send_keys(Keys.BACKSPACE)
        print("[DS] Dot removed")
        time.sleep(1)
        
        # Send message
        print("[DS] Sending message with Enter...")
        input_field.send_keys(Keys.ENTER)
        print("[DS] Enter pressed")
        
        # Check if sent
        time.sleep(2)
        
        field_after = input_field.get_attribute('value') or ''
        if field_after and len(field_after.strip()) > 10:
            print(f"[DS WARNING] Text still in field ({len(field_after)} chars)")
            
            # Try send button
            print("[DS] Trying send button...")
            buttons = driver.find_elements(By.TAG_NAME, "button")
            
            for btn in buttons:
                try:
                    if btn.is_displayed() and btn.is_enabled():
                        btn_class = btn.get_attribute('class') or ''
                        if 'send' in btn_class.lower() or 'submit' in btn_class.lower():
                            print("[DS] Clicking send button...")
                            btn.click()
                            time.sleep(2)
                            break
                except:
                    continue
        
        final_text = input_field.get_attribute('value') or ''
        if final_text and len(final_text.strip()) > 10:
            print(f"[DS ERROR] Message not sent. Field has {len(final_text)} chars")
            return False
        else:
            print("[DS SUCCESS] Message sent!")
            return True
            
    except Exception as e:
        print(f"[DS SEND ERROR] Failed to send: {str(e)[:100]}")
        return False

def send_to_ds(text):
    """Send text to DeepSeek with dot method"""
    try:
        print(f"[DS] Processing {len(text)} chars")
        
        # Find input field
        input_field = None
        selectors = ["textarea", "textarea[placeholder]", "div[contenteditable='true']"]
        
        for selector in selectors:
            elements = driver.find_elements(By.CSS_SELECTOR, selector)
            for elem in elements:
                if elem.is_displayed() and elem.is_enabled():
                    input_field = elem
                    print(f"[DS] Found input field: {selector}")
                    break
            if input_field:
                break
        
        if not input_field:
            print("[DS ERROR] Input field not found")
            return False
        
        # Focus field
        print("[DS] Focusing field...")
        input_field.click()
        time.sleep(1)
        
        # Clear field
        print("[DS] Clearing field...")
        driver.execute_script("arguments[0].value = '';", input_field)
        time.sleep(1)
        
        # INSERT TEXT
        print("[DS] Inserting text...")
        inserted_text = insert_text_to_field(input_field, text)
        
        if not inserted_text or len(inserted_text) < len(text) * 0.8:
            print("[DS WARNING] Not all text inserted")
            driver.execute_script("arguments[0].value = arguments[1];", input_field, text)
            time.sleep(1)
        
        # Verify text is in field
        current_text = driver.execute_script("return arguments[0].value;", input_field)
        print(f"[DS] Field contains {len(current_text)} chars")
        
        if len(current_text) > 0:
            print("[DS SUCCESS] Text inserted in field")
            
            # ADD DOT AND SEND
            send_success = add_dot_and_send(input_field)
            
            if send_success:
                print("[DS COMPLETE] Text sent with dot method")
                return True
            else:
                print("[DS WARNING] Send may have failed")
                return False
        else:
            print("[DS ERROR] Field is empty")
            return False
        
    except Exception as e:
        print(f"[DS ERROR] Failed: {str(e)[:100]}")
        return False

def main_full_cycle():
    """Complete cycle: JC -> DS -> Wait -> DS -> JC"""
    print("\n" + "="*70)
    print("FULL AUTOMATION CYCLE")
    print(f"Cycles: {MAX_CYCLES} | Wait time: {WAIT_TIME} seconds")
    print("="*70)
    
    cycle_count = 0
    
    while cycle_count < MAX_CYCLES:
        cycle_count += 1
        
        print(f"\n{'='*70}")
        print(f"CYCLE {cycle_count}/{MAX_CYCLES}")
        print(f"{'='*70}")
        
        # ===== PHASE 1: JC -> DS =====
        print("\n[PHASE 1] JC -> DeepSeek")
        
        # Switch to JC
        print("[1.1] Switching to JuicyChat...")
        if not switch_to_tab(0, "JuicyChat"):
            break
        
        # Get message from JC
        print("[1.2] Getting last JC message...")
        jc_message = get_last_message_jc()
        if not jc_message:
            print("[ERROR] No JC message, skipping cycle")
            wait_action(WAIT_TIME, "Skipping cycle")
            continue
        
        wait_action(WAIT_TIME, "JC message ready, switching to DS")
        
        # Switch to DS
        print("[1.3] Switching to DeepSeek...")
        if not switch_to_tab(1, "DeepSeek"):
            break
        
        # Send to DS
        print("[1.4] Sending to DeepSeek...")
        send_success_ds = send_to_ds(jc_message)
        
        if send_success_ds:
            print("[SUCCESS] Message sent to DeepSeek")
        else:
            print("[WARNING] DS send may have failed")
        
        # Wait for DS response
        print(f"\n[1.5] Waiting {WAIT_TIME} seconds for DeepSeek response...")
        wait_action(WAIT_TIME, "Waiting for DS response")
        
        # ===== PHASE 2: DS -> JC =====
        print("\n[PHASE 2] DeepSeek -> JC")
        
        # Get message from DS
        print("[2.1] Getting last DS message...")
        ds_message = get_last_message_ds()
        if not ds_message:
            print("[WARNING] No DS message, skipping phase 2")
            wait_action(WAIT_TIME, "Skipping to next cycle")
            continue
        
        wait_action(WAIT_TIME, "DS message ready, switching to JC")
        
        # Switch to JC
        print("[2.2] Switching to JuicyChat...")
        if not switch_to_tab(0, "JuicyChat"):
            break
        
        # Send to JC - USING FIXED FUNCTION
        print("[2.3] Sending to JuicyChat...")
        send_success_jc = send_to_jc(ds_message)
        
        if send_success_jc:
            print("[SUCCESS] Message sent to JuicyChat")
        else:
            print("[WARNING] JC send may have failed")
        
        # Wait before next cycle
        print(f"\n[2.4] Waiting {WAIT_TIME} seconds before next cycle...")
        wait_action(WAIT_TIME, "Cycle complete, waiting")
        
        # Cycle statistics
        print(f"\n[STATS] Cycle {cycle_count} completed")
        print(f"        JC->DS: {len(jc_message) if jc_message else 0} chars")
        print(f"        DS->JC: {len(ds_message) if ds_message else 0} chars")
    
    print(f"\n{'='*70}")
    print(f"COMPLETED {cycle_count} CYCLES")
    print(f"{'='*70}")

try:
    # Initial setup
    tabs = driver.window_handles
    print(f"[INIT] Found {len(tabs)} tabs")
    
    if len(tabs) < 2:
        print("[ERROR] Need 2 tabs open:")
        print("        Tab 0: JuicyChat.AI")
        print("        Tab 1: DeepSeek")
    else:
        # Show tab info
        for i, tab in enumerate(tabs):
            driver.switch_to.window(tab)
            print(f"  Tab {i}: {driver.title[:50]}...")
        
        # Start on JC tab
        driver.switch_to.window(tabs[0])
        
        print(f"\n[INIT] Starting {MAX_CYCLES} cycles...")
        wait_action(5, "Initial delay")
        
        # Run full cycle
        main_full_cycle()
        
except KeyboardInterrupt:
    print("\n\n[INFO] Stopped by user (Ctrl+C)")
    
except Exception as e:
    print(f"\n[ERROR] {type(e).__name__}: {str(e)[:200]}")

finally:
    print("\n" + "="*70)
    print("SCRIPT FINISHED")
    print("="*70)