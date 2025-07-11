import streamlit as st
import pandas as pd
import time
import random
import csv
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# Streamlit Config
st.set_page_config(page_title="Octolife's Data Scrapping Toolkit", layout="wide")

# Custom background (neon green)
st.markdown(
    """
    <style>
    .reportview-container {
        background: #39ff14;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Main Title
st.title("Octolife's Data Extracting Toolkit")
# st.logo("logo.png", size = "large")

# Sidebar Menu
mode = st.sidebar.radio(
    "Select Operation",
    [
        "Croma",
        "VijaySales",
        "Flipkart",
        "BEE Star Label"
    ]
)

# Welcome Screen
if mode == "Croma":
    st.subheader("Extract AC Data from Croma's website")
    st.caption(
        "This tool extracts Title, Brand, Model No, Capacity, BEE rating, ISEER rating, Price, Customer Rating, Number of Reviews, Cooling Power, Air Flow and Product Link")
    st.divider()
    SEARCH_FOR = st.text_input("Which product do you want to scrape?", placeholder="Split AC")
    if st.button("Start Extracting"):
        try:
            # Setup WebDriver
            options = webdriver.ChromeOptions()
            options.add_argument('--disable-gpu')
            options.add_argument("--window-size=1920,1080")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--no-sandbox")
            driver = webdriver.Chrome(options=options)
            driver.get("https://www.croma.com")
            counter = 0

            # Search for "Split AC"
            searchbar = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, "searchV2"))
            )
            searchbar.clear()
            searchbar.send_keys(SEARCH_FOR)
            searchbar.send_keys(Keys.RETURN)

            # Wait for results to load
            WebDriverWait(driver, 15).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, "h3.product-title a"))
            )

            # Auto-click "View More" until gone
            while True:
                try:
                    view_more_button = WebDriverWait(driver, 5).until(
                        EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'View More')]"))
                    )
                    driver.execute_script("arguments[0].click();", view_more_button)
                    time.sleep(1)
                except:
                    break

            # Collect product links
            product_links = driver.find_elements(By.CSS_SELECTOR, "h3.product-title a")
            links_list = [link.get_attribute("href") for link in product_links]
            # print(f"Total products found: {len(links_list)}")

            # Set up CSV file
            filename = "Croma_Data.csv"
            COLUMNS = ["Title", "Brand", "Model No", "Capacity", "BEE Star", "ISEER", "Price", "Review",
                       "No of Reviews",
                       "Cooling", "Air Flow", "Product Link"]

            # Create CSV with headers only if not already present
            with open(filename, mode="w", newline='', encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(COLUMNS)

            #Time Calculator
            total_links = len(links_list)
            st.write(f"🔍 Found **{total_links}** products. Starting detailed scrape...")
            progress_bar = st.progress(0)
            status_text = st.empty()
            start_time = time.time()

            # Loop through each product link
            for i in range(len(links_list)):
                new_link = links_list[i]
                # print("Opening:", new_link)
                counter += 1

                try:
                    driver.get(new_link)
                    elapsed = time.time() - start_time
                    avg_time = elapsed / (i + 1)
                    remaining = avg_time * (total_links - (i + 1))
                    progress = int(((i + 1) / total_links) * 100)

                    status_text.markdown(f"⏳ Estimated time left: **{int(remaining)} sec**")
                    progress_bar.progress(progress)

                    WebDriverWait(driver, 25).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "h1.pd-title.pd-title-normal"))
                    )

                    # print("✅ Product page loaded.")
                    # print(f"📦 Product Number {counter}")

                except TimeoutException:
                    # print(f"⚠️ Skipping product {counter} due to loading timeout.\n")
                    continue

                driver.execute_script("window.scrollBy(0, 1500);")
                time.sleep(1)

                try:
                    view_more_buttons = WebDriverWait(driver, 5).until(
                        EC.presence_of_all_elements_located((By.CLASS_NAME, "btn-viewmore-click"))
                    )
                    driver.execute_script("arguments[0].click();", view_more_buttons[0])
                    time.sleep(1)

                except Exception as e:
                    st.warning(f"⚠️ 'View More' button not found or clickable: {e}")

                titles = driver.find_elements(By.CSS_SELECTOR, "li.cp-specification-spec-title > h4")
                values = driver.find_elements(By.CSS_SELECTOR, "li.cp-specification-spec-details")

                if not titles or not values:
                    st.warning("❌ Specs not found.")
                else:
                    # print(f"✅ Found {len(titles)} spec titles and {len(values)} values.")

                    specs = {t.text.strip(): v.text.strip() for t, v in zip(titles, values)}

                # Main Product Details
                try:
                    # Wait for both title and price to appear (max 15 seconds each)
                    WebDriverWait(driver, 15).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "h1.pd-title.pd-title-normal"))
                    )
                    WebDriverWait(driver, 15).until(
                        EC.presence_of_element_located((By.ID, "pdp-product-price"))
                    )

                    # Extract title
                    item_title = driver.find_element(By.CSS_SELECTOR, "h1.pd-title.pd-title-normal").text.strip()

                    # Extract price — sometimes it's in a <span> inside the div
                    price_block = driver.find_element(By.ID, "pdp-product-price")
                    try:
                        price_span = price_block.find_element(By.TAG_NAME, "span")
                        item_price = price_span.text.strip() or price_block.text.strip()
                    except:
                        item_price = price_block.text.removeprefix('₹').strip()

                    # Extract review
                    try:
                        item_review = driver.find_element(By.CSS_SELECTOR,
                                                          "span[style*='color: rgb(18, 218, 168)']").text.strip()
                        item_num_review = driver.find_element(By.CSS_SELECTOR, "a.pr-review.review-text").text.strip()
                    except:
                        item_review = "NA"
                        item_num_review = "NA"

                except Exception as e:
                    st.warning(f"⚠️ Error loading title/price/review: {e}")
                    item_title = "NA"
                    item_price = "NA"
                    item_review = "NA"
                    item_num_review = "NA"

                item_brand = specs.get('Brand', 'Not Available')
                item_model = specs.get('Model Number', 'Not Available')
                item_capacity = specs.get('Air Conditioner Capacity', 'Not Available')
                item_BEEstar = specs.get('Energy Efficiency (Star Rating)', 'Not Available')
                item_ISSER = specs.get('Indian Seasonal Energy Efficiency Ratio (ISEER)', 'Not Available')
                item_cooling = specs.get('Cooling Capacity', 'Not Available')
                item_airflow = specs.get('Air Flow Volume', 'Not Available')

                # Write row to CSV immediately
                with open(filename, mode="a", newline='', encoding="utf-8") as f:
                    writer = csv.writer(f)
                    writer.writerow([
                        item_title,
                        item_brand,
                        item_model,
                        item_capacity,
                        item_BEEstar,
                        item_ISSER,
                        item_price,
                        item_review,
                        item_num_review,
                        item_cooling,
                        item_airflow,
                        new_link
                    ])

            # Clean exit
            driver.quit()
            progress_bar.empty()
            status_text.success("✅ Scraping complete. Data saved to Flipkart_Data.csv")

            # Preview CSV
            df = pd.read_csv(filename)
            st.write("📄 Preview of Extracted Data:")
            st.dataframe(df.head(10), use_container_width=True)

            # Download Button
            with open(filename, "rb") as f:
                st.download_button(
                    label="⬇️ Download CSV",
                    data=f,
                    file_name=filename,
                    mime="text/csv"
                )

        except Exception as e:
            st.error(f"Error occurred: {e}")


# MODULE 2
if mode == "VijaySales":
    st.subheader("Extract AC Data from Vijay Sales website")
    st.caption(
        "This tool extracts Title, Brand, Model No, Capacity, BEE rating, ISEER rating, Price, Customer Rating, Number of Reviews, Number of Buyers, Listing Date,  Cooling Power and Product Link")
    st.divider()
    SEARCH_FOR = st.text_input("Which product do you want to scrape?", placeholder="Split AC")
    if st.button("Start Extracting"):
        try:
            def close_popup():
                # Close or hide popup if it appears
                try:
                    popup = driver.find_element(By.ID, "notify-visitors-confirm-popup-box")
                    if popup.is_displayed():
                        driver.execute_script("""
                                   let popup = document.getElementById('notify-visitors-confirm-popup-box');
                                   if (popup) popup.style.display = 'none';
                               """)
                        # print("✅ Closed blocking popup")
                        time.sleep(0.5)
                except:
                    pass  # Popup not found or already closed


            def specification_extraction():
                spec_dict = {}
                try:
                    WebDriverWait(driver, 5).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "ul li span.panel-list-key"))
                    )
                    spec_items = driver.find_elements(By.CSS_SELECTOR, "ul li")
                    for item in spec_items:
                        try:
                            key = item.find_element(By.CSS_SELECTOR, "span.panel-list-key").text.strip()
                            value = item.find_element(By.CSS_SELECTOR, "span.panel-list-value").text.strip()
                            spec_dict[key] = value
                        except NoSuchElementException:
                            continue
                except Exception as e:
                    pass
                    # print("❌ Specs section not found initially:", e)
                return spec_dict


            # STEP 1: Setup WebDriver
            driver = webdriver.Chrome()
            driver.get(f"https://www.vijaysales.com/search-listing?q={SEARCH_FOR}")
            counter = 0

            # Wait for results page to load
            WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "a.product-card__link"))
            )

            # print("✅ Search results loaded.")

            # Step 2: Initiate Scrapping
            links_list = []

            while True:
                # Wait for initial load
                WebDriverWait(driver, 15).until(
                    EC.presence_of_all_elements_located((By.CSS_SELECTOR, "a.product-card__link"))
                )

                products = driver.find_elements(By.CSS_SELECTOR, "a.product-card__link")
                for item in products:
                    link = item.get_attribute("href")
                    links_list.append(link)

                # Check if "NEXT" button is available
                try:
                    close_popup()
                    # Find and click the "Next" button
                    next_btn = WebDriverWait(driver, 5).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, "a.arrow-btn[jsname='nextBtn']"))
                    )
                    is_disabled = next_btn.get_attribute("disabled")
                    WebDriverWait(driver, 15).until(
                        EC.presence_of_all_elements_located((By.CSS_SELECTOR, "a.product-card__link"))
                    )
                    if is_disabled:
                        # print("🔚 Reached last page.")
                        break
                    else:
                        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", next_btn)
                        time.sleep(2)
                        next_btn.click()
                        time.sleep(5)  # Let the next page load
                except Exception as e:
                    # print(f"❌ Could not click next: {e}")
                    break

            # STEP 3: Set up CSV file
            filename = "VS_Data.csv"
            COLUMNS = ["Title", "Brand", "Model No", "Capacity", "BEE Star", "ISEER", "Price", "Review",
                       "No of Reviews",
                       "Cooling", "Num Buyers", "Listing Date", "Product Link"]

            # Create CSV with headers only if not already present
            with open(filename, mode="w", newline='', encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(COLUMNS)

            # Time Calculator
            start_time = time.time()
            progress_bar = st.progress(0)
            status_text = st.empty()
            total_links = len(links_list)
            count = 0
            # Loop through each product link
            for i in range(len(links_list)):
                new_link = links_list[i]
                # print("Opening:", new_link)
                counter += 1
                try:
                    driver.get(new_link)
                    close_popup()
                    WebDriverWait(driver, 25).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "h1.productFullDetail__productName"))
                    ) or WebDriverWait(driver, 15).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "p.product__tags--label.label-two"))
                    )
                    # print("✅ Product page loaded.")
                    # print(f"📦 Product Number {counter}")

                except TimeoutException:
                    # print(f"⚠️ Skipping product {counter} due to loading timeout.\n")
                    continue

                # === Extract title ===
                try:
                    item_title = driver.find_element(By.CSS_SELECTOR, "h1.productFullDetail__productName").text.strip()
                except NoSuchElementException:
                    item_title = "NA"

                # == Num of Buyers == #
                try:
                    num_buyers = driver.find_element(By.CSS_SELECTOR, "p.product__tags--label.label-two").text
                except NoSuchElementException:
                    num_buyers = "NA"

                # === Extract price ===
                try:
                    item_price_elem = driver.find_element(By.CLASS_NAME, "product__price--price")
                    item_price = item_price_elem.get_attribute("data-final-price")
                    if item_price is None:
                        item_price = item_price_elem.text.strip().removeprefix("₹")
                except NoSuchElementException:
                    item_price = "NA"

                # === Extract review text ===
                try:
                    item_review = driver.find_element(By.CSS_SELECTOR, "p.product__title--stats").text.strip()
                except NoSuchElementException:
                    item_review = "NA"

                # === Extract number of reviews ===
                try:
                    item_no_of_reviews = driver.find_element(By.CSS_SELECTOR,
                                                             "p.product__title--stats span").text.strip()
                    item_no_of_reviews = item_no_of_reviews.removeprefix("(").removesuffix(")")
                except NoSuchElementException:
                    item_no_of_reviews = "NA"

                # == Extract Model No ==
                try:
                    item_no_of_reviews = driver.find_element(By.CSS_SELECTOR,
                                                             "p.product__title--stats span").text.strip()
                    item_no_of_reviews = item_no_of_reviews.removeprefix("(").removesuffix(")")
                except NoSuchElementException:
                    item_no_of_reviews = "NA"

                # == Extracting data from specifications ==
                scroll_attempts = 3
                scroll_height = 1200
                spec_dict = {}

                for attempt in range(scroll_attempts):
                    driver.execute_script(f"window.scrollBy(0, {scroll_height});")
                    time.sleep(1)  # Wait for content to load
                    spec_dict = specification_extraction()
                    if spec_dict:  # Break if we got the specs
                        break
                    scroll_height += 350

                if not spec_dict:
                    pass
                    # print("⚠️ Specs not found even after scrolling.")

                item_brand = spec_dict.get('BRAND', "NA")
                item_model = spec_dict.get('MODEL NAME', "NA")
                item_capacity = spec_dict.get('CAPACITY', "NA")
                item_star_rating = spec_dict.get('STAR RATING') or spec_dict.get('ENERGY RATING', 'NA')
                item_iseer = spec_dict.get('ISEER VALUE') or spec_dict.get('ISEER', 'NA')
                item_cooling = spec_dict.get('COOLING') or spec_dict.get('RATED COOLING CAPACITY', 'NA')
                item_date = spec_dict.get('ITEM AVAILABLE FROM DATE', "NA")

                # Write row to CSV immediately
                with open(filename, mode="a", newline='', encoding="utf-8") as f:
                    writer = csv.writer(f)
                    writer.writerow([
                        item_title,
                        item_brand,
                        item_model,
                        item_capacity,
                        item_star_rating,
                        item_iseer,
                        item_price,
                        item_review,
                        item_no_of_reviews,
                        item_cooling,
                        num_buyers,
                        item_date,
                        new_link
                    ])

                    # Time Update
                    count += 1
                    elapsed = time.time() - start_time
                    avg_time = elapsed / count if count else 0
                    remaining = avg_time * (total_links - count)
                    percent = min(int((count / total_links) * 100), 100)

                    progress_bar.progress(percent)
                    status_text.markdown(
                        f"⏳ Scraped {count}/{total_links} products. Estimated time left: **{int(remaining)} seconds**")

                # Random sleep
                # time.sleep(random.uniform(1.5, 3.5))

            # Clean exit
            driver.quit()
            progress_bar.empty()
            status_text.success("✅ Scraping complete!")

            # Preview CSV
            df = pd.read_csv(filename)
            st.write("📄 Preview of Extracted Data:")
            st.dataframe(df.head(10), use_container_width=True)

            # Download Button
            with open(filename, "rb") as f:
                st.download_button(
                    label="⬇️ Download CSV",
                    data=f,
                    file_name=filename,
                    mime="text/csv"
                )

        except Exception as e:
            st.error(f"Error occurred: {e}")

# MODULE 3
if mode == "Flipkart":
    st.subheader("Extract AC Data from Flipkart website")
    st.caption(
        "This tool extracts Title, Price, Customer Rating, Number of Reviews and Product Link. Clean the data in excel to extract brand, ton and BEE rating")
    st.divider()
    SEARCH_FOR = st.text_input("Which product do you want to scrape?", placeholder="Split AC")
    if st.button("Start Extracting"):
        try:
            # Setup WebDriver
            driver = webdriver.Chrome()
            SEARCH = "Split AC"
            driver.get(f"https://www.flipkart.com/search?q={SEARCH_FOR}")
            wait = WebDriverWait(driver, 15)


            # STEP 1: Close Login Popup
            def close_popup():
                try:
                    wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button._2KpZ6l._2doB4z"))).click()
                    # print("✅ Login popup closed.")
                except:
                    pass
                    #print("ℹ️ No login popup to close.")


            close_popup()

            # STEP 2: Get total number of pages
            try:
                total_pages_text = driver.find_element(By.CSS_SELECTOR, "div._1G0WLw span").text
                total_pages = int(total_pages_text.strip().split("of")[-1].strip())
            except:
                total_pages = 1  # fallback if pagination not found

            # print(f"🔢 Total pages: {total_pages}")

            # STEP 3: Prepare CSV
            filename = "FlipKart_Data.csv"
            COLUMNS = ["Title", "Price", "Star Rating", "Num Reviews", "Product Link"]
            with open(filename, mode="w", newline='', encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(COLUMNS)

            # Time Calculator
            start_time = time.time()
            progress_bar = st.progress(0)
            status_text = st.empty()

            # Estimate total number of products roughly (assume ~24 per page as a rough guess)
            estimated_total = total_pages * 24
            count = 0

            # STEP 4: Loop through each page
            for PAGE in range(1, total_pages + 1):
                # print(f"\n📄 Scraping page {PAGE}")
                driver.get(f"https://www.flipkart.com/search?q={SEARCH}&page={PAGE}")

                try:
                    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.tUxRFH")))
                except TimeoutException:
                    # print("❌ Page did not load properly. Skipping...")
                    continue

                products = driver.find_elements(By.CSS_SELECTOR, "div.tUxRFH")

                for product in products:
                    try:
                        title = product.find_element(By.CSS_SELECTOR, "div.KzDlHZ").text.strip()
                    except:
                        title = "NA"

                    try:
                        price = product.find_element(By.CSS_SELECTOR, "div.Nx9bqj._4b5DiR").text.replace("₹",
                                                                                                         "").replace(
                            ",",
                            "").strip()
                    except:
                        price = "NA"

                    try:
                        rating = product.find_element(By.CSS_SELECTOR, "div.XQDdHH").text.strip()
                    except:
                        rating = "NA"

                    try:
                        num_reviews = product.find_element(By.CSS_SELECTOR, "span.Wphh3N").text.strip()
                    except:
                        num_reviews = "NA"

                    try:
                        link = product.find_element(By.CSS_SELECTOR, "a.CGtC98").get_attribute("href")
                    except:
                        link = "NA"

                    # Time Update
                    count += 1
                    elapsed = time.time() - start_time
                    avg_time = elapsed / count if count else 0
                    remaining = avg_time * (estimated_total - count)
                    percent = min(int((count / estimated_total) * 100), 100)

                    # Update UI
                    progress_bar.progress(percent)
                    status_text.markdown(f"⏳ Scraped {count} items. Estimated time left: **{int(remaining)} seconds**")

                    with open(filename, mode="a", newline='', encoding="utf-8") as f:
                        writer = csv.writer(f)
                        writer.writerow([title, price, rating, num_reviews, link])

                    # time.sleep(random.uniform(0.3, 0.6))  # polite delay

            driver.quit()
            progress_bar.empty()
            status_text.success("✅ Scraping complete. Data saved to Flipkart_Data.csv")

            # Preview CSV
            df = pd.read_csv(filename)
            st.write("📄 Preview of Extracted Data:")
            st.dataframe(df.head(10), use_container_width=True)

            # Download Button
            with open(filename, "rb") as f:
                st.download_button(
                    label="⬇️ Download CSV",
                    data=f,
                    file_name=filename,
                    mime="text/csv"
                )

        except Exception as e:
            st.error(f"Error occurred: {e}")


# MODULE 4
if mode == "BEE Star Label":
    st.subheader("Extract AC Data from official BEE star label website by GOI")
    st.caption(
        "This tool extracts Title, Type, ISEER, Ton, Electricity Consumption and Rating Validity. Clean the data in excel to extract brand and BEE rating")
    st.divider()
    appliance_options = ('Room Air Conditioners (Variable Speed)', 'Light Commercial AC Variable Speed', 'Light Commercial Air Conditioners', 'Room Air Conditioners (Fixed Speed)')
    brand_options = ('Select All', 'PANASONIC', 'DAIKIN', 'LG', 'HAIER', 'SAMSUNG', 'BLUE STAR', 'MITSUBISHI', 'VOLTAS','GENERAL','GREE', 'wybor')
    SEARCH_FOR = st.selectbox("Select Appliance", options=appliance_options, placeholder='Room Air Conditioners (Variable Speed)')
    SEARCH_FOR_DICT = {'Room Air Conditioners (Variable Speed)': '179', 'Room Air Conditioners (Fixed Speed)': '1', 'Light Commercial AC Variable Speed': '1211', 'Light Commercial Air Conditioners': '1205'}
    SEARCH_FOR_BRAND = st.selectbox("Select Brand",options=brand_options, placeholder="Select All")
    if st.button("Start Extracting"):
        try:
            # Filters
            APPLIANCE_SEARCH = SEARCH_FOR_DICT[SEARCH_FOR]
            BRAND = SEARCH_FOR_BRAND
            AC_TYPE = "Select All"
            MODEL = "Select All"
            FAMILY_MODEL = "Select All"
            ISEER = "Select All"
            NMC_TON = "Select All"
            BEESTAR = "Select All"

            # Setup WebDriver
            driver = webdriver.Chrome()
            driver.get("https://www.beestarlabel.com/SearchCompare")
            counter = 0

            # STEP 3: Prepare CSV
            filename = "BEEstarlabel_Data.csv"
            COLUMNS = ["Title", "Type", "ISEER", "Ton", "Electricity Consumption (kWh/year)", "Valid Till Date"]
            with open(filename, mode="w", newline='', encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(COLUMNS)

            try:
                # Select from dropdown
                searchbar = WebDriverWait(driver, 20).until(
                    EC.presence_of_element_located((By.ID, "Equipment"))
                )
                select = Select(driver.find_element(By.ID, "Equipment"))
                select.select_by_value(APPLIANCE_SEARCH)
            except TimeoutException:
                st.warning("⏰ Equipment dropdown took too long to load. TRY AGAIN")
                driver.quit()
                exit()

            # Wait for filters to load
            try:
                WebDriverWait(driver, 20).until(
                    EC.presence_of_all_elements_located((By.CSS_SELECTOR, "ul.filter_listing"))
                )
            except TimeoutException:
                st.warning("⏰ Filters didn't load. TRY AGAIN")
                driver.quit()
                exit()

            # Auto-select filters
            try:
                Select(driver.find_element(By.ID, "brand")).select_by_visible_text(BRAND)
                Select(driver.find_element(By.ID, "type")).select_by_visible_text(AC_TYPE)
                Select(driver.find_element(By.ID, "model")).select_by_visible_text(MODEL)
                Select(driver.find_element(By.ID, "fModel")).select_by_visible_text(FAMILY_MODEL)
                Select(driver.find_element(By.ID, "Isser")).select_by_visible_text(ISEER)
                Select(driver.find_element(By.ID, "NMC")).select_by_visible_text(NMC_TON)
                Select(driver.find_element(By.ID, "starlabel")).select_by_visible_text(BEESTAR)
            except Exception as e:
                st.warning(f"⚠️ Error selecting filters: {e}. TRY AGAIN")
                driver.quit()
                exit()

            # Submit search
            try:
                submit_button = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.ID, "btnSearchresult"))
                )
                submit_button.send_keys(Keys.RETURN)
            except TimeoutException:
                st.warning("⏰ Submit button not found. TRY AGAIN")
                driver.quit()
                exit()

            status_text = st.empty()
            status_text.markdown(
                f"⏳ Please wait fetching products...."
            )

            # Wait for results
            try:
                products = WebDriverWait(driver, 300).until(
                    EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div.product-column"))
                )

            except TimeoutException:
                st.warning("⏰ Results page did not load in 300 seconds. TRY AGAIN")
                driver.quit()
                exit()

            # Timer setup
            start_time = time.time()
            progress_bar = st.progress(0)
            status_text = st.empty()
            total_products = len(products)
            count = 0

            # Loop through each product
            for product in products:
                try:
                    title = product.find_element(By.CSS_SELECTOR, "div.bg-navy-blue").text.strip()
                except:
                    title = "NA"

                try:
                    values = product.find_elements(By.CSS_SELECTOR, "div.product-body-content strong")
                    extracted = [v.text.strip() for v in values]

                    rac_type = extracted[0] if len(extracted) > 0 else "NA"
                    iseer_rating = extracted[1] if len(extracted) > 1 else "NA"
                    nmc_ton = extracted[2] if len(extracted) > 2 else "NA"
                    elec_consump = extracted[3] if len(extracted) > 3 else "NA"
                    validity = extracted[4] if len(extracted) > 4 else "NA"
                except:
                    rac_type = iseer_rating = nmc_ton = elec_consump = validity = "NA"

                with open(filename, mode="a", newline='', encoding="utf-8") as f:
                    writer = csv.writer(f)
                    writer.writerow([title, rac_type, iseer_rating, nmc_ton, elec_consump, validity])

                    # Time + progress update
                    count += 1
                    elapsed = time.time() - start_time
                    avg_time = elapsed / count if count else 0
                    remaining = avg_time * (total_products - count)
                    percent = min(int((count / total_products) * 100), 100)

                    progress_bar.progress(percent)
                    status_text.markdown(
                        f"⏳ Scraped {count}/{total_products} entries. Estimated time left: **{int(remaining)} seconds**"
                    )

            driver.quit()
            progress_bar.empty()
            status_text.success("✅ Scraping complete. Data saved to BEEstarlabel_Data.csv")

            # Preview CSV
            df = pd.read_csv(filename)
            st.write("📄 Preview of Extracted Data:")
            st.dataframe(df.head(10), use_container_width=True)

            # Download Button
            with open(filename, "rb") as f:
                st.download_button(
                    label="⬇️ Download CSV",
                    data=f,
                    file_name=filename,
                    mime="text/csv"
                )

        except Exception as e:
            st.error(f"Error occurred: {e}")