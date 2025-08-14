from robocorp.tasks import task
from robocorp import browser
from RPA.HTTP import HTTP
from RPA.Tables import Tables
from RPA.PDF import PDF
from RPA.Archive import Archive


@task
def order_robots_from_RobotSpareBin():
    """
    Orders robots from RobotSpareBin Industries Inc.
    Saves the order HTML receipt as a PDF file.
    Saves the screenshot of the ordered robot.
    Embeds the screenshot of the robot to the PDF receipt.
    Creates ZIP archive of the receipts and the images.
    """
    browser.configure(
        slowmo=10,
    )
    open_robot_order_website()
    close_annoying_modal()
    orders = get_orders()
    for item in orders:
        fill_the_form(item)
    archive_receipts()


def open_robot_order_website():
    browser.goto("https://robotsparebinindustries.com/#/robot-order")


def get_orders():
    http = HTTP()
    http.download(
        url="https://robotsparebinindustries.com/orders.csv",
        overwrite=True,
    )
    library = Tables()
    orders = library.read_table_from_csv(
        "orders.csv",
        header=True,
    )
    return orders


def close_annoying_modal():
    page = browser.page()
    page.click("button:text('OK')")


def fill_the_form(robot):
    page = browser.page()
    page.wait_for_load_state("networkidle")
    alert_buttons = page.query_selector("div.modal")

    if alert_buttons is not None:
        display_value = alert_buttons.evaluate(
            "el => window.getComputedStyle(el).display")
        if display_value == "none":
            pass
        else:
            print('Alert buttons found, closing the modal.')
            close_annoying_modal()

    page.select_option("#head", str(robot['Head']))
    page.check(f"input[type='radio'][value='{str(robot['Body'])}']")
    page.fill(
        "input[placeholder='Enter the part number for the legs']", str(robot['Legs']))
    page.fill("#address", str(robot['Address']))
    page.click("button:text('Preview')")
    page.click("button:text('Order')")

    alert_div = page.query_selector("div.alert-danger")
    while alert_div is not None:
        page.click("button:text('Order')")
        alert_div = page.query_selector("div.alert-danger")

    pdf = store_receipt_as_pdf(robot['Order number'])
    screenshot = screenshot_robot(robot['Order number'])
    embed_screenshot_to_receipt(screenshot, pdf)
    page.click("button:text('Order another robot')")


def store_receipt_as_pdf(order_number):
    pdf = PDF()
    page = browser.page()
    pdf_path = f"output/receipts/{order_number}.pdf"
    receipt_html = page.locator("#receipt").inner_html()
    pdf.html_to_pdf(
        receipt_html,
        f"output/receipts/{order_number}.pdf",
    )
    return pdf_path


def screenshot_robot(order_number):
    page = browser.page()
    page.wait_for_load_state("networkidle")

    # Locate the specific div
    element = page.query_selector("#robot-preview-image")
    screenshot_path = f"output/images/{order_number}.png"

    if element:
        element.screenshot(path=screenshot_path)
    else:
        raise Exception("Element #robot-preview-image not found")
    return screenshot_path


def embed_screenshot_to_receipt(screenshot, pdf_file):
    pdf = PDF()
    temp_pdf = "image.pdf"
    pdf.html_to_pdf(
        f'<img src="{screenshot}" style="max-width:100%; max-height:100vh;"/>',
        temp_pdf,
    )
    pdf.add_files_to_pdf([pdf_file, temp_pdf], pdf_file)


def archive_receipts():
    archive = Archive()
    archive.archive_folder_with_zip("output/receipts", "output/receipts.zip")
    print("Archive created successfully.")
